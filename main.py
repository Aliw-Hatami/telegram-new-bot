import os
import json
import time
import feedparser
import requests
import asyncio
from flask import Flask
from threading import Thread
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RSS_FEEDS = [
    "https://www.zoomit.ir/feed/",
    "https://digiato.com/feed"
]
CHECK_INTERVAL = 600
SENT_TITLES_FILE = "sent_titles.json"
CHANNEL_LINK = "https://t.me/Daijoplus"

def load_sent_titles():
    if not os.path.exists(SENT_TITLES_FILE):
        return set()
    with open(SENT_TITLES_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_sent_titles(titles):
    with open(SENT_TITLES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(titles), f, ensure_ascii=False, indent=2)

def is_valid_image(url):
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200 and "image" in r.headers.get("content-type", "")
    except Exception:
        return False

async def fetch_and_send(bot):
    sent_titles = load_sent_titles()
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or title in sent_titles:
                    continue

                image_url = None
                if "media_content" in entry and entry.media_content:
                    image_url = entry.media_content[0].get("url")
                elif "enclosures" in entry and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image"):
                            image_url = enc.get("href")
                            break

                message = f"{title}\n\nلینک کانال: {CHANNEL_LINK}"
                try:
                    if image_url and is_valid_image(image_url):
                        await bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=message)
                    else:
                        await bot.send_message(chat_id=CHAT_ID, text=message)

                    print(f"ارسال شد: {title}")
                    sent_titles.add(title)
                    save_sent_titles(sent_titles)
                except Exception as send_error:
                    print(f"خطا در ارسال: {send_error}")
        except Exception as fetch_error:
            print(f"خطا در دریافت فید: {fetch_error}")

app = Flask(__name__)
@app.route("/")
def home():
    return "ربات فعال است."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

async def main():
    bot = Bot(token=BOT_TOKEN)
    keep_alive()
    while True:
        await fetch_and_send(bot)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "main":
    asyncio.run(main())
