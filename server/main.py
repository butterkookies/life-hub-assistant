"""FastAPI main application for Andrei's Life Hub Assistant."""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from server.database import init_db
from server.routes import (
    agents,
    auth,
    conversations,
    health,
    media,
    messages,
    notifications,
)
from server.services.briefing_service import briefing_service

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("server.main")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "microphone=(self), camera=(self)"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "media-src 'self' blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: ws: wss:; "
            "manifest-src 'self'; "
            "worker-src 'self';"
        )
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite database & directories
    logger.info("Initializing Life Hub database...")
    init_db()

    # 2. Start independent briefing scheduler task
    briefing_task = None
    if settings.DAILY_BRIEFING_ENABLED:
        briefing_task = asyncio.create_task(briefing_service.start_scheduler())

    yield

    # Shutdown
    if briefing_task:
        briefing_task.cancel()
        try:
            await briefing_task
        except asyncio.CancelledError:
            pass

def create_app() -> FastAPI:
    app = FastAPI(
        title="Andrei's Life Hub Assistant",
        description="Mobile-first PWA and API for Notion AI Assistant",
        version="1.0.0",
        lifespan=lifespan
    )

    # 1. Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. CORS (Explicit origins with credentials, plus common cloud domains)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.WEB_ALLOWED_ORIGINS,
        allow_origin_regex=r"^https?://.*(onrender\.com|up\.railway\.app|trycloudflare\.com|localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
    )

    # 3. Structured JSON Exception Handlers (never leak stack traces or internals)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(status_code=exc.status_code, content={"error": detail})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(detail)
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again."
                }
            }
        )

    # 4. Include API Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(conversations.router)
    app.include_router(messages.router)
    app.include_router(media.router)
    app.include_router(notifications.router)

    # 5. Static files & SPA fallback
    web_dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    web_public = Path(__file__).resolve().parent.parent / "web" / "public"

    if web_dist.exists() and (web_dist / "index.html").exists():
        logger.info(f"Mounting compiled frontend from {web_dist}")
        assets_dir = web_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        icons_dir = web_dist / "icons"
        if icons_dir.exists():
            app.mount("/icons", StaticFiles(directory=str(icons_dir)), name="icons")

        @app.get("/manifest.webmanifest", include_in_schema=False)
        async def manifest():
            manifest_file = web_dist / "manifest.webmanifest"
            if not manifest_file.exists():
                manifest_file = web_public / "manifest.webmanifest"
            if manifest_file.exists():
                return FileResponse(str(manifest_file), media_type="application/manifest+json")
            raise HTTPException(status_code=404)

        @app.get("/sw.js", include_in_schema=False)
        async def service_worker():
            sw_file = web_dist / "sw.js"
            if not sw_file.exists():
                sw_file = web_public / "sw.js"
            if sw_file.exists():
                return FileResponse(str(sw_file), media_type="application/javascript")
            raise HTTPException(status_code=404)

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str):
            # If path starts with api/, return 404
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "API endpoint not found."})
            target_file = web_dist / full_path
            if target_file.exists() and target_file.is_file():
                return FileResponse(str(target_file))
            return FileResponse(str(web_dist / "index.html"))

    else:
        logger.info("web/dist not found. Serving development placeholder.")
        @app.get("/", response_class=HTMLResponse)
        async def dev_root():
            return HTMLResponse(
                """
                <!DOCTYPE html>
                <html>
                <head><title>Andrei's Life Hub Assistant (API Active)</title></head>
                <body style="font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; line-height: 1.6;">
                    <h2>Andrei's Life Hub Assistant</h2>
                    <p>🟢 FastAPI Backend is active and running!</p>
                    <p>The web frontend has not been compiled yet. Run <code>cd web && npm run build</code> or start the Vite dev server with <code>cd web && npm run dev</code>.</p>
                    <p><a href="/api/health">Check API Health</a></p>
                </body>
                </html>
                """
            )

    return app

app = create_app()

def main():
    import uvicorn
    port = settings.PORT or 8000
    print(f"🚀 Starting Life Hub Assistant server on port {port}...")
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
