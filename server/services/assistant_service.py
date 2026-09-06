"""Transport-neutral shared assistant service connecting Gemini and Notion."""

import asyncio
import functools
import logging
from typing import Any, Dict, List, Optional
from google.genai import types
from config import settings
from gemini_agent import gemini_agent
from server.models import Message
from server.schemas import AttachmentSummary, MessageResponse
from server.services.conversation_service import conversation_service

logger = logging.getLogger("server.assistant_service")


class MessageStillProcessingError(Exception):
    """Raised when a replay arrives before its original response is stored."""


class AssistantService:
    def _get_idempotent_reply(
        self, conversation_id: str, user_id: str, client_message_id: str
    ) -> Optional[MessageResponse]:
        reply_id = f"reply:{client_message_id}"
        reply = conversation_service.find_message_by_client_id(
            conversation_id, user_id, reply_id
        )
        if not reply:
            return None
        return MessageResponse(
            id=reply.id,
            conversation_id=reply.conversation_id,
            role="assistant",
            content=reply.content,
            status=reply.status,
            client_message_id=reply.client_message_id,
            created_at=reply.created_at,
            error_message=reply.error_message,
        )

    def _rehydrate_gemini_history(self, conversation_id: str) -> None:
        """Rehydrate Gemini chat history from persistent SQLite records if not already in memory."""
        if conversation_id in gemini_agent.histories and gemini_agent.histories[conversation_id]:
            return

        turns = conversation_service.get_recent_turns(conversation_id, limit=20)
        if not turns:
            return

        rehydrated: List[Any] = []
        for turn in turns:
            role = turn["role"]  # 'user' or 'model'
            text = turn["content"]
            if not text:
                continue
            try:
                rehydrated.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text)]
                    )
                )
            except Exception as e:
                logger.debug(f"Could not convert turn to Content: {e}")

        if rehydrated:
            gemini_agent.histories[conversation_id] = rehydrated
            logger.info(f"Rehydrated {len(rehydrated)} conversation turns for {conversation_id}")

    async def process_text_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        client_message_id: Optional[str] = None,
        attachment_ids: Optional[List[str]] = None,
    ) -> MessageResponse:
        """Process user text message idempotently through Gemini agent."""
        # 1. Idempotency check: if client_message_id already exists, return existing reply
        if client_message_id:
            existing_user_msg = conversation_service.find_message_by_client_id(
                conversation_id, user_id, client_message_id
            )
            if existing_user_msg:
                reply = self._get_idempotent_reply(conversation_id, user_id, client_message_id)
                if reply:
                    return reply
                raise MessageStillProcessingError(client_message_id)

        # 2. Save user message to database
        try:
            conversation_service.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=content,
                client_message_id=client_message_id,
                attachment_ids=attachment_ids
            )
        except Exception:
            if client_message_id and conversation_service.find_message_by_client_id(
                conversation_id, user_id, client_message_id
            ):
                reply = self._get_idempotent_reply(conversation_id, user_id, client_message_id)
                if reply:
                    return reply
                raise MessageStillProcessingError(client_message_id)
            raise

        # 3. Rehydrate context
        self._rehydrate_gemini_history(conversation_id)

        # 4. Execute turn asynchronously without blocking event loop
        loop = asyncio.get_running_loop()
        try:
            raw_reply = await loop.run_in_executor(
                None,
                gemini_agent.process_text_message,
                conversation_id,
                content
            )
            # Remove any Telegram fallback tags if present, keeping clean text
            clean_reply = raw_reply.strip()

            assistant_msg = conversation_service.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=clean_reply,
                client_message_id=f"reply:{client_message_id}" if client_message_id else None,
                status="completed"
            )

            return MessageResponse(
                id=assistant_msg.id,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_msg.content,
                status="completed",
                created_at=assistant_msg.created_at
            )

        except Exception as e:
            logger.error(f"Error processing text message for conversation {conversation_id}: {e}", exc_info=True)
            # Safe sanitization: never leak internal exceptions or API keys to client
            error_content = "⚠️ I encountered an issue processing your request in Notion. Please try again."
            assistant_msg = conversation_service.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=error_content,
                client_message_id=f"reply:{client_message_id}" if client_message_id else None,
                status="failed",
                error_message="AI processing error"
            )
            return MessageResponse(
                id=assistant_msg.id,
                conversation_id=conversation_id,
                role="assistant",
                content=error_content,
                status="failed",
                created_at=assistant_msg.created_at,
                error_message="AI processing error"
            )

    async def process_voice_message(
        self,
        conversation_id: str,
        user_id: str,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        client_message_id: Optional[str] = None,
        attachment_id: Optional[str] = None,
    ) -> MessageResponse:
        """Process user voice note through Gemini agent."""
        # 1. Save user placeholder message
        user_msg = conversation_service.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content="🎙️ [Voice note]",
            client_message_id=client_message_id,
            attachment_ids=[attachment_id] if attachment_id else None
        )

        # 2. Rehydrate context
        self._rehydrate_gemini_history(conversation_id)

        # 3. Execute turn
        loop = asyncio.get_running_loop()
        try:
            raw_reply = await loop.run_in_executor(
                None,
                gemini_agent.process_voice_message,
                conversation_id,
                audio_bytes,
                mime_type
            )
            clean_reply = raw_reply.strip()

            assistant_msg = conversation_service.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=clean_reply,
                status="completed"
            )

            return MessageResponse(
                id=assistant_msg.id,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_msg.content,
                status="completed",
                created_at=assistant_msg.created_at
            )

        except Exception as e:
            logger.error(f"Error processing voice message for conversation {conversation_id}: {e}", exc_info=True)
            error_content = "⚠️ I could not process the voice recording. Please try speaking again or send text."
            assistant_msg = conversation_service.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=error_content,
                status="failed",
                error_message="Voice processing error"
            )
            return MessageResponse(
                id=assistant_msg.id,
                conversation_id=conversation_id,
                role="assistant",
                content=error_content,
                status="failed",
                created_at=assistant_msg.created_at,
                error_message="Voice processing error"
            )

assistant_service = AssistantService()
