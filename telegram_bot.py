import asyncio
import io
import logging
import sys
import threading
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
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

import html
import re

def format_for_telegram(text: str) -> str:
    """Convert AI markdown output into clean, reliable, and beautifully rendered Telegram HTML."""
    if not text:
        return ""
    
    # 1. Protect code blocks (```...```)
    code_blocks = []
    def save_cb(match):
        code_blocks.append(match.group(1))
        return f"___CODEBLOCK_{len(code_blocks)-1}___"
    
    formatted = re.sub(r'```(?:[a-zA-Z]*\n)?(.*?)```', save_cb, text, flags=re.DOTALL)
    
    # 2. Protect inline code (`...`)
    inline_codes = []
    def save_ic(match):
        inline_codes.append(match.group(1))
        return f"___INLINECODE_{len(inline_codes)-1}___"
    
    formatted = re.sub(r'`([^`]+)`', save_ic, formatted)
    
    # 3. Escape raw HTML entities
    formatted = html.escape(formatted)
    
    # 4. Convert Markdown Headings (###, ##, #) to bold header lines
    formatted = re.sub(r'^[ \t]*#{1,6}[ \t]+(.*)$', r'<b>\1</b>', formatted, flags=re.MULTILINE)
    
    # 5. Convert horizontal rules (--- or ***) to subtle dividers
    formatted = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '───────────────', formatted, flags=re.MULTILINE)
    
    # 6. Convert Markdown Links [text](url) -> <a href="url">text</a>
    def replace_link(match):
        title = match.group(1)
        url = html.unescape(match.group(2))
        return f'<a href="{url}">{title}</a>'
    
    formatted = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', replace_link, formatted)
    
    # 7. Convert bold (**text** or __text__)
    formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', formatted)
    formatted = re.sub(r'__(.+?)__', r'<b>\1</b>', formatted)
    
    # 8. Convert single star *text* -> <b>text</b>
    formatted = re.sub(r'(?<!\w)\*([^*\n]+?)\*(?!\w)', r'<b>\1</b>', formatted)
    
    # 9. Convert single underscore _text_ -> <i>text</i>
    formatted = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'<i>\1</i>', formatted)
    
    # 10. Clean bullet points: `* ` or `- ` at line start -> `• `
    formatted = re.sub(r'^[ \t]*[\*\-][ \t]+', '• ', formatted, flags=re.MULTILINE)
    
    # 11. Restore inline code and code blocks
    for i, code in enumerate(inline_codes):
        formatted = formatted.replace(f"___INLINECODE_{i}___", f"<code>{html.escape(code)}</code>")
        
    for i, code in enumerate(code_blocks):
        formatted = formatted.replace(f"___CODEBLOCK_{i}___", f"<pre>{html.escape(code)}</pre>")
        
    return formatted

