"""Rewrite a transcript so the result differs from the original by ~target ratio."""

from __future__ import annotations

import difflib
import re

from .config import Config

_SYSTEM_PROMPT = (
    "You are a professional scriptwriter. Rewrite the user's video transcript so the "
    "meaning and key information are preserved, but the wording, sentence structure, "
    "examples and phrasing are changed substantially. Keep the same language as the "
    "input. Do not add commentary, headers, or markdown — return only the rewritten "
    "script as plain prose."
)


def _diff_ratio(a: str, b: str) -> float:
    """Fraction of text that changed (0 = identical, 1 = completely different)."""
    return 1.0 - difflib.SequenceMatcher(None, a, b).ratio()


def _build_prompt(text: str, target: float) -> str:
    pct = int(round(target * 100))
    return (
        f"Rewrite the following transcript so that roughly {pct}% of the content is "
        f"different from the original (different wording, structure, and examples) "
        f"while keeping the same core message and language.\n\n"
        f"--- TRANSCRIPT START ---\n{text}\n--- TRANSCRIPT END ---"
    )


def _rewrite_openai(cfg: Config, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=cfg.openai_api_key)
    resp = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )
    return (resp.choices[0].message.content or "").strip()


def _rewrite_anthropic(cfg: Config, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    resp = client.messages.create(
        model=cfg.anthropic_model,
        max_tokens=4096,
        temperature=0.9,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [block.text for block in resp.content if block.type == "text"]
    return "".join(parts).strip()


def _rewrite_naive(text: str) -> str:
    """Offline fallback: light shuffling so there is *some* difference. Low quality."""
    chunks = [c.strip() for c in re.split(r"[.!?\n,]+", text) if c.strip()]
    if len(chunks) <= 1:
        # No punctuation to split on (e.g. song lyrics): reorder word halves.
        words = text.split()
        if len(words) <= 1:
            return text
        mid = len(words) // 2
        return " ".join(words[mid:] + words[:mid])
    mid = len(chunks) // 2
    return ". ".join(chunks[mid:] + chunks[:mid]) + "."


def rewrite(cfg: Config, text: str) -> tuple[str, float]:
    """Return (rewritten_text, achieved_diff_ratio)."""
    if not text.strip():
        return text, 0.0

    prompt = _build_prompt(text, cfg.target_diff_ratio)
    if cfg.llm_provider == "openai" and cfg.openai_api_key:
        result = _rewrite_openai(cfg, prompt)
    elif cfg.llm_provider == "anthropic" and cfg.anthropic_api_key:
        result = _rewrite_anthropic(cfg, prompt)
    else:
        result = _rewrite_naive(text)

    if not result.strip():
        result = _rewrite_naive(text)

    return result, _diff_ratio(text, result)
