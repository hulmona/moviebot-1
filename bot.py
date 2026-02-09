import os
import sys
import subprocess
import logging
import threading
from datetime import datetime

# ==================== AUTO INSTALL TELEGRAM BOT ====================
print("🔧 Checking and installing required packages...")

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
    print("✅ python-telegram-bot v13.15 installed")
except ImportError:
    print("📦 Installing python-telegram-bot v13.15...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.15"])
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
    print("✅ python-telegram-bot v13.15 installed successfully")

try:
    from pymongo import MongoClient
    from bson import ObjectId
    print("✅ pymongo already installed")
except ImportError:
    print("📦 Installing pymongo...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])
    from pymongo import MongoClient
    from bson import ObjectId
    print("✅ pymongo installed successfully")

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8298490569:AAGOm3fAOhqBxmvwsB2lrF-mCmvqbG3D7Fo")
DATABASE_URI = os.getenv("DATABASE_URI", "mongodb+srv://moviebot:Movie%4012345@cluster0.3qgtiud.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "autofilter")
ADMINS = list(map(int, os.getenv("ADMINS", "7916138581").split(",")))
BIN_CHANNEL = int(os.getenv("BIN_CHANNEL", "-1003801817080"))
AUTO_FFILTER = os.getenv("AUTO_FFILTER", "True") == "True"
SPELL_CHECK_REPLY = os.getenv("SPELL_CHECK_REPLY", "True") == "True"
MAX_BTN = int(os.getenv("MAX_BTN", "10"))
AUTO_DELETE = os.getenv("AUTO_DELETE", "True") == "True"
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "300"))

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================
try:
    mongo_client = MongoClient(DATABASE_URI)
    db = mongo_client[DATABASE_NAME]
    movies_col = db.movies
    users_col = db.users
    groups_col = db.groups
    
    # Create text index for search
    movies_col.create_index([("title", "text"), ("caption", "text")])
    print("✅ MongoDB connected successfully")
    print(f"📊 Total movies in DB: {movies_col.count_documents({})}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise

# ==================== HELPER FUNCTIONS ====================
def delete_later(bot, chat_id, message_id, delay=AUTO_DELETE_TIME):
    """Delete message after specified delay"""
    def delete():
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Delete error: {e}")
    threading.Timer(delay, delete).start()

def save_user(user_id, username=""):
    """Save user to database"""
    try:
        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"username": username, "joined_at": datetime.now()}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Save user error: {e}")

def save_group(chat_id, title=""):
    """Save group to database"""
    try:
        groups_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "added_at": datetime.now()}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Save group error: {e}")

