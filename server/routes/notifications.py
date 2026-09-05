"""Web Push and notification API routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from server.dependencies import get_current_user, verify_origin
from server.models import User
from server.schemas import PushStatusResponse, PushSubscribeRequest
from server.services.briefing_service import briefing_service
from server.services.web_push_service import web_push_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class PushDeviceStatusRequest(BaseModel):
    endpoint: str


@router.post("/device-status", response_model=PushStatusResponse)
async def get_device_push_status(
    payload: PushDeviceStatusRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin),
):
    """Check this device without putting its private push endpoint in URL logs."""
    return PushStatusResponse(
        configured=web_push_service.is_configured(),
        subscribed=web_push_service.is_subscribed(user.id, payload.endpoint),
        vapid_public_key=web_push_service.get_public_key(),
    )

@router.get("/status", response_model=PushStatusResponse)
async def get_push_status(user: User = Depends(get_current_user)):
    """Check Web Push status and get public VAPID key."""
    return PushStatusResponse(
        configured=web_push_service.is_configured(),
        subscribed=web_push_service.is_subscribed(user.id),
        vapid_public_key=web_push_service.get_public_key()
    )

@router.post("/subscribe")
async def subscribe_push(
    payload: PushSubscribeRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Register Web Push subscription."""
    if not web_push_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PUSH_NOT_CONFIGURED", "message": "Web Push VAPID keys not configured on server."}
        )

    web_push_service.save_subscription(
        user_id=user.id,
        endpoint=payload.endpoint,
        p256dh=payload.keys.p256dh,
        auth=payload.keys.auth,
        user_agent=payload.user_agent
    )

    return {"success": True, "message": "Web Push subscription saved."}

@router.delete("/subscribe")
async def unsubscribe_push(
    payload: PushSubscribeRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Remove Web Push subscription."""
    removed = web_push_service.remove_subscription(user.id, payload.endpoint)
    return {"success": True, "message": "Subscription removed." if removed else "Subscription not found."}

@router.post("/test")
async def send_test_notification(
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Send a test push notification to user's registered devices."""
    if not web_push_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PUSH_NOT_CONFIGURED", "message": "Web Push VAPID keys not configured on server."}
        )

    sent = await asyncio.to_thread(
        web_push_service.send_notification,
        user_id=user.id,
        title="🔔 Test Notification",
        body="Andrei's Life Hub Assistant push notifications are working smoothly!",
        data={"url": "/"}
    )
    return {"success": sent > 0, "delivered_devices": sent}

@router.post("/briefing/trigger")
async def trigger_briefing(
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Generate and dispatch today's morning briefing immediately."""
    result = await briefing_service.dispatch_briefing(user_id=user.id)
    return {"success": True, "result": result}
