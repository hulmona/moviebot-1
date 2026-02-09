import os
import logging
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from pymongo import MongoClient
from bson import ObjectId
import threading

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URI = os.getenv("DATABASE_URI")
PORT = int(os.environ.get("PORT", 10000))

AUTO_DELETE_TIME = 300  # 5 min
MAX_BTN = 10

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
mongo = MongoClient(DATABASE_URI)
db = mongo["autofilter"]
movies_col = db.movies

# ================= WEB SERVER =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    app.run(host="0.0.0.0", port=PORT)

# ================= HELPERS =================
def delete_later(bot, chat_id, msg_id, delay=AUTO_DELETE_TIME):
    def delete():
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Timer(delay, delete).start()

# ================= START COMMAND =================
def start(update, context):
    user = update.message.from_user.first_name

    text = f"""
👋 হ্যালো {user}!

🤖 আমি একটি অটো মুভি সার্চ বট  
🎬 মুভির নাম লিখলেই রেজাল্ট পাবেন  

📌 ব্যবহার:
গ্রুপে আমাকে add করুন  
তারপর মুভির নাম লিখুন  

⚠️ গুরুত্বপূর্ণ:
মুভি ফাইল ৫ মিনিট পর ডিলিট হয়ে যাবে  
(কপিরাইট ইস্যুর কারণে)

তাই ফাইল অন্য কোথাও ফরওয়ার্ড করে  
ডাউনলোড শুরু করুন।
"""

    btn = [
        [InlineKeyboardButton("➕ গ্রুপে এড করুন", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn))

# ================= SEARCH =================
def search_handler(update, context):
    query = update.message.text
    chat_id = update.message.chat_id

    if not query:
        return

    results = list(movies_col.find(
        {"$text": {"$search": query}}
    ).limit(MAX_BTN))

    if not results:
        update.message.reply_text("❌ এই নামে কোনো মুভি পাওয়া যায়নি")
        return

    buttons = []
    for m in results:
        title = m.get("title", "movie")[:35]
        buttons.append(
            [InlineKeyboardButton(f"🎬 {title}", callback_data=f"m_{m['_id']}")]
        )

    msg = update.message.reply_text(
        f"🔍 '{query}' এর রেজাল্ট:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    delete_later(context.bot, chat_id, msg.message_id, 120)

# ================= BUTTON CLICK =================
def callback(update, context):
    q = update.callback_query
    q.answer()

    data = q.data

    if data.startswith("m_"):
        movie_id = data.split("_")[1]

        movie = movies_col.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            q.edit_message_text("মুভি পাওয়া যায়নি")
            return

        caption = f"""
🎬 {movie.get('title')}

⚠️ গুরুত্বপূর্ণ ⚠️
এই ফাইলটি ৫ মিনিট পর ডিলিট হয়ে যাবে  
(কপিরাইট ইস্যুর কারণে)

দ্রুত অন্য চ্যাটে ফরওয়ার্ড করুন  
এবং ডাউনলোড শুরু করুন।
"""

        file_msg = context.bot.send_document(
            chat_id=q.message.chat_id,
            document=movie["file_id"],
            caption=caption
        )

        delete_later(context.bot, q.message.chat_id, file_msg.message_id)

# ================= BOT THREAD =================
def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_handler))
    dp.add_handler(CallbackQueryHandler(callback))

    updater.start_polling()
    updater.idle()

# ================= MAIN =================
if __name__ == "__main__":
    Thread(target=run_bot).start()
    run_web()
