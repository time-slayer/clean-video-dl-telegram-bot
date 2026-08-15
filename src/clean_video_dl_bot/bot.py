import logging

from telegram import MessageEntity
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN
from .handlers import help_command, inline_video, send_video, start, unknown

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    # Build Application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Register Message Handlers for TikTok Links
    link_filter = filters.TEXT & (
        filters.Entity(MessageEntity.URL) | filters.Entity(MessageEntity.TEXT_LINK)
    )
    app.add_handler(MessageHandler(link_filter, send_video))

    # Register Inline Query Handlers
    app.add_handler(InlineQueryHandler(inline_video))

    # Start Polling
    app.run_polling()
