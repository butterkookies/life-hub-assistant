"""Web Push notifications service using VAPID and standards-based Push API."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pywebpush import WebPushException, webpush
from config import settings
from server.database import get_db

logger = logging.getLogger("server.web_push_service")

class WebPushService:
    def is_configured(self) -> bool:
        """Check if VAPID keys are configured."""
        return bool(
            settings.WEB_PUSH_VAPID_PUBLIC_KEY
            and settings.WEB_PUSH_VAPID_PRIVATE_KEY
            and settings.WEB_PUSH_CONTACT
        )

    def get_public_key(self) -> Optional[str]:
        if not self.is_configured():
            return None
        return settings.WEB_PUSH_VAPID_PUBLIC_KEY

    def is_subscribed(self, user_id: str) -> bool:
        with get_db() as db:
            row = db.execute(
                "SELECT COUNT(id) as count FROM push_subscriptions WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return bool(row and row["count"] > 0)

    def save_subscription(
        self,
        user_id: str,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: Optional[str] = None
    ) -> None:
        """Save or update Web Push subscription."""
        sub_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            db.execute(
                """
                INSERT INTO push_subscriptions (id, user_id, endpoint, p256dh, auth, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(endpoint) DO UPDATE SET
                    p256dh = excluded.p256dh,
                    auth = excluded.auth,
                    user_agent = excluded.user_agent,
                    user_id = excluded.user_id
                """,
                (sub_id, user_id, endpoint, p256dh, auth, user_agent, now)
            )

    def remove_subscription(self, user_id: str, endpoint: str) -> bool:
        with get_db() as db:
            cursor = db.execute(
                "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
                (user_id, endpoint)
            )
            return cursor.rowcount > 0

    def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Send push notification to all active devices registered by user."""
        if not self.is_configured():
            logger.warning("Web Push not configured, skipping notification dispatch.")
            return 0

        with get_db() as db:
            rows = db.execute(
                "SELECT id, endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?",
                (user_id,)
            ).fetchall()

        if not rows:
            return 0

        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/icons/icon-192.png",
            "badge": "/icons/icon-192.png",
            "data": data or {"url": "/"}
        })

        vapid_claims = {
            "sub": settings.WEB_PUSH_CONTACT
        }

        sent_count = 0
        stale_endpoints: List[str] = []

        for r in rows:
            sub_info = {
                "endpoint": r["endpoint"],
                "keys": {
                    "p256dh": r["p256dh"],
                    "auth": r["auth"]
                }
            }
            try:
                webpush(
                    subscription_info=sub_info,
                    data=payload,
                    vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims
                )
                sent_count += 1
            except WebPushException as ex:
                status_code = getattr(ex.response, "status_code", None) if hasattr(ex, "response") else None
                if status_code in (404, 410):
                    # Subscription has expired or user revoked it
                    logger.info(f"Removing expired subscription {r['endpoint'][:30]}...")
                    stale_endpoints.append(r["endpoint"])
                else:
                    logger.warning(f"Web push dispatch failed for endpoint {r['endpoint'][:30]}: {ex}")
            except Exception as ex:
                logger.warning(f"Unexpected push dispatch error: {ex}")

        if stale_endpoints:
            with get_db() as db:
                for ep in stale_endpoints:
                    db.execute("DELETE FROM push_subscriptions WHERE endpoint = ?", (ep,))

        return sent_count

web_push_service = WebPushService()
