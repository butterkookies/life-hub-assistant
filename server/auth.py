"""Authentication, password verification, session tokens, and rate limiting."""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from fastapi import Request, Response
from config import settings
from server.database import get_db

logger = logging.getLogger("server.auth")

COOKIE_NAME = "life_hub_session"

# In-memory sliding window rate limiter for login attempts: ip -> [timestamps]
_LOGIN_ATTEMPTS: Dict[str, list[float]] = {}
MAX_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 minutes
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes

def hash_password(password: str, iterations: int = 600000) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 600,000 rounds and random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations
    )
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    if not password or not hashed:
        return False
    try:
        # Check if Argon2
        if hashed.startswith("$argon2"):
            try:
                import argon2
                ph = argon2.PasswordHasher()
                return ph.verify(hashed, password)
            except Exception:
                return False

        # PBKDF2 format: pbkdf2:sha256:iterations$salt$hash
        if not hashed.startswith("pbkdf2:sha256:"):
            return False
        header, salt, hash_hex = hashed.split("$")
        iterations = int(header.split(":")[2])
        test_derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations
        )
        return hmac.compare_digest(test_derived.hex(), hash_hex)
    except Exception:
        return False

def check_login_rate_limit(client_ip: str) -> Tuple[bool, int]:
    """Check if client IP is currently rate-limited. Returns (is_allowed, retry_after_seconds)."""
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(client_ip, [])
    # Filter attempts within window
    recent_attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    _LOGIN_ATTEMPTS[client_ip] = recent_attempts

    if len(recent_attempts) >= MAX_ATTEMPTS:
        oldest = recent_attempts[0]
        retry_after = int(LOCKOUT_DURATION_SECONDS - (now - oldest))
        return False, max(1, retry_after)
    return True, 0

def record_failed_login(client_ip: str) -> None:
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(client_ip, [])
    attempts.append(now)
    _LOGIN_ATTEMPTS[client_ip] = attempts

def record_successful_login(client_ip: str) -> None:
    _LOGIN_ATTEMPTS.pop(client_ip, None)

def create_session(user_id: str) -> Tuple[str, str]:
    """Create a persistent signed session. Returns (session_id, token_secret)."""
    session_id = secrets.token_urlsafe(24)
    token_secret = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_secret.encode("utf-8")).hexdigest()
    
    duration = timedelta(days=settings.WEB_SESSION_DAYS)
    expires_at = (datetime.now(timezone.utc) + duration).isoformat()
    created_at = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        db.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, token_hash, expires_at, created_at)
        )
    return session_id, token_secret

def format_cookie_token(session_id: str, token_secret: str) -> str:
    """Format combined session cookie value."""
    secret_key = settings.WEB_SESSION_SECRET or "dev-secret-key-change-in-production"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        f"{session_id}.{token_secret}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"{session_id}.{token_secret}.{signature}"

def parse_cookie_token(cookie_value: str) -> Optional[Tuple[str, str]]:
    """Verify signature and parse session_id and token_secret from cookie."""
    if not cookie_value:
        return None
    parts = cookie_value.split(".")
    if len(parts) != 3:
        return None
    session_id, token_secret, signature = parts
    secret_key = settings.WEB_SESSION_SECRET or "dev-secret-key-change-in-production"
    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        f"{session_id}.{token_secret}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        return None
    return session_id, token_secret

def validate_session(cookie_value: str) -> Optional[str]:
    """Validate session token and return user_id if valid and unexpired."""
    parsed = parse_cookie_token(cookie_value)
    if not parsed:
        return None
    session_id, token_secret = parsed
    token_hash = hashlib.sha256(token_secret.encode("utf-8")).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        row = db.execute(
            """
            SELECT user_id, token_hash, expires_at
            FROM sessions
            WHERE id = ?
            """,
            (session_id,)
        ).fetchone()

        if not row:
            return None

        if row["expires_at"] < now_iso:
            # Expired session
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return None

        if not hmac.compare_digest(row["token_hash"], token_hash):
            return None

        return str(row["user_id"])

def destroy_session(cookie_value: str) -> None:
    """Revoke session from database."""
    parsed = parse_cookie_token(cookie_value)
    if parsed:
        session_id, _ = parsed
        with get_db() as db:
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

def set_auth_cookie(response: Response, request: Request, session_id: str, token_secret: str) -> None:
    cookie_val = format_cookie_token(session_id, token_secret)
    max_age = settings.WEB_SESSION_DAYS * 86400
    # On HTTPS or Tailscale Serve, Secure=True. For plain localhost dev, allow fallback.
    is_secure = request.url.scheme == "https" or "tailscale" in request.headers.get("host", "").lower()
    response.set_cookie(
        key=COOKIE_NAME,
        value=cookie_val,
        max_age=max_age,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/"
    )

def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/"
    )
