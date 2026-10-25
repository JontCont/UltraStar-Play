---
name: ultrastar-song-import
description: "Use when importing a local song into the UltraStar Play library, creating a draft TXT chart from local MP3/MP4 media plus user-supplied lyrics, or when the user gives a YouTube URL and a folder and asks to build a chart. 適用於 UltraStar 歌曲匯入、歌詞轉譜、草稿譜面生成與發布到本機歌庫。"
---

# UltraStar song import

Builds a draft UltraStar TXT chart from local audio, optional local video, and lyrics the user supplies, then validates it and publishes it to the local song library. The pipeline lives in `scripts\` next to this file.

## Policies (read first)

- **YouTube is local-only.** Never run yt-dlp, `scripts\download_media.py`, or any other downloader on a YouTube URL (`youtube.com`, `youtu.be`). When the user gives a YouTube URL, ask for the local MP3/MP4 path they downloaded. This is the approved `local_only` policy.
- **Direct non-YouTube links** may use `python scripts\download_media.py "<url>" -o "<work folder>"` from the repo root. If it fails, report the error. Do not switch to another downloader.
- **Rights.** The user confirms they have rights to the audio and lyrics. The user pastes lyrics from a licensed source. Never scrape lyric sites (for example KKBOX) and never fetch or generate lyrics.
- **Lyric privacy.** Lyric text may exist only in the work folder and the destination library. Do not print lyric text in chat, logs, reports, tests, or committed files. Report counts and indices only.
- **Repo hygiene.** Work folders live outside the repo. Do not commit media, lyrics, work folders, or `__pycache__`. Do not hardcode user paths in committed files. Use the placeholders in this document.
- **No overwrites.** `publish` refuses any song folder that already contains a `.txt` or `AI-chart-review.json`. Never delete or replace a published chart to get around this.

## Inputs

Ask for anything missing. Use `ask_user` for structured choices.

| Input | Required | Notes |
|---|---|---|
| Audio path | yes | Local MP3 preferred. |
| Video path | no | Local MP4. Written to `#VIDEO`. |
| Lyrics | yes | Pasted by the user. UTF-8, singing order, one phrase per line. |
| Artist, title | yes | Exact strings for `#ARTIST` and `#TITLE`. Chinese names are allowed. |
| Skip lines | no | Leading header lines to ignore (`--skip-lines`). |
| Library | yes | Example: `%USERPROFILE%\Music\UltraStar Play`. |
| Work folder | yes | Outside the repo. Example: `%LOCALAPPDATA%\UltraStarSongImport\<artist>-<title>`. |

Lyrics handling:
- Save the pasted lyrics to `<WORK>\lyrics.txt` as UTF-8. Keep this file out of the repo.
- A line break starts a new phrase. Spaces inside a line split the phrase further, so remove stray spaces.
- Lyrics are taken in singing order. A repeated chorus must appear again wherever it is sung.
- Check the phrase count is plausible before the first run. Do not echo the text.

## Environment

- Run commands from the repo root with the project venv, `.venv\Scripts\python.exe`.
- Install ML dependencies only when an import fails: `.venv\Scripts\python.exe -m pip install -r .agents\skills\ultrastar-song-import\scripts\requirements-ml.txt`.
- `ffmpeg` must be on PATH. The `separate` step decodes audio with it.
- After changing the scripts, run the unit tests from the repo root: `.venv\Scripts\python.exe -m unittest discover -s .agents\skills\ultrastar-song-import\scripts -p "test_*.py"`. The expected result is 41 tests passing.

## Pipeline

`--work` is required on every stage. Each stage reads the cached output of the previous one and skips recomputation unless `--force` is given.

`<CLI>` below means `.venv\Scripts\python.exe .agents\skills\ultrastar-song-import\scripts\song_import.py`.

```
<CLI> prepare --work <WORK> --audio <AUDIO> [--video <VIDEO>] --lyrics <WORK>\lyrics.txt --artist <ARTIST> --title <TITLE> [--skip-lines N]
<CLI> separate --work <WORK>
<CLI> align --work <WORK> [--align-start S] [--align-end E] [--pool-accent-variants]
<CLI> crepe --work <WORK>          (or: <CLI> pitch --work <WORK>)
<CLI> render --work <WORK> [--pitch auto|crepe|pyin] [--bpm 274] [--review-freestyle]
<CLI> check --work <WORK>
<CLI> publish --work <WORK> --library <LIBRARY>
```

