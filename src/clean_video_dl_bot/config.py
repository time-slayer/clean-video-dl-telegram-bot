import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
DOWNLOADS_DIR = "downloads"
BYTES_PER_MB = 1024 * 1024
TELEGRAM_MAX_SIZE_MB = 50
MAX_DOWNLOAD_SIZE_BYTES = TELEGRAM_MAX_SIZE_MB * BYTES_PER_MB
