"""Build a simple SRT from rewritten text spread evenly over a duration."""

from __future__ import annotations

import re
from pathlib import Path


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。])\s+", text.replace("\n", " ").strip())
    return [p.strip() for p in parts if p.strip()]


def _fmt_ts(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(text: str, total_duration: float, out_path: Path) -> Path:
    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text.strip() or " "]

    # Weight each cue by its character length so longer lines stay on screen longer.
    weights = [max(len(s), 1) for s in sentences]
    total_weight = sum(weights)

    lines: list[str] = []
    cursor = 0.0
    for idx, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
        span = total_duration * (weight / total_weight)
        start = cursor
        end = min(total_duration, cursor + span)
        cursor = end
        lines.append(str(idx))
        lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
        lines.append(sentence)
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
