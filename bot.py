import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
API_ID = 38438389
API_HASH = "327b2592682ff56d760110350e66425e"
BOT_TOKEN = "8298490569:AAGOm3fAOhqBxmvwsB2lrF-mCmvqbG3D7Fo"

BIN_CHANNEL = -1003801817080
AUTO_DELETE_TIME = 300

# ================= BOT =================
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= WEB SERVER (Render free) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= AUTO DELETE =================
def delete_later(chat_id, msg_id):
    def delete():
        try:
            bot.delete_messages(chat_id, msg_id)
        except:
            pass
    threading.Timer(AUTO_DELETE_TIME, delete).start()

# ================= START =================
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    text = """
👋 হ্যালো!

🎬 আমি একটি অটো মুভি বট  
গ্রুপে মুভির নাম লিখলেই রেজাল্ট দিব।

⚠️ সতর্কতা:
মুভি ফাইল ৫ মিনিট পর ডিলিট হবে (copyright issue)
ডাউনলোড করতে হলে অন্য চ্যাটে forward করুন।
"""
    await message.reply_text(text)

# ================= SEARCH =================
@bot.on_message(filters.text & filters.group)
async def search(client, message):
    query = message.text.lower()

    async for msg in bot.search_messages(BIN_CHANNEL, query, limit=5):
        file_id = msg.document.file_id

        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📥 Download", callback_data=f"get_{file_id}")]]
        )

        await message.reply_text(
            f"🎬 Result for: {query}",
            reply_markup=btn
        )
        break

# ================= BUTTON =================
@bot.on_callback_query()
async def cb(client, query):
    data = query.data

    if data.startswith("get_"):
        file_id = data.split("_", 1)[1]

        sent = await query.message.reply_document(
            file_id,
            caption="⚠️ ৫ মিনিট পর ফাইল ডিলিট হবে\nForward করে ডাউনলোড করুন"
        )

        delete_later(sent.chat.id, sent.id)

# ================= RUN =================
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run()
