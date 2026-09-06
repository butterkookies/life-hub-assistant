"""Transport-neutral workout and treadmill image scan confirmation service."""

import asyncio
import functools
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from image_models import (
    AttachmentResult,
    ImageAnalysis,
    PendingImageScan,
    TreadmillScan,
    WorkoutUpsertResult,
)
from config import settings
from gemini_agent import gemini_agent
from notion_service import notion_service
from server.database import get_db
from server.schemas import PendingScanResponse
from server.storage import object_storage

logger = logging.getLogger("server.workout_scan_service")

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB
SUPPORTED_IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

def validate_image_bytes(image_bytes: bytes, declared_mime: str) -> Tuple[bool, str]:
    """Validate image size, MIME type, and magic bytes signature."""
    if not image_bytes:
        return False, "Uploaded image is empty"
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return False, "Image exceeds maximum allowed size of 15 MB"

    mime = declared_mime.lower().strip()
    if mime not in SUPPORTED_IMAGE_MIMES:
        return False, f"Unsupported image format: {declared_mime}. Allowed: JPEG, PNG, WebP, HEIC, HEIF"

    # Magic byte verification
    header = image_bytes[:32]
    if mime == "image/jpeg" and not header.startswith(b"\xff\xd8\xff"):
        return False, "File content does not match JPEG signature"
    elif mime == "image/png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return False, "File content does not match PNG signature"
    elif mime == "image/webp":
        if not (header.startswith(b"RIFF") and b"WEBP" in header[:16]):
            return False, "File content does not match WebP signature"
    elif mime in ("image/heic", "image/heif"):
        if b"ftyp" not in header[:20]:
            return False, "File content does not match HEIC/HEIF signature"

    return True, ""

