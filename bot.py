import os
import logging
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from pymongo import MongoClient
from bson import ObjectId
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URI = os.getenv("DATABASE_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "autofilter")
PORT = int(os.environ.get("PORT", 10000))
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", 300))
MAX_BTN = int(os.getenv("MAX_BTN", 10))

logging.basicConfig(level=logging.INFO)

# ===== DB =====
mongo = MongoClient(DATABASE_URI)
db = mongo[DATABASE_NAME]
movies = db.movies

# ===== WEB =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

def run_web():
    app.run(host="0.0.0.0", port=PORT)

# ===== DELETE =====
def delete_later(bot, chat_id, msg_id, delay=AUTO_DELETE_TIME):
    def delete():
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Timer(delay, delete).start()

# ===== START =====
def start(update, context):
    text = """
👋 হ্যালো!

🎬 মুভির নাম লিখুন  
আমি সার্চ করে দিব  

⚠️ ফাইল ৫ মিনিট পর ডিলিট হবে  
(কপিরাইট ইস্যুর কারণে)

ফাইল অন্য চ্যাটে ফরওয়ার্ড করে  
ডাউনলোড শুরু করুন।
"""
    update.message.reply_text(text)

# ===== SEARCH =====
def search(update, context):
    query = update.message.text
    chat_id = update.message.chat_id

    results = list(movies.find(
        {"$text": {"$search": query}}
    ).limit(MAX_BTN))

    if not results:
        update.message.reply_text("❌ মুভি পাওয়া যায়নি")
        return

    buttons = []
    for m in results:
        buttons.append([
            InlineKeyboardButton(
                m.get("title","movie"),
                callback_data=f"m_{m['_id']}"
            )
        ])

    msg = update.message.reply_text(
        "রেজাল্ট:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    delete_later(context.bot, chat_id, msg.message_id, 120)

# ===== BUTTON =====
def callback(update, context):
    q = update.callback_query
    q.answer()

    movie_id = q.data.split("_")[1]
    movie = movies.find_one({"_id": ObjectId(movie_id)})

    caption = """
⚠️ এই ফাইল ৫ মিনিট পর ডিলিট হবে  
(কপিরাইট ইস্যু)

দ্রুত ফরওয়ার্ড করুন।
"""

    file_msg = context.bot.send_document(
        chat_id=q.message.chat_id,
        document=movie["file_id"],
        caption=caption
    )

    delete_later(context.bot, q.message.chat_id, file_msg.message_id)

# ===== BOT =====
def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search))
    dp.add_handler(CallbackQueryHandler(callback))

    updater.start_polling()
    updater.idle()

# ===== MAIN =====
if __name__ == "__main__":
    Thread(target=run_bot).start()
    run_web()
