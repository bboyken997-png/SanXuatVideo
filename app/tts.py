"""Generate narration audio from text using edge-tts (free, no API key)."""

from __future__ import annotations

from pathlib import Path

import edge_tts


async def synthesize(text: str, voice: str, out_path: Path) -> Path:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))
    return out_path
