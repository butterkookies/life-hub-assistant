"""Media upload, voice processing, and image workout scan confirmation routes."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from server.database import get_db
from server.dependencies import get_current_user, verify_origin
from server.models import User
from server.schemas import (
    AttachmentSummary,
    ImageScanCorrectRequest,
    MessageResponse,
    PendingScanResponse,
)
from server.services.assistant_service import assistant_service
from server.services.conversation_service import conversation_service
from server.services.workout_scan_service import (
    MAX_IMAGE_BYTES,
    SUPPORTED_IMAGE_MIMES,
    validate_image_bytes,
    workout_scan_service,
)
from server.storage import StorageQuotaExceeded, object_storage

logger = logging.getLogger("server.media")

router = APIRouter(tags=["media"])

SUPPORTED_AUDIO_MIMES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/mp3",
    "audio/mpeg",
    "audio/m4a",
    "audio/mp4",
    "audio/x-m4a",
}

@router.post("/api/conversations/{conversation_id}/attachments")
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    client_message_id: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Upload media (voice or image), validate safety, and dispatch processing."""
    # Verify conversation ownership
    detail = conversation_service.get_conversation_detail(user.id, conversation_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found."}
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "Uploaded file is empty."}
        )

    if len(file_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_IMAGE_BYTES // (1024*1024)} MB limit."}
        )


    declared_mime = (file.content_type or "application/octet-stream").lower().split(";")[0].strip()
    raw_filename = file.filename or "attachment"
    safe_basename = Path(raw_filename).name  # Prevent path traversal
    att_id = str(uuid.uuid4())
    storage_key = object_storage.attachment_key(user.id, att_id, safe_basename)
    try:
        await asyncio.to_thread(object_storage.put_bytes, storage_key, file_bytes, declared_mime)
    except StorageQuotaExceeded as err:
        raise HTTPException(
            status_code=507,
            detail={"code": "STORAGE_SAFETY_LIMIT", "message": str(err)},
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    # Save attachment metadata
    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO attachments (id, conversation_id, user_id, filename, file_path, mime_type, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (att_id, conversation_id, user.id, safe_basename, storage_key, declared_mime, len(file_bytes), now_iso)
            )
    except Exception:
        await asyncio.to_thread(object_storage.delete_quietly, storage_key)
        raise

    # 1. Audio / Voice Note Handling
    if declared_mime in SUPPORTED_AUDIO_MIMES or "audio" in declared_mime:
        response = await assistant_service.process_voice_message(
            conversation_id=conversation_id,
            user_id=user.id,
            audio_bytes=file_bytes,
            mime_type=declared_mime,
            client_message_id=client_message_id,
            attachment_id=att_id
        )
        return {
            "type": "voice",
            "message": response
        }

    # 2. Image / Workout Handling
    if declared_mime in SUPPORTED_IMAGE_MIMES or "image" in declared_mime:
        try:
            scan_result = await workout_scan_service.process_image_upload(
                user_id=user.id,
                conversation_id=conversation_id,
                filename=safe_basename,
                mime_type=declared_mime,
                image_bytes=file_bytes,
                caption=caption or ""
            )

            # Record in conversation timeline
            if scan_result["action"] == "saved":
                scan_data = scan_result.get("scan", {})
                content = (
                    f"✅ **Workout saved to Notion**\n"
                    f"- Date: `{scan_data.get('date')}`\n"
                    f"- Duration: `{scan_data.get('duration_minutes')} min`\n"
                    f"- Distance: `{scan_data.get('distance_km')} km`\n"
                    f"- Steps: `{scan_data.get('steps')}`\n"
                    f"- Calories: `{scan_data.get('calories_kcal')} kcal`"
                )
                msg = conversation_service.save_message(
                    conversation_id=conversation_id,
                    user_id=user.id,
                    role="assistant",
                    content=content,
                    status="completed",
                    attachment_ids=[att_id]
                )
                return {
                    "type": "image",
                    "action": "saved",
                    "message": MessageResponse(
                        id=msg.id,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=msg.content,
                        status="completed",
                        attachments=[
                            AttachmentSummary(
                                id=att_id,
                                filename=safe_basename,
                                mime_type=declared_mime,
                                size_bytes=len(file_bytes),
                                url=f"/api/attachments/{att_id}"
                            )
                        ],
                        created_at=msg.created_at
                    )
                }

            elif scan_result["action"] in ("requires_confirmation", "conflict"):
                # Return pending scan response so the frontend renders the confirmation card
                return {
                    "type": "image",
                    "action": scan_result["action"],
                    "token": scan_result["token"],
                    "scan": scan_result["scan"]
                }
            else:
                # Non-workout image
                msg = conversation_service.save_message(
                    conversation_id=conversation_id,
                    user_id=user.id,
                    role="assistant",
                    content=f"🖼️ Image analysis: {scan_result.get('summary', 'Image received.')}",
                    status="completed",
                    attachment_ids=[att_id]
                )
                return {
                    "type": "image",
                    "action": "non_workout",
                    "message": MessageResponse(
                        id=msg.id,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=msg.content,
                        status="completed",
                        attachments=[
                            AttachmentSummary(
                                id=att_id,
                                filename=safe_basename,
                                mime_type=declared_mime,
                                size_bytes=len(file_bytes),
                                url=f"/api/attachments/{att_id}"
                            )
                        ],
                        created_at=msg.created_at
                    )
                }
        except StorageQuotaExceeded as err:
            with get_db() as db:
                db.execute("DELETE FROM attachments WHERE id = ? AND user_id = ?", (att_id, user.id))
            await asyncio.to_thread(object_storage.delete_quietly, storage_key)
            raise HTTPException(
                status_code=507,
                detail={"code": "STORAGE_SAFETY_LIMIT", "message": str(err)},
            )
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_IMAGE", "message": str(err)}
            )
        except Exception as err:
            logger.error(f"Image scan failed: {err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "IMAGE_SCAN_FAILED", "message": "Could not read image display. Please retry."}
            )

    with get_db() as db:
        db.execute("DELETE FROM attachments WHERE id = ? AND user_id = ?", (att_id, user.id))
    await asyncio.to_thread(object_storage.delete_quietly, storage_key)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "UNSUPPORTED_TYPE", "message": f"Unsupported file type: {declared_mime}"}
    )

