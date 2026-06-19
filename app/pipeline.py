"""End-to-end pipeline: YouTube URL -> rewritten, re-edited video file."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import downloader, editor, rewriter, subtitles, transcriber, tts
from .config import Config

ProgressCb = Callable[[str], None]


@dataclass
class PipelineResult:
    output_path: Path
    title: str
    original_text: str
    rewritten_text: str
    diff_ratio: float
    work_dir: Path


def _noop(_: str) -> None:
    pass


def run(cfg: Config, url: str, progress: ProgressCb | None = None) -> PipelineResult:
    progress = progress or _noop
    work_dir = Path(tempfile.mkdtemp(prefix="ytrw_"))

    progress("Đang tải video...")
    dl = downloader.download(url, work_dir, cfg)

    progress("Đang tách âm thanh & nhận dạng lời thoại...")
    audio_path = transcriber.extract_audio(dl.video_path, work_dir)
    transcript = transcriber.transcribe(audio_path, cfg.whisper_model)

    progress("Đang viết lại nội dung (~40% khác biệt)...")
    rewritten, diff_ratio = rewriter.rewrite(cfg, transcript.text)

    progress("Đang tạo lời thoại mới (TTS)...")
    narration_path = work_dir / "narration.mp3"
    asyncio.run(tts.synthesize(rewritten, cfg.tts_voice, narration_path))

    progress("Đang dựng lại video...")
    narration_duration = editor._ffprobe_duration(narration_path)
    srt_path = subtitles.write_srt(rewritten, narration_duration, work_dir / "subs.srt")
    output_path = work_dir / "output.mp4"
    editor.rebuild_video(
        source_video=dl.video_path,
        narration_audio=narration_path,
        out_path=output_path,
        subtitle_path=srt_path,
    )

    return PipelineResult(
        output_path=output_path,
        title=dl.title,
        original_text=transcript.text,
        rewritten_text=rewritten,
        diff_ratio=diff_ratio,
        work_dir=work_dir,
    )


def cleanup(work_dir: Path) -> None:
    shutil.rmtree(work_dir, ignore_errors=True)