class WorkoutScanService:
    def _cleanup_expired(self) -> None:
        """Remove expired pending scans from database and disk."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            rows = db.execute(
                "SELECT token, image_path FROM pending_image_scans WHERE expires_at < ?",
                (now_iso,)
            ).fetchall()
            db.execute("DELETE FROM pending_image_scans WHERE expires_at < ?", (now_iso,))
        for row in rows:
            object_storage.delete_quietly(str(row["image_path"]))

    def get_pending_scan(self, token: str, user_id: str) -> Optional[PendingScanResponse]:
        """Fetch pending scan by token and user_id."""
        self._cleanup_expired()
        with get_db() as db:
            row = db.execute(
                """
                SELECT token, user_id, conversation_id, filename, mime_type, image_path,
                       analysis_json, awaiting_correction, shown_conflicts_json,
                       created_at, expires_at
                FROM pending_image_scans
                WHERE token = ? AND user_id = ?
                """,
                (token, user_id)
            ).fetchone()

            if not row:
                return None

            analysis = ImageAnalysis.model_validate_json(row["analysis_json"])
            scan = analysis.treadmill
            if not scan:
                return None

            conflicts = None
            if row["shown_conflicts_json"]:
                try:
                    conflicts = json.loads(row["shown_conflicts_json"])
                except Exception:
                    pass

            metrics = {
                "duration_minutes": scan.duration_minutes,
                "distance_km": scan.distance_km,
                "steps": scan.steps,
                "calories_kcal": scan.calories_kcal,
                "speed_kmh": scan.speed_kmh,
                "heart_rate_bpm": scan.heart_rate_bpm,
                "trax_program": scan.trax_program,
                "workout_type": scan.workout_type,
            }

            validation_errors = scan.validation_errors()
            can_save = len(validation_errors) == 0

            return PendingScanResponse(
                token=str(row["token"]),
                filename=str(row["filename"]),
                date=scan.date,
                metrics=metrics,
                confidence=scan.confidence,
                uncertain_fields=scan.uncertain_fields,
                conflicts=conflicts,
                validation_errors=validation_errors,
                can_save=can_save,
                awaiting_correction=bool(row["awaiting_correction"])
            )

    def create_pending_scan(
        self,
        user_id: str,
        conversation_id: str,
        filename: str,
        mime_type: str,
        image_bytes: bytes,
        analysis: ImageAnalysis,
        shown_conflicts: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store pending scan record on disk and in database with 10 min TTL."""
        self._cleanup_expired()
        token = secrets.token_urlsafe(12)
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(minutes=10)).isoformat()
        now_iso = now.isoformat()

        storage_key = object_storage.pending_scan_key(user_id, token, filename)
        object_storage.put_bytes(storage_key, image_bytes, mime_type)

        conflicts_json = json.dumps(shown_conflicts) if shown_conflicts else None

        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO pending_image_scans (
                        token, user_id, conversation_id, filename, mime_type,
                        image_path, analysis_json, awaiting_correction,
                        shown_conflicts_json, created_at, expires_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    """,
                    (
                        token, user_id, conversation_id, filename, mime_type,
                        storage_key, analysis.model_dump_json(),
                        conflicts_json, now_iso, expires_at
                    )
                )
        except Exception:
            object_storage.delete_quietly(storage_key)
            raise
        return token

    async def process_image_upload(
        self,
        user_id: str,
        conversation_id: str,
        filename: str,
        mime_type: str,
        image_bytes: bytes,
        caption: str = ""
    ) -> Dict[str, Any]:
        """Analyze image and either auto-save or return pending confirmation."""
        # 1. Validate
        valid, err = validate_image_bytes(image_bytes, mime_type)
        if not valid:
            raise ValueError(err)

        # 2. Run Gemini analysis
        loop = asyncio.get_running_loop()
        analysis: ImageAnalysis = await loop.run_in_executor(
            None,
            gemini_agent.process_image_message,
            user_id,
            image_bytes,
            mime_type,
            caption
        )

        logger.info(f"Image analysis completed. Domain: {analysis.domain}, confidence: {analysis.confidence}")

        if analysis.domain != "treadmill" or not analysis.treadmill:
            return {
                "action": "non_workout",
                "summary": analysis.summary,
                "domain": analysis.domain,
                "confidence": analysis.confidence
            }

        scan = analysis.treadmill

        # 3. If auto-save eligible, attempt direct upsert
        if scan.is_auto_save_eligible():
            try:
                result: WorkoutUpsertResult = await loop.run_in_executor(
                    None,
                    functools.partial(
                        notion_service.upsert_daily_workout,
                        scan,
                        allow_overwrite=False
                    )
                )

                if result.action == "conflict":
                    # Conflict found with existing Notion page, hold for confirmation
                    token = self.create_pending_scan(
                        user_id, conversation_id, filename, mime_type, image_bytes, analysis, result.conflicts
                    )
                    return {
                        "action": "conflict",
                        "token": token,
                        "conflicts": result.conflicts,
                        "scan": self.get_pending_scan(token, user_id)
                    }

                # Attach image
                attachment: Optional[AttachmentResult] = None
                if result.action in ("created", "updated"):
                    attachment = await loop.run_in_executor(
                        None,
                        notion_service.attach_image,
                        result.page_id,
                        image_bytes,
                        mime_type,
                        filename
                    )

                return {
                    "action": "saved",
                    "result": result.model_dump(),
                    "attachment": attachment.model_dump() if attachment else None,
                    "scan": scan.model_dump()
                }
            except Exception as e:
                logger.error(f"Auto-save failed: {e}", exc_info=True)
                # Fall back to pending confirmation
                pass

        # 4. Require user confirmation
        token = self.create_pending_scan(
            user_id, conversation_id, filename, mime_type, image_bytes, analysis
        )
        return {
            "action": "requires_confirmation",
            "token": token,
            "scan": self.get_pending_scan(token, user_id)
        }

    async def confirm_scan(
        self, token: str, user_id: str, allow_overwrite: bool = True
    ) -> Dict[str, Any]:
        """Confirm and persist pending scan to Notion."""
        self._cleanup_expired()
        with get_db() as db:
            row = db.execute(
                """
                SELECT token, user_id, filename, mime_type, image_path, analysis_json,
                       shown_conflicts_json
                FROM pending_image_scans
                WHERE token = ? AND user_id = ?
                """,
                (token, user_id)
            ).fetchone()

            if not row:
                raise ValueError("Scan expired or not found")

            analysis = ImageAnalysis.model_validate_json(row["analysis_json"])
            scan = analysis.treadmill
            if not scan:
                raise ValueError("Scan does not contain treadmill values")

            image_path = str(row["image_path"])

            shown_conflicts = None
            if row["shown_conflicts_json"]:
                try:
                    shown_conflicts = json.loads(row["shown_conflicts_json"])
                except Exception:
                    pass

        try:
            image_bytes = object_storage.get_bytes(image_path)
        except Exception:
            image_bytes = b""

        loop = asyncio.get_running_loop()
        result: WorkoutUpsertResult = await loop.run_in_executor(
            None,
            functools.partial(
                notion_service.upsert_daily_workout,
                scan,
                allow_overwrite=allow_overwrite,
                expected_conflicts=shown_conflicts
            )
        )

        attachment: Optional[AttachmentResult] = None
        if result.action in ("created", "updated") and image_bytes:
            attachment = await loop.run_in_executor(
                None,
                notion_service.attach_image,
                result.page_id,
                image_bytes,
                row["mime_type"],
                row["filename"]
            )

        # Cleanup pending scan
        self.cancel_scan(token, user_id)

        return {
            "action": "saved",
            "result": result.model_dump(),
            "attachment": attachment.model_dump() if attachment else None,
            "scan": scan.model_dump()
        }

    async def correct_scan(
        self, token: str, user_id: str, correction_text: str
    ) -> Optional[PendingScanResponse]:
        """Apply natural-language correction to a pending scan."""
        self._cleanup_expired()
        with get_db() as db:
            row = db.execute(
                "SELECT analysis_json FROM pending_image_scans WHERE token = ? AND user_id = ?",
                (token, user_id)
            ).fetchone()

            if not row:
                raise ValueError("Scan expired or not found")

            original_analysis = ImageAnalysis.model_validate_json(row["analysis_json"])

        loop = asyncio.get_running_loop()
        updated_analysis = await loop.run_in_executor(
            None,
            gemini_agent.apply_image_correction,
            original_analysis,
            correction_text
        )

        with get_db() as db:
            db.execute(
                """
                UPDATE pending_image_scans
                SET analysis_json = ?, awaiting_correction = 0
                WHERE token = ? AND user_id = ?
                """,
                (updated_analysis.model_dump_json(), token, user_id)
            )

        return self.get_pending_scan(token, user_id)

    def cancel_scan(self, token: str, user_id: str) -> bool:
        """Cancel and delete pending scan."""
        storage_key = None
        with get_db() as db:
            row = db.execute(
                "SELECT image_path FROM pending_image_scans WHERE token = ? AND user_id = ?",
                (token, user_id)
            ).fetchone()
            if row:
                storage_key = str(row["image_path"])
                db.execute("DELETE FROM pending_image_scans WHERE token = ? AND user_id = ?", (token, user_id))
        if storage_key:
            object_storage.delete_quietly(storage_key)
            return True
        return False

workout_scan_service = WorkoutScanService()
