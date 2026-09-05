"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from config import settings
from server.auth import (
    COOKIE_NAME,
    check_login_rate_limit,
    clear_auth_cookie,
    create_session,
    destroy_session,
    record_failed_login,
    record_successful_login,
    set_auth_cookie,
    verify_password,
)
from server.dependencies import get_current_user, get_optional_user, verify_origin
from server.models import User
from server.schemas import (
    LoginRequest,
    LoginResponse,
    SessionResponse,
    UserSummary,
)
from server.services.web_push_service import web_push_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(verify_origin)
):
    """Authenticate user, set HttpOnly session cookie."""
    client_ip = get_client_ip(request)
    allowed, retry_after = check_login_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMITED",
                "message": f"Too many failed login attempts. Please wait {retry_after} seconds."
            }
        )

    stored_hash = settings.WEB_PASSWORD_HASH
    if not stored_hash:
        # Strict fail closed if auth configuration is missing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "AUTH_NOT_CONFIGURED",
                "message": "Authentication is not configured on the server. Please set WEB_PASSWORD_HASH in .env."
            }
        )

    if not verify_password(payload.password, stored_hash):
        record_failed_login(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid password. Access denied."
            }
        )

    record_successful_login(client_ip)
    user_id = "andrei-main"
    session_id, token_secret = create_session(user_id)
    set_auth_cookie(response, request, session_id, token_secret)

    return LoginResponse(
        success=True,
        user=UserSummary(id=user_id, username="andrei")
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    _csrf: None = Depends(verify_origin)
):
    """Log out user and invalidate session."""
    cookie_val = request.cookies.get(COOKIE_NAME)
    if cookie_val:
        destroy_session(cookie_val)
    clear_auth_cookie(response)
    return {"success": True, "message": "Logged out successfully."}

@router.get("/session", response_model=SessionResponse)
async def get_session(user: User = Depends(get_optional_user)):
    """Check current session status and push configuration."""
    if not user:
        return SessionResponse(
            authenticated=False,
            user=None,
            push_configured=web_push_service.is_configured(),
            vapid_public_key=web_push_service.get_public_key()
        )

    return SessionResponse(
        authenticated=True,
        user=UserSummary(id=user.id, username=user.username),
        push_configured=web_push_service.is_configured(),
        vapid_public_key=web_push_service.get_public_key()
    )