1. **prepare** records inputs and lyric phrases. It runs no analysis.
2. **separate** isolates vocals with HDemucs.
3. **align** matches lyric characters to the Chinese CTC model's emissions. It writes `alignment.json` and `recognition-check.json`.
   - `--align-start` and `--align-end` (seconds, start before end) bound the singing region. Use them when intro or outro audio confuses the alignment. The defaults are the start and end of the audio.
   - `--pool-accent-variants` merges zh/ch/sh with z/c/s and ng with n. Use it only for an accent-heavy singer.
4. **Pitch tracker.** Choose one:
   - `crepe` (CREPE via torchcrepe, writes `pitch-crepe.npz`). The default in `analyze`.
   - `pitch` (pYIN, writes `pitch.npz`).
5. **render** builds the draft chart. `--pitch auto` (default) prefers `pitch-crepe.npz` and falls back to `pitch.npz`.
   - `--bpm` is the timebase BPM. Default `274`, maximum `322`. See the BPM policy below.
   - `--review-freestyle` turns uncertain alignment into freestyle notes (`F`). Freestyle notes are never scored in-game. At most 40% of notes may be freestyle.
6. **check** validates the draft. It prints counts only.
7. **publish** copies the audio, the optional video, the chart, and `AI-chart-review.json` into a song folder under `<LIBRARY>` named from the artist and title.

Shortcut: `analyze --work <WORK> [--pitch crepe|pyin] [--align-start S] [--align-end E] [--pool-accent-variants] [--bpm N] [--review-freestyle] [--force]` runs separate, align, the pitch tracker, and render in order. It does not run `check` or `publish`. Run those two separately.

Each draft contains the header `#EDITION:AI draft - needs review`.

## BPM policy

- Default `274`. This is the timebase that was validated in-game on the user's reference chart.
- Maximum `322` (`MAX_BPM`). The pitch analysis window is capped at 2048 samples. A note needs at least 3 periods of its pitch inside the window. Above about 322 BPM at 44.1 kHz, the window shrinks below 2048 and most notes score zero.
- Never pass the song's musical tempo as `--bpm`. At 1500 BPM every window falls to 256 samples, and in-game scores were zero. This was confirmed on three songs.

## Quality gates

`render` fails without writing a chart when any of these hold. It still writes `review.json` and `draft-notes.json` to the work folder.
- More than 20% of notes have no measured pitch.
- More than 20% of notes have low alignment confidence and `--review-freestyle` is not set.
- With `--review-freestyle`, more than 40% of notes are freestyle.

If the gate fails:
1. Narrow `--align-start` and `--align-end` to the singing region.
2. Try the other pitch tracker (`crepe` or `pitch`).
3. Use `--pool-accent-variants` only if the singer is accent-heavy.
4. Use `--review-freestyle` only when the user agrees to review and fix freestyle notes in-game.

Do not lower the gate thresholds to get a chart through.

## Reporting

After `render` and `check`, report only these values:
- note count, scored note count
- pushed notes and forced minimum-length notes
- maximum start drift in milliseconds
- gate result
- library folder path

Do not report lyric text.

After `publish`, ask the user to play-test the song in-game, starting on Easy. Check timing, pitch, and whether every note scores. A draft is not verified until the user has played it. If a song scores zero, check the BPM first.

## Known limits

- The ML stages (`separate`, `align`, `pitch`, `crepe`) have not been run end to end on new audio. The measurement, quantization, render gate, and publish steps match the original pipeline on three cached songs. Update this section after the first full run on a new song.
- Note starts are quantized to the timebase beat, so the error is up to half a beat. At 274 BPM that is about 27 ms.
- Sentence breaks come only from line breaks in the lyrics file.

## Troubleshooting

- `ffmpeg` not found: `separate` fails. Install ffmpeg or add it to PATH.
- "run ... first" error: a stage ran out of order. Run the stage the message names.
- "Source media changed since analysis": rerun `prepare` and the stages after it.
- `publish` refuses an existing folder: ask the user which folder to use. Never overwrite.
- ML import errors: install `requirements-ml.txt` into `.venv` as shown above.
- Before committing, delete `__pycache__` folders under `scripts\`.
