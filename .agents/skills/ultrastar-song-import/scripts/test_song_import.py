"""CLI tests for song_import using synthetic fixtures. Lyric strings are invented placeholders."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import chart_core as core
import song_import as cli

try:
    import numpy as np
except ImportError:
    np = None

CHARS = "甲乙丙丁戊己"
PHRASES = ["甲乙丙", "丁戊己"]
PHRASE_OF = ["甲乙丙"] * 3 + ["丁戊己"] * 3
MIDIS = [60, 62, 64, 65, 67, 69]
DURATION = 5.0
CHAR_START = [0.5 + 0.6 * k for k in range(6)]
CHAR_END = [start + 0.5 for start in CHAR_START]


def has_lyric(text):
    return core.CJK_CHARACTER.search(text) is not None


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class ImportTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.work = root / "work"
        self.library = root / "library"
        self.audio = root / "song.mp3"
        self.lyrics = root / "lyrics.txt"
        self.audio.write_bytes(b"placeholder-audio")
        self.lyrics.write_text("\n".join(PHRASES) + "\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self):
        return run_cli("prepare", "--work", str(self.work), "--audio", str(self.audio),
                       "--lyrics", str(self.lyrics), "--artist", "Test", "--title", "Sample")

    def write_alignment(self, confidence=0.5):
        self.work.mkdir(parents=True, exist_ok=True)
        items = [{"text": CHARS[k], "phrase": PHRASE_OF[k], "start": CHAR_START[k],
                  "end": CHAR_END[k], "confidence": confidence} for k in range(6)]
        core.write_json(self.work / "alignment.json", items)
        core.write_json(self.work / "recognition-check.json", {"duration": DURATION})

    def write_pitch(self, name="pitch-crepe.npz"):
        self.work.mkdir(parents=True, exist_ok=True)
        times = np.arange(0, DURATION, 0.01)
        f0 = np.full(times.shape, np.nan)
        for k, midi in enumerate(MIDIS):
            inside = (times >= CHAR_START[k]) & (times < CHAR_END[k])
            f0[inside] = 440.0 * 2 ** ((midi - 69) / 12)
        voiced = np.isfinite(f0)
        np.savez(self.work / name, time=times, f0=f0, voiced=voiced,
                 probability=np.where(voiced, 0.9, 0.0), rms=np.full(times.shape, 0.1))


class PrepareTests(ImportTestCase):
    def test_records_phrases(self):
        code, _ = self.prepare()
        self.assertEqual(code, 0)
        source = core.read_json(self.work / "source.json")
        self.assertEqual(source["phrases"], PHRASES)

    def test_rejects_different_inputs_in_same_work_folder(self):
        self.prepare()
        self.lyrics.write_text("甲乙\n", encoding="utf-8")
        code, _ = self.prepare()
        self.assertEqual(code, 1)

    def test_rejects_missing_audio(self):
        code, _ = run_cli("prepare", "--work", str(self.work), "--audio", str(self.work / "missing.mp3"),
                          "--lyrics", str(self.lyrics), "--artist", "Test", "--title", "Sample")
        self.assertEqual(code, 1)


class StageGuardTests(ImportTestCase):
    def test_separate_needs_prepare(self):
        code, _ = run_cli("separate", "--work", str(self.work))
        self.assertEqual(code, 1)

    def test_align_needs_vocals(self):
        self.prepare()
        code, _ = run_cli("align", "--work", str(self.work))
        self.assertEqual(code, 1)

    def test_align_range_must_be_ordered(self):
        self.prepare()
        code, _ = run_cli("align", "--work", str(self.work), "--align-start", "5", "--align-end", "1")
        self.assertEqual(code, 1)


class TrackerTests(ImportTestCase):
    def touch(self, name):
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / name).write_bytes(b"x")

    def test_auto_prefers_crepe(self):
        self.touch("pitch.npz")
        self.touch("pitch-crepe.npz")
        self.assertEqual(cli.choose_tracker(self.work, "auto"), "pitch-crepe.npz")

    def test_auto_falls_back_to_pyin(self):
        self.touch("pitch.npz")
        self.assertEqual(cli.choose_tracker(self.work, "auto"), "pitch.npz")

    def test_auto_without_any_tracker_fails(self):
        self.work.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(core.ChartError):
            cli.choose_tracker(self.work, "auto")

    def test_explicit_missing_tracker_fails(self):
        self.touch("pitch.npz")
        with self.assertRaises(core.ChartError):
            cli.choose_tracker(self.work, "crepe")


@unittest.skipUnless(np is not None, "numpy is required for render tests")
class RenderTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.prepare()[0], 0)
        self.write_alignment()
        self.write_pitch()
        self.chart = self.work / "Test - Sample.txt"

    def test_render_writes_crlf_chart_and_keeps_lyrics_out_of_output(self):
        code, output = run_cli("render", "--work", str(self.work))
        self.assertEqual(code, 0, output)
        self.assertFalse(has_lyric(output))
        data = self.chart.read_bytes()
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))
        self.assertIn(b"#BPM:274", data)
        review = (self.work / "review.json").read_text(encoding="utf-8")
        self.assertFalse(has_lyric(review))
        self.assertEqual(json.loads(review)["gate_failures"], [])

    def test_check_then_publish_once(self):
        self.assertEqual(run_cli("render", "--work", str(self.work))[0], 0)
        code, output = run_cli("check", "--work", str(self.work))
        self.assertEqual(code, 0, output)
        self.assertFalse(has_lyric(output))
        code, output = run_cli("publish", "--work", str(self.work), "--library", str(self.library))
        self.assertEqual(code, 0, output)
        folder = self.library / "Test-Sample"
        self.assertTrue((folder / "Test - Sample.txt").is_file())
        self.assertTrue((folder / core.REVIEW_NAME).is_file())
        self.assertTrue((folder / "song.mp3").is_file())
        self.assertEqual(run_cli("publish", "--work", str(self.work), "--library", str(self.library))[0], 1)

    def test_gate_blocks_low_confidence_and_removes_stale_chart(self):
        self.chart.write_bytes(b"stale")
        self.write_alignment(confidence=0.0)
        code, output = run_cli("render", "--work", str(self.work))
        self.assertEqual(code, 1)
        self.assertFalse(self.chart.exists())
        self.assertFalse(has_lyric(output))
        review = json.loads((self.work / "review.json").read_text(encoding="utf-8"))
        self.assertTrue(review["gate_failures"])

    def test_rejects_bpm_outside_range(self):
        for bpm in ("0", "324", "1500"):
            code, _ = run_cli("render", "--work", str(self.work), "--bpm", bpm)
            self.assertEqual(code, 1, bpm)
            self.assertFalse(self.chart.exists())


if __name__ == "__main__":
    unittest.main()
