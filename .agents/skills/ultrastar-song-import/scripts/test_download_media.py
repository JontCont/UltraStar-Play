import contextlib
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from download_media import DownloadError, download_media, main, safe_filename


MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"test audio bytes" * 12000
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2" + b"test video bytes"


class MediaHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/audio.mp3")
            self.end_headers()
            return
        if self.path == "/redirect-ftp":
            self.send_response(302)
            self.send_header("Location", "ftp://127.0.0.1/media.mp3")
            self.end_headers()
            return
        if self.path == "/missing.mp3":
            self.send_error(404)
            return
        data = MP4 if self.path.endswith(".mp4") else MP3
        content_type = "application/octet-stream"
        if self.path == "/login.mp3":
            data = b"<!DOCTYPE html><html>Sign in</html>"
            content_type = "text/html"
        if self.path == "/empty.mp3":
            data = b""
        if self.path == "/mpeg.mp3":
            data = b"\xff\xfb\x90\x00" + b"test MPEG frame bytes"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        if self.path != "/no-length.mp3":
            length = len(data) + 10 if self.path == "/truncated.mp3" else len(data)
            self.send_header("Content-Length", str(length))
        if self.path == "/disposition":
            self.send_header(
                "Content-Disposition",
                "attachment; filename*=UTF-8''%E6%B8%AC%E8%A9%A6%20%E6%AD%8C%E6%9B%B2.mp3",
            )
        if self.path == "/unsafe":
            self.send_header("Content-Disposition", 'attachment; filename="../../outside.mp3"')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        pass


class DownloadMediaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MediaHandler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.output = Path(self.temporary_directory.name) / "media"

    def download(self, path: str) -> Path:
        return download_media(self.base_url + path, self.output)

    def test_downloads_mp3_and_mp4_without_changing_bytes(self) -> None:
        self.assertEqual(self.download("/audio.mp3").read_bytes(), MP3)
        self.assertEqual(self.download("/video.mp4").read_bytes(), MP4)
        self.assertEqual(len(list(self.output.iterdir())), 2)

    def test_accepts_mp3_without_id3_tag(self) -> None:
        self.assertEqual(self.download("/mpeg.mp3").suffix, ".mp3")

    def test_follows_redirect_and_uses_final_filename(self) -> None:
        target = self.download("/redirect")
        self.assertEqual(target.name, "audio.mp3")
        self.assertEqual(target.read_bytes(), MP3)

    def test_rejects_redirect_to_non_http_scheme(self) -> None:
        with self.assertRaises(DownloadError):
            self.download("/redirect-ftp")
        self.assertFalse(self.output.exists())

    def test_refuses_youtube_urls_without_requesting_them(self) -> None:
        for url in ("https://youtu.be/Uv_p43UAdBY", "https://www.youtube.com/watch?v=YacpC7sUXMM"):
            with self.subTest(url=url), patch("download_media.build_opener") as opener:
                with self.assertRaisesRegex(DownloadError, "local MP3/MP4"):
                    download_media(url, self.output)
                opener.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_handles_unicode_disposition_filename(self) -> None:
        target = self.download("/disposition")
        self.assertEqual(target.name, "\u6e2c\u8a66 \u6b4c\u66f2.mp3")
        self.assertEqual(target.read_bytes(), MP3)

    def test_keeps_server_filename_inside_output_directory(self) -> None:
        target = self.download("/unsafe")
        self.assertEqual(target, self.output / "outside.mp3")
        self.assertFalse((self.output.parent / "outside.mp3").exists())

    def test_handles_url_without_extension_or_content_length(self) -> None:
        self.assertEqual(self.download("/media?token=test").name, "media.mp3")
        self.assertEqual(self.download("/no-length.mp3").read_bytes(), MP3)

    def test_refuses_overwrite_and_removes_no_existing_files(self) -> None:
        self.output.mkdir()
        target = self.output / "audio.mp3"
        target.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            self.download("/audio.mp3")
        self.assertEqual(target.read_bytes(), b"existing")
        self.assertEqual(list(self.output.iterdir()), [target])

    def test_rejects_html_and_empty_response_despite_extension(self) -> None:
        for path in ("/login.mp3", "/empty.mp3"):
            with self.subTest(path=path), self.assertRaises(DownloadError):
                self.download(path)
        self.assertFalse(self.output.exists())

    def test_cleans_up_truncated_download(self) -> None:
        with self.assertRaisesRegex(DownloadError, "Incomplete download"):
            self.download("/truncated.mp3")
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cleans_up_after_timeout_or_cancellation(self) -> None:
        for failure in (TimeoutError("Read timed out"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__):
                response = MagicMock()
                response.status = 200
                response.headers = Message()
                response.geturl.return_value = self.base_url + "/cancelled.mp3"
                response.read.side_effect = [MP3[:65536], failure]
                with patch("download_media.build_opener") as opener:
                    opener.return_value.open.return_value.__enter__.return_value = response
                    with self.assertRaises(type(failure)):
                        self.download("/cancelled.mp3")
                self.assertEqual(list(self.output.iterdir()), [])

    def test_reports_http_error_without_creating_files(self) -> None:
        with self.assertRaises(HTTPError):
            self.download("/missing.mp3")
        self.assertFalse(self.output.exists())

    def test_rejects_invalid_urls_without_creating_files(self) -> None:
        for url in (
            "file:///audio.mp3",
            "ftp://example.test/audio.mp3",
            "not a url",
            "https://example.test:bad/audio.mp3",
            "https://user:password@example.test/audio.mp3",
        ):
            with self.subTest(url=url), self.assertRaises(DownloadError):
                download_media(url, self.output)
        self.assertFalse(self.output.exists())

    def test_sanitizes_windows_reserved_names(self) -> None:
        for name in ("CON.mp3", "aux.mp3", "COM1.mp3", "LPT9.mp3"):
            with self.subTest(name=name):
                self.assertTrue(safe_filename(name, ".mp3").startswith("_"))
        self.assertEqual(safe_filename("bad:name?.mp3", ".mp3"), "bad_name_.mp3")

    def test_batch_reports_failure_and_continues_to_next_url(self) -> None:
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = main(
                [
                    self.base_url + "/login.mp3",
                    self.base_url + "/video.mp4",
                    "-o",
                    str(self.output),
                ]
            )
        self.assertEqual(result, 1)
        self.assertIn("ERROR:", errors.getvalue())
        self.assertIn("1 succeeded, 1 failed", output.getvalue())
        self.assertEqual((self.output / "video.mp4").read_bytes(), MP4)

    def test_batch_success_exit_code(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(
                [self.base_url + "/audio.mp3", self.base_url + "/video.mp4", "-o", str(self.output)]
            )
        self.assertEqual(result, 0)

    def test_command_line_process_downloads_and_reports_real_exit_codes(self) -> None:
        script = str(Path(__file__).with_name("download_media.py"))
        for index, (paths, expected_code) in enumerate(
            (
                (("/audio.mp3", "/video.mp4"), 0),
                (("/login.mp3", "/video.mp4"), 1),
            )
        ):
            with self.subTest(expected_code=expected_code):
                output = self.output / str(index)
                result = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        script,
                        *(self.base_url + path for path in paths),
                        "-o",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(result.returncode, expected_code, result.stderr)
                self.assertEqual((output / "video.mp4").read_bytes(), MP4)
                if expected_code == 0:
                    self.assertEqual((output / "audio.mp3").read_bytes(), MP3)
                    self.assertEqual(result.stderr, "")
                else:
                    self.assertIn("ERROR:", result.stderr)
                self.assertEqual(list(output.glob("*.part")), [])


if __name__ == "__main__":
    unittest.main()
