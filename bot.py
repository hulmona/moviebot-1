import os
import logging
import threading
from flask import Flask
from threading import Thread
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from bson import ObjectId

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URI = os.getenv("DATABASE_URI")
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)

mongo = MongoClient(DATABASE_URI)
db = mongo["autofilter"]
movies = db.movies

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot alive"

def run_web():
    app.run(host="0.0.0.0", port=PORT)

def delete_later(bot, chat_id, msg_id, delay=300):
    def delete():
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Timer(delay, delete).start()

def start(update, context):
    update.message.reply_text(
        "👋 হ্যালো!\n\nমুভির নাম লিখুন।\nফাইল ৫ মিনিট পর ডিলিট হবে (কপিরাইট ইস্যু)"
    )

def search(update, context):
    query = update.message.text
    chat_id = update.message.chat_id

    results = list(movies.find({"$text": {"$search": query}}).limit(10))

    if not results:
        update.message.reply_text("মুভি পাওয়া যায়নি")
        return

    btn = []
    for m in results:
        btn.append([InlineKeyboardButton(m["title"], callback_data=str(m["_id"]))])

    update.message.reply_text(
        "রেজাল্ট:",
        reply_markup=InlineKeyboardMarkup(btn)
    )

def callback(update, context):
    q = update.callback_query
    q.answer()

    movie = movies.find_one({"_id": ObjectId(q.data)})

    msg = context.bot.send_document(
        chat_id=q.message.chat_id,
        document=movie["file_id"],
        caption="⚠️ ৫ মিনিট পর ফাইল ডিলিট হবে"
    )

    delete_later(context.bot, q.message.chat_id, msg.message_id)

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search))
    dp.add_handler(CallbackQueryHandler(callback))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    Thread(target=run_bot).start()
    run_web()
