import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== CONFIG =====
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL"))
AUTO_DELETE_TIME = 300

bot = Client("moviebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== WEB SERVER (Render free keep alive) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ===== AUTO DELETE =====
def delete_later(chat_id, msg_id):
    def delete():
        try:
            bot.delete_messages(chat_id, msg_id)
        except:
            pass
    threading.Timer(AUTO_DELETE_TIME, delete).start()

# ===== START =====
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply_text(
        "👋 হ্যালো!\n\n"
        "গ্রুপে মুভির নাম লিখলেই রেজাল্ট দিব।\n"
        "ফাইল ৫ মিনিট পর ডিলিট হবে।"
    )

# ===== SEARCH IN GROUP =====
@bot.on_message(filters.text & filters.group)
async def search(_, message):
    query = message.text.lower()

    async for msg in bot.get_chat_history(BIN_CHANNEL):
        if msg.document and msg.caption:
            if query in msg.caption.lower():

                file_id = msg.document.file_id

                btn = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📥 Download", callback_data=f"get_{file_id}")]]
                )

                await message.reply_text(
                    f"🎬 {msg.caption}",
                    reply_markup=btn
                )
                return

    await message.reply_text("❌ কিছু পাওয়া যায়নি")

# ===== BUTTON =====
@bot.on_callback_query()
async def cb(_, query):
    data = query.data

    if data.startswith("get_"):
        file_id = data.split("_", 1)[1]

        sent = await query.message.reply_document(
            file_id,
            caption="⚠️ ৫ মিনিট পর ডিলিট হবে\nForward করে ডাউনলোড করুন"
        )

        delete_later(sent.chat.id, sent.id)

# ===== RUN =====
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
