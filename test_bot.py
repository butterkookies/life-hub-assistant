import sys
import os
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

def test_notion_connection():
    print("\n--- Testing Notion Service ---")
    try:
        from notion_service import notion_service
        results = notion_service.search_workspace(query="", filter_type="page")
        print(f"✅ Notion connection successful! Found {len(results)} pages.")
        for p in results[:3]:
            print(f"  - [{p['type'].upper()}] {p['title']} (ID: {p['id']})")
        return True
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False

def test_gemini_agent(prompt: str = "Search for projects in my Notion workspace"):
    print(f"\n--- Testing Gemini Agent with prompt: '{prompt}' ---")
    try:
        from gemini_agent import gemini_agent
        reply = gemini_agent.process_text_message(user_id="test_user", message_text=prompt)
        print("✅ Gemini Response:")
        print(reply)
        return True
    except Exception as e:
        print(f"❌ Gemini Agent failed: {e}")
        return False

if __name__ == "__main__":
    print("=== WhatsApp Notion Bot Diagnostic Test ===")
    if not os.path.exists(".env"):
        print("⚠️ .env file not found. Copying .env.example to .env for you...")
        with open(".env.example", "r", encoding="utf-8") as src, open(".env", "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print("👉 Please edit .env with your NOTION_API_KEY, GEMINI_API_KEY, and TWILIO credentials.")
        sys.exit(0)

    notion_ok = test_notion_connection()
    if notion_ok:
        test_gemini_agent()
