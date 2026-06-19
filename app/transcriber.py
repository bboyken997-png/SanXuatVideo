"""Transcribe audio locally with faster-whisper."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    segments: list[Segment]

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


def extract_audio(video_path: Path, work_dir: Path) -> Path:
    audio_path = work_dir / "audio.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path


def transcribe(audio_path: Path, model_size: str = "base") -> Transcript:
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(str(audio_path), vad_filter=True)
    segments = [
        Segment(start=seg.start, end=seg.end, text=seg.text.strip())
        for seg in segments_iter
    ]
    return Transcript(language=info.language, segments=segments)
