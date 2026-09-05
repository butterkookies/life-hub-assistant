"""Typed models for server data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class User:
    id: str
    username: str
    created_at: str

@dataclass
class Session:
    id: str
    user_id: str
    token_hash: str
    expires_at: str
    created_at: str

@dataclass
class Conversation:
    id: str
    user_id: str
    agent_id: str
    title: str
    created_at: str
    updated_at: str

@dataclass
class Message:
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    status: str = "completed"
    client_message_id: Optional[str] = None
    error_message: Optional[str] = None
    tool_activity_json: Optional[str] = None
    created_at: str = ""

@dataclass
class Attachment:
    id: str
    conversation_id: str
    user_id: str
    filename: str
    file_path: str
    mime_type: str
    size_bytes: int
    created_at: str
    message_id: Optional[str] = None

@dataclass
class PendingScanRecord:
    token: str
    user_id: str
    conversation_id: str
    filename: str
    mime_type: str
    image_path: str
    analysis_json: str
    awaiting_correction: bool
    shown_conflicts_json: Optional[str]
    created_at: str
    expires_at: str

@dataclass
class PushSubscriptionRecord:
    id: str
    user_id: str
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str]
    created_at: str
