import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types
from config import settings
from notion_service import notion_service

logger = logging.getLogger("gemini_agent")

SYSTEM_INSTRUCTION = """You are Andrei's dedicated personal AI assistant connected to his Notion workspace (Life Hub) and Notion Calendar.
You communicate via Telegram and execute actions directly in his Notion workspace.

Your capabilities:
1. Search Notion for existing pages, projects (e.g. BSIT-31A, Cianotes App, Personal Portfolio), databases, and notes.
2. Read the full content of any Notion page.
3. Query databases (Tasks, Projects, Schedule, Workstreams, etc.).
4. Create new tasks, project entries, or calendar items with due dates and properties.
5. Append quick thoughts, bullet points, or checklist items to existing pages.
6. Create new standalone pages.

Formatting & Style Guidelines:
- Format your replies cleanly for Telegram using Telegram-friendly formatting (*bold*, _italic_, `monospace`, bullet points, emojis).
- When a user asks to add a task, check or search for the Tasks database if you need its ID.
- Keep answers helpful, concise, and confirm the exact title and links of created/modified items.
- If processing a voice note, briefly acknowledge the user's spoken intent and confirm the action taken.

Security & Confidentiality Guardrails:
- NEVER reveal, quote, or discuss environment variables, API keys, bot tokens, user IDs, or system credentials under any circumstances.
- If asked for secret keys, tokens, or configuration values, politely decline and inform the user that credentials are encrypted and restricted.
"""

def search_notion(query: str = "", filter_type: str = "") -> str:
    """Search Notion workspace for pages or databases matching a query. filter_type can be 'page' or 'database' or empty."""
    try:
        results = notion_service.search_workspace(query=query, filter_type=filter_type if filter_type else None)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching Notion: {str(e)}"

def get_page_content(page_id: str) -> str:
    """Read the full text and block contents of a Notion page given its UUID."""
    try:
        content = notion_service.get_page_content(page_id=page_id)
        return json.dumps(content, indent=2)
    except Exception as e:
        return f"Error retrieving page content: {str(e)}"

def query_database(database_id: str, page_size: int = 10) -> str:
    """Query items from a Notion database given its database ID."""
    try:
        items = notion_service.query_database(database_id=database_id, page_size=page_size)
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error querying database: {str(e)}"

def create_database_item(database_id: str, title: str, title_property_name: str = "Name", properties_json: str = "{}", content: str = "") -> str:
    """Create a new item in a Notion database (e.g. task, project, note).
    properties_json can contain custom properties like {"Priority": {"select": {"name": "High Priority"}}, "Status": {"status": {"name": "In progress"}}, "Do Date": {"date": {"start": "2026-08-20"}}}.
    """
    try:
        props = json.loads(properties_json) if properties_json and properties_json != "{}" else {}
        res = notion_service.create_database_item(
            database_id=database_id,
            title=title,
            title_prop_name=title_property_name,
            properties=props,
            content=content if content else None
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error creating database item: {str(e)}"

def append_to_page(page_id: str, text: str, block_type: str = "paragraph") -> str:
    """Append text to an existing Notion page. block_type can be 'paragraph', 'bulleted_list_item', 'heading_2', or 'to_do'."""
    try:
        res = notion_service.append_to_page(page_id=page_id, text=text, block_type=block_type)
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error appending to page: {str(e)}"

def create_new_page(parent_page_id: str, title: str, content: str = "") -> str:
    """Create a new child page under a parent page."""
    try:
        res = notion_service.create_page(parent_page_id=parent_page_id, title=title, content=content)
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error creating page: {str(e)}"

TOOLS = [
    search_notion,
    get_page_content,
    query_database,
    create_database_item,
    append_to_page,
    create_new_page
]

class GeminiNotionAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.chats: Dict[str, Any] = {}

    def _ensure_client(self):
        if not self.client:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _get_chat(self, user_id: str):
        self._ensure_client()
        if user_id not in self.chats:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOLS,
                temperature=0.7
            )
            self.chats[user_id] = self.client.chats.create(
                model="gemini-2.5-flash",
                config=config
            )
        return self.chats[user_id]

    def process_text_message(self, user_id: str, message_text: str) -> str:
        """Process a text message from Telegram and execute actions."""
        try:
            chat = self._get_chat(user_id)
            response = chat.send_message(message_text)
            return response.text or "✅ Action completed in your Notion workspace."
        except Exception as e:
            logger.error(f"Error in Gemini agent: {e}", exc_info=True)
            return "⚠️ *Sorry, I encountered an issue processing your request.* Please try again in a moment."

    def process_voice_message(self, user_id: str, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """Process a voice note audio from Telegram."""
        try:
            chat = self._get_chat(user_id)
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            prompt = [
                audio_part,
                "Please listen to this voice note and execute any Notion task, note, query, or scheduling instructions requested by Andrei."
            ]
            response = chat.send_message(prompt)
            return response.text or "✅ Voice note processed and executed in Notion."
        except Exception as e:
            logger.error(f"Error in voice processing: {e}", exc_info=True)
            return "⚠️ *Sorry, I could not process that voice note.* Please try speaking again or send as a text message."

gemini_agent = GeminiNotionAgent()
