"""Tests for workout scan confirmations, corrections, expiration, and ownership."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from starlette.testclient import TestClient

from config import settings
from image_models import ImageAnalysis, TreadmillScan
from server.auth import COOKIE_NAME, create_session, format_cookie_token, hash_password
from server.database import get_db, init_db
from server.main import create_app
from server.services.conversation_service import conversation_service
from server.services.workout_scan_service import workout_scan_service

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00fakeimagecontent"

def make_sample_analysis(confidence=0.85, uncertain_fields=None):
    return ImageAnalysis(
        domain="treadmill",
        summary="TRAX treadmill display",
        confidence=confidence,
        uncertain_fields=uncertain_fields or ["distance_km"],
        treadmill=TreadmillScan(
            date="2026-09-04",
            duration_minutes=35.0,
            distance_km=2.5,
            steps=3500,
            calories_kcal=180,
            confidence=confidence,
            uncertain_fields=uncertain_fields or ["distance_km"],
        )
    )

class ServerWorkoutScanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_scans.db")
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
        })
        self.env_patch.start()
        init_db()

        with get_db() as db:
            db.execute("INSERT INTO users (id, username, created_at) VALUES ('user2', 'user2', datetime('now'))")

        sess1_id, token1 = create_session("andrei-main")
        self.auth_headers = {
            "Cookie": f"{COOKIE_NAME}={format_cookie_token(sess1_id, token1)}",
            "Origin": "http://testserver"
        }

        sess2_id, token2 = create_session("user2")
        self.user2_headers = {
            "Cookie": f"{COOKIE_NAME}={format_cookie_token(sess2_id, token2)}",
            "Origin": "http://testserver"
        }

        self.conv = conversation_service.create_conversation("andrei-main", title="Workouts")

        self.app = create_app()
        self.client = TestClient(self.app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_pending_scan_preview_and_ownership(self):
        """User creates pending scan; only user can confirm or cancel it."""
        analysis = make_sample_analysis()
        token = workout_scan_service.create_pending_scan(
            user_id="andrei-main",
            conversation_id=self.conv.id,
            filename="treadmill.jpg",
            mime_type="image/jpeg",
            image_bytes=VALID_JPEG,
            analysis=analysis
        )

        # 1. Preview
        preview = workout_scan_service.get_pending_scan(token, "andrei-main")
        self.assertIsNotNone(preview)
        self.assertEqual(preview.date, "2026-09-04")
        self.assertEqual(preview.metrics["duration_minutes"], 35.0)

        # 2. User 2 cannot preview or confirm it
        other_preview = workout_scan_service.get_pending_scan(token, "user2")
        self.assertIsNone(other_preview)

        confirm_res = self.client.post(
            f"/api/image-scans/{token}/confirm",
            headers=self.user2_headers
        )
        self.assertEqual(confirm_res.status_code, 400)

        # 3. User 1 can cancel it
        cancel_res = self.client.post(
            f"/api/image-scans/{token}/cancel",
            headers=self.auth_headers
        )
        self.assertEqual(cancel_res.status_code, 200)
        self.assertTrue(cancel_res.json()["success"])

    def test_scan_expiration(self):
        """Expired pending scan is automatically rejected and purged."""
        analysis = make_sample_analysis()
        token = workout_scan_service.create_pending_scan(
            user_id="andrei-main",
            conversation_id=self.conv.id,
            filename="treadmill.jpg",
            mime_type="image/jpeg",
            image_bytes=VALID_JPEG,
            analysis=analysis
        )

        # Artificially expire the scan in SQLite
        past = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        with get_db() as db:
            db.execute("UPDATE pending_image_scans SET expires_at = ? WHERE token = ?", (past, token))

        # Attempt to confirm expired scan
        confirm_res = self.client.post(
            f"/api/image-scans/{token}/confirm",
            headers=self.auth_headers
        )
        self.assertEqual(confirm_res.status_code, 400)
        self.assertIn("expired", confirm_res.json()["error"]["message"].lower())

    @patch("gemini_agent.gemini_agent.apply_image_correction")
    def test_scan_correction(self, mock_apply_correction):
        """User can submit natural language correction to update pending scan."""
        analysis = make_sample_analysis(confidence=0.8, uncertain_fields=["distance_km"])
        token = workout_scan_service.create_pending_scan(
            user_id="andrei-main",
            conversation_id=self.conv.id,
            filename="treadmill.jpg",
            mime_type="image/jpeg",
            image_bytes=VALID_JPEG,
            analysis=analysis
        )

        # Mock corrected analysis
        corrected_analysis = make_sample_analysis(confidence=0.98, uncertain_fields=[])
        corrected_analysis.treadmill.distance_km = 3.1
        mock_apply_correction.return_value = corrected_analysis

        correct_res = self.client.post(
            f"/api/image-scans/{token}/correct",
            json={"correction_text": "Distance was actually 3.1 km"},
            headers=self.auth_headers
        )
        self.assertEqual(correct_res.status_code, 200)
        data = correct_res.json()
        self.assertEqual(data["metrics"]["distance_km"], 3.1)
        self.assertEqual(data["confidence"], 0.98)

if __name__ == "__main__":
    unittest.main()