@router.get("/api/attachments/{attachment_id}")
async def get_attachment(
    attachment_id: str,
    user: User = Depends(get_current_user)
):
    """Serve attachment file ensuring ownership check and path traversal safety."""
    with get_db() as db:
        row = db.execute(
            "SELECT file_path, filename, mime_type FROM attachments WHERE id = ? AND user_id = ?",
            (attachment_id, user.id)
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ATTACHMENT_NOT_FOUND", "message": "Attachment not found."}
            )

        storage_key = str(row["file_path"])
        filename = str(row["filename"])
        mime_type = str(row["mime_type"])

    try:
        content = await asyncio.to_thread(object_storage.get_bytes, storage_key)
    except StorageQuotaExceeded as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "STORAGE_SAFETY_LIMIT", "message": str(err)},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_MISSING", "message": "Stored file is missing."}
        )

    encoded_filename = quote(filename, safe="")
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": (
                f"inline; filename=attachment; filename*=UTF-8''{encoded_filename}"
            )
        }
    )

# Image Scan Confirmations
@router.post("/api/image-scans/{token}/confirm")
async def confirm_scan(
    token: str,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Confirm pending image scan and persist workout to Notion."""
    try:
        result = await workout_scan_service.confirm_scan(token, user.id, allow_overwrite=True)
        return result
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SCAN_ERROR", "message": str(err)}
        )
    except Exception as err:
        logger.error(f"Error confirming scan: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CONFIRMATION_FAILED", "message": "Could not save workout to Notion."}
        )

@router.post("/api/image-scans/{token}/correct", response_model=PendingScanResponse)
async def correct_scan(
    token: str,
    payload: ImageScanCorrectRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Apply correction to pending image scan."""
    try:
        updated = await workout_scan_service.correct_scan(token, user.id, payload.correction_text)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SCAN_EXPIRED", "message": "Pending scan expired or not found."}
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SCAN_ERROR", "message": str(err)}
        )
    except Exception as err:
        logger.error(f"Error correcting scan: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CORRECTION_FAILED", "message": "Could not apply correction."}
        )

@router.post("/api/image-scans/{token}/cancel")
async def cancel_scan(
    token: str,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Cancel pending image scan."""
    cancelled = workout_scan_service.cancel_scan(token, user.id)
    return {"success": cancelled, "message": "Scan cancelled." if cancelled else "Scan not found or expired."}
