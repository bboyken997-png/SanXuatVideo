"""Telegram bot entrypoint."""

from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import downloader, pipeline
from .config import Config

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("yt-rewriter-bot")

WELCOME = (
    "Xin chào! Gửi cho tôi một link YouTube, tôi sẽ tạo lại video với nội dung "
    "khác khoảng 40% (viết lại lời thoại, lồng tiếng mới, dựng lại hình + phụ đề).\n\n"
    "Chỉ dùng với video bạn sở hữu hoặc có quyền chỉnh sửa."
)


def _allowed(cfg: Config, user_id: int | None) -> bool:
    if not cfg.allowed_user_ids:
        return True
    return user_id in cfg.allowed_user_ids


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg: Config = context.application.bot_data["cfg"]
    message = update.message
    if message is None:
        return

    user = update.effective_user
    if not _allowed(cfg, user.id if user else None):
        await message.reply_text("Bạn không có quyền dùng bot này.")
        return

    text = message.text or ""
    if not downloader.is_youtube_url(text):
        await message.reply_text("Vui lòng gửi một link YouTube hợp lệ.")
        return

    url = text.strip()
    try:
        duration = downloader.probe_duration(url, cfg)
    except Exception as exc:  # noqa: BLE001
        logger.exception("probe failed")
        await message.reply_text(f"Không đọc được video: {exc}")
        return

    if duration and duration > cfg.max_duration_seconds:
        await message.reply_text(
            f"Video dài {duration}s, vượt giới hạn {cfg.max_duration_seconds}s."
        )
        return

    status = await message.reply_text("Đã nhận link. Bắt đầu xử lý...")

    loop = asyncio.get_running_loop()

    def progress(msg: str) -> None:
        asyncio.run_coroutine_threadsafe(status.edit_text(msg), loop)

    try:
        result = await loop.run_in_executor(
            None, lambda: pipeline.run(cfg, url, progress)
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("pipeline failed")
        await status.edit_text(f"Lỗi khi xử lý: {exc}")
        return

    await message.chat.send_action(ChatAction.UPLOAD_VIDEO)
    caption = (
        f"{result.title}\n"
        f"Mức khác biệt lời thoại: ~{int(result.diff_ratio * 100)}%"
    )
    try:
        with open(result.output_path, "rb") as fh:
            await message.reply_video(video=fh, caption=caption)
        await status.edit_text("Hoàn tất ✅")
    finally:
        pipeline.cleanup(result.work_dir)


def main() -> None:
    cfg = Config.from_env()
    app = Application.builder().token(cfg.telegram_bot_token).build()
    app.bot_data["cfg"] = cfg
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
