"""Download authorized MP3/MP4 direct files or YouTube videos."""

import argparse
from email.message import Message
from http.client import HTTPException, HTTPResponse
from importlib.util import find_spec
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.error import URLError
from urllib.parse import parse_qs, unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class DownloadError(Exception):
    """A media download cannot be completed."""


def validate_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise DownloadError("Use an HTTP(S) direct media URL.")
        if parts.username is not None or parts.password is not None:
            raise DownloadError("URLs containing login credentials are not supported.")
        _ = parts.port
    except ValueError as error:
        raise DownloadError("Invalid URL or port.") from error


class MediaRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: HTTPResponse,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> Request | None:
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def media_extension(prefix: bytes) -> str:
    if len(prefix) >= 10 and prefix.startswith(b"ID3"):
        return ".mp3"
    if (
        len(prefix) >= 4
        and prefix[0] == 0xFF
        and prefix[1] & 0xE0 == 0xE0
        and prefix[1] & 0x06 != 0
        and prefix[2] & 0xF0 not in (0, 0xF0)
        and prefix[2] & 0x0C != 0x0C
    ):
        return ".mp3"
    if len(prefix) >= 12 and prefix[4:8] == b"ftyp":
        return ".mp4"
    raise DownloadError(
        "The response has no supported MP3/MP4 header. "
        "Use a direct file URL, not a web page, playlist or login page."
    )


def safe_filename(name: str, extension: str) -> str:
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', "_", name).strip(" .")
    stem = Path(name).stem.strip(" .") if name else "media"
    stem = stem[:120].rstrip(" .") or "media"
    if re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", stem, re.I):
        stem = "_" + stem
    return stem + extension


def publish_download(source: Path, target: Path) -> None:
    # Windows rename refuses existing files; link provides that guarantee on POSIX.
    if os.name == "nt":
        source.rename(target)
    else:
        os.link(source, target)


def youtube_video_url(url: str) -> str | None:
    validate_url(url)
    parts = urlsplit(url)
    if parts.hostname in ("youtu.be", "www.youtu.be"):
        video_id = parts.path.removeprefix("/")
    elif parts.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        if parts.path == "/watch":
            video_id = parse_qs(parts.query).get("v", [""])[0]
        else:
            match = re.fullmatch(r"/(?:shorts|live|embed)/([^/]+)/?", parts.path)
            video_id = match.group(1) if match else ""
    else:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise DownloadError("Use a YouTube single-video URL, not a channel or playlist URL.")
    return f"https://www.youtube.com/watch?v={video_id}"


def download_youtube(url: str, output_dir: Path, media_format: str) -> list[Path]:
    video_url = youtube_video_url(url)
    if video_url is None:
        raise DownloadError("Expected a YouTube video URL.")
    if media_format not in ("mp3", "mp4", "both"):
        raise DownloadError("YouTube format must be mp3, mp4 or both.")
    if find_spec("yt_dlp") is None:
        raise DownloadError(
            "YouTube support needs yt-dlp in this Python environment. Run: "
            f'"{sys.executable}" -m pip install -r scripts/requirements-media.txt'
        )
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        raise DownloadError("YouTube support needs FFmpeg and ffprobe on PATH. See the media guide.")
    runtime = next(
        ((name, path) for name in ("deno", "node", "bun", "qjs") if (path := shutil.which(name))),
        None,
    )
    if runtime is None:
        raise DownloadError("YouTube support needs a JavaScript runtime (Deno or Node.js) on PATH.")

    formats = ("mp3", "mp4") if media_format == "both" else (media_format,)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=".youtube-") as staging:
        downloads: list[tuple[Path, Path]] = []
        for extension in formats:
            work_dir = Path(staging) / extension
            work_dir.mkdir()
            command = [
                sys.executable, "-m", "yt_dlp",
                "--ignore-config", "--no-plugin-dirs", "--no-remote-components",
                "--no-playlist", "--no-overwrites", "--abort-on-error",
                "--windows-filenames", "--newline", "--socket-timeout", "30",
                "--js-runtimes", f"{runtime[0]}:{runtime[1]}",
                "--ffmpeg-location", str(Path(ffmpeg).parent),
                "--paths", str(work_dir),
                "--output", "%(title).100B [%(id)s].%(ext)s",
            ]
            if extension == "mp3":
                command += [
                    "--format", "bestaudio/best",
                    "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
                ]
            else:
                command += [
                    "--format",
                    "bv[ext=mp4][vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4][vcodec^=avc1]"
                    "/bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
                    "--merge-output-format", "mp4", "--remux-video", "mp4",
                ]
            command += ["--", video_url]
            result = subprocess.run(command, check=False)
            if result.returncode != 0:
                raise DownloadError(
                    f"yt-dlp failed for {extension} (exit {result.returncode}); see its error above. "
                    "No access restrictions are bypassed."
                )
            files = list(work_dir.glob(f"*.{extension}"))
            if len(files) != 1 or files[0].stat().st_size == 0:
                raise DownloadError(f"yt-dlp did not produce exactly one non-empty {extension} file.")
            source = files[0]
            with source.open("rb") as stream:
                if media_extension(stream.read(65536)) != "." + extension:
                    raise DownloadError(f"yt-dlp produced an unexpected {extension} file header.")
            target = output_dir / source.name
            if target.exists() or target.is_symlink():
                raise FileExistsError(f"File already exists (not overwritten): {target}")
            downloads.append((source, target))

        targets = []
        for source, target in downloads:
            publish_download(source, target)
            targets.append(target)
        return targets


