"""Command-line entry point for the ultrastar-song-import skill.

Stages write into a work folder outside the repository. `prepare` records the
inputs, `analyze` runs the whole local pipeline, and `render`, `check`, and
`publish` use only numpy and the standard library. ML stages cache their output;
pass --force to recompute one. Logs never contain lyric text.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
from pathlib import Path

from chart_core import (
    DEFAULT_BPM,
    MAX_BPM,
    ChartError,
    chart_file_name,
    chart_headers,
    chart_text,
    check_chart,
    digest,
    log,
    lyric_phrases,
    publish_draft,
    quantize_notes,
    read_json,
    write_json,
)
from ml_stages import align, crepe_pitch, measure_notes, pyin_pitch, separate

STAGE_OUTPUTS = {
    "separate": ("vocals.wav", "separation.json"),
    "align": ("alignment.json", "alignment-homophones.json", "phonetic-emissions.npz",
              "recognition-check.json"),
    "pitch": ("pitch.npz",),
    "crepe": ("pitch-crepe.npz",),
}
DRAFT_LIMITATIONS = [
    "Not manually listened or fully corrected",
    "Median pitch per character does not encode every melisma",
    "Freestyle notes lack reliable F0 or alignment and are not scored",
    "Low alignment confidence and pitch variation need review",
]


def require(path: Path, hint: str) -> Path:
    if not path.is_file():
        raise ChartError(f"Missing {path.name}; {hint}")
    return path


def read_source(work: Path) -> dict:
    return read_json(require(work / "source.json", "run prepare first"))


def clear_outputs(work: Path, stage: str) -> None:
    for name in STAGE_OUTPUTS[stage]:
        (work / name).unlink(missing_ok=True)


def run_ml(step) -> None:
    import torch

    torch.set_num_threads(max(1, min(6, os.cpu_count() or 1)))
    step()
    gc.collect()


def do_prepare(work: Path, audio: Path, video: Path | None, lyrics: Path, artist: str,
               title: str, skip_lines: int) -> None:
    for path in (audio, lyrics, video):
        if path is not None and not path.is_file():
            raise ChartError(f"Input file not found: {path.name}")
    identity = {
        "artist": artist,
        "title": title,
        "audio": str(audio.resolve()),
        "audio_sha256": digest(audio),
        "video": str(video.resolve()) if video else None,
        "video_sha256": digest(video) if video else None,
        "lyrics": str(lyrics.resolve()),
        "lyrics_sha256": digest(lyrics),
        "phrases": lyric_phrases(lyrics.read_text(encoding="utf-8-sig"), skip_lines),
    }
    work.mkdir(parents=True, exist_ok=True)
    manifest = work / "source.json"
    if manifest.exists():
        if read_json(manifest) != identity:
            raise ChartError("source.json describes different inputs; use a new work folder")
        log("Inputs match the existing source.json")
    else:
        write_json(manifest, identity)
    log(f"Recorded {len(identity['phrases'])} phrases")


def do_separate(work: Path, force: bool) -> None:
    source = read_source(work)
    if force:
        clear_outputs(work, "separate")
    run_ml(lambda: separate(work, Path(source["audio"])))


def do_align(work: Path, align_start: float | None, align_end: float | None,
             pool_accent_variants: bool, force: bool) -> None:
    if align_start is not None and align_end is not None and align_start >= align_end:
        raise ChartError("--align-start must be before --align-end")
    source = read_source(work)
    require(work / "vocals.wav", "run separate first")
    if force:
        clear_outputs(work, "align")
    run_ml(lambda: align(work, source["phrases"], (align_start, align_end), pool_accent_variants))


def do_pitch(work: Path, force: bool) -> None:
    require(work / "vocals.wav", "run separate first")
    if force:
        clear_outputs(work, "pitch")
    run_ml(lambda: pyin_pitch(work))


def do_crepe(work: Path, force: bool) -> None:
    require(work / "vocals.wav", "run separate first")
    if force:
        clear_outputs(work, "crepe")
    run_ml(lambda: crepe_pitch(work))


def choose_tracker(work: Path, pitch: str) -> str:
    if pitch == "auto":
        if (work / "pitch-crepe.npz").exists():
            return "pitch-crepe.npz"
        return require(work / "pitch.npz", "run the crepe or pyin stage first").name
    name = {"crepe": "pitch-crepe.npz", "pyin": "pitch.npz"}[pitch]
    return require(work / name, f"run the {pitch} stage first").name


def do_render(work: Path, bpm: float, review_freestyle: bool, pitch: str) -> dict:
    if not 0 < bpm <= MAX_BPM:
        raise ChartError(f"BPM must be above 0 and at most {MAX_BPM}")
    source = read_source(work)
    recognition = read_json(require(work / "recognition-check.json", "run align first"))
    alignment = read_json(require(work / "alignment.json", "run align first"))
    tracker = choose_tracker(work, pitch)
    chart_path = work / chart_file_name(source["artist"], source["title"])
    chart_path.unlink(missing_ok=True)
    (work / "review.json").unlink(missing_ok=True)

    measured, warnings = measure_notes(work, alignment, tracker, review_freestyle)
    notes, stats = quantize_notes(measured, bpm)
    total = len(notes)
    freestyle = sum(note["kind"] == "F" for note in notes)
    unmeasured = sum("no_reliable_pitch_freestyle" in item["issues"] for item in measured)
    low_confidence = sum("low_alignment_confidence" in item["issues"] for item in measured)
    failures = []
    if unmeasured > .2 * total:
        failures.append("more than 20% of notes lack reliable pitch")
    if review_freestyle:
        if freestyle > .4 * total:
            failures.append("more than 40% of notes are freestyle in review mode")
    elif low_confidence > .2 * total:
        failures.append("more than 20% of notes have low alignment confidence")

    report = {
        "status": "AI_DRAFT_REQUIRES_MANUAL_TIMING_AND_PITCH_REVIEW",
        "artist": source["artist"],
        "title": source["title"],
        "notes": total,
        "phrases": len(source["phrases"]),
        "scored_notes": total - freestyle,
        "freestyle_notes": freestyle,
        "low_alignment_confidence": low_confidence,
        "unmeasured_pitch_notes": unmeasured,
        "review_freestyle_mode": review_freestyle,
        "pitch_tracker": tracker,
        "bpm_timebase_not_musical_tempo": bpm,
        "maximum_time_quantization_seconds": stats["maximum_time_quantization_seconds"],
        "quantization": stats,
        "method": f"Local HDemucs vocals; Chinese Wav2Vec2 CTC pooled by Mandarin syllable; "
                  f"median F0 from {tracker}",
        "limitations": DRAFT_LIMITATIONS,
        "audio_sha256": source["audio_sha256"],
        "video_sha256": source.get("video_sha256"),
        "lyrics_sha256": source["lyrics_sha256"],
        "gate_failures": failures,
        "warnings": warnings,
    }
    write_json(work / "draft-notes.json", notes)
    write_json(work / "review.json", report)
    if failures:
        raise ChartError("Quality gate failed (" + "; ".join(failures) + "); no chart written; see review.json")

    text = chart_text(notes, chart_headers(source, bpm))
    summary = check_chart(text, source["phrases"], recognition["duration"])
    chart_path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    log(f"Draft written: {summary['notes']} notes, {summary['scored_notes']} scored, "
        f"{stats['pushed_notes']} pushed, {stats['forced_minimum_length_notes']} forced; "
        f"max start drift {stats['max_start_drift_seconds'] * 1000:.1f} ms")
    return {**summary, **stats}


def do_check(work: Path) -> dict:
    source = read_source(work)
    recognition = read_json(require(work / "recognition-check.json", "run align first"))
    chart = require(work / chart_file_name(source["artist"], source["title"]), "run render first")
    return check_chart(chart.read_bytes().decode("utf-8"), source["phrases"], recognition["duration"])


def cmd_prepare(args) -> None:
    do_prepare(Path(args.work), Path(args.audio), Path(args.video) if args.video else None,
               Path(args.lyrics), args.artist, args.title, args.skip_lines)


def cmd_separate(args) -> None:
    do_separate(Path(args.work), args.force)


def cmd_align(args) -> None:
    do_align(Path(args.work), args.align_start, args.align_end, args.pool_accent_variants, args.force)


def cmd_pitch(args) -> None:
    do_pitch(Path(args.work), args.force)


def cmd_crepe(args) -> None:
    do_crepe(Path(args.work), args.force)


def cmd_render(args) -> None:
    log(json.dumps(do_render(Path(args.work), args.bpm, args.review_freestyle, args.pitch),
                   ensure_ascii=False))


def cmd_check(args) -> None:
    log(json.dumps(do_check(Path(args.work)), ensure_ascii=False))


def cmd_publish(args) -> None:
    chart = publish_draft(Path(args.work), Path(args.library))
    log(f"Published draft chart to {chart.parent}")


def cmd_analyze(args) -> None:
    work = Path(args.work)
    do_separate(work, args.force)
    do_align(work, args.align_start, args.align_end, args.pool_accent_variants, args.force)
    if args.pitch == "crepe":
        do_crepe(work, args.force)
    else:
        do_pitch(work, args.force)
    log(json.dumps(do_render(work, args.bpm, args.review_freestyle, args.pitch),
                   ensure_ascii=False))


def add_alignment_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--align-start", type=float, default=None,
                        help="Seconds where the supplied lyrics begin (default: start of audio)")
    parser.add_argument("--align-end", type=float, default=None,
                        help="Seconds where the supplied lyrics end (default: end of audio)")
    parser.add_argument("--pool-accent-variants", action="store_true",
                        help="Pool zh/ch/sh with z/c/s and ng with n; use only for an accent-heavy singer")


def add_render_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bpm", type=float, default=DEFAULT_BPM,
                        help=f"Timebase BPM; the default {DEFAULT_BPM} is the validated value, max {MAX_BPM}")
    parser.add_argument("--review-freestyle", action="store_true",
                        help="Uncertain alignment becomes freestyle (never scored); at most 40%% freestyle")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an AI draft UltraStar chart from local media and supplied lyrics.")
    stages = parser.add_subparsers(dest="stage", required=True)

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = stages.add_parser(name, help=help_text)
        sub.add_argument("--work", required=True, help="Work folder outside the repository")
        return sub

    prepare = add("prepare", "Record inputs and lyric phrases; no analysis")
    prepare.add_argument("--audio", required=True, help="Local audio file (MP3 recommended)")
    prepare.add_argument("--video", help="Optional local video file for #VIDEO")
    prepare.add_argument("--lyrics", required=True, help="UTF-8 lyric text in singing order")
    prepare.add_argument("--artist", required=True)
    prepare.add_argument("--title", required=True)
    prepare.add_argument("--skip-lines", type=int, default=0, help="Leading header lines to ignore")
    prepare.set_defaults(run=cmd_prepare)

    for name, handler, text in (("separate", cmd_separate, "Separate vocals with HDemucs"),
                                ("pitch", cmd_pitch, "Estimate vocal F0 with pYIN"),
                                ("crepe", cmd_crepe, "Estimate vocal F0 with CREPE")):
        sub = add(name, text)
        sub.add_argument("--force", action="store_true", help="Recompute this stage's output")
        sub.set_defaults(run=handler)

    align_parser = add("align", "Align supplied characters with Chinese CTC emissions")
    align_parser.add_argument("--force", action="store_true", help="Recompute the alignment")
    add_alignment_options(align_parser)
    align_parser.set_defaults(run=cmd_align)

    render = add("render", "Build the draft chart from cached measurements")
    render.add_argument("--pitch", choices=("auto", "crepe", "pyin"), default="auto")
    add_render_options(render)
    render.set_defaults(run=cmd_render)

    check = add("check", "Validate the draft chart; prints counts only")
    check.set_defaults(run=cmd_check)

    publish = add("publish", "Copy the validated draft into the song library")
    publish.add_argument("--library", required=True, help="UltraStar song library folder")
    publish.set_defaults(run=cmd_publish)

    analyze = add("analyze", "Run separate, align, pitch, and render in order")
    analyze.add_argument("--force", action="store_true", help="Recompute ML stages")
    analyze.add_argument("--pitch", choices=("crepe", "pyin"), default="crepe")
    add_alignment_options(analyze)
    add_render_options(analyze)
    analyze.set_defaults(run=cmd_analyze)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.run(args)
    except (ChartError, FileExistsError, OSError, subprocess.CalledProcessError) as error:
        log(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
