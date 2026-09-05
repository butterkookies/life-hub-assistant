"""Tests for Web Push subscriptions, scheduled briefing duplicate prevention, health, and Telegram-disabled startup."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from config import settings
from server.auth import COOKIE_NAME, create_session, format_cookie_token, hash_password
from server.database import get_db, init_db
from server.main import create_app
from server.services.briefing_service import briefing_service
from server.services.web_push_service import web_push_service
from py_vapid import Vapid
import telegram_bot

class ServerNotificationsAndBriefingsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_notif.db")
        self.upload_dir = os.path.join(self.temp_dir.name, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.test_password = "Password123!"
        self.test_hash = hash_password(self.test_password)
        self.test_secret = "test-session-secret-key-32-chars-long!"

        self.env_patch = patch.dict(os.environ, {
            "DATABASE_PATH": self.db_path,
            "UPLOAD_DIR": self.upload_dir,
            "WEB_PASSWORD_HASH": self.test_hash,
            "WEB_SESSION_SECRET": self.test_secret,
            "WEB_ALLOWED_ORIGINS": "http://testserver",
            "WEB_PUSH_VAPID_PUBLIC_KEY": "test-vapid-public-key",
            "WEB_PUSH_VAPID_PRIVATE_KEY": "test-vapid-private-key",
            "WEB_PUSH_CONTACT": "mailto:andrei@test.local",
            "ENABLE_TELEGRAM": "false",
            "TELEGRAM_BOT_TOKEN": ""
        })
        self.env_patch.start()
        init_db()

        sess_id, token = create_session("andrei-main")
        self.auth_headers = {
            "Cookie": f"{COOKIE_NAME}={format_cookie_token(sess_id, token)}",
            "Origin": "http://testserver"
        }

        self.app = create_app()
        self.client = TestClient(self.app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_web_push_subscription_management(self):
        """User can subscribe and unsubscribe Web Push subscriptions."""
        endpoint = "https://fcm.googleapis.com/fcm/send/sample-token"
        
        # 1. Subscribe
        sub_res = self.client.post(
            "/api/notifications/subscribe",
            json={
                "endpoint": endpoint,
                "keys": {"p256dh": "dummy-p256dh", "auth": "dummy-auth"},
                "user_agent": "Mozilla/5.0 iPhone"
            },
            headers=self.auth_headers
        )
        self.assertEqual(sub_res.status_code, 200)
        self.assertTrue(web_push_service.is_subscribed("andrei-main"))

        # Check status endpoint
        status_res = self.client.get("/api/notifications/status", headers=self.auth_headers)
        self.assertEqual(status_res.status_code, 200)
        data = status_res.json()
        self.assertTrue(data["subscribed"])
        self.assertEqual(data["vapid_public_key"], "test-vapid-public-key")

        # 2. Unsubscribe
        unsub_res = self.client.request(
            "DELETE",
            "/api/notifications/subscribe",
            json={
                "endpoint": endpoint,
                "keys": {"p256dh": "dummy-p256dh", "auth": "dummy-auth"}
            },
            headers=self.auth_headers
        )
        self.assertEqual(unsub_res.status_code, 200)
        self.assertFalse(web_push_service.is_subscribed("andrei-main"))

    def test_duplicate_briefing_prevention(self):
        """Briefing delivery records prevent sending multiple briefings on the same date."""
        date_str = "2026-09-04"
        channel = "web_push"
        recipient = "andrei-main"

        self.assertFalse(briefing_service.is_delivered(date_str, channel, recipient))

        # Record delivery
        briefing_service.record_delivery(date_str, channel, recipient, "delivered")

        self.assertTrue(briefing_service.is_delivered(date_str, channel, recipient))

        # Different channel or date should not be marked delivered
        self.assertFalse(briefing_service.is_delivered(date_str, "email", recipient))
        self.assertFalse(briefing_service.is_delivered("2026-09-05", channel, recipient))

    def test_device_status_does_not_use_another_devices_subscription(self):
        web_push_service.save_subscription('andrei-main', 'https://push.example/desktop', 'key', 'auth')
        desktop = self.client.post('/api/notifications/device-status', json={'endpoint': 'https://push.example/desktop'}, headers=self.auth_headers)
        phone = self.client.post('/api/notifications/device-status', json={'endpoint': 'https://push.example/phone'}, headers=self.auth_headers)
        self.assertTrue(desktop.json()['subscribed'])
        self.assertFalse(phone.json()['subscribed'])

    def test_pem_push_key_and_separate_provider_claims(self):
        key = Vapid()
        key.generate_keys()
        web_push_service.save_subscription('andrei-main', 'https://push.example/desktop', 'key', 'auth')
        web_push_service.save_subscription('andrei-main', 'https://other.example/phone', 'key', 'auth')
        calls = []

        def fake_send(**kwargs):
            self.assertIsInstance(kwargs['vapid_private_key'], Vapid)
            self.assertNotIn('aud', kwargs['vapid_claims'])
            self.assertGreater(kwargs['ttl'], 0)
            self.assertEqual(kwargs['timeout'], 10)
            kwargs['vapid_claims']['aud'] = 'provider-specific-audience'
            calls.append(kwargs)

        with patch.dict(os.environ, {'WEB_PUSH_VAPID_PRIVATE_KEY': key.private_pem().decode()}), patch('server.services.web_push_service.webpush', side_effect=fake_send):
            self.assertEqual(web_push_service.send_notification('andrei-main', 'Test', 'Test notification'), 2)
        self.assertEqual(len(calls), 2)
        self.assertIsNot(calls[0]['vapid_claims'], calls[1]['vapid_claims'])

    def test_zero_device_test_is_not_reported_as_success(self):
        response = self.client.post('/api/notifications/test', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['delivered_devices'], 0)

    @patch("gemini_agent.gemini_agent.generate_daily_briefing")
    async def test_dispatch_briefing_creates_conversation_message(self, mock_gen_briefing):
        """Dispatching briefing creates a dedicated conversation and records message."""
        mock_gen_briefing.return_value = "☀️ Good morning Andrei! Here is your plan for today."

        res = await briefing_service.dispatch_briefing(user_id="andrei-main", target_date="2026-09-04")
        self.assertIn("conversation_id", res)

        # Verify conversation in SQLite
        with get_db() as db:
            row = db.execute("SELECT content FROM messages WHERE conversation_id = ?", (res["conversation_id"],)).fetchone()
            self.assertIsNotNone(row)
            self.assertIn("Good morning Andrei!", row["content"])

    def test_health_endpoint(self):
        """Health endpoint returns system status and configuration."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database_ok"])
        self.assertFalse(data["telegram_enabled"])

    def test_telegram_disabled_startup(self):
        """telegram_bot.main() exits cleanly without TELEGRAM_BOT_TOKEN when ENABLE_TELEGRAM=false."""
        with patch("builtins.print") as mock_print:
            telegram_bot.main()
            mock_print.assert_called_with("ℹ️ Telegram bot is disabled (ENABLE_TELEGRAM=false). Set ENABLE_TELEGRAM=true to run Telegram.")

if __name__ == "__main__":
    unittest.main()
