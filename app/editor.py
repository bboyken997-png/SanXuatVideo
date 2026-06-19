"""Re-edit the source video: new narration audio + visual changes via ffmpeg."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _ffprobe_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    return float(data["format"]["duration"])


def _escape_subtitles(path: Path) -> str:
    # ffmpeg subtitles filter needs escaped path characters.
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def rebuild_video(
    source_video: Path,
    narration_audio: Path,
    out_path: Path,
    subtitle_path: Path | None = None,
    flip: bool = True,
) -> Path:
    """Mux new narration over the (visually altered) source video.

    The output duration matches the narration. The source video is looped if it is
    shorter than the narration and trimmed if longer. Visual filters (horizontal flip,
    mild contrast/saturation boost, optional burned-in subtitles) increase the visual
    difference from the original.
    """
    target_duration = _ffprobe_duration(narration_audio)

    vf_parts: list[str] = []
    if flip:
        vf_parts.append("hflip")
    vf_parts.append("eq=contrast=1.06:saturation=1.12:brightness=0.02")
    if subtitle_path is not None and subtitle_path.exists():
        vf_parts.append(f"subtitles='{_escape_subtitles(subtitle_path)}'")
    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(source_video),
        "-i",
        str(narration_audio),
        "-t",
        f"{target_duration:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path
