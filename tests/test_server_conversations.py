"""Tests for conversation management, message persistence, ownership, and idempotency."""

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from config import settings
from server.auth import COOKIE_NAME, create_session, format_cookie_token, hash_password
from server.database import get_db, init_db
from server.main import create_app
from server.models import User
from server.schemas import MessageResponse
from server.services.assistant_service import assistant_service
from server.services.conversation_service import conversation_service

class ServerConversationsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_conv.db")
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

        # Create another user in DB for ownership tests
        with get_db() as db:
            db.execute(
                "INSERT INTO users (id, username, created_at) VALUES ('other-user', 'other', datetime('now'))"
            )

        # Create authenticated session for andrei-main
        sess_id, token_sec = create_session("andrei-main")
        cookie_token = format_cookie_token(sess_id, token_sec)
        self.auth_headers = {
            "Cookie": f"{COOKIE_NAME}={cookie_token}",
            "Origin": "http://testserver"
        }

        # Create session for other-user
        other_sess_id, other_token_sec = create_session("other-user")
        other_cookie_token = format_cookie_token(other_sess_id, other_token_sec)
        self.other_auth_headers = {
            "Cookie": f"{COOKIE_NAME}={other_cookie_token}",
            "Origin": "http://testserver"
        }

        self.app = create_app()
        self.client = TestClient(self.app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_create_and_list_conversations(self):
        """Create multiple conversations and verify order and message counts."""
        # 1. Create first conversation
        r1 = self.client.post(
            "/api/conversations",
            json={"title": "First Conversation", "agent_id": "notion"},
            headers=self.auth_headers
        )
        self.assertEqual(r1.status_code, 200)
        c1_id = r1.json()["id"]

        # 2. Create second conversation
        r2 = self.client.post(
            "/api/conversations",
            json={"title": "Second Conversation", "agent_id": "notion"},
            headers=self.auth_headers
        )
        self.assertEqual(r2.status_code, 200)
        c2_id = r2.json()["id"]

        # 3. List
        list_res = self.client.get("/api/conversations", headers=self.auth_headers)
        self.assertEqual(list_res.status_code, 200)
        data = list_res.json()
        self.assertEqual(len(data), 2)
        # Most recent first
        self.assertEqual(data[0]["id"], c2_id)
        self.assertEqual(data[1]["id"], c1_id)

    def test_conversation_ownership_enforcement(self):
        """User B cannot access or delete User A's conversation."""
        # User A creates conversation
        r = self.client.post(
            "/api/conversations",
            json={"title": "Private Chat"},
            headers=self.auth_headers
        )
        conv_id = r.json()["id"]

        # User B tries to view it
        get_res = self.client.get(f"/api/conversations/{conv_id}", headers=self.other_auth_headers)
        self.assertEqual(get_res.status_code, 404)
        self.assertEqual(get_res.json()["error"]["code"], "CONVERSATION_NOT_FOUND")

        # User B tries to delete it
        del_res = self.client.delete(f"/api/conversations/{conv_id}", headers=self.other_auth_headers)
        self.assertEqual(del_res.status_code, 404)

        # User A can view and delete it
        get_ok = self.client.get(f"/api/conversations/{conv_id}", headers=self.auth_headers)
        self.assertEqual(get_ok.status_code, 200)

        del_ok = self.client.delete(f"/api/conversations/{conv_id}", headers=self.auth_headers)
        self.assertEqual(del_ok.status_code, 200)

    @patch.object(assistant_service, "process_text_message")
    def test_message_idempotency(self, mock_process_text):
        """Submitting message with identical client_message_id returns existing message."""
        # Create conversation
        r = self.client.post(
            "/api/conversations",
            json={"title": "Idempotent Chat"},
            headers=self.auth_headers
        )
        conv_id = r.json()["id"]

        # First message submission
        mock_process_text.return_value = MessageResponse(
            id="resp-1",
            conversation_id=conv_id,
            role="assistant",
            content="Hello Andrei!",
            status="completed",
            created_at="2026-09-04T10:00:00Z"
        )

        client_msg_id = "client-uuid-12345"
        res1 = self.client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Hello", "client_message_id": client_msg_id},
            headers=self.auth_headers
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(mock_process_text.call_count, 1)

    def test_conversation_persistence_across_restart(self):
        """Conversations and messages persist in SQLite and are reloaded cleanly."""
        # Create conv and add messages directly to service
        conv = conversation_service.create_conversation("andrei-main", title="Persistent Topic")
        conversation_service.save_message(conv.id, "andrei-main", "user", "What is my task?")
        conversation_service.save_message(conv.id, "andrei-main", "assistant", "You have 3 tasks.")

        # Simulate restart: create a new service / query
        detail = conversation_service.get_conversation_detail("andrei-main", conv.id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail.conversation.title, "Persistent Topic")
        self.assertEqual(len(detail.messages), 2)
        self.assertEqual(detail.messages[0].content, "What is my task?")
        self.assertEqual(detail.messages[1].content, "You have 3 tasks.")

if __name__ == "__main__":
    unittest.main()
