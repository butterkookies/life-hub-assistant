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

def update_page_properties(page_id: str, properties_json: str) -> str:
    """Update properties of an existing Notion page or database item (e.g. task status to Done, change priority, or archive).
    properties_json example: {"Status": "Done"} or {"Status": {"status": {"name": "Done"}}} or {"Priority": "High Priority"}.
    """
    try:
        props = json.loads(properties_json) if properties_json and properties_json != "{}" else {}
        res = notion_service.update_page_properties(page_id=page_id, properties=props)
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error updating page properties: {str(e)}"

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
    update_page_properties,
    append_to_page,
    create_new_page
]

MODEL_TIERS = [
    {"model": "gemini-3.7-flash", "display": "Gemini 3.7 Flash", "thinking": True},
    {"model": "gemini-3.6-flash", "display": "Gemini 3.6 Flash", "thinking": False},
    {"model": "gemini-2.5-flash", "display": "Gemini 2.5 Flash", "thinking": False},
    {"model": "gemini-flash-latest", "display": "Gemini Flash Latest", "thinking": False},
]

class GeminiNotionAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.histories: Dict[str, List[Any]] = {}

    def _ensure_client(self):
        if not self.client:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _build_config(self, enable_thinking: bool = False) -> types.GenerateContentConfig:
        thinking_cfg = types.ThinkingConfig(thinking_budget=-1) if enable_thinking else None
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=TOOLS,
            temperature=0.7,
            thinking_config=thinking_cfg
        )

    def _execute_turn(self, user_id: str, prompt_content: Any) -> str:
        """Execute a prompt turn across tiered models with unified rolling conversation history."""
        self._ensure_client()
        user_history = self.histories.get(user_id, [])
        last_error = None

        for tier_index, tier in enumerate(MODEL_TIERS):
            model_id = tier["model"]
            model_display = tier["display"]
            enable_thinking = tier["thinking"]

            try:
                config = self._build_config(enable_thinking=enable_thinking)
                chat = self.client.chats.create(
                    model=model_id,
                    config=config,
                    history=list(user_history)
                )

                response = chat.send_message(prompt_content)
                
                # Persist rolling conversation history (keep last 20 turns)
                try:
                    self.histories[user_id] = chat.get_history()[-20:]
                except Exception:
                    pass

                reply_text = response.text or "✅ Action completed in your Notion workspace."
                
                # Append discreet notification tag if served by a fallback model
                if tier_index > 0:
                    reply_text += f"\n\n_⚡ Handled via {model_display} fallback_"

                return reply_text

            except Exception as e:
                last_error = e
                logger.warning(f"Tier {model_display} ({model_id}) unavailable: {e}. Stepping down to next tier...")
                continue

        logger.error(f"All model tiers failed for user {user_id}: {last_error}", exc_info=True)
        return "⚠️ *Sorry, the AI service is experiencing a temporary spike.* Please try again in a few seconds."

    def process_text_message(self, user_id: str, message_text: str) -> str:
        """Process a text message from Telegram with tiered model fallback."""
        return self._execute_turn(user_id, message_text)

    def process_voice_message(self, user_id: str, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """Process a voice note audio from Telegram with tiered model fallback."""
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = [
            audio_part,
            "Please listen to this voice note and execute any Notion task, note, query, or scheduling instructions requested by Andrei."
        ]
        return self._execute_turn(user_id, prompt)

gemini_agent = GeminiNotionAgent()
