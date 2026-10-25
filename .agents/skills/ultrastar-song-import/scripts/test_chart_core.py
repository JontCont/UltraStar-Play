"""Unit tests for chart_core. Lyric strings are invented placeholders."""

import json
import tempfile
import unittest
from pathlib import Path

import chart_core as core

HEADERS = ["#TITLE:Sample", "#ARTIST:Test", "#MP3:song.mp3", "#BPM:274", "#GAP:0"]
BODY = [": 0 2 0 甲", ": 2 2 2 乙", "- 4", ": 8 2 4 丙", ": 10 2 5 丁", ": 12 2 7 戊", ": 14 2 0 己"]
PHRASES = ["甲乙", "丙丁戊己"]
DURATION = 10.0


def build(body, headers=HEADERS, terminate=True):
    lines = headers + body + (["E"] if terminate else [])
    return "\n".join(lines) + "\n"


def has_lyric(text):
    return core.CJK_CHARACTER.search(text) is not None


class LyricPhraseTests(unittest.TestCase):
    def test_skips_header_lines(self):
        self.assertEqual(core.lyric_phrases("標題\n甲乙丙\n", skip_lines=1), ["甲乙丙"])

    def test_space_separated_groups_start_new_phrases(self):
        self.assertEqual(core.lyric_phrases("甲乙 丙丁"), ["甲乙", "丙丁"])

    def test_long_groups_are_chunked(self):
        self.assertEqual([len(p) for p in core.lyric_phrases("甲" * 30)], [14, 14, 2])

    def test_non_cjk_characters_are_dropped(self):
        self.assertEqual(core.lyric_phrases("甲a1,乙!"), ["甲乙"])

    def test_empty_lyrics_are_rejected(self):
        with self.assertRaises(core.ChartError):
            core.lyric_phrases("abc\n")


class PitchWindowTests(unittest.TestCase):
    def test_window_follows_beat_and_cap(self):
        self.assertEqual(core.pitch_window(274, 44100), 2048)
        self.assertEqual(core.pitch_window(274, 48000), 2048)
        self.assertEqual(core.pitch_window(322, 44100), 2048)
        self.assertEqual(core.pitch_window(324, 44100), 1024)
        self.assertEqual(core.pitch_window(1500, 44100), 256)

    def test_uncovered_low_pitches(self):
        self.assertEqual(core.uncovered_pitch_count([35, 36, 60], 274, 44100), 1)
        self.assertEqual(core.uncovered_pitch_count([36, 37, 38], 274, 48000), 2)


class QuantizeTests(unittest.TestCase):
    def setUp(self):
        self.step = core.beat_seconds(274)

    def test_overlaps_are_pushed_and_short_notes_get_minimum_length(self):
        measured = [
            {"text": "甲", "phrase": "甲乙", "kind": ":", "pitch": 0, "start": 0.0, "end": 0.2},
            {"text": "乙", "phrase": "甲乙", "kind": ":", "pitch": 2, "start": 0.05, "end": 0.12},
        ]
        notes, stats = core.quantize_notes(measured, 274)
        self.assertEqual(notes[1]["beat"], 4)
        self.assertEqual(notes[1]["length"], 1)
        self.assertEqual(stats["pushed_notes"], 1)
        self.assertEqual(stats["forced_minimum_length_notes"], 1)

    def test_drift_stays_within_half_a_beat_without_pushes(self):
        measured = []
        for k in range(10):
            start = (2 * k + 0.4) * self.step
            measured.append({"text": "甲", "phrase": "甲", "kind": ":", "pitch": 0,
                             "start": start, "end": start + self.step})
        notes, stats = core.quantize_notes(measured, 274)
        self.assertEqual(stats["pushed_notes"], 0)
        self.assertEqual(stats["forced_minimum_length_notes"], 0)
        self.assertLessEqual(stats["max_start_drift_seconds"], self.step / 2 + 1e-9)
        self.assertEqual([note["beat"] for note in notes], [2 * k for k in range(10)])

    def test_quantized_notes_pass_the_checker(self):
        layout = [("甲", "甲乙", 0, 2, 0), ("乙", "甲乙", 2, 2, 2), ("丙", "丙丁戊己", 8, 2, 4),
                  ("丁", "丙丁戊己", 10, 2, 5), ("戊", "丙丁戊己", 12, 2, 7), ("己", "丙丁戊己", 14, 2, 0)]
        measured = [{"text": text, "phrase": phrase, "kind": ":", "pitch": pitch,
                     "start": beat * self.step, "end": (beat + length) * self.step}
                    for text, phrase, beat, length, pitch in layout]
        notes, _ = core.quantize_notes(measured, 274)
        source = {"title": "Sample", "artist": "Test", "audio": "C:/work/song.mp3", "video": None}
        text = core.chart_text(notes, core.chart_headers(source, 274))
        summary = core.check_chart(text, PHRASES, DURATION)
        self.assertEqual(summary["notes"], 6)
        self.assertEqual(summary["distinct_pitches"], 5)
        self.assertIn("- 4\n", text)
        self.assertIn("#MP3:song.mp3", text)