# ==================== HANDLERS ====================
def start_command(update, context):
    """Handle /start command"""
    user = update.message.from_user
    save_user(user.id, user.username)
    
    welcome_text = f"""
👋 **হ্যালো {user.first_name}!**

🤖 **আমি একটি অটো মুভি সার্চ বট**
🎬 **20,000+ মুভি ডাটাবেজ**
⚡ **অটো সার্চ & অটো ডিলিট**

📌 **ইউজেজ:**
1. আমাকে কোনো গ্রুপে এড করুন (Admin দিতে হবে)
2. গ্রুপে মুভির নাম লিখুন
3. আমি সার্চ করে ফলাফল দিব
4. বাটনে ক্লিক করে মুভি ডাউনলোড করুন

⚠️ **সতর্কতা:**
• মুভি ফাইল ৫ মিনিট পর অটো ডিলিট হয়ে যাবে
• ফাইল অন্য চ্যাটে ফরওয়ার্ড করে ডাউনলোড শুরু করুন

🔗 **সাপোর্ট গ্রুপ:** @movieniverse
    """
    
    keyboard = [
        [InlineKeyboardButton("📢 আপডেট চ্যানেল", url="https://t.me/moviechannelbd")],
        [InlineKeyboardButton("📞 সাপোর্ট গ্রুপ", url="https://t.me/movieniverse")],
        [InlineKeyboardButton("➕ গ্রুপে এড করুন", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def help_command(update, context):
    """Handle /help command"""
    help_text = """
🆘 **হেল্প মেনু:**

🔍 **সার্চ করতে:**
গ্রুপে শুধু মুভির নাম লিখুন

⚙️ **এডমিন কমান্ড:**
• /stats - বট স্ট্যাটাস

📌 **ফিচারস:**
• অটো মুভি সার্চ
• ইনলাইন বাটন রেজাল্ট
• অটো ডিলিট ৫ মিনিট পর
• 20K+ মুভি ডাটাবেজ
• বাংলা ইংলিশ সব ভাষা

🔗 **চ্যানেল:** @moviechannelbd
👥 **গ্রুপ:** @movieniverse
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def stats_command(update, context):
    """Handle /stats command (admin only)"""
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        update.message.reply_text("❌ এই কমান্ড শুধু এডমিনদের জন্য।")
        return
    
    try:
        total_movies = movies_col.count_documents({})
        total_users = users_col.count_documents({})
        total_groups = groups_col.count_documents({})
        
        stats_text = f"""
📊 **বট স্ট্যাটিস্টিক্স:**

🎬 **মোট মুভি:** {total_movies}
👤 **মোট ইউজার:** {total_users}
👥 **মোট গ্রুপ:** {total_groups}
⏰ **আপটাইম:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        update.message.reply_text(stats_text, parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text(f"❌ স্ট্যাটস লোড করতে সমস্যা: {e}")

def auto_filter_handler(update, context):
    """Handle auto filter in groups"""
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    query = update.message.text.strip()
    
    # Save group info
    save_group(chat_id, update.message.chat.title)
    
    if not query or len(query) < 2:
        return
    
    logger.info(f"Search query: '{query}' from {user_id} in {chat_id}")
    
    # Search in database
    try:
        results = list(movies_col.find(
            {"$text": {"$search": query}}
        ).limit(MAX_BTN))
        
        if not results:
            if SPELL_CHECK_REPLY:
                update.message.reply_text("❌ এই নামে কোনো মুভি পাওয়া যায়নি।")
            return
        
        buttons = []
        for movie in results:
            title = movie.get('title', 'Unknown')[:35]
            quality = movie.get('quality', 'N/A')
            size = movie.get('size', 'N/A')
            year = movie.get('year', '')
            
            button_text = f"🎬 {title}"
            if year:
                button_text += f" ({year})"
            button_text += f" | {quality} | {size}"
            
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"movie_{movie['_id']}")])
        
        # Add page navigation if many results
        if len(results) == MAX_BTN:
            buttons.append([InlineKeyboardButton("📖 আরো রেজাল্ট দেখুন", callback_data=f"next_1_{query}")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        result_msg = update.message.reply_text(
            f"🔍 **'{query}'** এর জন্য {len(results)}টি রেজাল্ট:\n\n"
            "⬇️ নিচের বাটনে ক্লিক করে মুভি ডাউনলোড করুন:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Auto delete search results after 2 minutes
        if AUTO_DELETE:
            delete_later(context.bot, chat_id, result_msg.message_id, 120)
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        update.message.reply_text("❌ সার্চ করতে সমস্যা হয়েছে।")

def callback_handler(update, context):
    """Handle button callbacks"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    logger.info(f"Callback: {data} from {user_id}")
    
    if data.startswith("movie_"):
        # Send movie file
        movie_id = data.split("_")[1]
        
        try:
            movie = movies_col.find_one({"_id": ObjectId(movie_id)})
            if not movie:
                query.edit_message_text("❌ মুভিটি পাওয়া যায়নি।")
                return
            
            # Prepare caption
            caption = f"""
🎬 **{movie.get('title', 'Unknown')}**
📅 ইয়ার: {movie.get('year', 'N/A')}
🗂 কোয়ালিটি: {movie.get('quality', 'N/A')}
📦 সাইজ: {movie.get('size', 'N/A')}
🎭 জেনার: {movie.get('genre', 'N/A')}
🌍 ভাষা: {movie.get('language', 'N/A')}

⚠️ **গুরুত্বপূর্ণ ⚠️**
এই মুভি ফাইলটি {AUTO_DELETE_TIME//60} মিনিট পর অটো ডিলিট হয়ে যাবে (কপিরাইট ইস্যু)। 
**অনুগ্রহ করে এই ফাইলটি অন্য কোথাও ফরওয়ার্ড করুন এবং সেখানে ডাউনলোড শুরু করুন।**
            """
            
            # Send movie file
            try:
                file_msg = context.bot.send_document(
                    chat_id=chat_id,
                    document=movie['file_id'],
                    caption=caption,
                    parse_mode='Markdown'
                )
                
                # Auto delete movie after specified time
                if AUTO_DELETE:
                    delete_later(context.bot, chat_id, file_msg.message_id, AUTO_DELETE_TIME)
                
                # Send reminder
                reminder_text = f"""
⏰ **রিমাইন্ডার**
এই ফাইলটি {AUTO_DELETE_TIME//60} মিনিট পর ডিলিট হবে।
দ্রুত অন্য চ্যাটে **ফরওয়ার্ড** করুন এবং ডাউনলোড শুরু করুন!
                """
                reminder_msg = context.bot.send_message(chat_id, reminder_text)
                delete_later(context.bot, chat_id, reminder_msg.message_id, AUTO_DELETE_TIME - 60)
                
            except Exception as e:
                logger.error(f"Send document error: {e}")
                query.edit_message_text("❌ ফাইল সেন্ড করতে সমস্যা হয়েছে।")
        
        except Exception as e:
            logger.error(f"Movie fetch error: {e}")
            query.edit_message_text("❌ মুভি লোড করতে সমস্যা হয়েছে।")
    
    elif data.startswith("next_"):
        # Handle pagination
        query.edit_message_text("📖 পরের পেজ ডেভেলপমেন্ট চলছে...")

def main():
    """Main function to run the bot"""
    print("=" * 50)
    print("🎬 MOVIE BOT STARTING...")
    print(f"📊 Movies in DB: {movies_col.count_documents({})}")
    print("=" * 50)
    
    try:
        # Create Updater
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("stats", stats_command))
        
        # Auto filter handler for groups
        if AUTO_FFILTER:
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.group, auto_filter_handler))
        
        # Callback query handler
        dp.add_handler(CallbackQueryHandler(callback_handler))
        
        # Start the bot
        updater.start_polling()
        print("✅ Bot started successfully!")
        print(f"🤖 Username: @{updater.bot.username}")
        print("=" * 50)
        
        updater.idle()
        
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")

if __name__ == "__main__":
    main()
