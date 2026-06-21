import os
import logging
from typing import Dict
from uuid import uuid4

from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from telegram import Update, InlineQueryResultVideo, MessageEntity
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler
from telegram.constants import ChatAction

DOWNLOADS_DIR = 'downloads'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    start_message = f"👋 Welcome, {user.mention_html()}\n" \
                    "📨 Send me a TikTok link and I'll return the media\n" \
                    "🔗 Just paste a TikTok URL here and I'll do the rest"
    await update.message.reply_html(start_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = "📌 <b>How to use this bot:</b>\n\n" \
                   "➊ Copy a link to any TikTok video or photo post\n" \
                   "➋ Send it here\n" \
                   "➌ Get the video or photo gallery with no watermark"
    await update.message.reply_html(help_message)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Sorry, I didn\'t understand that command.',
    )


async def inline_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    video_info = extract_video_info(query)
    result = InlineQueryResultVideo(
        id='1',
        video_url=video_info.get('url'),
        mime_type='video/mp4',
        thumbnail_url=video_info.get('thumbnail'),
        title=video_info.get('title'),
    )
    await update.inline_query.answer([result])


async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    video_bytes = download_video(update.message.text)
    if not video_bytes:
        await update.message.reply_text('Failed to download / Not supported :(', reply_to_message_id=update.message.message_id)
        return
    await update.message.reply_video(video_bytes, reply_to_message_id=update.message.message_id)


def download_video(url: str) -> bytes | None:
    try:
        unique_id = uuid4()
        ydl_opts = {
            'format': 'bv[ext=mp4][height<=1080]+ba/b',
            'outtmpl': os.path.join(DOWNLOADS_DIR, f'{unique_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_ext = info.get('ext')

        video_path = os.path.join(DOWNLOADS_DIR, f'{unique_id}.{video_ext}')
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        os.remove(video_path)
        return video_bytes

    except Exception as e:
        logging.error(e)
        return None


def extract_video_info(url: str) -> Dict[str, str] | None:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail'),
            }
    except Exception as e:
        logging.error(e)
        return None


def main() -> None:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.add_handler(
        MessageHandler(filters.TEXT & (filters.Entity(MessageEntity.URL) | filters.Entity(MessageEntity.TEXT_LINK)),
                       send_video)
    )

    application.add_handler(InlineQueryHandler(inline_video))

    application.run_polling()


if __name__ == '__main__':
    main()
