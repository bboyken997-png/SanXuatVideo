"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_user_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            ids.add(int(part))
    return ids


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    llm_provider: str
    openai_api_key: str
    anthropic_api_key: str
    openai_model: str
    anthropic_model: str
    whisper_model: str
    tts_voice: str
    subtitle_font_size: int
    target_diff_ratio: float
    max_duration_seconds: int
    yt_cookies_file: str
    yt_cookies_from_browser: str
    allowed_user_ids: set[int] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set. Create one via @BotFather and put it in .env"
            )
        return cls(
            telegram_bot_token=token,
            llm_provider=os.environ.get("LLM_PROVIDER", "openai").strip().lower(),
            openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "").strip(),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip(),
            anthropic_model=os.environ.get(
                "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"
            ).strip(),
            whisper_model=os.environ.get("WHISPER_MODEL", "base").strip(),
            tts_voice=os.environ.get("TTS_VOICE", "vi-VN-HoaiMyNeural").strip(),
            subtitle_font_size=int(os.environ.get("SUBTITLE_FONT_SIZE", "14")),
            target_diff_ratio=float(os.environ.get("TARGET_DIFF_RATIO", "0.40")),
            max_duration_seconds=int(os.environ.get("MAX_DURATION_SECONDS", "900")),
            yt_cookies_file=os.environ.get("YT_COOKIES_FILE", "").strip(),
            yt_cookies_from_browser=os.environ.get(
                "YT_COOKIES_FROM_BROWSER", ""
            ).strip(),
            allowed_user_ids=_parse_user_ids(os.environ.get("ALLOWED_USER_IDS", "")),
        )
