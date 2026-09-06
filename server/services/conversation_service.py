"""Conversation and message persistence service with strict user ownership and idempotency."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from server.database import get_db
from server.models import Message
from server.schemas import (
    AttachmentSummary,
    ConversationDetailResponse,
    ConversationSummary,
    MessageResponse,
)
from server.storage import object_storage

class ConversationService:
    def list_conversations(self, user_id: str) -> List[ConversationSummary]:
        """List all conversations for user ordered by updated_at descending."""
        with get_db() as db:
            rows = db.execute(
                """
                SELECT c.id, c.agent_id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                """,
                (user_id,)
            ).fetchall()

            return [
                ConversationSummary(
                    id=str(r["id"]),
                    agent_id=str(r["agent_id"]),
                    title=str(r["title"]),
                    created_at=str(r["created_at"]),
                    updated_at=str(r["updated_at"]),
                    message_count=int(r["message_count"])
                )
                for r in rows
            ]

    def create_conversation(
        self, user_id: str, agent_id: str = "notion", title: Optional[str] = None
    ) -> ConversationSummary:
        """Create a new conversation."""
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conv_title = title.strip() if title and title.strip() else "New Conversation"

        with get_db() as db:
            db.execute(
                """
                INSERT INTO conversations (id, user_id, agent_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (conv_id, user_id, agent_id, conv_title, now, now)
            )

        return ConversationSummary(
            id=conv_id,
            agent_id=agent_id,
            title=conv_title,
            created_at=now,
            updated_at=now,
            message_count=0
        )

    def get_conversation_detail(
        self, user_id: str, conversation_id: str
    ) -> Optional[ConversationDetailResponse]:
        """Get conversation metadata and all messages with ownership enforcement."""
        with get_db() as db:
            conv_row = db.execute(
                """
                SELECT id, agent_id, title, created_at, updated_at
                FROM conversations
                WHERE id = ? AND user_id = ?
                """,
                (conversation_id, user_id)
            ).fetchone()

            if not conv_row:
                return None

            # Fetch attachments
            att_rows = db.execute(
                """
                SELECT id, message_id, filename, mime_type, size_bytes
                FROM attachments
                WHERE conversation_id = ? AND user_id = ?
                """,
                (conversation_id, user_id)
            ).fetchall()
            
            attachments_by_msg: Dict[str, List[AttachmentSummary]] = {}
            for a in att_rows:
                msg_id = str(a["message_id"]) if a["message_id"] else "__unlinked__"
                attachments_by_msg.setdefault(msg_id, []).append(
                    AttachmentSummary(
                        id=str(a["id"]),
                        filename=str(a["filename"]),
                        mime_type=str(a["mime_type"]),
                        size_bytes=int(a["size_bytes"]),
                        url=f"/api/attachments/{a['id']}"
                    )
                )

            # Fetch messages
            msg_rows = db.execute(
                """
                SELECT id, conversation_id, role, content, status, client_message_id,
                       error_message, tool_activity_json, created_at
                FROM messages
                WHERE conversation_id = ? AND user_id = ?
                ORDER BY created_at ASC
                """,
                (conversation_id, user_id)
            ).fetchall()

            messages: List[MessageResponse] = []
            for m in msg_rows:
                msg_id = str(m["id"])
                tool_activity = None
                if m["tool_activity_json"]:
                    try:
                        tool_activity = json.loads(m["tool_activity_json"])
                    except Exception:
                        pass

                messages.append(
                    MessageResponse(
                        id=msg_id,
                        conversation_id=str(m["conversation_id"]),
                        role=m["role"],
                        content=str(m["content"]),
                        status=m["status"],
                        client_message_id=m["client_message_id"],
                        tool_activity=tool_activity,
                        attachments=attachments_by_msg.get(msg_id, []),
                        created_at=str(m["created_at"]),
                        error_message=m["error_message"]
                    )
                )

            conv_summary = ConversationSummary(
                id=str(conv_row["id"]),
                agent_id=str(conv_row["agent_id"]),
                title=str(conv_row["title"]),
                created_at=str(conv_row["created_at"]),
                updated_at=str(conv_row["updated_at"]),
                message_count=len(messages)
            )

            return ConversationDetailResponse(
                conversation=conv_summary,
                messages=messages
            )

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete conversation and cascade delete its messages and attachments."""
        storage_keys: List[str] = []
        with get_db() as db:
            storage_keys = [
                str(row["file_path"])
                for row in db.execute(
                    "SELECT file_path FROM attachments WHERE conversation_id = ? AND user_id = ?",
                    (conversation_id, user_id),
                ).fetchall()
            ]
            cursor = db.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            )
            deleted = cursor.rowcount > 0
        if deleted:
            for key in storage_keys:
                object_storage.delete_quietly(key)
        return deleted

    def find_message_by_client_id(
        self, conversation_id: str, user_id: str, client_message_id: str
    ) -> Optional[Message]:
        """Check for duplicate message submission via client_message_id."""
        if not client_message_id:
            return None
        with get_db() as db:
            row = db.execute(
                """
                SELECT id, conversation_id, user_id, role, content, status,
                       client_message_id, error_message, tool_activity_json, created_at
                FROM messages
                WHERE conversation_id = ? AND user_id = ? AND client_message_id = ?
                """,
                (conversation_id, user_id, client_message_id)
            ).fetchone()

            if not row:
                return None
            return Message(
                id=str(row["id"]),
                conversation_id=str(row["conversation_id"]),
                user_id=str(row["user_id"]),
                role=str(row["role"]),
                content=str(row["content"]),
                status=str(row["status"]),
                client_message_id=row["client_message_id"],
                error_message=row["error_message"],
                tool_activity_json=row["tool_activity_json"],
                created_at=str(row["created_at"])
            )

    def save_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        client_message_id: Optional[str] = None,
        status: str = "completed",
        error_message: Optional[str] = None,
        tool_activity_json: Optional[str] = None,
        attachment_ids: Optional[List[str]] = None,
    ) -> Message:
        """Save a message and update conversation's updated_at."""
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with get_db() as db:
            db.execute(
                """
                INSERT INTO messages (
                    id, conversation_id, user_id, client_message_id, role,
                    content, status, error_message, tool_activity_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id, conversation_id, user_id, client_message_id, role,
                    content, status, error_message, tool_activity_json, now
                )
            )

            # Link attachments if any
            if attachment_ids:
                for att_id in attachment_ids:
                    db.execute(
                        "UPDATE attachments SET message_id = ? WHERE id = ? AND conversation_id = ?",
                        (msg_id, att_id, conversation_id)
                    )

            # Update conversation title if this is the first user message and title is default
            if role == "user":
                conv = db.execute(
                    "SELECT title FROM conversations WHERE id = ?",
                    (conversation_id,)
                ).fetchone()
                if conv and conv["title"] == "New Conversation":
                    # Generate concise title from first message
                    clean_title = content.strip().replace("\n", " ")
                    short_title = (clean_title[:36] + "...") if len(clean_title) > 36 else clean_title
                    db.execute(
                        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                        (short_title, now, conversation_id)
                    )
                else:
                    db.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (now, conversation_id)
                    )
            else:
                db.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id)
                )

        return Message(
            id=msg_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            status=status,
            client_message_id=client_message_id,
            error_message=error_message,
            tool_activity_json=tool_activity_json,
            created_at=now
        )

    def get_recent_turns(self, conversation_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get recent conversation history for Gemini rehydration."""
        with get_db() as db:
            rows = db.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ? AND status = 'completed' AND role IN ('user', 'assistant')
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (conversation_id, limit)
            ).fetchall()

            # Reverse to chronological order
            ordered = list(reversed(rows))
            return [
                {
                    "role": "user" if r["role"] == "user" else "model",
                    "content": r["content"]
                }
                for r in ordered
            ]

conversation_service = ConversationService()
