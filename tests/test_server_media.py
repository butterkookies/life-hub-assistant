"""Tests for media validation, upload limits, magic-byte checks, and path traversal protection."""

import io
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from config import settings
from image_models import ImageAnalysis, TreadmillScan
from server.auth import COOKIE_NAME, create_session, format_cookie_token, hash_password
from server.database import get_db, init_db
from server.main import create_app
from server.services.conversation_service import conversation_service
from server.services.workout_scan_service import validate_image_bytes

VALID_JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
VALID_PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

class ServerMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_media.db")
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

        # Add second user
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

        self.conv = conversation_service.create_conversation("andrei-main", title="Media Conversation")

        self.app = create_app()
        self.client = TestClient(self.app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_magic_byte_validation(self):
        """Magic bytes check accepts real JPEG/PNG signatures and rejects forged headers."""
        # Genuine JPEG header
        ok, _ = validate_image_bytes(VALID_JPEG_HEADER + b"data", "image/jpeg")
        self.assertTrue(ok)

        # Genuine PNG header
        ok, _ = validate_image_bytes(VALID_PNG_HEADER + b"data", "image/png")
        self.assertTrue(ok)

        # Forged file: HTML pretending to be JPEG
        forged_content = b"<html><script>alert(1)</script></html>"
        ok, err = validate_image_bytes(forged_content, "image/jpeg")
        self.assertFalse(ok)
        self.assertIn("signature", err)

        # Unsupported format
        ok, err = validate_image_bytes(b"GIF89a...", "image/gif")
        self.assertFalse(ok)
        self.assertIn("Unsupported", err)

    def test_upload_size_limit_rejection(self):
        """Files exceeding 15MB are rejected with 413."""
        oversized_data = b"X" * (16 * 1024 * 1024)  # 16 MB
        files = {
            "file": ("huge.jpg", io.BytesIO(oversized_data), "image/jpeg")
        }
        res = self.client.post(
            f"/api/conversations/{self.conv.id}/attachments",
            files=files,
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 413)
        self.assertEqual(res.json()["error"]["code"], "FILE_TOO_LARGE")

    def test_path_traversal_protection(self):
        """Attempting path traversal in filename is sanitized to safe basename."""
        traversal_filename = "../../../evil_script.sh"
        fake_voice = b"RIFFfakeWAVcontent"
        files = {
            "file": (traversal_filename, io.BytesIO(fake_voice), "audio/wav")
        }

        with patch("server.services.assistant_service.assistant_service.process_voice_message") as mock_voice:
            from server.schemas import MessageResponse
            mock_voice.return_value = MessageResponse(
                id="msg-voice-1",
                conversation_id=self.conv.id,
                role="assistant",
                content="Voice note transcribed",
                status="completed",
                created_at="2026-09-04T10:00:00Z"
            )

            res = self.client.post(
                f"/api/conversations/{self.conv.id}/attachments",
                files=files,
                headers=self.auth_headers
            )
            self.assertEqual(res.status_code, 200)

        # Verify attachment record in DB only has safe filename 'evil_script.sh'
        with get_db() as db:
            row = db.execute("SELECT filename, file_path FROM attachments WHERE conversation_id = ?", (self.conv.id,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["filename"], "evil_script.sh")
            self.assertNotIn("..", row["file_path"])

    def test_attachment_ownership_enforcement(self):
        """User B cannot download User A's attachment."""
        # 1. User A uploads file
        fake_audio = b"AUDIO_DATA_FOR_USER_A"
        files = {
            "file": ("note.wav", io.BytesIO(fake_audio), "audio/wav")
        }
        with patch("server.services.assistant_service.assistant_service.process_voice_message") as mock_voice:
            from server.schemas import MessageResponse
            mock_voice.return_value = MessageResponse(
                id="msg-1",
                conversation_id=self.conv.id,
                role="assistant",
                content="Noted",
                status="completed",
                created_at="2026-09-04T10:00:00Z"
            )
            self.client.post(
                f"/api/conversations/{self.conv.id}/attachments",
                files=files,
                headers=self.auth_headers
            )

        with get_db() as db:
            row = db.execute("SELECT id FROM attachments WHERE conversation_id = ?", (self.conv.id,)).fetchone()
            att_id = str(row["id"])

        # User B attempts to download User A's attachment -> 404
        b_res = self.client.get(f"/api/attachments/{att_id}", headers=self.user2_headers)
        self.assertEqual(b_res.status_code, 404)
        self.assertEqual(b_res.json()["error"]["code"], "ATTACHMENT_NOT_FOUND")

        # User A downloads it successfully -> 200
        a_res = self.client.get(f"/api/attachments/{att_id}", headers=self.auth_headers)
        self.assertEqual(a_res.status_code, 200)
        self.assertEqual(a_res.content, fake_audio)

if __name__ == "__main__":
    unittest.main()
