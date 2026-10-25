"""Chart logic for the UltraStar song import skill.

Standard library only, so the unit tests and the render/publish stages run
without the ML stack that the draft stage needs. Reports and logs carry counts
and indices, never lyric text.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import time
from pathlib import Path

DEFAULT_BPM = 274
MAX_BPM = 322
LONGEST_SINGABLE_SAMPLES = 2048
SAMPLE_RATES = (44100, 48000)
PHRASE_CHARACTERS = 14
MIN_DISTINCT_PITCHES = 5
PITCH_RANGE = (-24, 24)
DEFAULT_LANGUAGE = "Chinese (Traditional)"
REVIEW_NAME = "AI-chart-review.json"
CJK_CHARACTER = re.compile(r"[\u3400-\u9fff]")
NOTE_LINE = re.compile(r"^([:*F])\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s(.+)$")
BREAK_LINE = re.compile(r"^-\s+(-?\d+)(?:\s+-?\d+)?\s*$")


class ChartError(ValueError):
    """A draft that must not be written or published."""


def log(message: str) -> None:
    print(time.strftime("%H:%M:%S"), message, flush=True)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def safe_name(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip().rstrip(".")


def chart_file_name(artist: str, title: str) -> str:
    return f"{safe_name(artist)} - {safe_name(title)}.txt"


def lyric_phrases(text: str, skip_lines: int = 0) -> list[str]:
    # Every line and every space-separated group starts a new phrase. Only CJK
    # ideographs are kept, and long groups are split into fixed-size chunks.
    phrases: list[str] = []
    for line in text.splitlines()[skip_lines:]:
        for part in re.split(r"\s+", line.strip()):
            characters = "".join(CJK_CHARACTER.findall(part))
            phrases.extend(characters[i:i + PHRASE_CHARACTERS] for i in range(0, len(characters), PHRASE_CHARACTERS))
    phrases = [phrase for phrase in phrases if phrase]
    if not phrases:
        raise ChartError("No Chinese lyric characters remain after skipping header lines")
    return phrases


def beat_seconds(bpm: float) -> float:
    return 60.0 / (bpm * 4.0)


def _previous_power_of_two(value: int) -> int:
    power = 1
    while power * 2 <= value:
        power *= 2
    return power


def pitch_window(bpm: float, sample_rate: int) -> int:
    # Mirrors DywaAudioSamplesAnalyzer: the window is the previous power of two
    # of one beat in samples, capped at LONGEST_SINGABLE_SAMPLES.
    beat_samples = int(beat_seconds(bpm) * sample_rate)
    return min(_previous_power_of_two(beat_samples), LONGEST_SINGABLE_SAMPLES)


def midi_to_hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def uncovered_pitch_count(midis: list[int], bpm: float, sample_rate: int) -> int:
    window = pitch_window(bpm, sample_rate)
    return sum(midi_to_hz(midi) * window / sample_rate < 3.0 for midi in midis)


def _round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def quantize_notes(measured: list[dict], bpm: float) -> tuple[list[dict], dict]:
    step = beat_seconds(bpm)
    notes: list[dict] = []
    drifts: list[float] = []
    previous_end = pushed = forced = 0
    for item in measured:
        beat = max(0, _round_half_up(item["start"] / step))
        if beat < previous_end:
            beat = previous_end
            pushed += 1
        raw_end = _round_half_up(item["end"] / step)
        if raw_end <= beat:
            forced += 1
        end = max(beat + 1, raw_end)
        drifts.append(abs(beat * step - item["start"]))
        notes.append({"text": item["text"], "phrase": item["phrase"], "kind": item["kind"],
                      "pitch": item["pitch"], "beat": beat, "length": end - beat})
        previous_end = end
    stats = {
        "notes": len(notes),
        "pushed_notes": pushed,
        "forced_minimum_length_notes": forced,
        "max_start_drift_seconds": max(drifts) if drifts else 0.0,
        "mean_start_drift_seconds": sum(drifts) / len(drifts) if drifts else 0.0,
        "maximum_time_quantization_seconds": step / 2,
    }
    return notes, stats


def chart_headers(source: dict, bpm: float, language: str = DEFAULT_LANGUAGE) -> list[str]:
    headers = [f"#TITLE:{source['title']}", f"#ARTIST:{source['artist']}",
               f"#MP3:{Path(source['audio']).name}"]
    if source.get("video"):
        headers.append(f"#VIDEO:{Path(source['video']).name}")
    headers += ["#VIDEOGAP:0", f"#LANGUAGE:{language}", "#EDITION:AI draft - needs review",
                "#CREATOR:Local CPU analysis of user-provided lyrics", f"#BPM:{bpm:g}", "#GAP:0"]
    return headers


def chart_text(notes: list[dict], headers: list[str]) -> str:
    lines = list(headers)
    for index, note in enumerate(notes):
        lines.append(f"{note['kind']} {note['beat']} {note['length']} {note['pitch']} {note['text']}")
        following = notes[index + 1] if index + 1 < len(notes) else None
        if following is not None and following["phrase"] != note["phrase"]:
            lines.append(f"- {note['beat'] + note['length']}")
    lines.append("E")
    return "\n".join(lines) + "\n"


def check_chart(text: str, expected_phrases: list[str], duration_seconds: float) -> dict:
    # Error messages cite line numbers only, never the line content.
    lines = text.splitlines()
    header_bpm = None
    for line in lines:
        if line.startswith("#BPM:"):
            header_bpm = float(line.split(":", 1)[1])
    if header_bpm is None:
        raise ChartError("Missing #BPM header")
    if not 0 < header_bpm <= MAX_BPM:
        raise ChartError(f"BPM {header_bpm:g} is outside 0-{MAX_BPM}")
    if not lines or lines[-1] != "E":
        raise ChartError("Chart does not end with E")
    step = beat_seconds(header_bpm)
    notes: list[tuple[str, int, int, int]] = []
    lyric: list[str] = []
    previous_end = 0
    pending_break = None
    for number, line in enumerate(lines, 1):
        if line.startswith("#") or line == "E":
            continue
        match = NOTE_LINE.match(line)
        if match:
            kind, start_text, length_text, pitch_text, sung = match.groups()
            start, length, pitch = int(start_text), int(length_text), int(pitch_text)
            if start < previous_end:
                raise ChartError(f"Overlapping note at line {number}")
            if length <= 0:
                raise ChartError(f"Empty note at line {number}")
            if not PITCH_RANGE[0] <= pitch <= PITCH_RANGE[1]:
                raise ChartError(f"Pitch outside range at line {number}")
            if pending_break is not None and not previous_end <= pending_break <= start:
                raise ChartError(f"Sentence break before line {number} is out of place")
            pending_break = None
            notes.append((kind, start, length, pitch))
            lyric.append(sung)
            previous_end = start + length
            continue
        break_match = BREAK_LINE.match(line)
        if break_match:
            pending_break = int(break_match.group(1))
            continue
        raise ChartError(f"Unrecognized chart line {number}")
    if "".join(lyric) != "".join(expected_phrases):
        raise ChartError("Chart lyric sequence does not match the supplied lyrics")
    scored = [note for note in notes if note[0] != "F"]
    distinct = {pitch for _, _, _, pitch in scored}
    if len(distinct) < MIN_DISTINCT_PITCHES:
        raise ChartError("Too few distinct scored pitches; output may be constant")
    end_seconds = previous_end * step
    if end_seconds > duration_seconds:
        raise ChartError("Chart runs past the end of the source audio")
    midis = [pitch + 60 for _, _, _, pitch in scored]
    windows = {}
    for rate in SAMPLE_RATES:
        uncovered = uncovered_pitch_count(midis, header_bpm, rate)
        if uncovered:
            raise ChartError(f"{uncovered} scored notes span fewer than 3 periods of the "
                             f"{pitch_window(header_bpm, rate)}-sample pitch window at {rate} Hz")
        windows[str(rate)] = pitch_window(header_bpm, rate)
    return {"notes": len(notes), "scored_notes": len(scored), "freestyle_notes": len(notes) - len(scored),
            "distinct_pitches": len(distinct), "end_seconds": end_seconds, "pitch_windows": windows}


def destination_folder(library: Path, artist: str, title: str) -> Path:
    return library / safe_name(f"{artist}-{title}")


def assert_destination_free(folder: Path) -> None:
    if any(folder.glob("*.txt")) or (folder / REVIEW_NAME).exists():
        raise FileExistsError(f"{folder} already has a chart; refusing to overwrite or duplicate it")


def publish_draft(work: Path, library: Path) -> Path:
    source = read_json(work / "source.json")
    recognition = read_json(work / "recognition-check.json")
    chart_name = chart_file_name(source["artist"], source["title"])
    if not (work / chart_name).is_file() or not (work / "review.json").is_file():
        raise ChartError("Draft chart or review report is missing; run render first")
    chart_bytes = (work / chart_name).read_bytes()
    check_chart(chart_bytes.decode("utf-8"), source["phrases"], recognition["duration"])
    folder = destination_folder(library, source["artist"], source["title"])
    assert_destination_free(folder)
    media = [(Path(source["audio"]), source["audio_sha256"])]
    if source.get("video"):
        media.append((Path(source["video"]), source["video_sha256"]))
    for origin, expected in media:
        if digest(origin) != expected:
            raise ChartError("Source media changed since analysis; rerun draft")
    folder.mkdir(parents=True, exist_ok=True)
    for origin, expected in media:
        target = folder / origin.name
        if target.exists():
            if digest(target) != expected:
                raise FileExistsError(f"{target.name} already exists with different content")
            continue
        shutil.copyfile(origin, target)
    chart_path = folder / chart_name
    with chart_path.open("xb") as stream:
        stream.write(chart_bytes)
    with (folder / REVIEW_NAME).open("xb") as stream:
        stream.write((work / "review.json").read_bytes())
    write_json(work / "published.json", {"path": str(chart_path), "sha256": digest(chart_path)})
    return chart_path