class CheckChartTests(unittest.TestCase):
    def assertRejects(self, text, phrases=PHRASES, duration=DURATION, expected=None):
        with self.assertRaises(core.ChartError) as context:
            core.check_chart(text, phrases, duration)
        self.assertFalse(has_lyric(str(context.exception)))
        if expected is not None:
            self.assertIn(expected, str(context.exception))

    def test_accepts_valid_chart(self):
        summary = core.check_chart(build(BODY), PHRASES, DURATION)
        self.assertEqual(summary["notes"], 6)
        self.assertEqual(summary["scored_notes"], 6)
        self.assertEqual(summary["pitch_windows"], {"44100": 2048, "48000": 2048})

    def test_rejects_overlap(self):
        body = [": 0 2 0 甲", ": 1 2 2 乙"] + BODY[2:]
        self.assertRejects(build(body), expected="Overlapping")

    def test_rejects_lyric_mismatch(self):
        self.assertRejects(build(BODY), phrases=["甲乙", "丙丁戊庚"], expected="lyric sequence")

    def test_rejects_constant_pitch(self):
        body = [": 0 2 0 甲", ": 2 2 0 乙", "- 4", ": 8 2 0 丙", ": 10 2 0 丁", ": 12 2 0 戊", ": 14 2 0 己"]
        self.assertRejects(build(body), expected="distinct")

    def test_rejects_bpm_above_cap(self):
        self.assertRejects(build(BODY, headers=[h.replace("274", "324") for h in HEADERS]), expected="BPM")

    def test_rejects_draft_bpm_1500(self):
        self.assertRejects(build(BODY, headers=[h.replace("274", "1500") for h in HEADERS]), expected="BPM")

    def test_rejects_low_pitch_that_48k_cannot_cover(self):
        body = BODY[:-1] + [": 14 2 -24 己"]
        self.assertRejects(build(body), expected="fewer than 3 periods")

    def test_rejects_missing_end_marker(self):
        self.assertRejects(build(BODY, terminate=False), expected="end with E")

    def test_rejects_break_inside_a_note(self):
        body = [": 0 2 0 甲", ": 2 2 2 乙", "- 3"] + BODY[3:]
        self.assertRejects(build(body), expected="out of place")

    def test_rejects_chart_running_past_audio(self):
        self.assertRejects(build(BODY), duration=0.5, expected="past the end")

    def test_rejects_empty_note(self):
        body = [": 0 0 0 甲"] + BODY[1:]
        self.assertRejects(build(body), expected="Empty note")

    def test_rejects_pitch_outside_range(self):
        body = BODY[:-1] + [": 14 2 25 己"]
        self.assertRejects(build(body), expected="Pitch outside range")

    def test_rejects_unrecognized_line(self):
        body = BODY[:2] + ["X 1 2"] + BODY[2:]
        self.assertRejects(build(body), expected="Unrecognized")


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.work = root / "work"
        self.library = root / "library"
        self.work.mkdir()
        self.library.mkdir()
        self.audio = root / "song.mp3"
        self.audio.write_bytes(b"placeholder-audio")
        source = {"artist": "Test", "title": "Sample", "audio": str(self.audio),
                  "audio_sha256": core.digest(self.audio), "video": None, "video_sha256": None,
                  "phrases": PHRASES}
        core.write_json(self.work / "source.json", source)
        core.write_json(self.work / "recognition-check.json", {"duration": DURATION})
        core.write_json(self.work / "review.json", {"status": "AI_DRAFT"})
        (self.work / "Test - Sample.txt").write_bytes(build(BODY).encode("utf-8"))

    def tearDown(self):
        self.temp.cleanup()

    def test_publishes_chart_media_and_review(self):
        chart = core.publish_draft(self.work, self.library)
        folder = self.library / "Test-Sample"
        self.assertEqual(chart, folder / "Test - Sample.txt")
        self.assertTrue((folder / "song.mp3").is_file())
        self.assertTrue((folder / core.REVIEW_NAME).is_file())
        self.assertTrue((self.work / "published.json").is_file())

    def test_refuses_second_publish(self):
        core.publish_draft(self.work, self.library)
        with self.assertRaises(FileExistsError):
            core.publish_draft(self.work, self.library)

    def test_refuses_missing_draft(self):
        (self.work / "Test - Sample.txt").unlink()
        with self.assertRaises(core.ChartError):
            core.publish_draft(self.work, self.library)

    def test_refuses_media_changed_after_analysis(self):
        self.audio.write_bytes(b"different-audio")
        with self.assertRaises(core.ChartError):
            core.publish_draft(self.work, self.library)
        self.assertFalse((self.library / "Test-Sample").exists())


if __name__ == "__main__":
    unittest.main()
