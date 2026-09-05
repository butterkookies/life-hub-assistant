"""Backend authentication and security tests."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from starlette.testclient import TestClient

from config import settings
from server.auth import (
    COOKIE_NAME,
    _LOGIN_ATTEMPTS,
    hash_password,
    verify_password,
)
from server.database import get_db, init_db
from server.main import create_app

class ServerAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_auth.db")
        self.upload_dir = os.path.join(self.temp_dir.name, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.test_password = "CorrectHorseBatteryStaple99!"
        self.test_hash = hash_password(self.test_password)
        self.test_secret = "test-session-secret-key-32-chars-long!"

        _LOGIN_ATTEMPTS.clear()

        # Patch environment variables
        self.env_patch = patch.dict(os.environ, {
            "DATABASE_PATH": self.db_path,
            "UPLOAD_DIR": self.upload_dir,
            "WEB_PASSWORD_HASH": self.test_hash,
            "WEB_SESSION_SECRET": self.test_secret,
            "WEB_ALLOWED_ORIGINS": "http://testserver,http://localhost:5173",
        })
        self.env_patch.start()

        init_db()
        self.app = create_app()
        self.client = TestClient(self.app, base_url="http://testserver")

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()


    def test_password_hash_and_verify(self):
        """Verify PBKDF2 hashing produces distinct salts and validates correctly."""
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        self.assertNotEqual(h1, h2)
        self.assertTrue(verify_password("secret123", h1))
        self.assertTrue(verify_password("secret123", h2))
        self.assertFalse(verify_password("wrong", h1))

    def test_login_success(self):
        """Successful login returns user summary and sets HttpOnly cookie."""
        res = self.client.post(
            "/api/auth/login",
            json={"password": self.test_password},
            headers={"Origin": "http://testserver"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "andrei")

        # Check cookie
        self.assertIn(COOKIE_NAME, res.cookies)
        cookie_header = res.headers.get("set-cookie", "")
        self.assertIn("HttpOnly", cookie_header)
        self.assertIn("SameSite=lax", cookie_header)

    def test_login_failure_invalid_password(self):
        """Failed login returns 401 with generic error message."""
        res = self.client.post(
            "/api/auth/login",
            json={"password": "wrongpassword"},
            headers={"Origin": "http://testserver"}
        )
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertEqual(data["error"]["code"], "INVALID_CREDENTIALS")
        self.assertNotIn(COOKIE_NAME, res.cookies)

    def test_missing_auth_configuration_fails_closed(self):
        """Missing WEB_PASSWORD_HASH causes server to fail closed with 500."""
        with patch.dict(os.environ, {"WEB_PASSWORD_HASH": ""}):
            res = self.client.post(
                "/api/auth/login",
                json={"password": self.test_password},
                headers={"Origin": "http://testserver"}
            )
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json()["error"]["code"], "AUTH_NOT_CONFIGURED")


    def test_login_rate_limiting(self):
        """Lock out client after 5 consecutive failed attempts."""
        for _ in range(5):
            res = self.client.post(
                "/api/auth/login",
                json={"password": "badpassword"},
                headers={"Origin": "http://testserver"}
            )
            self.assertEqual(res.status_code, 401)

        # 6th attempt should be rate limited (429)
        res = self.client.post(
            "/api/auth/login",
            json={"password": "badpassword"},
            headers={"Origin": "http://testserver"}
        )
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.json()["error"]["code"], "RATE_LIMITED")

    def test_csrf_origin_rejection(self):
        """Reject state-changing requests from untrusted origins."""
        res = self.client.post(
            "/api/auth/login",
            json={"password": self.test_password},
            headers={"Origin": "http://malicious-site.com"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN_ORIGIN")

    def test_unauthorized_api_access_rejected(self):
        """Protected endpoints reject requests without valid session cookie."""
        res = self.client.get("/api/conversations")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "UNAUTHORIZED")

    def test_session_expiration(self):
        """Expired session is rejected and removed."""
        # 1. Login
        login_res = self.client.post(
            "/api/auth/login",
            json={"password": self.test_password},
            headers={"Origin": "http://testserver"}
        )
        cookie_val = login_res.cookies.get(COOKIE_NAME)

        # 2. Artificially expire the session in SQLite
        past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with get_db() as db:
            db.execute("UPDATE sessions SET expires_at = ?", (past_time,))

        # 3. Access protected route with expired session
        res = self.client.get(
            "/api/conversations",
            headers={"Cookie": f"{COOKIE_NAME}={cookie_val}"}
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "SESSION_EXPIRED")

    def test_logout(self):
        """Logout revokes session in DB and deletes cookie."""
        # 1. Login
        login_res = self.client.post(
            "/api/auth/login",
            json={"password": self.test_password},
            headers={"Origin": "http://testserver"}
        )
        cookie_val = login_res.cookies.get(COOKIE_NAME)

        # 2. Logout
        logout_res = self.client.post(
            "/api/auth/logout",
            headers={"Cookie": f"{COOKIE_NAME}={cookie_val}", "Origin": "http://testserver"}
        )
        self.assertEqual(logout_res.status_code, 200)

        # 3. Old session cookie is now rejected
        res = self.client.get(
            "/api/conversations",
            headers={"Cookie": f"{COOKIE_NAME}={cookie_val}"}
        )
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
