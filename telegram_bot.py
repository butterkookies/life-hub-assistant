import asyncio
import io
import logging
import sys
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from config import settings
from gemini_agent import gemini_agent
from notion_service import notion_service

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("telegram_bot")

async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else 0
    if not settings.is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt from user ID {user_id}")
        if update.message:
            await update.message.reply_text(
                f"⛔ *Access Denied:* Your Telegram User ID (`{user_id}`) is not authorized to interact with this Notion workspace.",
                parse_mode=ParseMode.MARKDOWN
            )
        return False
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not await check_auth(update):
        return

    user_name = update.effective_user.first_name if update.effective_user else "there"
    welcome_text = (
        f"👋 *Hi {user_name}! I'm your Notion AI Assistant.*\n\n"
        "I am connected to your *Life Hub* workspace and ready to help you manage your projects, tasks, and notes from your phone.\n\n"
        "✨ *Things you can do:*\n"
        "• 💬 *Text me:* _'What are my high priority tasks for BSIT-31A?'_\n"
        "• 🎙️ *Send a Voice Note:* Hold the mic button and tell me what tasks or notes to record.\n"
        "• ➕ *Create Tasks:* _'Add task: Study for midterms due Friday'_\n"
        "• 🔍 *Search Workspace:* _'Find notes on Cianotes App'_\n"
        "• ✍️ *Append Notes:* _'Add bullet point to my Daily Journal: Completed project setup today'_\n\n"
        "Use /help to see more examples or /status to check connections."
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not await check_auth(update):
        return

    help_text = (
        "💡 *Notion AI Assistant Help & Examples*\n\n"
        "📋 *Tasks & Projects:*\n"
        "• _'List all active projects in my Life Hub'_\n"
        "• _'Add a high-priority task for BSIT-31A: 3D FaceModel activity'_\n"
        "• _'Show me what is overdue or due this week'_\n\n"
        "📝 *Notes & Pages:*\n"
        "• _'Read the page BSIT-31A'_\n"
        "• _'Create a new page called Weekend Shopping List under Life Hub'_\n"
        "• _'Append to my Journal: Great progress on the AI assistant today'_\n\n"
        "🎙️ *Voice Notes:*\n"
        "• Simply send any voice message and I will transcribe and execute your request!"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not await check_auth(update):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        pages = notion_service.search_workspace(query="", filter_type="page")
        status_text = (
            "✅ *System Status: ALL SYSTEMS OPERATIONAL*\n\n"
            f"• 🤖 *AI Engine:* Google Gemini 2.5 Flash\n"
            f"• 🗄️ *Notion Status:* Connected ({len(pages)} accessible pages found)\n"
            f"• 👤 *Authorized User ID:* `{update.effective_user.id}`\n"
            "• 🎙️ *Voice Note Processing:* Active"
        )
    except Exception as e:
        status_text = f"⚠️ *Notion Connection Error:* {str(e)}"

    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text message."""
    if not await check_auth(update):
        return

    user_text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    # Process with Gemini Agent in a background thread to prevent blocking the event loop
    loop = asyncio.get_running_loop()
    reply = await loop.run_in_executor(
        None,
        gemini_agent.process_text_message,
        user_id,
        user_text
    )

    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        # Fallback to plain text if markdown parsing fails
        await update.message.reply_text(reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice note."""
    if not await check_auth(update):
        return

    user_id = str(update.effective_user.id)
    voice = update.message.voice or update.message.audio
    if not voice:
        await update.message.reply_text("⚠️ Could not detect audio stream.")
        return

    # Send typing / recording indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # Download voice note audio bytes
    file = await context.bot.get_file(voice.file_id)
    audio_buffer = io.BytesIO()
    await file.download_to_memory(audio_buffer)
    audio_bytes = audio_buffer.getvalue()

    # Process with Gemini Agent
    loop = asyncio.get_running_loop()
    reply = await loop.run_in_executor(
        None,
        gemini_agent.process_voice_message,
        user_id,
        audio_bytes,
        "audio/ogg"
    )

    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(reply)

def main():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not set in .env")
        return

    print("🤖 Starting Telegram Notion AI Bot...")
    
    # Configure custom timeout for reliable connection
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    app = Application.builder().token(token).request(request).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("🚀 Bot is running in polling mode. Waiting for messages from Telegram...")
    app.run_polling(bootstrap_retries=5)

if __name__ == "__main__":
    main()
