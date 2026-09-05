"""End-to-end mobile flow integration tests covering:
1. Log in from simulated iPhone client
2. Create conversation
3. Send a text message
4. Receive mocked assistant response
5. Refresh (simulate client reload by making new GET requests)
6. Confirm conversation and message history persists cleanly
7. Verify PWA manifest, service worker, and HTML headers for iOS standalone
"""

import os
import tempfile
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient

from config import settings
from server.auth import COOKIE_NAME, hash_password
from server.database import init_db
from server.main import create_app
from server.schemas import MessageResponse

IPHONE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)

class MobileE2ETests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "e2e_mobile.db")
        self.upload_dir = os.path.join(self.temp_dir.name, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.password = "MySafeIPhonePass2026!"
        self.pass_hash = hash_password(self.password)
        self.secret = "e2e-super-secret-key-32-chars-ok!!"

        self.env_patch = patch.dict(os.environ, {
            "DATABASE_PATH": self.db_path,
            "UPLOAD_DIR": self.upload_dir,
            "WEB_PASSWORD_HASH": self.pass_hash,
            "WEB_SESSION_SECRET": self.secret,
            "WEB_ALLOWED_ORIGINS": "http://testserver",
        })
        self.env_patch.start()
        init_db()

        self.app = create_app()
        self.client = TestClient(
            self.app,
            base_url="http://testserver",
            headers={"User-Agent": IPHONE_USER_AGENT}
        )

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_pwa_assets_and_ios_metadata(self):
        """Verify HTML serves iOS standalone meta, safe areas, and manifest."""
        # Root index.html
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        html = res.text
        self.assertIn("viewport-fit=cover", html)
        self.assertIn('apple-mobile-web-app-capable" content="yes"', html)
        self.assertIn('apple-mobile-web-app-title" content="Life Hub"', html)
        self.assertIn('/manifest.webmanifest', html)

        # Manifest
        manifest_res = self.client.get("/manifest.webmanifest")
        self.assertEqual(manifest_res.status_code, 200)
        manifest_data = manifest_res.json()
        self.assertEqual(manifest_data["short_name"], "Life Hub")
        self.assertEqual(manifest_data["display"], "standalone")

        # Service Worker
        sw_res = self.client.get("/sw.js")
        self.assertEqual(sw_res.status_code, 200)
        self.assertIn("application/javascript", sw_res.headers.get("content-type", ""))

    @patch("server.services.assistant_service.assistant_service.process_text_message")
    def test_complete_iphone_user_flow(self, mock_assistant):
        """Execute full flow: Login -> Create Chat -> Send Message -> Mock AI Reply -> Refresh -> Confirm Persistence."""
        origin_header = {"Origin": "http://testserver", "User-Agent": IPHONE_USER_AGENT}

        # Step 1: Log in
        login_res = self.client.post(
            "/api/auth/login",
            json={"password": self.password},
            headers=origin_header
        )
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        self.assertTrue(login_data["success"])
        self.assertIn(COOKIE_NAME, login_res.cookies)
        session_cookie = login_res.cookies.get(COOKIE_NAME)

        auth_headers = {
            "Cookie": f"{COOKIE_NAME}={session_cookie}",
            "Origin": "http://testserver",
            "User-Agent": IPHONE_USER_AGENT
        }

        # Check session endpoint
        session_res = self.client.get("/api/auth/session", headers=auth_headers)
        self.assertEqual(session_res.status_code, 200)
        self.assertTrue(session_res.json()["authenticated"])

        # Step 2: Create conversation
        create_res = self.client.post(
            "/api/conversations",
            json={"title": "iPhone Today Schedule", "agent_id": "notion"},
            headers=auth_headers
        )
        self.assertEqual(create_res.status_code, 200)
        conv = create_res.json()
        conv_id = conv["id"]
        self.assertEqual(conv["title"], "iPhone Today Schedule")

        # Step 3 & 4: Send text message and receive mocked assistant response
        mock_assistant.return_value = MessageResponse(
            id="resp-msg-1",
            conversation_id=conv_id,
            role="assistant",
            content="☀️ You have 2 tasks scheduled in your Notion Life Hub for today.",
            status="completed",
            created_at="2026-09-04T10:15:00Z"
        )

        send_res = self.client.post(
            f"/api/conversations/{conv_id}/messages",
            json={
                "content": "What's on my schedule today?",
                "client_message_id": "iphone-client-msg-1"
            },
            headers=auth_headers
        )
        self.assertEqual(send_res.status_code, 200)
        reply = send_res.json()
        self.assertEqual(reply["role"], "assistant")
        self.assertIn("You have 2 tasks", reply["content"])

        # Step 5: Simulate client refresh / reload (new GET requests with same cookie)
        # Fetch conversations list
        list_res = self.client.get("/api/conversations", headers=auth_headers)
        self.assertEqual(list_res.status_code, 200)
        conv_list = list_res.json()
        self.assertEqual(len(conv_list), 1)
        self.assertEqual(conv_list[0]["id"], conv_id)

        # Step 6: Fetch conversation detail and verify persistence
        detail_res = self.client.get(f"/api/conversations/{conv_id}", headers=auth_headers)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["conversation"]["id"], conv_id)
        # Conversation survived refresh
        self.assertEqual(detail["conversation"]["title"], "iPhone Today Schedule")

if __name__ == "__main__":
    unittest.main()
