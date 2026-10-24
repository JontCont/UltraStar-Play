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
from unittest.mock import patch

from download_media import DownloadError, download_youtube, main, youtube_video_url


VIDEO_URL = "https://www.youtube.com/watch?v=unitTest001"
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"test"
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2"


class YouTubeDownloadTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "\u6e2c\u8a66"
        self.addCleanup(patch.stopall)
        patch("download_media.find_spec", return_value=object()).start()
        patch("download_media.shutil.which", side_effect=self.find_tool).start()
        self.commands: list[list[str]] = []

    @staticmethod
    def find_tool(name: str) -> str | None:
        return str(Path("tools") / name) if name in ("ffmpeg", "ffprobe", "node") else None

    def fake_download(self, command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        folder = Path(command[command.index("--paths") + 1])
        extension = "mp3" if "--extract-audio" in command else "mp4"
        (folder / f"Test [unitTest001].{extension}").write_bytes(MP3 if extension == "mp3" else MP4)
        return subprocess.CompletedProcess(command, 0)

    def test_normalizes_video_urls_and_removes_tracking_and_playlist(self) -> None:
        for url in (
            VIDEO_URL + "&source_ve_path=123&list=other",
            "https://youtu.be/unitTest001?si=tracking",
            "https://m.youtube.com/watch?v=unitTest001",
            "https://music.youtube.com/watch?v=unitTest001",
            "https://youtube.com/shorts/unitTest001",
            "https://www.youtube.com/live/unitTest001",
            "https://www.youtube.com/embed/unitTest001",
        ):
            with self.subTest(url=url):
                self.assertEqual(youtube_video_url(url), VIDEO_URL)

    def test_leaves_unrelated_hosts_on_direct_download_path(self) -> None:
        self.assertIsNone(youtube_video_url("https://example.org/audio.mp3"))
        self.assertIsNone(youtube_video_url("https://youtube.com.example.org/audio.mp3"))

    def test_rejects_playlist_channel_and_invalid_video_id(self) -> None:
        for url in (
            "https://youtube.com/playlist?list=123",
            "https://youtube.com/@channel",
            "https://youtu.be/not-valid",
        ):
            with self.subTest(url=url), self.assertRaises(DownloadError):
                youtube_video_url(url)

    def test_downloads_all_output_modes_and_passes_safe_options(self) -> None:
        with patch("download_media.subprocess.run", side_effect=self.fake_download):
            for mode in ("mp3", "mp4", "both"):
                with self.subTest(mode=mode):
                    folder = self.output / mode
                    targets = download_youtube(VIDEO_URL, folder, mode)
                    expected = {".mp3", ".mp4"} if mode == "both" else {"." + mode}
                    self.assertEqual({target.suffix for target in targets}, expected)
                    self.assertEqual(set(folder.iterdir()), set(targets))
        for command in self.commands:
            self.assertEqual(command[-2:], ["--", VIDEO_URL])
            self.assertIn("--no-playlist", command)
            self.assertIn("--no-overwrites", command)
            self.assertIn("--ignore-config", command)
            self.assertIn("--no-plugin-dirs", command)
            self.assertIn("--no-remote-components", command)
            self.assertNotIn("--cookies-from-browser", command)
            self.assertIn("node:", command[command.index("--js-runtimes") + 1])

    def test_refuses_to_overwrite_existing_output(self) -> None:
        self.output.mkdir()
        target = self.output / "Test [unitTest001].mp3"
        target.write_bytes(b"keep")
        with patch("download_media.subprocess.run", side_effect=self.fake_download):
            with self.assertRaises(FileExistsError):
                download_youtube(VIDEO_URL, self.output, "mp3")
        self.assertEqual(target.read_bytes(), b"keep")
        self.assertEqual(list(self.output.iterdir()), [target])

    def test_reports_missing_dependencies_before_creating_files(self) -> None:
        scenarios = (
            ("download_media.find_spec", None, "yt-dlp"),
            ("download_media.shutil.which", None, "FFmpeg"),
        )
        for name, value, message in scenarios:
            with self.subTest(name=name), patch(name, return_value=value):
                with self.assertRaisesRegex(DownloadError, message):
                    download_youtube(VIDEO_URL, self.output, "mp3")
        with patch(
            "download_media.shutil.which",
            side_effect=lambda name: name if name in ("ffmpeg", "ffprobe") else None,
        ):
            with self.assertRaisesRegex(DownloadError, "JavaScript"):
                download_youtube(VIDEO_URL, self.output, "mp3")
        self.assertFalse(self.output.exists())

    def test_cleans_staging_on_failure_and_cancellation(self) -> None:
        for failure in (DownloadError, KeyboardInterrupt):
            def fail(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
                folder = Path(command[command.index("--paths") + 1])
                (folder / "partial.part").write_bytes(b"partial")
                if failure is KeyboardInterrupt:
                    raise KeyboardInterrupt
                return subprocess.CompletedProcess(command, 1)

            with self.subTest(failure=failure), patch("download_media.subprocess.run", side_effect=fail):
                with self.assertRaises(failure):
                    download_youtube(VIDEO_URL, self.output, "both")
                self.assertEqual(list(self.output.iterdir()), [])

    def test_requires_actual_nonempty_media_output_even_when_process_succeeds(self) -> None:
        with patch("download_media.subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
            with self.assertRaisesRegex(DownloadError, "exactly one"):
                download_youtube(VIDEO_URL, self.output, "mp3")
        self.assertEqual(list(self.output.iterdir()), [])

    def test_rejects_wrong_media_header_and_cleans_staging(self) -> None:
        def wrong_media(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
            folder = Path(command[command.index("--paths") + 1])
            (folder / "test.mp3").write_text("<html>not audio</html>", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        with patch("download_media.subprocess.run", side_effect=wrong_media):
            with self.assertRaises(DownloadError):
                download_youtube(VIDEO_URL, self.output, "mp3")
        self.assertEqual(list(self.output.iterdir()), [])

    def test_both_does_not_publish_first_format_if_second_download_fails(self) -> None:
        def fail_second(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
            if "--extract-audio" in command:
                return self.fake_download(command, check=check)
            return subprocess.CompletedProcess(command, 1)

        with patch("download_media.subprocess.run", side_effect=fail_second):
            with self.assertRaises(DownloadError):
                download_youtube(VIDEO_URL, self.output, "both")
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_defaults_to_both_and_reports_youtube_errors(self) -> None:
        errors = io.StringIO()
        with (
            patch("download_media.download_youtube", side_effect=DownloadError("Unavailable")) as youtube,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(errors),
        ):
            result = main([VIDEO_URL, "-o", str(self.output)])
        self.assertEqual(result, 1)
        self.assertIn("Unavailable", errors.getvalue())
        youtube.assert_called_once_with(VIDEO_URL, self.output, "both")

    def test_cli_routes_youtube_and_preserves_direct_urls(self) -> None:
        with (
            patch("download_media.download_youtube", return_value=[]) as youtube,
            patch("download_media.download_media") as direct,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            direct.return_value = Path(__file__)
            code = main([VIDEO_URL, "https://example.org/a.mp3", "--format", "mp3", "-o", str(self.output)])
        self.assertEqual(code, 0)
        youtube.assert_called_once_with(VIDEO_URL, self.output, "mp3")
        direct.assert_called_once_with("https://example.org/a.mp3", self.output)


class QuietFileHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@unittest.skipUnless(
    find_spec("yt_dlp") is not None
    and shutil.which("ffmpeg") is not None
    and shutil.which("ffprobe") is not None
    and any(shutil.which(name) for name in ("deno", "node", "bun", "qjs")),
    "Optional integration test requires yt-dlp, FFmpeg, ffprobe and a JavaScript runtime.",
)
class YouTubePipelineIntegrationTest(unittest.TestCase):
    def test_real_ytdlp_and_ffmpeg_outputs_without_external_media(self) -> None:
        real_run = subprocess.run
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture"
            fixture.mkdir()
            real_run(
                [
                    "ffmpeg", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc2=size=160x90:rate=10", "-t", "1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(fixture / "video.mp4"),
                ],
                check=True, capture_output=True, timeout=30,
            )
            real_run(
                [
                    "ffmpeg", "-v", "error", "-f", "lavfi",
                    "-i", "sine=frequency=440:sample_rate=44100", "-t", "1",
                    "-c:a", "aac", str(fixture / "audio.m4a"),
                ],
                check=True, capture_output=True, timeout=30,
            )
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), partial(QuietFileHandler, directory=str(fixture))
            )
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                info = {
                    "id": "unitTest001", "title": "Local \u6e2c\u8a66", "extractor_key": "Generic",
                    "extractor": "generic", "webpage_url": base + "/fixture",
                    "formats": [
                        {
                            "format_id": "video", "url": base + "/video.mp4",
                            "ext": "mp4", "vcodec": "avc1.64000a", "acodec": "none",
                            "width": 160, "height": 90, "protocol": "http",
                        },
                        {
                            "format_id": "audio", "url": base + "/audio.m4a",
                            "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2",
                            "abr": 128, "protocol": "http",
                        },
                    ],
                }
                info_file = root / "fixture.info.json"
                info_file.write_text(json.dumps(info), encoding="utf-8")

                def local_download(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
                    command = command[:-2] + ["--load-info-json", str(info_file)]
                    result = real_run(command, capture_output=True, text=True, timeout=60, check=check)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    return result

                with patch("download_media.subprocess.run", side_effect=local_download):
                    for mode in ("mp3", "mp4", "both"):
                        with self.subTest(mode=mode):
                            output = root / "\u4e2d\u6587\u76ee\u9304" / mode
                            targets = download_youtube(VIDEO_URL, output, mode)
                            expected = {".mp3", ".mp4"} if mode == "both" else {"." + mode}
                            self.assertEqual({target.suffix for target in targets}, expected)
                            self.assertEqual(set(output.iterdir()), set(targets))
                            for target in targets:
                                probe = real_run(
                                    [
                                        "ffprobe", "-v", "error", "-show_streams",
                                        "-of", "json", str(target),
                                    ],
                                    capture_output=True, text=True, check=True, timeout=15,
                                )
                                streams = json.loads(probe.stdout)["streams"]
                                codecs = {stream["codec_name"] for stream in streams}
                                self.assertEqual(codecs, {"mp3"} if target.suffix == ".mp3" else {"h264", "aac"})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