async def send_clean_reply(message, text: str):
    """Send a response formatted cleanly as Telegram HTML with fallback."""
    formatted_html = format_for_telegram(text)
    try:
        await message.reply_text(
            formatted_html,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.warning(f"HTML send failed ({e}), sending plain text")
        await message.reply_text(text)

async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else 0
    if not settings.is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt from user ID {user_id}")
        if update.message:
            await update.message.reply_text(
                f"⛔ <b>Access Denied:</b> Your Telegram User ID (<code>{user_id}</code>) is not authorized to interact with this Notion workspace.",
                parse_mode=ParseMode.HTML
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
        "I am connected to your *Life Hub* workspace and ready to help you manage your projects, tasks, schedule, and daily health from your phone.\n\n"
        "✨ *Things you can do:*\n"
        "• 🌅 *Daily Morning Briefing:* Type /briefing anytime, or receive it automatically every morning at 6:00 AM.\n"
        "• 💬 *Text me:* _'What are my high priority tasks for BSIT-31A?'_\n"
        "• 📅 *Check Schedule:* _'Scan my calendar and schedule for today'_\n"
        "• 🎙️ *Send a Voice Note:* Hold the mic button and tell me what tasks or notes to record.\n"
        "• ➕ *Create Tasks:* _'Add task: Study for midterms due Friday'_\n"
        "• 🏃 *Track Fitness:* _'Log 40min treadmill walk: 2.91 km, 4006 steps, 203 cal'_\n"
        "• 🔍 *Search Workspace:* _'Find notes on Cianotes App'_\n"
        "• ✍️ *Append Notes:* _'Add bullet point to my Daily Journal: Completed project setup today'_\n\n"
        "Use /help to see more examples or /status to check connections."
    )
    await send_clean_reply(update.message, welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not await check_auth(update):
        return

    help_text = (
        "💡 *Notion AI Assistant Help & Examples*\n\n"
        "🌅 *Morning Briefing:*\n"
        "• `/briefing` or `/briefing now` — Receive today's schedule briefing immediately\n"
        "• `/briefing status` — View your morning briefing schedule status\n\n"
        "📋 *Tasks & Schedule:*\n"
        "• _'Scan my calendar schedule for today'_\n"
        "• _'List all active projects in my Life Hub'_\n"
        "• _'Add a high-priority task for BSIT-31A: 3D FaceModel activity'_\n"
        "• _'Mark the task Study for Finals as Done'_\n\n"
        "🏃 *Health & Treadmill:*\n"
        "• _'Log my workout: 15 min brisk walk, 0.86 km, 1371 steps, 192 cal'_\n\n"
        "📝 *Notes & Pages:*\n"
        "• _'Read the page BSIT-31A'_\n"
        "• _'Create a new page called Weekend Shopping List under Life Hub'_\n"
        "• _'Append to my Journal: Great progress on the AI assistant today'_\n\n"
        "🎙️ *Voice Notes:*\n"
        "• Simply send any voice message and I will transcribe and execute your request!"
    )
    await send_clean_reply(update.message, help_text)

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /briefing command to trigger or view daily briefing status."""
    if not await check_auth(update):
        return

    user_id = str(update.effective_user.id)
    args = context.args or []
    
    if args and args[0].lower() in ("status", "info"):
        tz = timezone(timedelta(hours=settings.UTC_OFFSET_HOURS))
        current_time_str = datetime.now(tz).strftime("%I:%M %p")
        status_msg = (
            "🌅 <b>Daily Morning Briefing Settings</b>\n\n"
            f"• <b>Status:</b> {'🟢 Active (Sending daily)' if settings.DAILY_BRIEFING_ENABLED else '🔴 Paused'}\n"
            f"• <b>Scheduled Time:</b> <code>{settings.DAILY_BRIEFING_TIME}</code> (Asia/Manila, UTC+8)\n"
            f"• <b>Current Local Time:</b> <code>{current_time_str}</code>\n\n"
            "<b>Usage:</b>\n"
            "• <code>/briefing</code> or <code>/briefing now</code> — Generate today's briefing immediately."
        )
        await send_clean_reply(update.message, status_msg)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    loop = asyncio.get_running_loop()
    briefing_text = await loop.run_in_executor(
        None,
        gemini_agent.generate_daily_briefing,
        user_id
    )
    await send_clean_reply(update.message, briefing_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not await check_auth(update):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        pages = notion_service.search_workspace(query="", filter_type="page")
        status_text = (
            "✅ *System Status: ALL SYSTEMS OPERATIONAL*\n\n"
            "• 🤖 *AI Engine:* Google Gemini (High-Speed & Multi-Tier Fallback)\n"
            f"• 🗄️ *Notion Status:* Connected ({len(pages)} accessible pages found)\n"
            f"• 👤 *Authorized User ID:* `{update.effective_user.id}`\n"
            "• 🎙️ *Voice Note Processing:* Active\n"
            "• ⚡ *Active Tiers:* Gemini 3.5 Flash Lite / 3.1 Flash Lite / Flash Lite Latest / 3 Flash / 3.7 Flash"
        )
    except Exception as e:
        status_text = f"⚠️ *Notion Connection Error:* {str(e)}"

    await send_clean_reply(update.message, status_text)

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

    await send_clean_reply(update.message, reply)

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

    await send_clean_reply(update.message, reply)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal HTTP server responding to cloud health checks (Render, Koyeb, Railway)."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","service":"telegram-notion-ai-bot"}')

    def log_message(self, format, *args):
        # Suppress routine health check log noise
        pass

def start_health_server(port: int):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Health check HTTP server active on port {port}")
    except Exception as e:
        logger.warning(f"Could not bind health server on port {port}: {e}")

async def daily_briefing_scheduler(app: Application):
    """Background loop that sleeps until target morning briefing time and sends proactive messages."""
    logger.info(f"Daily briefing scheduler active. Scheduled: {settings.DAILY_BRIEFING_TIME} (UTC+{settings.UTC_OFFSET_HOURS})")
    
    while True:
        try:
            tz = timezone(timedelta(hours=settings.UTC_OFFSET_HOURS))
            now = datetime.now(tz)
            
            try:
                target_parts = settings.DAILY_BRIEFING_TIME.split(":")
                target_hour = int(target_parts[0])
                target_minute = int(target_parts[1])
            except Exception:
                target_hour, target_minute = 6, 0
                
            target_time_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if now >= target_time_today:
                next_trigger = target_time_today + timedelta(days=1)
            else:
                next_trigger = target_time_today
                
            sleep_seconds = (next_trigger - now).total_seconds()
            logger.info(f"Next daily briefing in {sleep_seconds/3600:.2f} hours ({next_trigger.strftime('%Y-%m-%d %H:%M:%S')})")
            
            await asyncio.sleep(sleep_seconds)
            
            if settings.DAILY_BRIEFING_ENABLED:
                logger.info("Broadcasting scheduled morning briefing to authorized users...")
                loop = asyncio.get_running_loop()
                
                for user_id in settings.ALLOWED_TELEGRAM_USER_IDS:
                    try:
                        briefing_text = await loop.run_in_executor(
                            None,
                            gemini_agent.generate_daily_briefing,
                            str(user_id)
                        )
                        formatted_html = format_for_telegram(briefing_text)
                        await app.bot.send_message(
                            chat_id=user_id,
                            text=formatted_html,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Morning briefing delivered to user ID {user_id}")
                    except Exception as err:
                        logger.error(f"Failed delivering morning briefing to user {user_id}: {err}")
            
            # Sleep 60 seconds after trigger to prevent double-firing
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("Daily briefing scheduler stopped.")
            break
        except Exception as e:
            logger.error(f"Error in daily briefing scheduler: {e}", exc_info=True)
            await asyncio.sleep(60)

async def post_init(application: Application) -> None:
    """Initialize background services when bot event loop starts."""
    asyncio.create_task(daily_briefing_scheduler(application))

def main():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not set in .env")
        return

    # Start background health server for Render / Koyeb / Railway port binding
    start_health_server(settings.PORT)

    print("🤖 Starting Telegram Notion AI Bot...")
    
    # Configure custom timeout for reliable connection
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    app = Application.builder().token(token).request(request).post_init(post_init).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("briefing", briefing_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print(f"🚀 Bot is running in polling mode on port {settings.PORT}. Daily briefing scheduled at {settings.DAILY_BRIEFING_TIME}.")
    app.run_polling(bootstrap_retries=5)

if __name__ == "__main__":
    main()