def download_media(url: str, output_dir: Path) -> Path:
    validate_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": "UltraStarPlay-MediaDownloader/1.0",
            "Accept-Encoding": "identity",
        },
    )
    opener = build_opener(MediaRedirectHandler())
    with opener.open(request, timeout=30) as response:
        if response.status != 200:
            raise DownloadError(f"Expected HTTP 200, received {response.status}.")
        prefix = response.read(64 * 1024)
        extension = media_extension(prefix)
        name = response.headers.get_filename() or unquote(
            urlsplit(response.geturl()).path.rsplit("/", 1)[-1]
        )
        length_header = response.headers.get("Content-Length")
        try:
            expected_length = int(length_header) if length_header is not None else None
        except ValueError as error:
            raise DownloadError("Invalid Content-Length header.") from error
        if expected_length is not None and expected_length < 0:
            raise DownloadError("Negative Content-Length header.")

        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / safe_filename(name, extension)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"File already exists (not overwritten): {target}")

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=output_dir, prefix=".download-", suffix=".part", delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                downloaded = temporary_file.write(prefix)
                while chunk := response.read(128 * 1024):
                    downloaded += temporary_file.write(chunk)
            if expected_length is not None and downloaded != expected_length:
                raise DownloadError(
                    f"Incomplete download: expected {expected_length} bytes, got {downloaded}."
                )
            publish_download(temporary_path, target)
            return target
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="HTTP(S) direct MP3/MP4 files or YouTube video URLs.")
    parser.add_argument(
        "-o", "--output-dir", required=True, type=Path, help="Folder to save downloaded files."
    )
    parser.add_argument(
        "--format", choices=("mp3", "mp4", "both"), default="both",
        help="YouTube output (default: both). Direct file downloads are not converted.",
    )
    args = parser.parse_args(argv)
    failed = 0
    for index, url in enumerate(args.urls, start=1):
        print(f"[{index}/{len(args.urls)}] Downloading...", flush=True)
        try:
            if youtube_video_url(url) is not None:
                targets = download_youtube(url, args.output_dir, args.format)
            else:
                targets = [download_media(url, args.output_dir)]
            for target in targets:
                print(f"Saved: {target} ({target.stat().st_size} bytes)", flush=True)
        except (DownloadError, OSError, URLError, HTTPException, ValueError) as error:
            print(f"[{index}/{len(args.urls)}] ERROR: {error}", file=sys.stderr)
            failed += 1
    print(f"Finished: {len(args.urls) - failed} succeeded, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled; incomplete temporary download removed.", file=sys.stderr)
        sys.exit(130)
