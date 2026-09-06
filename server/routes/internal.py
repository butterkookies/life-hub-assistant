"""Server-to-server routes used by trusted schedulers."""

import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status

from config import settings
from server.services.briefing_service import briefing_service

router = APIRouter(prefix="/api/internal", tags=["internal"])


def _authorize(authorization: Optional[str]) -> None:
    expected = settings.BRIEFING_TRIGGER_TOKEN
    supplied = ""
    if authorization and authorization.startswith("Bearer "):
        supplied = authorization.removeprefix("Bearer ").strip()
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid scheduler credentials."},
        )


@router.post("/briefings/daily")
async def run_daily_briefing(authorization: Optional[str] = Header(default=None)):
    """Run today's idempotent briefing for the primary Life Hub user."""
    _authorize(authorization)
    result = await briefing_service.dispatch_briefing(user_id="andrei-main")
    return {"success": True, **result}
