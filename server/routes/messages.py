"""Messages API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from server.dependencies import get_current_user, verify_origin
from server.models import User
from server.schemas import MessageResponse, MessageSendRequest
from server.services.assistant_service import MessageStillProcessingError, assistant_service
from server.services.conversation_service import conversation_service

router = APIRouter(prefix="/api/conversations/{conversation_id}/messages", tags=["messages"])

@router.post("", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    payload: MessageSendRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Send a message to the assistant within a conversation."""
    content = payload.content.strip()
    if not content and not payload.attachment_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "EMPTY_MESSAGE", "message": "Message content or attachments required."}
        )

    # Verify conversation ownership
    detail = conversation_service.get_conversation_detail(user.id, conversation_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found."}
        )

    try:
        response = await assistant_service.process_text_message(
            conversation_id=conversation_id,
            user_id=user.id,
            content=content,
            client_message_id=payload.client_message_id,
            attachment_ids=payload.attachment_ids
        )
    except MessageStillProcessingError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MESSAGE_IN_PROGRESS",
                "message": "This message is still processing. Retry in a moment.",
            },
        )

    return response
