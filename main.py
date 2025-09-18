import asyncio
from dotenv import load_dotenv
import telebot
from telebot.async_telebot import AsyncTeleBot
import requests
import os

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
bot = AsyncTeleBot(API_TOKEN)


@bot.message_handler(commands=['start'])
async def handle_start(message):
    start_message = (
        f"👋 Welcome, <b>{message.from_user.first_name}</b>\n"
        "Send me a TikTok link and I’ll return the media\n\n"
        "🔗 Just paste a TikTok URL here and I’ll do the rest"
    )
    await bot.send_message(message.chat.id, start_message, parse_mode="HTML")


@bot.message_handler(commands=['help'])
async def handle_help(message):
    help_message = (
        "📌 <b>How to use this bot:</b>\n\n"
        "➊ Copy a link to any TikTok video or photo post\n"
        "➋ Send it here\n"
        "➌ Get the video or photo gallery with no watermark"
    )
    await bot.send_message(message.chat.id, help_message, parse_mode="HTML")


@bot.message_handler(func=lambda msg: "https://" in msg.text and "tiktok.com/" in msg.text)
async def handle_tiktok_link(message) -> None:
    try:
        media = get_tiktok_media(message.text.strip())

        if media["type"] == "video":
            await bot.send_chat_action(message.chat.id, 'upload_video')
            await bot.send_video(message.chat.id, media["url"], reply_to_message_id=message.message_id)
        elif media["type"] == "images":
            await send_photo_gallery(message.chat.id, media["urls"], message.message_id)
    except Exception as e:
        await bot.reply_to(message, f"❌ Unexpected error:\n{e}")


async def send_photo_gallery(chat_id: int, photos: str, reply_to: int) -> None:
    CHUNK_SIZE = 10
    for i in range(0, len(photos), CHUNK_SIZE):
        chunk = photos[i:i + CHUNK_SIZE]
        media_group = [telebot.types.InputMediaPhoto(url) for url in chunk]
        await bot.send_chat_action(chat_id, 'upload_photo', 10)
        await bot.send_media_group(chat_id, media_group, reply_to_message_id=reply_to)


@bot.message_handler(func=lambda message: True)
async def handle_other(message):
    await bot.reply_to(message, "This is not a valid TikTok video link")


def get_tiktok_media(tiktok_url: str) -> dict:
    api_url = "https://tikwm.com/api/"
    params = {"url": tiktok_url}
    response = requests.get(api_url, params=params)

    data = response.json()
    if data.get("code") != 0:
        raise Exception("API error: " + data.get("msg", "Unknown"))

    media = data["data"]
    if media.get('images'):
        return {"type": "images", "urls": media["images"]}
    return {"type": "video", "url": media["play"]}


if __name__ == '__main__':
    asyncio.run(bot.polling())
