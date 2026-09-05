"""FastAPI dependency injection for authentication, CSRF, and user resolution."""

from typing import Optional
from urllib.parse import urlparse
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from config import settings
from server.auth import COOKIE_NAME, validate_session
from server.database import get_db
from server.models import User

def verify_origin(request: Request) -> None:
    """CSRF protection: verify Origin or Referer for state-changing requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    host = request.headers.get("host", "").lower()

    target = origin or referer
    if not target:
        # If neither Origin nor Referer provided on a state-changing request,
        # allow only if Host matches localhost or Tailscale
        if host.startswith("localhost") or host.startswith("127.0.0.1"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CSRF_DETECTED", "message": "Missing Origin and Referer header."}
        )

    parsed = urlparse(target)
    target_origin = f"{parsed.scheme}://{parsed.netloc}".lower()

    # Check allowed origins
    allowed = [o.rstrip("/").lower() for o in settings.WEB_ALLOWED_ORIGINS]
    # Also allow current request host
    current_host_http = f"http://{host}".lower()
    current_host_https = f"https://{host}".lower()
    allowed.extend([current_host_http, current_host_https])

    if target_origin not in allowed and parsed.netloc.lower() != host:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_ORIGIN", "message": f"Untrusted origin: {target_origin}"}
        )

async def get_current_user(
    request: Request,
    _csrf: None = Depends(verify_origin)
) -> User:
    """Require valid authenticated session."""
    cookie_value = request.cookies.get(COOKIE_NAME)
    if not cookie_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}
        )

    user_id = validate_session(cookie_value)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "SESSION_EXPIRED", "message": "Session expired or invalid. Please log in again."}
        )

    with get_db() as db:
        row = db.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "USER_NOT_FOUND", "message": "User record not found."}
            )
        return User(id=str(row["id"]), username=str(row["username"]), created_at=str(row["created_at"]))

async def get_optional_user(request: Request) -> Optional[User]:
    """Optional session resolution without raising 401."""
    cookie_value = request.cookies.get(COOKIE_NAME)
    if not cookie_value:
        return None
    user_id = validate_session(cookie_value)
    if not user_id:
        return None
    try:
        with get_db() as db:
            row = db.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return User(id=str(row["id"]), username=str(row["username"]), created_at=str(row["created_at"]))
    except Exception:
        pass
    return None
