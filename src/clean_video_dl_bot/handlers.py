import logging
import os
from uuid import uuid4

import anyio
from telegram import InlineQueryResultVideo, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from yt_dlp import YoutubeDL

DOWNLOADS_DIR = "downloads"
BYTES_PER_MB = 1024 * 1024
TELEGRAM_MAX_SIZE_MB = 50
MAX_DOWNLOAD_SIZE_BYTES = TELEGRAM_MAX_SIZE_MB * BYTES_PER_MB

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    start_message = (
        f"👋 Howdy, {user_first_name}\n"
        "📨 Send me a TikTok link and I'll fetch the video for you\n"
        "🔗 Just paste URL here — I'll handle the rest!"
    )
    await update.message.reply_html(start_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "📌 <b>How to use this bot:</b>\n\n"
        "➊ Copy the link to a video from TikTok or another supported platform\n"
        "➋ Send me the link\n"
        "➌ I'll send back video with no watermark"
    )
    await update.message.reply_html(help_message)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sorry, I didn't understand that command. Try /help",
    )


async def inline_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    video_info = extract_video_info(query)
    if not video_info:
        return
    result = InlineQueryResultVideo(
        id=str(uuid4()),
        video_url=video_info.get("url"),
        mime_type="video/mp4",
        thumbnail_url=video_info.get("thumbnail"),
        title=video_info.get("title"),
    )
    await update.inline_query.answer([result])


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    filepath, error_msg = await download_video(update.message.text)
    if error_msg:
        await update.message.reply_text(
            error_msg, reply_to_message_id=update.message.id
        )
        return

    try:
        with open(filepath, "rb") as video_file:
            await update.message.reply_video(
                video_file, reply_to_message_id=update.message.message_id
            )
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


async def download_video(url: str) -> tuple[str | None, str | None]:
    """
    Download a video from a given URL using `yt-dlp`.

    Args:
        url (str): The URL of the video to download.

    Returns:
        tuple[str | None, str | None]: A tuple containing the file path and an error message.
            On success returns (`filepath`, `None`).
            On failure returns (`None`, `error_message`).
    """
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    unique_id = uuid4()
    ydl_opts = {
        "format": "bv[ext=mp4][height<=1080]+ba/b",
        "outtmpl": os.path.join(DOWNLOADS_DIR, f"{unique_id}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None, "Could not extract video information."

            file_size = info.get("filesize") or info.get("filesize_approx") or 0
            if file_size > MAX_DOWNLOAD_SIZE_BYTES:
                mb_size = file_size / BYTES_PER_MB
                return (
                    None,
                    f"Video is too large ({mb_size:.1f} MB). Current limit is {TELEGRAM_MAX_SIZE_MB} MB.",
                )

            ydl.download(url)
            video_path = ydl.prepare_filename(info)
        return video_path, None

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None, "Unexpected error"


def extract_video_info(url: str) -> dict[str, str] | None:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "url": info.get("url"),
                "thumbnail": info.get("thumbnail"),
            }
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None
