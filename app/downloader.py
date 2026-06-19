"""Download YouTube videos with yt-dlp."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from .config import Config

_YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)[\w\-]+",
    re.IGNORECASE,
)


def is_youtube_url(text: str) -> bool:
    return bool(_YOUTUBE_RE.search(text or ""))


@dataclass
class DownloadResult:
    video_path: Path
    title: str
    duration: int
    description: str
    uploader: str


def _cookie_opts(cfg: Config | None) -> dict:
    opts: dict = {}
    if cfg is None:
        return opts
    if cfg.yt_cookies_file:
        opts["cookiefile"] = cfg.yt_cookies_file
    elif cfg.yt_cookies_from_browser:
        # e.g. "chrome", or "chrome:/path/to/profile"
        spec = cfg.yt_cookies_from_browser
        if ":" in spec:
            browser, profile = spec.split(":", 1)
            opts["cookiesfrombrowser"] = (browser, profile, None, None)
        else:
            opts["cookiesfrombrowser"] = (spec,)
    return opts


def probe_duration(url: str, cfg: Config | None = None) -> int:
    """Return the video duration in seconds without downloading."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    opts.update(_cookie_opts(cfg))
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return int(info.get("duration") or 0)


def download(url: str, work_dir: Path, cfg: Config | None = None) -> DownloadResult:
    work_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(work_dir / "source.%(ext)s")
    opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    opts.update(_cookie_opts(cfg))
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_path = work_dir / "source.mp4"
    if not video_path.exists():
        # Fall back to whatever extension yt-dlp produced.
        candidates = sorted(work_dir.glob("source.*"))
        if not candidates:
            raise RuntimeError("Download failed: no output file produced")
        video_path = candidates[0]

    return DownloadResult(
        video_path=video_path,
        title=info.get("title") or "video",
        duration=int(info.get("duration") or 0),
        description=info.get("description") or "",
        uploader=info.get("uploader") or "",
    )
