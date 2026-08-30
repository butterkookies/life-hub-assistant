import asyncio
import functools
import io
import logging
import secrets
import sys
import threading
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from config import settings
from gemini_agent import gemini_agent
from image_models import AttachmentResult, ImageAnalysis, PendingImageScan, WorkoutUpsertResult
from notion_service import notion_service
from email_service import email_service

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("telegram_bot")

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_PENDING_IMAGE_SCANS = 4
MAX_PENDING_IMAGE_BYTES = 40 * 1024 * 1024
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}
PENDING_IMAGE_SCANS: dict[str, PendingImageScan] = {}
RECENT_IMAGE_FILE_IDS: dict[str, datetime] = {}
FAILED_IMAGE_ATTACHMENTS: dict[str, tuple[str, Optional[str], datetime]] = {}

import html
import re

def format_for_telegram(text: str) -> str:
    """Convert AI markdown output into clean, curated, and beautifully rendered Telegram HTML."""
    if not text:
        return ""
    
    # 1. Protect code blocks (```...```)
    code_blocks = []
    def save_cb(match):
        code_blocks.append(match.group(1))
        return f"CODEBLOCKTAG{len(code_blocks)-1}TAG"
    
    formatted = re.sub(r'```(?:[a-zA-Z]*\n)?(.*?)```', save_cb, text, flags=re.DOTALL)
    
    # 2. Protect inline code (`...`)
    inline_codes = []
    def save_ic(match):
        inline_codes.append(match.group(1))
        return f"INLINECODETAG{len(inline_codes)-1}TAG"
    
    formatted = re.sub(r'`([^`]+)`', save_ic, formatted)
    
    # 3. Escape ONLY <, >, & (quote=False keeps apostrophes & quotes clean)
    formatted = html.escape(formatted, quote=False)
    
    # 4. Clean bullet points first: `* ` or `- ` at line start -> `• `
    formatted = re.sub(r'^[ \t]*[\*\-][ \t]+', '• ', formatted, flags=re.MULTILINE)
    
    # 5. Convert Markdown Headings (###, ##, #) to bold header lines
    formatted = re.sub(r'^[ \t]*#{1,6}[ \t]+(.*)$', r'<b>\1</b>', formatted, flags=re.MULTILINE)
    
    # 6. Convert horizontal rules (--- or ***) to subtle dividers
    formatted = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '───────────────', formatted, flags=re.MULTILINE)
    
    # 7. Convert Markdown Links [text](url) -> <a href="url">text</a>
    def replace_link(match):
        title = match.group(1)
        url = html.unescape(match.group(2))
        return f'<a href="{url}">{title}</a>'
    
    formatted = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', replace_link, formatted)
    
    # 8. Convert bold (**text** or __text__)
    formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', formatted)
    formatted = re.sub(r'__(.+?)__', r'<b>\1</b>', formatted)
    
    # 9. Convert parenthetical italic notes *(_text_)* or *(text)*
    formatted = re.sub(r'\*\(_(.+?)_\)\*', r'<i>(\1)</i>', formatted)
    formatted = re.sub(r'\*\((.+?)\)\*', r'<i>(\1)</i>', formatted)
    
    # 10. Convert single underscore _text_ -> <i>text</i>
    formatted = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'<i>\1</i>', formatted)
    
    # 11. Convert single star *text* -> <b>text</b>
    formatted = re.sub(r'(?<!\w)\*([^*\n]+?)\*(?!\w)', r'<b>\1</b>', formatted)
    
    # 12. Restore inline code and code blocks
    for i, code in enumerate(inline_codes):
        formatted = formatted.replace(f"INLINECODETAG{i}TAG", f"<code>{html.escape(code, quote=False)}</code>")
        
    for i, code in enumerate(code_blocks):
        formatted = formatted.replace(f"CODEBLOCKTAG{i}TAG", f"<pre>{html.escape(code, quote=False)}</pre>")
        
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
            await send_clean_reply(
                update.message,
                f"⛔ *Access Denied:* Your Telegram User ID (`{user_id}`) is not authorized to interact with this Notion workspace."
            )
        elif update.callback_query:
            await update.callback_query.answer("Access denied.", show_alert=True)
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
        "• 📧 *Email Notifications:* Morning briefings and alerts can be sent directly to your inbox. (Use /email for details)\n"
        "• 💬 *Text me:* _'What are my high priority tasks for BSIT-31A?'_\n"
        "• 📅 *Check Schedule:* _'Scan my calendar and schedule for today'_\n"
        "• 🎙️ *Send a Voice Note:* Hold the mic button and tell me what tasks or notes to record.\n"
        "• 📷 *Scan a Workout:* Send a clear treadmill display photo to extract and log its stats.\n"
        "• ➕ *Create Tasks:* _'Add task: Study for midterms due Friday'_\n"
        "• 🏃 *Track Fitness:* _'Log 40min treadmill walk: 2.91 km, 4006 steps, 203 cal'_\n"
        "• 🔍 *Search Workspace:* _'Find notes on Cianotes App'_\n"
        "• ✍️ *Append Notes:* _'Add bullet point to my Daily Journal: Completed project setup today'_\n\n"
        "Use /help to see more examples, /email for email alerts, or /status to check connections."
    )
    await send_clean_reply(update.message, welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not await check_auth(update):
        return

    help_text = (
        "💡 *Notion AI Assistant Help & Examples*\n\n"
        "🌅 *Morning Briefing & Email:*\n"
        "• `/briefing` or `/briefing now` — Receive today's schedule briefing immediately\n"
        "• `/briefing email` — Send today's briefing to your email inbox\n"
        "• `/briefing status` — View your morning briefing schedule settings\n"
        "• `/email status` — Check email notification configuration\n"
        "• `/email test` — Send a test email to verify delivery\n\n"
        "📋 *Tasks & Schedule:*\n"
        "• _'Scan my calendar schedule for today'_\n"
        "• _'List all active projects in my Life Hub'_\n"
        "• _'Add a high-priority task for BSIT-31A: 3D FaceModel activity'_\n"
        "• _'Mark the task Study for Finals as Done'_\n\n"
        "🏃 *Health & Treadmill:*\n"
        "• _'Log my workout: 15 min brisk walk, 0.86 km, 1371 steps, 192 cal'_\n\n"
        "📷 *Workout Images:*\n"
        "• Send a clear JPEG, PNG, WebP, HEIC, or HEIF treadmill display photo.\n"
        "• High-confidence scans save automatically; uncertain values show Save, Edit, and Cancel controls.\n\n"
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
        email_status_str = "🟢 Enabled" if (settings.EMAIL_NOTIFICATIONS_ENABLED and email_service.is_configured()) else ("🟡 Configured (Pending credentials)" if settings.NOTIFICATION_EMAIL_TO else "⚪ Disabled")
        status_msg = (
            "🌅 *Daily Morning Briefing Settings*\n\n"
            f"• *Status:* {'🟢 Active (Sending daily)' if settings.DAILY_BRIEFING_ENABLED else '🔴 Paused'}\n"
            f"• *Scheduled Time:* `{settings.DAILY_BRIEFING_TIME}` (Asia/Manila, UTC+8)\n"
            f"• *Current Local Time:* `{current_time_str}`\n"
            f"• *Email Notification:* {email_status_str}\n"
            f"• *Recipient Email:* `{settings.NOTIFICATION_EMAIL_TO or 'Not set'}`\n\n"
            "*Usage:*\n"
            "• `/briefing` or `/briefing now` — Generate today's briefing immediately.\n"
            "• `/briefing email` — Generate briefing and send directly to your email."
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

    # Check if user specifically requested email or if email is configured
    want_email = bool(args and "email" in [a.lower() for a in args])
    email_note = ""
    if (want_email or settings.EMAIL_NOTIFICATIONS_ENABLED) and email_service.is_configured():
        email_success, email_res = await loop.run_in_executor(
            None,
            email_service.send_briefing_email,
            briefing_text
        )
        if email_success:
            email_note = f"\n\n📧 _Also delivered to `{settings.NOTIFICATION_EMAIL_TO}`_"
        elif want_email:
            email_note = f"\n\n⚠️ _Email delivery note: {email_res}_"

    await send_clean_reply(update.message, briefing_text + email_note)

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /email command for managing and testing email notifications."""
    if not await check_auth(update):
        return

    user_id = str(update.effective_user.id)
    args = context.args or []
    action = args[0].lower() if args else "status"

    if action in ("status", "info"):
        is_conf = email_service.is_configured()
        recipient = settings.NOTIFICATION_EMAIL_TO or "Not set in .env"
        provider = "Resend API" if settings.RESEND_API_KEY else (f"SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT})" if settings.SMTP_USER else "None configured")
        
        status_msg = (
            "📧 *Email Notification Settings*\n\n"
            f"• *Status:* {'🟢 Active & Ready' if is_conf else '🔴 Inactive (Credentials needed)'}\n"
            f"• *Recipient:* `{recipient}`\n"
            f"• *Provider:* `{provider}`\n"
            f"• *Sender Name:* `{settings.EMAIL_FROM_NAME}`\n"
            f"• *Scheduled 6:00 AM Email:* {'✅ Enabled' if settings.EMAIL_NOTIFICATIONS_ENABLED else '❌ Disabled'}\n\n"
            "*Commands:*\n"
            "• `/email test` — Send a test notification email\n"
            "• `/briefing email` — Deliver today's briefing to your email inbox immediately"
        )
        await send_clean_reply(update.message, status_msg)
        return

    if action == "test":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        loop = asyncio.get_running_loop()
        success, res_msg = await loop.run_in_executor(
            None,
            email_service.send_notification_email,
            "Test Notification from Notion AI Bot",
            "This is a test notification confirming that your email dispatch is working perfectly with your Telegram Notion AI Bot!"
        )
        if success:
            await send_clean_reply(update.message, f"✅ *Email Sent Successfully!*\n{res_msg}\n\nCheck your inbox at `{settings.NOTIFICATION_EMAIL_TO}`.")
        else:
            await send_clean_reply(update.message, f"⚠️ *Email Dispatch Failed:*\n{res_msg}\n\nPlease check your `NOTIFICATION_EMAIL_TO` and `SMTP_USER/SMTP_PASSWORD` in your environment variables.")
        return

    if action in ("send", "now"):
        # Trigger on-demand briefing to email
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        loop = asyncio.get_running_loop()
        briefing_text = await loop.run_in_executor(
            None,
            gemini_agent.generate_daily_briefing,
            user_id
        )
        success, res_msg = await loop.run_in_executor(
            None,
            email_service.send_briefing_email,
            briefing_text
        )
        if success:
            await send_clean_reply(update.message, f"✅ *Daily Briefing Sent to Email!*\nDelivered to `{settings.NOTIFICATION_EMAIL_TO}`.")
        else:
            await send_clean_reply(update.message, f"⚠️ *Could not send email:*\n{res_msg}")
        return

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not await check_auth(update):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        pages = notion_service.search_workspace(query="", filter_type="page")
        email_badge = "🟢 Active" if email_service.is_configured() else "⚪ Optional (Not set)"
        status_text = (
            "✅ *System Status: ALL SYSTEMS OPERATIONAL*\n\n"
            "• 🤖 *AI Engine:* Google Gemini (High-Speed & Multi-Tier Fallback)\n"
            f"• 🗄️ *Notion Status:* Connected ({len(pages)} accessible pages found)\n"
            f"• 👤 *Authorized User ID:* `{update.effective_user.id}`\n"
            f"• 📧 *Email Notifications:* {email_badge}\n"
            "• 🎙️ *Voice Note Processing:* Active\n"
            "• 📷 *Treadmill Image Scanning:* Active (validated auto-save)\n"
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

    pending = _pending_correction_for_user(
        update.effective_user.id, update.effective_chat.id
    )
    if pending:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        loop = asyncio.get_running_loop()
        try:
            corrected = await loop.run_in_executor(
                None,
                gemini_agent.apply_image_correction,
                pending.analysis,
                user_text,
            )
        except Exception:
            logger.exception("Pending image correction failed")
            await send_clean_reply(
                update.message,
                "⚠️ I couldn't apply that correction. Please state the field and value again.",
            )
            return
        pending.analysis = corrected
        pending.awaiting_correction = False
        pending.shown_conflicts.clear()
        await _send_scan_preview(update.message, pending)
        return
    
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


def _cleanup_image_state() -> None:
    now = datetime.now(timezone.utc)
    expired_tokens = [
        token for token, pending in PENDING_IMAGE_SCANS.items() if pending.is_expired(now)
    ]
    for token in expired_tokens:
        PENDING_IMAGE_SCANS.pop(token, None)
    stale_file_ids = [
        file_id
        for file_id, processed_at in RECENT_IMAGE_FILE_IDS.items()
        if now >= processed_at + timedelta(hours=24)
    ]
    for file_id in stale_file_ids:
        RECENT_IMAGE_FILE_IDS.pop(file_id, None)
    stale_failures = [
        file_id
        for file_id, (_, _, failed_at) in FAILED_IMAGE_ATTACHMENTS.items()
        if now >= failed_at + timedelta(hours=24)
    ]
    for file_id in stale_failures:
        FAILED_IMAGE_ATTACHMENTS.pop(file_id, None)


async def image_state_cleanup_scheduler() -> None:
    """Discard expired image bytes even when the user sends no further updates."""
    while True:
        try:
            await asyncio.sleep(60)
            _cleanup_image_state()
        except asyncio.CancelledError:
            logger.info("Image state cleanup scheduler stopped.")
            break
        except Exception:
            logger.exception("Image state cleanup scheduler failed")


def _pending_correction_for_user(
    user_id: int, chat_id: int
) -> Optional[PendingImageScan]:
    _cleanup_image_state()
    matches = [
        pending
        for pending in PENDING_IMAGE_SCANS.values()
        if pending.user_id == user_id
        and pending.chat_id == chat_id
        and pending.awaiting_correction
    ]
    return max(matches, key=lambda item: item.created_at) if matches else None


def _image_media(message):
    if message.photo:
        photo = message.photo[-1]
        return photo, "image/jpeg", f"treadmill-{photo.file_unique_id}.jpg"
    document = message.document
    if document:
        mime_type = (document.mime_type or "").lower()
        filename = document.file_name or f"treadmill-{document.file_unique_id}"
        return document, mime_type, filename
    return None, "", ""


def _scan_preview_text(
    pending: PendingImageScan,
    conflicts: Optional[dict[str, tuple[object, object]]] = None,
) -> str:
    scan = pending.analysis.treadmill
    if not scan:
        return "⚠️ No treadmill values were found."
    labels = {
        "duration_minutes": "Duration",
        "distance_km": "Distance",
        "steps": "Steps",
        "calories_kcal": "Calories",
        "speed_kmh": "Speed",
        "heart_rate_bpm": "Heart rate",
        "trax_program": "TRAX program",
        "workout_type": "Workout type",
    }
    suffixes = {
        "duration_minutes": " min",
        "distance_km": " km",
        "steps": "",
        "calories_kcal": " kcal",
        "speed_kmh": " km/h",
        "heart_rate_bpm": " bpm",
        "trax_program": "",
        "workout_type": "",
    }
    lines = [
        "📷 *Review treadmill scan*",
        f"• Date: `{scan.date}`",
    ]
    for field, label in labels.items():
        value = getattr(scan, field)
        if value is not None:
            marker = " ⚠️" if field in scan.uncertain_fields else ""
            lines.append(f"• {label}: `{value}{suffixes[field]}`{marker}")
    if conflicts:
        lines.append("\n⚠️ *Existing values differ:* ")
        for field, (existing, incoming) in conflicts.items():
            lines.append(
                f"• {labels.get(field, field)}: `{existing}` → `{incoming}`"
            )
    validation_errors = scan.validation_errors()
    if validation_errors:
        lines.append("\n⚠️ " + "; ".join(validation_errors))
    lines.append(f"\nConfidence: `{scan.confidence:.0%}`")
    return "\n".join(lines)


def _scan_keyboard(token: str, allow_save: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if allow_save:
        buttons.append(
            InlineKeyboardButton("✅ Save", callback_data=f"scan:save:{token}")
        )
    buttons.extend(
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"scan:edit:{token}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"scan:cancel:{token}"),
        ]
    )
    return InlineKeyboardMarkup([buttons])


async def _send_scan_preview(
    message,
    pending: PendingImageScan,
    conflicts: Optional[dict[str, tuple[object, object]]] = None,
) -> None:
    scan = pending.analysis.treadmill
    allow_save = bool(scan and not scan.validation_errors())
    await message.reply_text(
        format_for_telegram(_scan_preview_text(pending, conflicts)),
        parse_mode=ParseMode.HTML,
        reply_markup=_scan_keyboard(pending.token, allow_save=allow_save),
        disable_web_page_preview=True,
    )


def _new_pending_scan(
    update: Update,
    analysis: ImageAnalysis,
    image_bytes: bytes,
    mime_type: str,
    filename: str,
    file_unique_id: str,
) -> PendingImageScan:
    # A user can review only one scan per chat. Replacing it also releases bytes.
    replaced_tokens = [
        token
        for token, existing in PENDING_IMAGE_SCANS.items()
        if existing.user_id == update.effective_user.id
        and existing.chat_id == update.effective_chat.id
    ]
    for token in replaced_tokens:
        PENDING_IMAGE_SCANS.pop(token, None)

    while PENDING_IMAGE_SCANS and (
        len(PENDING_IMAGE_SCANS) >= MAX_PENDING_IMAGE_SCANS
        or sum(len(item.image_bytes) for item in PENDING_IMAGE_SCANS.values())
        + len(image_bytes)
        > MAX_PENDING_IMAGE_BYTES
    ):
        oldest_token = min(
            PENDING_IMAGE_SCANS,
            key=lambda token: PENDING_IMAGE_SCANS[token].created_at,
        )
        PENDING_IMAGE_SCANS.pop(oldest_token, None)

    pending = PendingImageScan(
        token=secrets.token_urlsafe(8),
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
        image_bytes=image_bytes,
        mime_type=mime_type,
        filename=filename,
        file_unique_id=file_unique_id,
        analysis=analysis,
    )
    PENDING_IMAGE_SCANS[pending.token] = pending
    return pending


def _workout_confirmation(
    scan,
    result: WorkoutUpsertResult,
    attachment: Optional[AttachmentResult],
) -> str:
    verb = "created" if result.action == "created" else "updated"
    lines = [
        f"✅ *Workout saved* — daily record {verb}.",
        f"• Date: `{scan.date}`",
    ]
    display = {
        "duration_minutes": ("Duration", " min"),
        "distance_km": ("Distance", " km"),
        "steps": ("Steps", ""),
        "calories_kcal": ("Calories", " kcal"),
        "speed_kmh": ("Speed", " km/h"),
        "heart_rate_bpm": ("Heart rate", " bpm"),
    }
    for field, (label, suffix) in display.items():
        value = getattr(scan, field)
        if value is not None:
            lines.append(f"• {label}: `{value}{suffix}`")
    if attachment and attachment.attached:
        lines.append("• Source image: attached to Notion")
    elif attachment and attachment.retryable:
        lines.append("⚠️ Source image upload failed; resend the image to retry attachment.")
    elif attachment:
        lines.append(
            "⚠️ Notion did not confirm the image block. Check the page before retrying to avoid a duplicate."
        )
    if result.page_url:
        lines.append(f"[Open Daily Health & Workout Log]({result.page_url})")
    return "\n".join(lines)


async def _persist_pending_scan(
    pending: PendingImageScan,
    allow_overwrite: bool,
    expected_conflicts: Optional[dict[str, tuple[object, object]]] = None,
) -> tuple[WorkoutUpsertResult, Optional[AttachmentResult]]:
    scan = pending.analysis.treadmill
    if not scan:
        raise ValueError("Pending scan has no treadmill values")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        functools.partial(
            notion_service.upsert_daily_workout,
            scan,
            allow_overwrite=allow_overwrite,
            expected_conflicts=expected_conflicts,
        ),
    )
    attachment: Optional[AttachmentResult] = None
    if result.action in ("created", "updated"):
        attachment = await loop.run_in_executor(
            None,
            notion_service.attach_image,
            result.page_id,
            pending.image_bytes,
            pending.mime_type,
            pending.filename,
        )
        if pending.file_unique_id and attachment.attached:
            RECENT_IMAGE_FILE_IDS[pending.file_unique_id] = datetime.now(timezone.utc)
            FAILED_IMAGE_ATTACHMENTS.pop(pending.file_unique_id, None)
        elif pending.file_unique_id and attachment.retryable:
            FAILED_IMAGE_ATTACHMENTS[pending.file_unique_id] = (
                result.page_id,
                result.page_url,
                datetime.now(timezone.utc),
            )
    return result, attachment


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze an authorized Telegram image and safely persist treadmill stats."""
    if not await check_auth(update):
        return
    _cleanup_image_state()
    media, mime_type, filename = _image_media(update.message)
    if media is None:
        await send_clean_reply(update.message, "⚠️ Could not detect an image.")
        return
    if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
        await send_clean_reply(
            update.message,
            "⚠️ Unsupported image format. Send JPEG, PNG, WebP, HEIC, or HEIF.",
        )
        return
    if media.file_size and media.file_size > MAX_IMAGE_BYTES:
        await send_clean_reply(update.message, "⚠️ Image is larger than the 15 MiB limit.")
        return
    if media.file_unique_id in RECENT_IMAGE_FILE_IDS:
        await send_clean_reply(update.message, "ℹ️ This image was already processed recently.")
        return
    if any(
        pending.file_unique_id == media.file_unique_id
        for pending in PENDING_IMAGE_SCANS.values()
    ):
        await send_clean_reply(
            update.message, "ℹ️ This image is already awaiting your review."
        )
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    try:
        telegram_file = await context.bot.get_file(media.file_id)
        image_buffer = io.BytesIO()
        await telegram_file.download_to_memory(image_buffer)
        image_bytes = image_buffer.getvalue()
    except Exception as exc:
        logger.warning("Telegram image download failed: %s", type(exc).__name__)
        await send_clean_reply(
            update.message, "⚠️ I couldn't download that image. Please resend it."
        )
        return
    if len(image_bytes) > MAX_IMAGE_BYTES:
        await send_clean_reply(update.message, "⚠️ Image is larger than the 15 MiB limit.")
        return

    failed_attachment = FAILED_IMAGE_ATTACHMENTS.get(media.file_unique_id)
    if failed_attachment:
        page_id, page_url, _failed_at = failed_attachment
        loop = asyncio.get_running_loop()
        attachment = await loop.run_in_executor(
            None,
            notion_service.attach_image,
            page_id,
            image_bytes,
            mime_type,
            filename,
        )
        if attachment.attached:
            FAILED_IMAGE_ATTACHMENTS.pop(media.file_unique_id, None)
            RECENT_IMAGE_FILE_IDS[media.file_unique_id] = datetime.now(timezone.utc)
            message = "✅ Source image attached to the existing workout record."
            if page_url:
                message += f"\n[Open Daily Health & Workout Log]({page_url})"
            await send_clean_reply(update.message, message)
        elif attachment.retryable:
            FAILED_IMAGE_ATTACHMENTS[media.file_unique_id] = (
                page_id,
                page_url,
                datetime.now(timezone.utc),
            )
            await send_clean_reply(
                update.message,
                "⚠️ The workout metrics remain saved, but the image upload failed again. Please retry later.",
            )
        else:
            FAILED_IMAGE_ATTACHMENTS.pop(media.file_unique_id, None)
            message = (
                "⚠️ Notion did not confirm the image block. Check the page before "
                "retrying to avoid a duplicate."
            )
            if page_url:
                message += f"\n[Open Daily Health & Workout Log]({page_url})"
            await send_clean_reply(update.message, message)
        return

    loop = asyncio.get_running_loop()
    try:
        analysis = await loop.run_in_executor(
            None,
            gemini_agent.process_image_message,
            str(update.effective_user.id),
            image_bytes,
            mime_type,
            update.message.caption or "",
            update.message.date,
        )
    except Exception:
        logger.exception("Image analysis failed")
        await send_clean_reply(
            update.message,
            "⚠️ I couldn't read that image right now. Please resend a clearer photo.",
        )
        return

    logger.info("Image routed to domain=%s", analysis.domain)
    if analysis.domain != "treadmill" or not analysis.treadmill:
        await send_clean_reply(
            update.message,
            f"🖼️ I can read the image, but it is not a supported treadmill scan yet: {analysis.summary}",
        )
        return

    pending = _new_pending_scan(
        update,
        analysis,
        image_bytes,
        mime_type,
        filename,
        media.file_unique_id,
    )
    if not analysis.treadmill.is_auto_save_eligible():
        await _send_scan_preview(update.message, pending)
        return

    try:
        result, attachment = await _persist_pending_scan(pending, allow_overwrite=False)
    except Exception:
        logger.exception("Workout persistence failed")
        await _send_scan_preview(update.message, pending)
        return
    if result.action == "conflict":
        pending.shown_conflicts = result.conflicts
        await _send_scan_preview(update.message, pending, result.conflicts)
        return
    PENDING_IMAGE_SCANS.pop(pending.token, None)
    if result.action == "duplicate":
        RECENT_IMAGE_FILE_IDS[media.file_unique_id] = datetime.now(timezone.utc)
        await send_clean_reply(
            update.message,
            "ℹ️ This workout is already recorded for that date; no duplicate image was attached.",
        )
        return
    await send_clean_reply(
        update.message,
        _workout_confirmation(analysis.treadmill, result, attachment),
    )


async def handle_scan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Save/Edit/Cancel for an uncertain or conflicting scan."""
    query = update.callback_query
    if not query or not await check_auth(update):
        return
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3 or parts[0] != "scan":
        await query.answer("Invalid scan action.", show_alert=True)
        return
    action, token = parts[1], parts[2]
    pending = PENDING_IMAGE_SCANS.get(token)
    if not pending or pending.is_expired():
        PENDING_IMAGE_SCANS.pop(token, None)
        await query.answer("This scan expired. Please resend the image.", show_alert=True)
        return
    query_chat_id = getattr(query.message, "chat_id", None)
    if pending.user_id != query.from_user.id or pending.chat_id != query_chat_id:
        await query.answer("This scan is not yours.", show_alert=True)
        return
    if action == "cancel":
        PENDING_IMAGE_SCANS.pop(token, None)
        await query.answer("Cancelled")
        await query.edit_message_text("❌ Treadmill scan cancelled.")
        return
    if action == "edit":
        pending.awaiting_correction = True
        await query.answer("Reply with your correction")
        await query.edit_message_text(
            "✏️ Reply with the corrected field and value, for example: “Distance is 3.01 km.”"
        )
        return
    if action != "save":
        await query.answer("Invalid scan action.", show_alert=True)
        return

    scan = pending.analysis.treadmill
    if not scan or scan.validation_errors():
        await query.answer(
            "Fix the invalid values before saving.", show_alert=True
        )
        await query.edit_message_text(
            format_for_telegram(_scan_preview_text(pending)),
            parse_mode=ParseMode.HTML,
            reply_markup=_scan_keyboard(token, allow_save=False),
            disable_web_page_preview=True,
        )
        return

    await query.answer("Saving…")
    try:
        # Always inspect current Notion values first. A changed value gets shown once
        # before a second explicit Save can replace it.
        result, attachment = await _persist_pending_scan(
            pending, allow_overwrite=False
        )
        if result.action == "conflict":
            if pending.shown_conflicts != result.conflicts:
                pending.shown_conflicts = result.conflicts
                await query.edit_message_text(
                    format_for_telegram(
                        _scan_preview_text(pending, result.conflicts)
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=_scan_keyboard(token),
                    disable_web_page_preview=True,
                )
                return
            result, attachment = await _persist_pending_scan(
                pending,
                allow_overwrite=True,
                expected_conflicts=pending.shown_conflicts,
            )
            if result.action == "conflict":
                pending.shown_conflicts = result.conflicts
                await query.edit_message_text(
                    format_for_telegram(
                        _scan_preview_text(pending, result.conflicts)
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=_scan_keyboard(token),
                    disable_web_page_preview=True,
                )
                return
    except Exception:
        logger.exception("Confirmed workout persistence failed")
        await query.edit_message_text(
            "⚠️ The workout could not be saved. Please resend the image and try again."
        )
        return
    PENDING_IMAGE_SCANS.pop(token, None)
    if result.action == "duplicate":
        await query.edit_message_text(
            "ℹ️ This workout is already recorded; no duplicate image was attached."
        )
        return
    await query.edit_message_text(
        format_for_telegram(_workout_confirmation(scan, result, attachment)),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

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

                        # Dispatch morning briefing to email
                        if email_service.is_configured():
                            try:
                                em_ok, em_msg = await loop.run_in_executor(
                                    None,
                                    email_service.send_briefing_email,
                                    briefing_text
                                )
                                logger.info(f"Morning briefing email dispatch result: {em_msg}")
                            except Exception as em_err:
                                logger.error(f"Failed delivering morning briefing email: {em_err}")

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
    asyncio.create_task(image_state_cleanup_scheduler())

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
    app.add_handler(CommandHandler("email", email_command))
    app.add_handler(CallbackQueryHandler(handle_scan_callback, pattern=r"^scan:(save|edit|cancel):"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print(f"🚀 Bot is running in polling mode on port {settings.PORT}. Daily briefing scheduled at {settings.DAILY_BRIEFING_TIME}.")
    app.run_polling(bootstrap_retries=5)

if __name__ == "__main__":
    main()

