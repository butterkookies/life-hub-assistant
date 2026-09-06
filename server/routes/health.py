"""Health check API routes."""

from fastapi import APIRouter, Response, status
from config import settings
from server.database import get_db
from server.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    """Health check endpoint verifying database connectivity and provider configuration."""
    db_ok = False
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="life-hub-assistant",
        version="1.0.0",
        telegram_enabled=settings.ENABLE_TELEGRAM,
        database_ok=db_ok,
        gemini_configured=bool(settings.GEMINI_API_KEY),
        notion_configured=bool(settings.NOTION_API_KEY)
    )
