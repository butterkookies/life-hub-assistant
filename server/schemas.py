"""API Request and Response schemas for Andrei's Life Hub Assistant."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1)

class UserSummary(BaseModel):
    id: str
    username: str

class LoginResponse(BaseModel):
    success: bool
    user: UserSummary

class SessionResponse(BaseModel):
    authenticated: bool
    user: Optional[UserSummary] = None
    push_configured: bool = False
    vapid_public_key: Optional[str] = None

class AgentDefinition(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str]
    status: Literal["available", "busy", "offline"] = "available"

class ConversationCreateRequest(BaseModel):
    agent_id: str = "notion"
    title: Optional[str] = None

class ConversationSummary(BaseModel):
    id: str
    agent_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0

class AttachmentSummary(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    url: Optional[str] = None

class MessageSendRequest(BaseModel):
    content: str
    client_message_id: Optional[str] = None
    attachment_ids: Optional[List[str]] = Field(default_factory=list)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    status: Literal["pending", "completed", "failed"] = "completed"
    client_message_id: Optional[str] = None
    tool_activity: Optional[List[Dict[str, Any]]] = None
    attachments: List[AttachmentSummary] = Field(default_factory=list)
    created_at: str
    error_message: Optional[str] = None
    pending_scan: Optional[Dict[str, Any]] = None

class ConversationDetailResponse(BaseModel):
    conversation: ConversationSummary
    messages: List[MessageResponse]

class PendingScanResponse(BaseModel):
    token: str
    filename: str
    date: str
    metrics: Dict[str, Any]
    confidence: float
    uncertain_fields: List[str]
    conflicts: Optional[Dict[str, Any]] = None
    validation_errors: List[str]
    can_save: bool
    awaiting_correction: bool = False

class ImageScanCorrectRequest(BaseModel):
    correction_text: str

class PushKeys(BaseModel):
    p256dh: str
    auth: str

class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushKeys
    user_agent: Optional[str] = None

class PushStatusResponse(BaseModel):
    configured: bool
    subscribed: bool
    vapid_public_key: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "1.0.0"
    telegram_enabled: bool
    database_ok: bool
    gemini_configured: bool
    notion_configured: bool
