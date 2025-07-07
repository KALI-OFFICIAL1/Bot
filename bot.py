# funstat_telelog_bot.py
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
from pymongo import MongoClient

# Configuration
API_ID = int(os.getenv("API_ID","21546320"))
API_HASH = os.getenv("API_HASH","c16805d6f2393d35e7c49527daa317c7")
BOT_TOKEN = os.getenv("BOT_TOKEN","7635808558:AAFTTOt7adAuS3DRGvlufuJWj5hWfIAobxE")
MONGO_URI = os.getenv("MONGO_URI","mongodb+srv://Ishuxd:ishusomuxd@ishuxd.78ljc.mongodb.net/?retryWrites=true&w=majority&appName=Ishuxd")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID","-1002538785183"))

# Pyrogram Client
app = Client("funstat_telelog", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Setup
mongo = MongoClient(MONGO_URI)
db = mongo["FunStatTelelog"]
msg_db = db["message_stats"]
log_db = db["logs"]

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Count messages for stats
@app.on_message(filters.group & ~filters.service)
def count_messages(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    data = msg_db.find_one({"chat_id": message.chat.id, "user_id": user.id})
    if data:
        msg_db.update_one({"_id": data["_id"]}, {"$inc": {"count": 1}})
    else:
        msg_db.insert_one({
            "chat_id": message.chat.id,
            "user_id": user.id,
            "username": user.username or user.first_name,
            "count": 1
        })

# /me command: Show your stats
@app.on_message(filters.command("me") & filters.group)
def my_stats(client: Client, message: Message):
    user = message.from_user
    data = msg_db.find_one({"chat_id": message.chat.id, "user_id": user.id})
    count = data["count"] if data else 0
    message.reply_text(f"👤 Your message count: {count}")

# /top command: Show top users
@app.on_message(filters.command("top") & filters.group)
def top_stats(client: Client, message: Message):
    stats = msg_db.find({"chat_id": message.chat.id}).sort("count", -1).limit(10)
    leaderboard = "🏆 Top Active Users:\n"
    for i, user in enumerate(stats, 1):
        leaderboard += f"{i}. {user['username']} – {user['count']} msgs\n"
    message.reply_text(leaderboard)

# Log all messages for tracking
@app.on_message(filters.group, group=-100)
def deleted_logger(client: Client, message: Message):
    log_db.insert_one({
        "type": "message",
        "chat_id": message.chat.id,
        "user_id": message.from_user.id if message.from_user else None,
        "username": message.from_user.username if message.from_user else "N/A",
        "content": message.text or "[non-text]",
        "deleted": False,
        "timestamp": datetime.utcnow()
    })

# Log deleted messages
@app.on_deleted_messages()
def log_deleted_messages(client: Client, messages):
    for message in messages:
        if message:
            log_db.insert_one({
                "type": "deleted",
                "chat_id": message.chat.id,
                "user_id": message.from_user.id if message.from_user else None,
                "username": message.from_user.username if message.from_user else "N/A",
                "content": message.text or "[non-text]",
                "timestamp": datetime.utcnow()
            })
            try:
                client.send_message(
                    LOG_CHAT_ID,
                    f"🗑️ Deleted message from @{message.from_user.username if message.from_user else 'Unknown'} in {message.chat.title}:\n{message.text or '[non-text]'}"
                )
            except:
                pass

# Log edited messages
@app.on_edited_message(filters.group)
def edited_logger(client: Client, message: Message):
    log_db.insert_one({
        "type": "edited",
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "new_content": message.text,
        "timestamp": datetime.utcnow()
    })
    try:
        client.send_message(
            LOG_CHAT_ID,
            f"✏️ Edited message by @{message.from_user.username} in {message.chat.title}:\n{message.text}"
        )
    except:
        pass

# Log member joins/leaves
@app.on_message(filters.service & filters.group)
def service_logs(client: Client, message: Message):
    log_text = ""
    if message.new_chat_members:
        for user in message.new_chat_members:
            log_text += f"✅ Joined: @{user.username or user.first_name}\n"
    elif message.left_chat_member:
        log_text += f"❌ Left: @{message.left_chat_member.username or message.left_chat_member.first_name}"
    if log_text:
        log_db.insert_one({
            "type": "member_update",
            "chat_id": message.chat.id,
            "log": log_text,
            "timestamp": datetime.utcnow()
        })
        try:
            client.send_message(LOG_CHAT_ID, log_text)
        except:
            pass

# Run the bot
app.run()
