"""CLI tests for song_import using synthetic fixtures. Lyric strings are invented placeholders."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

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
        self.root = root
        self.work = root / "work"
        self.library = root / "library"
        self.library.mkdir()
        self.audio = root / "song.mp3"
        self.lyrics = root / "lyrics.txt"
        self.audio.write_bytes(b"placeholder-audio")
        self.lyrics.write_text("\n".join(PHRASES) + "\n", encoding="utf-8")
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("ULTRASTAR_LIBRARY", None)
        os.environ.pop("ULTRASTAR_WORK_ROOT", None)
        self.use_settings({})

    def tearDown(self):
        self.temp.cleanup()

    def use_settings(self, values):
        patcher = mock.patch.object(cli, "read_env_file", lambda: dict(values))
        patcher.start()
        self.addCleanup(patcher.stop)

    def prepare(self):
        return run_cli("prepare", "--work", str(self.work), "--audio", str(self.audio),
                       "--lyrics", str(self.lyrics), "--artist", "Test", "--title", "Sample")

    def write_alignment(self, confidence=0.5, work=None):
        work = work or self.work
        work.mkdir(parents=True, exist_ok=True)
        items = [{"text": CHARS[k], "phrase": PHRASE_OF[k], "start": CHAR_START[k],
                  "end": CHAR_END[k], "confidence": confidence} for k in range(6)]
        core.write_json(work / "alignment.json", items)
        core.write_json(work / "recognition-check.json", {"duration": DURATION})

    def write_pitch(self, name="pitch-crepe.npz", work=None):
        work = work or self.work
        work.mkdir(parents=True, exist_ok=True)
        times = np.arange(0, DURATION, 0.01)
        f0 = np.full(times.shape, np.nan)
        for k, midi in enumerate(MIDIS):
            inside = (times >= CHAR_START[k]) & (times < CHAR_END[k])
            f0[inside] = 440.0 * 2 ** ((midi - 69) / 12)
        voiced = np.isfinite(f0)
        np.savez(work / name, time=times, f0=f0, voiced=voiced,
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

    def test_publish_uses_library_from_settings(self):
        self.assertEqual(run_cli("render", "--work", str(self.work))[0], 0)
        self.use_settings({"ULTRASTAR_LIBRARY": str(self.library)})
        code, output = run_cli("publish", "--work", str(self.work))
        self.assertEqual(code, 0, output)
        self.assertTrue((self.library / "Test-Sample" / "Test - Sample.txt").is_file())

    def test_publish_without_any_library_fails(self):
        self.assertEqual(run_cli("render", "--work", str(self.work))[0], 0)
        code, output = run_cli("publish", "--work", str(self.work))
        self.assertEqual(code, 1)
        self.assertIn("No song library given", output)

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


@unittest.skipUnless(np is not None, "numpy is required for import tests")
class ImportTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.separate = mock.Mock(side_effect=lambda work, audio: (work / "vocals.wav").write_bytes(b"x"))
        self.align = mock.Mock(side_effect=lambda work, phrases, window, pool: self.write_alignment(work=work))
        self.crepe = mock.Mock(side_effect=lambda work: self.write_pitch("pitch-crepe.npz", work=work))
        self.workroot = self.root / "workroot"
        for name, fake in (("separate", self.separate), ("align", self.align),
                           ("crepe_pitch", self.crepe), ("run_ml", lambda step: step())):
            patcher = mock.patch.object(cli, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def import_song(self, *extra):
        return run_cli("import", "--artist", "Test", "--title", "Sample", "--audio", str(self.audio), *extra)

    def explicit(self):
        return ("--work", str(self.work), "--lyrics", str(self.lyrics), "--library", str(self.library))

    def test_uses_settings_defaults_for_work_and_library(self):
        self.use_settings({"ULTRASTAR_LIBRARY": str(self.library), "ULTRASTAR_WORK_ROOT": str(self.workroot)})
        work = self.workroot / "Test-Sample"
        work.mkdir(parents=True)
        (work / "lyrics.txt").write_text("\n".join(PHRASES) + "\n", encoding="utf-8")
        code, output = self.import_song()
        self.assertEqual(code, 0, output)
        self.assertFalse(has_lyric(output))
        self.assertEqual(core.read_json(work / "source.json")["phrases"], PHRASES)
        self.assertEqual(self.separate.call_count, 1)
        self.assertEqual(self.crepe.call_count, 1)
        self.assertTrue((self.library / "Test-Sample" / "Test - Sample.txt").is_file())

    def test_flags_override_settings(self):
        self.use_settings({"ULTRASTAR_LIBRARY": str(self.root / "missing"),
                           "ULTRASTAR_WORK_ROOT": str(self.workroot)})
        code, output = self.import_song(*self.explicit())
        self.assertEqual(code, 0, output)
        self.assertTrue((self.library / "Test-Sample" / "Test - Sample.txt").is_file())
        self.assertFalse(self.workroot.exists())

    def test_existing_destination_refused_before_ml(self):
        folder = self.library / "Test-Sample"
        folder.mkdir()
        (folder / "Test - Sample.txt").write_text("existing", encoding="utf-8")
        code, _ = self.import_song(*self.explicit())
        self.assertEqual(code, 1)
        self.assertEqual(self.separate.call_count, 0)
        self.assertEqual((folder / "Test - Sample.txt").read_text(encoding="utf-8"), "existing")

    def test_second_import_refused_before_ml(self):
        self.use_settings({"ULTRASTAR_LIBRARY": str(self.library), "ULTRASTAR_WORK_ROOT": str(self.workroot)})
        self.assertEqual(self.import_song("--lyrics", str(self.lyrics))[0], 0)
        self.separate.reset_mock()
        code, _ = self.import_song("--lyrics", str(self.lyrics))
        self.assertEqual(code, 1)
        self.assertEqual(self.separate.call_count, 0)

    def test_missing_library_setting_fails_before_ml(self):
        code, output = self.import_song("--work", str(self.work), "--lyrics", str(self.lyrics))
        self.assertEqual(code, 1)
        self.assertIn("No song library given", output)
        self.assertEqual(self.separate.call_count, 0)

    def test_library_folder_must_exist(self):
        self.use_settings({"ULTRASTAR_LIBRARY": str(self.root / "missing")})
        code, output = self.import_song("--work", str(self.work), "--lyrics", str(self.lyrics))
        self.assertEqual(code, 1)
        self.assertIn("not found", output)
        self.assertFalse((self.root / "missing").exists())
        self.assertEqual(self.separate.call_count, 0)

    def test_failed_gate_publishes_nothing(self):
        self.align.side_effect = lambda work, phrases, window, pool: self.write_alignment(confidence=0.0, work=work)
        code, output = self.import_song(*self.explicit())
        self.assertEqual(code, 1)
        self.assertFalse(has_lyric(output))
        self.assertFalse((self.library / "Test-Sample").exists())
        self.assertFalse((self.work / "Test - Sample.txt").exists())

    def youtube_import(self, *extra):
        return run_cli("import", "--artist", "Test", "--title", "Sample",
                       "--youtube", "https://youtu.be/Test123_abC", *self.explicit(), *extra)

    def download(self, url, output):
        output.mkdir(parents=True)
        audio, video = output / "Test123_abC.mp3", output / "Test123_abC.mp4"
        audio.write_bytes(b"synthetic audio")
        video.write_bytes(b"synthetic video")
        return audio, video

    def test_youtube_import_persists_supplied_lyrics_media_chart_and_report(self):
        with mock.patch.object(cli, "download_youtube", side_effect=self.download) as download:
            code, output = self.youtube_import()
        self.assertEqual(code, 0, output)
        download.assert_called_once()
        self.assertEqual((self.work / "lyrics.txt").read_bytes(), self.lyrics.read_bytes())
        folder = self.library / "Test-Sample"
        self.assertTrue((folder / "Test123_abC.mp3").is_file())
        self.assertTrue((folder / "Test123_abC.mp4").is_file())
        self.assertTrue((folder / core.REVIEW_NAME).is_file())
        chart = (folder / "Test - Sample.txt").read_text(encoding="utf-8")
        self.assertIn("#MP3:Test123_abC.mp3", chart)
        self.assertIn("#VIDEO:Test123_abC.mp4", chart)
        self.assertEqual(len(list(folder.glob("*.txt"))), 1)
        self.assertFalse(has_lyric(output))

    def test_missing_lyrics_stops_before_download(self):
        self.lyrics.unlink()
        with mock.patch.object(cli, "download_youtube") as download:
            code, output = self.youtube_import()
        self.assertEqual(code, 1)
        self.assertIn("lyrics", output)
        download.assert_not_called()

    def test_invalid_lyrics_stop_before_download(self):
        self.lyrics.write_text("not Chinese lyrics", encoding="utf-8")
        with mock.patch.object(cli, "download_youtube") as download:
            code, _ = self.youtube_import()
        self.assertEqual(code, 1)
        download.assert_not_called()

    def test_existing_destination_stops_before_download(self):
        folder = self.library / "Test-Sample"
        folder.mkdir()
        (folder / "existing.txt").write_bytes(b"existing")
        with mock.patch.object(cli, "download_youtube") as download:
            code, _ = self.youtube_import()
        self.assertEqual(code, 1)
        download.assert_not_called()

    def test_youtube_rejects_explicit_local_video(self):
        with mock.patch.object(cli, "download_youtube") as download:
            code, _ = self.youtube_import("--video", str(self.audio))
        self.assertEqual(code, 1)
        download.assert_not_called()

    def test_download_failure_stops_before_ml_and_publishing(self):
        with mock.patch.object(cli, "download_youtube", side_effect=cli.DownloadError("failed")):
            code, output = self.youtube_import()
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", output)
        self.separate.assert_not_called()
        self.assertFalse((self.library / "Test-Sample").exists())

    def test_failed_gate_then_retry_reuses_verified_media(self):
        self.align.side_effect = lambda work, phrases, window, pool: self.write_alignment(confidence=0.0, work=work)
        with mock.patch.object(cli, "download_youtube", side_effect=self.download) as download:
            self.assertEqual(self.youtube_import()[0], 1)
            self.assertFalse((self.library / "Test-Sample").exists())
            self.align.side_effect = lambda work, phrases, window, pool: self.write_alignment(work=work)
            code, output = self.youtube_import("--force")
            self.assertEqual(code, 0, output)
            self.assertEqual(download.call_count, 1)
        self.assertTrue((self.library / "Test-Sample" / "Test - Sample.txt").is_file())

    def test_cache_rejects_other_video_and_changed_media(self):
        with mock.patch.object(cli, "download_youtube", side_effect=self.download):
            cli.youtube_inputs(self.work, "https://youtu.be/Test123_abC")
        with mock.patch.object(cli, "download_youtube") as download:
            for url in ("https://youtu.be/Other123_ab", "https://youtu.be/Test123_abC"):
                if "Test123" in url:
                    (self.work / "media" / "Test123_abC.mp3").write_bytes(b"changed")
                with self.subTest(url=url), self.assertRaises(core.ChartError):
                    cli.youtube_inputs(self.work, url)
            download.assert_not_called()

    def test_corrupt_download_manifest_reports_error(self):
        self.work.mkdir()
        for contents in ("{", "{}", "[]"):
            (self.work / "download.json").write_text(contents, encoding="utf-8")
            with self.subTest(contents=contents):
                code, output = self.youtube_import()
                self.assertEqual(code, 1)
                self.assertIn("download.json", output)

    def test_mismatched_saved_lyrics_stop_before_download(self):
        self.work.mkdir()
        (self.work / "lyrics.txt").write_text("庚辛壬癸\n", encoding="utf-8")
        with mock.patch.object(cli, "download_youtube") as download:
            code, _ = self.youtube_import()
        self.assertEqual(code, 1)
        download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
