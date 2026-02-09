import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# -------- ENV --------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL"))
AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", 300))

API_ID = 123456
API_HASH = "0123456789abcdef0123456789abcdef"

# -------- BOT --------
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------- START --------
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Welcome!\nMovie name ba file link send korun."
    )

# -------- FILE SEND --------
@bot.on_message(filters.private & filters.text)
async def send_file(client, message):
    txt = message.text

    if txt.startswith("file_"):
        try:
            file_id = int(txt.split("file_")[1])

            sent = await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=BIN_CHANNEL,
                message_id=file_id
            )

            warn = await message.reply_text(
                "⚠️ Copyright issue er jonno file 5 min por delete hobe.\nForward kore nin."
            )

            await asyncio.sleep(AUTO_DELETE_TIME)

            try:
                await sent.delete()
                await warn.delete()
            except:
                pass

        except:
            await message.reply_text("File error")

# -------- WEB SERVER --------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running..."

def run_web():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# -------- MAIN --------
async def main():
    await bot.start()
    print("Bot started")
    await asyncio.Event().wait()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
