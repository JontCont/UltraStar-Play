"""YouTube routing and local synthetic-media tests; no external downloads."""

import contextlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import download_media as media

VIDEO_ID = "Test123_abC"
URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


class YoutubeUrlTests(unittest.TestCase):
    def test_normalizes_single_video_urls_and_discards_playlist_and_tracking(self):
        urls = (
            f"https://youtu.be/{VIDEO_ID}?si=tracking",
            f"https://music.youtube.com/watch?v={VIDEO_ID}&list=ignored",
            f"https://www.youtube.com/shorts/{VIDEO_ID}",
            f"https://youtube.com/live/{VIDEO_ID}",
            f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
            f"https://YOUTUBE.COM./watch?v={VIDEO_ID}&t=30",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(media.youtube_url(url), URL)

    def test_rejects_non_video_urls_without_network(self):
        for url in (
            "https://youtube.com/playlist?list=123",
            "https://youtube.com/@channel",
            "https://youtu.be/invalid",
            f"https://youtube.com/watch?v={VIDEO_ID}&v={VIDEO_ID}",
            f"https://youtube.com.evil.test/watch?v={VIDEO_ID}",
            f"https://youtube.com:bad/watch?v={VIDEO_ID}",
            f"https://user:password@youtube.com/watch?v={VIDEO_ID}",
            f"ftp://youtube.com/watch?v={VIDEO_ID}",
        ):
            with self.subTest(url=url), self.assertRaises(media.DownloadError):
                media.youtube_url(url)


class YoutubeDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "media"
        for name, value in (
            ("find_spec", mock.Mock(return_value=object())),
            ("required_tool", lambda name: name),
            ("run_media_command", mock.Mock(side_effect=self.run_command)),
        ):
            patcher = mock.patch.object(media, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_command(self, command):
        if "yt_dlp" in command:
            manifest = Path(command[command.index("--print-to-file") + 2])
            source = manifest.parent / "source.webm"
            source.write_bytes(b"synthetic source")
            manifest.write_text(str(source) + "\n", encoding="utf-8")
        elif "-show_streams" in command:
            codecs = (("video", "h264"), ("audio", "aac")) if command[-1].endswith(".mp4") else (("audio", "mp3"),)
            return json.dumps({"streams": [{"codec_type": kind, "codec_name": codec}
                                           for kind, codec in codecs], "format": {"duration": "1.0"}})
        else:
            Path(command[-1]).write_bytes(b"synthetic media")
        return ""

    def test_produces_both_formats_and_disables_implicit_integrations(self):
        audio, video = media.download_youtube(f"https://youtu.be/{VIDEO_ID}?list=ignored", self.output)
        self.assertEqual({path.name for path in self.output.iterdir()}, {audio.name, video.name})
        self.assertEqual((audio.suffix, video.suffix), (".mp3", ".mp4"))
        command = media.run_media_command.call_args_list[0].args[0]
        self.assertEqual(command[-1], URL)
        for flag in ("--ignore-config", "--no-plugin-dirs", "--no-playlist", "--no-remote-components"):
            self.assertIn(flag, command)
        self.assertNotIn("--cookies-from-browser", command)
        self.assertEqual(command[command.index("--js-runtimes") + 1], "node:node")

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir()
        target = self.output / f"{VIDEO_ID}.mp4"
        target.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            media.download_youtube(URL, self.output)
        media.run_media_command.assert_not_called()
        self.assertEqual(target.read_bytes(), b"existing")

    def test_missing_dependency_fails_before_creating_output(self):
        media.find_spec.return_value = None
        with self.assertRaisesRegex(media.DownloadError, "requirements-media"):
            media.download_youtube(URL, self.output)
        self.assertFalse(self.output.exists())

    def test_failed_second_conversion_publishes_nothing(self):
        def fail_audio(command):
            if command[-1].endswith(".mp3"):
                raise media.DownloadError("audio conversion failed")
            return self.run_command(command)
        media.run_media_command.side_effect = fail_audio
        with self.assertRaisesRegex(media.DownloadError, "audio conversion"):
            media.download_youtube(URL, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_invalid_codec_publishes_nothing(self):
        def wrong_codec(command):
            if "-show_streams" in command:
                return '{"streams": [], "format": {"duration": "1"}}'
            return self.run_command(command)
        media.run_media_command.side_effect = wrong_codec
        with self.assertRaisesRegex(media.DownloadError, "codecs"):
            media.download_youtube(URL, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_missing_download_manifest_is_an_error(self):
        media.run_media_command.return_value = ""
        media.run_media_command.side_effect = None
        with self.assertRaisesRegex(media.DownloadError, "did not report"):
            media.download_youtube(URL, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_failed_second_publish_rolls_back_only_our_first_file(self):
        publish = media.publish_download
        def concurrent_video(source, target):
            if target.suffix == ".mp4":
                target.write_bytes(b"concurrent file")
            publish(source, target)
        with mock.patch.object(media, "publish_download", side_effect=concurrent_video):
            with self.assertRaises(FileExistsError):
                media.download_youtube(URL, self.output)
        self.assertFalse((self.output / f"{VIDEO_ID}.mp3").exists())
        self.assertEqual((self.output / f"{VIDEO_ID}.mp4").read_bytes(), b"concurrent file")

    def test_cli_routes_youtube_to_both_outputs(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = media.main([URL, "-o", str(self.output)])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue().count("Saved:"), 2)


class CommandErrorTests(unittest.TestCase):
    def test_subprocess_failure_is_reported(self):
        failure = subprocess.CalledProcessError(2, ["tool"], stderr="conversion detail")
        with mock.patch.object(media.subprocess, "run", side_effect=failure):
            with self.assertRaisesRegex(media.DownloadError, "conversion detail"):
                media.run_media_command(["tool"])

    def test_missing_executable_is_reported(self):
        with mock.patch.object(media.shutil, "which", return_value=None):
            with self.assertRaisesRegex(media.DownloadError, "ffmpeg"):
                media.required_tool("ffmpeg")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe", "node"))
    and find_spec("yt_dlp") and find_spec("yt_dlp_ejs"),
    "yt-dlp, EJS, Node and FFmpeg are required for the synthetic integration test",
)
class LocalMediaIntegrationTests(unittest.TestCase):
    def test_real_downloader_and_ffmpeg_produce_playable_mp3_and_h264_mp4(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture.mp4"
            media.run_media_command([
                media.required_tool("ffmpeg"), "-nostdin", "-v", "error",
                "-f", "lavfi", "-i", "testsrc=size=64x64:rate=10",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
                "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(fixture),
            ])
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                local_url = f"http://127.0.0.1:{server.server_port}/fixture.mp4?v={VIDEO_ID}"
                # Only the URL gate is substituted; yt-dlp and both conversions run for real.
                with mock.patch.object(media, "youtube_url", return_value=local_url):
                    audio, video = media.download_youtube(URL, root / "output")
                media.validate_output(audio, media.required_tool("ffprobe"), video=False)
                media.validate_output(video, media.required_tool("ffprobe"), video=True)
                self.assertEqual({path.suffix for path in video.parent.iterdir()}, {".mp3", ".mp4"})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
