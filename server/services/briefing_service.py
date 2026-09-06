"""Scheduled briefing service independent of Telegram."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from config import settings
from gemini_agent import gemini_agent
from email_service import email_service
from server.database import get_db
from server.services.conversation_service import conversation_service
from server.services.web_push_service import web_push_service

logger = logging.getLogger("server.briefing_service")

class BriefingService:
    def is_delivered(self, delivery_date: str, channel: str, recipient: str) -> bool:
        """Check if briefing was already delivered today via this channel."""
        with get_db() as db:
            row = db.execute(
                """
                SELECT id FROM briefing_deliveries
                WHERE delivery_date = ? AND channel = ? AND recipient = ?
                """,
                (delivery_date, channel, recipient)
            ).fetchone()
            return bool(row)

    def record_delivery(
        self, delivery_date: str, channel: str, recipient: str, status: str = "success"
    ) -> None:
        """Record successful delivery to prevent duplicate dispatches."""
        record_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            db.execute(
                """
                INSERT INTO briefing_deliveries (id, delivery_date, channel, recipient, status, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(delivery_date, channel, recipient) DO UPDATE SET
                    status = excluded.status,
                    delivered_at = excluded.delivered_at
                """,
                (record_id, delivery_date, channel, recipient, status, now)
            )

    def claim_run(self, user_id: str, delivery_date: str) -> str:
        """Claim a date for dispatch, allowing a failed or stale run to resume."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        stale_before = (now - timedelta(minutes=20)).isoformat()
        with get_db() as db:
            inserted = db.execute(
                """
                INSERT INTO briefing_runs (user_id, delivery_date, status, started_at)
                VALUES (?, ?, 'running', ?)
                ON CONFLICT(user_id, delivery_date) DO NOTHING
                """,
                (user_id, delivery_date, now_iso),
            )
            if inserted.rowcount > 0:
                return "claimed"

            row = db.execute(
                "SELECT status, started_at FROM briefing_runs WHERE user_id = ? AND delivery_date = ?",
                (user_id, delivery_date),
            ).fetchone()
            if row and row["status"] == "completed":
                return "already_completed"
            if row and row["status"] == "running" and str(row["started_at"]) >= stale_before:
                return "in_progress"

            updated = db.execute(
                """
                UPDATE briefing_runs
                SET status = 'running', started_at = ?, completed_at = NULL, error_message = NULL
                WHERE user_id = ? AND delivery_date = ? AND status != 'completed'
                """,
                (now_iso, user_id, delivery_date),
            )
            return "claimed" if updated.rowcount > 0 else "in_progress"

    def complete_run(self, user_id: str, delivery_date: str) -> None:
        with get_db() as db:
            db.execute(
                """
                UPDATE briefing_runs
                SET status = 'completed', completed_at = ?, error_message = NULL
                WHERE user_id = ? AND delivery_date = ?
                """,
                (datetime.now(timezone.utc).isoformat(), user_id, delivery_date),
            )

    def fail_run(self, user_id: str, delivery_date: str, error: Exception) -> None:
        with get_db() as db:
            db.execute(
                """
                UPDATE briefing_runs SET status = 'failed', error_message = ?
                WHERE user_id = ? AND delivery_date = ?
                """,
                (str(error)[:500], user_id, delivery_date),
            )

    async def get_or_create_briefing_conversation(self, user_id: str) -> str:
        """Find or create dedicated '🌅 Morning Briefings' conversation."""
        with get_db() as db:
            row = db.execute(
                """
                SELECT id FROM conversations
                WHERE user_id = ? AND title = '🌅 Morning Briefings'
                LIMIT 1
                """,
                (user_id,)
            ).fetchone()
            if row:
                return str(row["id"])

        conv = conversation_service.create_conversation(
            user_id=user_id,
            agent_id="notion",
            title="🌅 Morning Briefings"
        )
        return conv.id

    async def dispatch_briefing(
        self, user_id: str = "andrei-main", target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate morning briefing and dispatch to web conversation, push, and email."""
        tz = timezone(timedelta(hours=settings.UTC_OFFSET_HOURS))
        now_tz = datetime.now(tz)
        date_str = target_date or now_tz.strftime("%Y-%m-%d")
        claim = self.claim_run(user_id, date_str)
        if claim != "claimed":
            return {"status": claim, "date": date_str}

        try:
            loop = asyncio.get_running_loop()
            conv_id = await self.get_or_create_briefing_conversation(user_id)
            message_key = f"briefing:{date_str}"
            existing = conversation_service.find_message_by_client_id(conv_id, user_id, message_key)
            if existing:
                briefing_text = existing.content
            else:
                briefing_text = await loop.run_in_executor(
                    None,
                    gemini_agent.generate_daily_briefing,
                    user_id,
                    date_str,
                )
                conversation_service.save_message(
                    conversation_id=conv_id,
                    user_id=user_id,
                    role="assistant",
                    content=briefing_text,
                    client_message_id=message_key,
                    status="completed",
                )

            results = {
                "status": "completed",
                "date": date_str,
                "conversation_id": conv_id,
                "web_push_sent": 0,
                "email_sent": False,
            }

            if not self.is_delivered(date_str, "web_push", user_id):
                if web_push_service.is_configured() and web_push_service.is_subscribed(user_id):
                    sent_count = web_push_service.send_notification(
                        user_id=user_id,
                        title=f"🌅 Life Hub Briefing — {now_tz.strftime('%A, %b %d')}",
                        body="Your daily schedule and morning briefing is ready in Life Hub.",
                        data={"url": f"/?conversation={conv_id}"},
                    )
                    if sent_count > 0:
                        self.record_delivery(date_str, "web_push", user_id, "delivered")
                        results["web_push_sent"] = sent_count

            recipient_email = settings.NOTIFICATION_EMAIL_TO
            if recipient_email and settings.EMAIL_NOTIFICATIONS_ENABLED and email_service.is_configured():
                if not self.is_delivered(date_str, "email", recipient_email):
                    success, msg = await loop.run_in_executor(
                        None,
                        email_service.send_briefing_email,
                        briefing_text,
                    )
                    if success:
                        self.record_delivery(date_str, "email", recipient_email, "delivered")
                        results["email_sent"] = True
                    else:
                        logger.warning("Briefing email failed: %s", msg)

            self.complete_run(user_id, date_str)
            return results
        except Exception as exc:
            self.fail_run(user_id, date_str, exc)
            raise

    async def start_scheduler(self) -> None:
        """Background task running continuously to deliver scheduled briefings."""
        logger.info(
            f"Web briefing scheduler active. Target: {settings.DAILY_BRIEFING_TIME} (UTC+{settings.UTC_OFFSET_HOURS})"
        )
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

                target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                if now >= target_today:
                    next_trigger = target_today + timedelta(days=1)
                else:
                    next_trigger = target_today

                sleep_seconds = (next_trigger - now).total_seconds()
                logger.info(f"Next scheduled briefing in {sleep_seconds/3600:.2f}h ({next_trigger.strftime('%Y-%m-%d %H:%M:%S')})")

                await asyncio.sleep(sleep_seconds)

                if settings.DAILY_BRIEFING_ENABLED:
                    today_str = datetime.now(tz).strftime("%Y-%m-%d")
                    logger.info(f"Triggering scheduled morning briefing for {today_str}...")
                    await self.dispatch_briefing(user_id="andrei-main", target_date=today_str)

                # Small sleep to prevent double firing on exact second
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("Briefing scheduler task cancelled.")
                break
            except Exception as ex:
                logger.error(f"Error in briefing scheduler: {ex}", exc_info=True)
                await asyncio.sleep(60)

briefing_service = BriefingService()
