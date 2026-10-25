"""Download authorized direct media, or MP3 and MP4 from one YouTube video."""

import argparse
from email.message import Message
from http.client import HTTPException, HTTPResponse
from importlib.util import find_spec
import json
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


YOUTUBE_HOSTS = ("youtu.be", "youtube.com", "youtube-nocookie.com")


def is_youtube_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in YOUTUBE_HOSTS)


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


def youtube_url(url: str) -> str:
    validate_url(url)
    if not is_youtube_url(url):
        raise DownloadError("Expected a single YouTube video URL.")
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().rstrip(".")
    segments = parts.path.strip("/").split("/")
    if host == "youtu.be" or host.endswith(".youtu.be"):
        video_id = segments[0] if len(segments) == 1 else ""
    elif parts.path == "/watch":
        ids = parse_qs(parts.query).get("v", [])
        video_id = ids[0] if len(ids) == 1 else ""
    elif len(segments) == 2 and segments[0] in ("shorts", "live", "embed"):
        video_id = segments[1]
    else:
        video_id = ""
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) is None:
        raise DownloadError("Use a single YouTube watch, short, live or embed video URL, not a playlist.")
    return f"https://www.youtube.com/watch?v={video_id}"


def run_media_command(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()[-2000:]
        raise DownloadError(f"Media command failed (exit {error.returncode}): {detail}") from error
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr, flush=True)
    return result.stdout


def validate_output(path: Path, ffprobe: str, video: bool) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise DownloadError(f"Missing or empty output: {path.name}")
    try:
        data = json.loads(run_media_command(
            [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
        streams = {(item["codec_type"], item.get("codec_name")) for item in data["streams"]}
        duration = float(data["format"]["duration"])
    except (ValueError, KeyError, TypeError) as error:
        raise DownloadError(f"Invalid media metadata: {path.name}") from error
    expected = {("video", "h264"), ("audio", "aac")} if video else {("audio", "mp3")}
    if not expected.issubset(streams) or not 0 < duration < float("inf"):
        raise DownloadError(f"Unexpected codecs or duration: {path.name}")


def required_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise DownloadError(f"{name} was not found on PATH; YouTube download needs FFmpeg and Node.")
    return path


def download_youtube(url: str, output_dir: Path) -> tuple[Path, Path]:
    canonical = youtube_url(url)
    video_id = parse_qs(urlsplit(canonical).query)["v"][0]
    audio, video = output_dir / f"{video_id}.mp3", output_dir / f"{video_id}.mp4"
    for target in (audio, video):
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"File already exists (not overwritten): {target}")
    for module in ("yt_dlp", "yt_dlp_ejs"):
        if find_spec(module) is None:
            raise DownloadError("Install scripts\\requirements-media.txt with this Python before YouTube download.")
    ffmpeg, ffprobe, node = (required_tool(name) for name in ("ffmpeg", "ffprobe", "node"))
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=".youtube-") as temporary:
        staging = Path(temporary)
        manifest = staging / "download-path.txt"
        run_media_command([
            sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-plugin-dirs",
            "--no-remote-components", "--no-js-runtimes", "--js-runtimes", f"node:{node}",
            "--no-playlist", "--no-overwrites", "--no-progress", "--no-simulate", "--encoding", "utf-8",
            "--ffmpeg-location", str(Path(ffmpeg).parent),
            "--format", "bv*[height<=?1080]+ba/b[height<=?1080]",
            "--merge-output-format", "mkv", "--output", str(staging / "source.%(ext)s"),
            "--print-to-file", "after_move:filepath", str(manifest), "--", canonical,
        ])
        if not manifest.is_file():
            raise DownloadError("Downloader did not report a completed media file.")
        paths = manifest.read_text(encoding="utf-8").splitlines()
        if len(paths) != 1:
            raise DownloadError("Downloader must produce exactly one video.")
        source = Path(paths[0]).resolve()
        if source.parent != staging.resolve() or not source.is_file():
            raise DownloadError("Downloader output is missing or outside its staging folder.")
        staged_video, staged_audio = staging / video.name, staging / audio.name
        run_media_command([
            ffmpeg, "-nostdin", "-v", "error", "-n", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0", "-c:v", "libx264", "-preset", "fast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
            str(staged_video),
        ])
        run_media_command([
            ffmpeg, "-nostdin", "-v", "error", "-n", "-i", str(staged_video),
            "-map", "0:a:0", "-c:a", "libmp3lame", "-q:a", "2", str(staged_audio),
        ])
        validate_output(staged_video, ffprobe, video=True)
        validate_output(staged_audio, ffprobe, video=False)
        published = []
        try:
            for source_path, target in ((staged_audio, audio), (staged_video, video)):
                publish_download(source_path, target)
                published.append(target)
        except BaseException:
            # Roll back only files published by this attempt, including on cancellation.
            for target in published:
                target.unlink()
            raise
    return audio, video


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
        if is_youtube_url(newurl):
            raise DownloadError("A direct media URL cannot redirect to a YouTube page.")
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


def download_media(url: str, output_dir: Path) -> Path:
    validate_url(url)
    if is_youtube_url(url):
        raise DownloadError("Use download_youtube for YouTube, or supply a local MP3/MP4 file.")
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
    parser.add_argument("urls", nargs="+", help="HTTP(S) direct media or single YouTube video URLs.")
    parser.add_argument(
        "-o", "--output-dir", required=True, type=Path, help="Folder to save downloaded files."
    )
    args = parser.parse_args(argv)
    failed = 0
    for index, url in enumerate(args.urls, start=1):
        print(f"[{index}/{len(args.urls)}] Downloading...", flush=True)
        try:
            validate_url(url)
            targets = (download_youtube(url, args.output_dir) if is_youtube_url(url)
                       else (download_media(url, args.output_dir),))
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
