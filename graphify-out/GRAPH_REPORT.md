# Graph Report - NOTION  (2026-09-05)

## Corpus Check
- 74 files · ~39,624 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1204 nodes · 2239 edges · 88 communities (71 shown, 17 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 287 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d2226f42`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 54 edges
2. `ImageAnalysis` - 46 edges
3. `WorkoutUpsertResult` - 38 edges
4. `NotionDesktopWidget` - 38 edges
5. `AttachmentResult` - 37 edges
6. `TreadmillScan` - 35 edges
7. `PendingImageScan` - 32 edges
8. `User` - 32 edges
9. `MessageResponse` - 30 edges
10. `NotionService` - 27 edges

## Surprising Connections (you probably didn't know these)
- `_values_match()` --calls--> `float`  [INFERRED]
  notion_service.py → config.py
- `int` --uses--> `ImageAnalysis`  [INFERRED]
  gemini_agent.py → image_models.py
- `str` --uses--> `ImageAnalysis`  [INFERRED]
  gemini_agent.py → image_models.py
- `bool` --uses--> `ImageAnalysis`  [INFERRED]
  gemini_agent.py → image_models.py
- `GeminiNotionAgent` --uses--> `ImageAnalysis`  [INFERRED]
  gemini_agent.py → image_models.py

## Communities (88 total, 17 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (24): DailyProgress(), DailyProgressProps, FilterBar(), FilterBarProps, InlineTaskAdd(), InlineTaskAddProps, QuickAddModal(), QuickAddModalProps (+16 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (57): DEFAULT_TYPE, briefing_command(), check_auth(), _cleanup_image_state(), daily_briefing_scheduler(), email_command(), format_for_telegram(), handle_image() (+49 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (21): str, append_to_page(), create_database(), create_database_item(), create_new_page(), get_page_content(), Update properties of an existing Notion page or database item (e.g. task status, Append text to an existing Notion page. block_type can be 'paragraph', 'bulleted (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (32): CONFIG_PATH, createTrayIcon(), createWindow(), DEFAULT_CONFIG, _dirname, loadConfig(), saveConfig(), setupTray() (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (32): dependencies, clsx, dotenv, lucide-react, @notionhq/client, react, react-dom, tailwind-merge (+24 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (35): _notion_property_value(), NotionService, Query items in a Notion database or data source., Create or safely update the single health-log row for a date., Retrieve scheduled tasks and calendar events for a specific date (YYYY-MM-DD) or, Search pages and databases across the workspace., Fetch all projects and map their IDs (both hyphenated and clean) to project name, Retrieve rich tasks for a specific date (YYYY-MM-DD), with mapped project names (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (25): last_synced, projects, 3be271025287811dab16ed7bb7156ce1, 3be271025287812cb2f9fd5c3690f556, 3be271025287813aa28cf73397265eab, 3be2710252878146bb43d2622fd62e0f, 3be27102528781508acff8d2b9c52119, 3be2710252878167957cf6825d481689 (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (33): bool, int, str, float, ALLOWED_TELEGRAM_USER_IDS(), DAILY_BRIEFING_ENABLED(), DAILY_BRIEFING_TIME(), DATABASE_PATH() (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (13): bool, str, EmailService, Wrap the briefing content into a modern, responsive newsletter-style email conta, Service to handle formatting and delivering rich HTML email notifications and da, Send email via SMTP (Gmail, SendGrid, Brevo, Outlook, etc.)., Check if minimum required email credentials are configured., Send email via Resend REST API. (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (11): _(), A, ae, F, ie, j(), K, L (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (40): ConversationDrawer(), ConversationDrawerProps, ConversationTimeline(), ConversationTimelineProps, GREETINGS, Header(), HeaderProps, IosInstallGuide() (+32 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (5): NotionDesktopWidget, Hide main window and notify user in system tray., Save settings and cleanly exit., Main Windows Home Screen Widget Application., Fetch tasks and project map from Notion in a background thread.

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (5): Any, str, Create task in Notion and update UI., Render task cards into the scrollable list., Optimistically update UI and sync new status to Notion.

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (6): Interactive card representing a single task., TaskCard, Test Suite for Notion Tasks Desktop Widget Verifies config persistence, cache ma, TestNotionTasksSync, TestWidgetManager, TestWidgetUIInitialization

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (13): always_on_top, auto_refresh_minutes, filter_mode, height, opacity, pinned_to_desktop, show_completed, start_with_windows (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (6): get_project_color(), main(), QuickAddTaskDialog, Notion Tasks - Modern Windows Desktop Widget A sleek, customizable desktop widge, Deterministically assign a color pair to a project name., Modal dialog for quickly adding a new task to Notion for today.

### Community 26 - "Community 26"
Cohesion: 0.23
Nodes (21): LoginRequest, get_client_ip(), get_session(), login(), logout(), Authentication API routes., Authenticate user, set HttpOnly session cookie., Log out user and invalidate session. (+13 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (26): dependencies, clsx, dompurify, lucide-react, marked, react, react-dom, tailwind-merge (+18 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (19): FastAPI, list_agents(), Agent registry API routes., List available AI agents and capabilities., Conversations CRUD API routes., Media upload, voice processing, and image workout scan confirmation routes., Validate session token and return user_id if valid and unexpired., validate_session() (+11 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (25): 1. Prerequisites, 2. Install Dependencies, 3. Generate Security Credentials, 4. Configure Your `.env` File, 🏛️ Andrei's Life Hub Assistant (Mobile-First PWA + FastAPI + Notion AI), code:block1 ([ 📱 iPhone / iPad (Safari PWA) ] ──── [ 💻 Windows / Desktop ), code:bash (cd web), code:bash (# Python backend dependencies) (+17 more)

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (20): Connection, PendingScanResponse, get_db(), Context manager for SQLite connections with row factory and foreign keys., PendingScanResponse, Any, bool, bytes (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.20
Nodes (11): ConversationCreateRequest, create_conversation(), delete_conversation(), get_conversation(), list_conversations(), List all conversations for the authenticated user., Create a new conversation., Retrieve full conversation details and message history. (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (16): ConversationSummary, Message, ConversationDetailResponse, ConversationSummary, bool, int, str, ConversationService (+8 more)

### Community 33 - "Community 33"
Cohesion: 0.10
Nodes (10): Lock out client after 5 consecutive failed attempts., Reject state-changing requests from untrusted origins., Protected endpoints reject requests without valid session cookie., Expired session is rejected and removed., Logout revokes session in DB and deletes cookie., Verify PBKDF2 hashing produces distinct salts and validates correctly., Successful login returns user summary and sets HttpOnly cookie., Failed login returns 401 with generic error message. (+2 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.28
Nodes (12): ConversationDetailResponse, MessageResponse, Message, AttachmentSummary, MessageResponse, bytes, str, AssistantService (+4 more)

### Community 36 - "Community 36"
Cohesion: 0.18
Nodes (7): TelegramImageHandlerTests, test_attachment_failure_keeps_saved_metrics_and_warns(), test_first_save_that_finds_conflicts_requires_second_confirmation(), test_save_callback_is_bound_to_pending_user(), test_uncertain_scan_creates_preview_without_notion_write(), test_valid_scan_auto_saves_and_attaches(), treadmill_analysis()

### Community 37 - "Community 37"
Cohesion: 0.21
Nodes (14): check_login_rate_limit(), destroy_session(), parse_cookie_token(), bool, int, str, Authentication, password verification, session tokens, and rate limiting., Verify signature and parse session_id and token_secret from cookie. (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (15): PushSubscribeRequest, get_push_status(), Web Push and notification API routes., Check Web Push status and get public VAPID key., Register Web Push subscription., Remove Web Push subscription., Send a test push notification to user's registered devices., Generate and dispatch today's morning briefing immediately. (+7 more)

### Community 39 - "Community 39"
Cohesion: 0.18
Nodes (10): Any, bool, str, BriefingService, Scheduled briefing service independent of Telegram., Background task running continuously to deliver scheduled briefings., Check if briefing was already delivered today via this channel., Record successful delivery to prevent duplicate dispatches. (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.19
Nodes (9): Any, bool, int, str, Web Push notifications service using VAPID and standards-based Push API., Check if VAPID keys are configured., Save or update Web Push subscription., Send push notification to all active devices registered by user. (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (5): AgentDefinition, AgentDefinition, str, AgentRegistry, Agent Registry for Life Hub Assistant and future agents.

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (11): bool, datetime, str, Typed contracts for Telegram image analysis and workout persistence., Structured values observed on a treadmill display., Return deterministic plausibility failures without mutating the scan., TreadmillScan, AttachmentResult (+3 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (14): ImageScanCorrectRequest, cancel_scan(), confirm_scan(), correct_scan(), get_attachment(), Serve attachment file ensuring ownership check and path traversal safety., Confirm pending image scan and persist workout to Notion., Apply correction to pending image scan. (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (13): BaseModel, MessageSendRequest, Send a message to the assistant within a conversation., send_message(), str, User, ConversationCreateRequest, ErrorDetail (+5 more)

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (12): 1. Executive Summary & Core Value, 2. End-to-End System Architecture, 3. Repository File Map & Responsibilities, 6. Configuration & Environment Variables, 8. Testing & Diagnostics Suite, 📘 Andrei's Life Hub Assistant — Onboarding & Architecture Guide, code:block1 ([ 📱 iPhone / iPad (Safari PWA) ] ────── [ 💻 Windows / Deskto), code:block2 (NOTION/) (+4 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (9): init_db(), Initialize SQLite database with schema and ensure default user exists., create_app(), lifespan(), FastAPI main application for Andrei's Life Hub Assistant., Backend authentication and security tests., MobileE2ETests, End-to-end mobile flow integration tests covering: 1. Log in from simulated iPho (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.17
Nodes (12): 7. Getting Started & Local Execution, code:bash (pip install -r requirements.txt), code:bash (cd web), code:bash (# 1. Generate password hash for your access password:), code:bash (python test_connections.py), code:bash (python -m uvicorn server.main:app --host 0.0.0.0 --port 8000), Prerequisites, Step 1: Install Backend Dependencies (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (13): create_session(), format_cookie_token(), hash_password(), Format combined session cookie value., Hash password using PBKDF2-HMAC-SHA256 with 600,000 rounds and random salt., Create a persistent signed session. Returns (session_id, token_secret)., Tests for conversation management, message persistence, ownership, and idempoten, Tests for Web Push subscriptions, scheduled briefing duplicate prevention, healt (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.22
Nodes (7): Any, bytes, datetime, ImageAnalysis, Run typed image extraction through the stable model fallback chain., Classify an image and extract a typed treadmill scan when applicable., Apply an authorized natural-language correction to a pending extraction.

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (15): Application, InlineKeyboardMarkup, AttachmentResult, ImageAnalysis, Outcome of a deterministic daily workout write., Domain routing and structured extraction result for one image., WorkoutUpsertResult, int (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (6): Tests for media validation, upload limits, magic-byte checks, and path traversal, Attempting path traversal in filename is sanitized to safe basename., User B cannot download User A's attachment., Magic bytes check accepts real JPEG/PNG signatures and rejects forged headers., Files exceeding 15MB are rejected with 413., ServerMediaTests

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (5): Health endpoint returns system status and configuration., telegram_bot.main() exits cleanly without TELEGRAM_BOT_TOKEN when ENABLE_TELEGRA, User can subscribe and unsubscribe Web Push subscriptions., Briefing delivery records prevent sending multiple briefings on the same date., ServerNotificationsAndBriefingsTests

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (11): code:bash (python scripts/export_env_for_cloud.py), code:cmd (run_prod.bat), code:cmd (cloudflared tunnel --url http://127.0.0.1:8000), Hosting Andrei's Life Hub Assistant, Option 1: Render (Recommended — 100% Free 24/7 Cloud), Option 2: Railway (Best Performance & Persistent Volume), Option 3: Cloudflare Quick Tunnel (Host from your PC, Zero Cloud Signup), Step 1: Create a Web Service on Render (+3 more)

### Community 54 - "Community 54"
Cohesion: 0.50
Nodes (3): BaseHTTPMiddleware, Request, SecurityHeadersMiddleware

### Community 55 - "Community 55"
Cohesion: 0.20
Nodes (7): bytes, Execute a prompt turn across tiered models with unified rolling conversation his, Execute a prompt turn across tiered models with unified rolling conversation his, Process a text message from Telegram with live date context and tiered model fal, Process a voice note audio from Telegram with live date context and tiered model, Process a text message from Telegram with live date context and tiered model fal, Process a voice note audio from Telegram with live date context and tiered model

### Community 56 - "Community 56"
Cohesion: 0.27
Nodes (8): health_check(), Health check API routes., Health check endpoint verifying database connectivity and provider configuration, get_db_path(), get_upload_dir(), str, SQLite persistence layer for Andrei's Life Hub Assistant., HealthResponse

### Community 57 - "Community 57"
Cohesion: 0.20
Nodes (3): AssistantServiceTests, Tests for shared assistant service, context rehydration, and error sanitization., Recent messages in SQLite are rehydrated into Gemini history for coherence.

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (4): User B cannot access or delete User A's conversation., Conversations and messages persist in SQLite and are reloaded cleanly., Create multiple conversations and verify order and message counts., ServerConversationsTests

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (8): 9. Tailscale Serve HTTPS & iPhone PWA Setup, code:powershell (tailscale serve --bg 8000), code:block11 (https://andrei-pc.tailscale.net), code:env (WEB_ALLOWED_ORIGINS="http://localhost:8000,https://andrei-pc), Step 1: Install Tailscale on Windows & iPhone, Step 2: Enable Tailscale Serve on Windows, Step 3: Configure Allowed Origins, Step 4: Install on iPhone

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (7): 10. Developer Extension Guide (How to Add Features), A. Adding a New Agent to the Registry, B. Adding a New Tool to the Notion Assistant, C. Adding a New Database to the Workspace, code:python (class MySpecializedAgent:), code:python (registry.register(MySpecializedAgent())), 💡 Quick Tips for Future AI Agents

### Community 63 - "Community 63"
Cohesion: 0.29
Nodes (7): 5. Web PWA & Shared Backend Architecture, Agent Registry & Transport-Neutral Assistant, FastAPI & Security Layer, SQLite Persistence & Idempotency, Telegram Bot (Decoupled Secondary Fallback), Web Push & Briefing Scheduler, Workout Confirmation Pipeline

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (6): Attachment, Conversation, PendingScanRecord, PushSubscriptionRecord, Typed models for server data structures., Session

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (5): get_calendar_schedule(), Generate a structured, motivating morning briefing based on today's Notion sched, Generate a structured, motivating morning briefing based on today's Notion sched, Retrieve scheduled tasks, events, and deadlines for a specific date (YYYY-MM-DD, Retrieve scheduled tasks, events, and deadlines for a specific date (YYYY-MM-DD

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (5): networked, options, payload, STATIC_ASSETS, url

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (4): int, str, backup(), Crash-safe online SQLite backup script for Andrei's Life Hub Assistant.

### Community 68 - "Community 68"
Cohesion: 0.50
Nodes (3): bool, GenerateContentConfig, _image_analysis_config()

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (4): int, query_database(), Query items from a Notion database given its database ID., Query items from a Notion database given its database ID.

### Community 70 - "Community 70"
Cohesion: 0.67
Nodes (3): generate_keys(), main(), Generate VAPID keys for Andrei's Life Hub Assistant Web Push notifications.

### Community 71 - "Community 71"
Cohesion: 0.50
Nodes (4): 4. Notion Workspace & Database Schemas, Dynamic Property Normalization, Known Data Sources & IDs, Tasks Database Schema & Property Types

### Community 72 - "Community 72"
Cohesion: 0.50
Nodes (3): Restore SQLite database from backup for Andrei's Life Hub Assistant., restore(), str

### Community 85 - "Community 85"
Cohesion: 0.20
Nodes (3): PendingImageScan, Short-lived image state used by Telegram confirmation callbacks., TreadmillScanTests

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (4): BaseHTTPRequestHandler, HealthCheckHandler, Minimal HTTP server responding to cloud health checks (Render, Koyeb, Railway)., Minimal HTTP server responding to cloud health checks (Render, Koyeb, Railway).

## Knowledge Gaps
- **237 isolated node(s):** `str`, `int`, `str`, `str`, `str` (+232 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `Community 30` to `Community 32`, `Community 33`, `Community 35`, `Community 37`, `Community 39`, `Community 40`, `Community 42`, `Community 43`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 56`, `Community 57`, `Community 58`, `Community 28`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `ImageAnalysis` connect `Community 50` to `Community 1`, `Community 2`, `Community 36`, `Community 69`, `Community 68`, `Community 42`, `Community 44`, `Community 48`, `Community 49`, `Community 51`, `Community 85`, `Community 86`, `Community 60`, `Community 30`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `TreadmillScan` connect `Community 42` to `Community 36`, `Community 5`, `Community 44`, `Community 48`, `Community 50`, `Community 51`, `Community 85`, `Community 30`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `ImageAnalysis` (e.g. with `str` and `int`) actually correct?**
  _`ImageAnalysis` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `WorkoutUpsertResult` (e.g. with `NotionService` and `str`) actually correct?**
  _`WorkoutUpsertResult` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `NotionDesktopWidget` (e.g. with `TestWidgetManager` and `TestNotionTasksSync`) actually correct?**
  _`NotionDesktopWidget` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `AttachmentResult` (e.g. with `NotionService` and `str`) actually correct?**
  _`AttachmentResult` has 31 INFERRED edges - model-reasoned connections that need verification._