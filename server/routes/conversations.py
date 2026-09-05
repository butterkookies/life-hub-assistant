"""Conversations CRUD API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from server.dependencies import get_current_user, verify_origin
from server.models import User
from server.schemas import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationSummary,
)
from server.services.conversation_service import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationSummary])
async def list_conversations(user: User = Depends(get_current_user)):
    """List all conversations for the authenticated user."""
    return conversation_service.list_conversations(user.id)

@router.post("", response_model=ConversationSummary)
async def create_conversation(
    payload: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Create a new conversation."""
    return conversation_service.create_conversation(
        user_id=user.id,
        agent_id=payload.agent_id or "notion",
        title=payload.title
    )

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user)
):
    """Retrieve full conversation details and message history."""
    detail = conversation_service.get_conversation_detail(user.id, conversation_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found or not owned by user."}
        )
    return detail

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_origin)
):
    """Delete a conversation."""
    deleted = conversation_service.delete_conversation(user.id, conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found or not owned by user."}
        )
    return {"success": True, "message": "Conversation deleted."}
