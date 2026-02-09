import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL"))
AUTO_DELETE_TIME = 300

bot = Client("moviebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# web server
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# auto delete
def delete_later(chat_id, msg_id):
    def delete():
        try:
            bot.delete_messages(chat_id, msg_id)
        except:
            pass
    threading.Timer(AUTO_DELETE_TIME, delete).start()

# start
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 হ্যালো!\nমুভির নাম লিখুন, রেজাল্ট পাবেন।"
    )

# search
@bot.on_message(filters.text)
async def search(client, message):
    query = message.text.lower()

    async for msg in bot.search_messages(BIN_CHANNEL, query, limit=1):
        if msg.document:
            file_id = msg.document.file_id

            btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📥 Download", callback_data=f"get_{file_id}")]]
            )

            await message.reply_text("🎬 Movie found", reply_markup=btn)
            return

# button
@bot.on_callback_query()
async def cb(client, query):
    if query.data.startswith("get_"):
        file_id = query.data.split("_", 1)[1]

        sent = await query.message.reply_document(
            file_id,
            caption="⚠️ ৫ মিনিট পর ডিলিট হবে"
        )
        delete_later(sent.chat.id, sent.id)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
