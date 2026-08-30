# Graph Report - .  (2026-08-28)

## Corpus Check
- Corpus is ~21,764 words - fits in a single context window. You may not need a graph.

## Summary
- 445 nodes · 699 edges · 25 communities (19 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

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
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]

## God Nodes (most connected - your core abstractions)
1. `NotionDesktopWidget` - 37 edges
2. `projects` - 23 edges
3. `compilerOptions` - 16 edges
4. `NotionService` - 15 edges
5. `str` - 14 edges
6. `str` - 13 edges
7. `str` - 12 edges
8. `EmailService` - 12 edges
9. `str` - 12 edges
10. `send_clean_reply()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `TestWidgetManager` --uses--> `NotionDesktopWidget`  [INFERRED]
  widget/legacy_python_widget/test_widget.py → widget/legacy_python_widget/desktop_widget.py
- `TestNotionTasksSync` --uses--> `NotionDesktopWidget`  [INFERRED]
  widget/legacy_python_widget/test_widget.py → widget/legacy_python_widget/desktop_widget.py
- `TestWidgetUIInitialization` --uses--> `NotionDesktopWidget`  [INFERRED]
  widget/legacy_python_widget/test_widget.py → widget/legacy_python_widget/desktop_widget.py
- `TestWidgetManager` --uses--> `TaskCard`  [INFERRED]
  widget/legacy_python_widget/test_widget.py → widget/legacy_python_widget/desktop_widget.py
- `TestNotionTasksSync` --uses--> `TaskCard`  [INFERRED]
  widget/legacy_python_widget/test_widget.py → widget/legacy_python_widget/desktop_widget.py

## Communities (25 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (28): DailyProgress(), DailyProgressProps, FilterBar(), FilterBarProps, Header(), HeaderProps, InlineTaskAdd(), InlineTaskAddProps (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (34): Application, BaseHTTPRequestHandler, DEFAULT_TYPE, briefing_command(), check_auth(), daily_briefing_scheduler(), email_command(), format_for_telegram() (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (27): bytes, Any, bool, int, str, GenerateContentConfig, append_to_page(), create_database_item() (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (32): dependencies, clsx, dotenv, lucide-react, @notionhq/client, react, react-dom, tailwind-merge (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (18): CONFIG_PATH, createTrayIcon(), createWindow(), DEFAULT_CONFIG, _dirname, loadConfig(), saveConfig(), setupTray() (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.16
Nodes (15): NotionService, Query items in a Notion database or data source., Retrieve scheduled tasks and calendar events for a specific date (YYYY-MM-DD) or, Search pages and databases across the workspace., Fetch all projects and map their IDs (both hyphenated and clean) to project name, Retrieve rich tasks for a specific date (YYYY-MM-DD), with mapped project names, Format arbitrary Python types into Notion property structures., Create a new page/entry in a Notion database. (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (25): last_synced, projects, 3be271025287811dab16ed7bb7156ce1, 3be271025287812cb2f9fd5c3690f556, 3be271025287813aa28cf73397265eab, 3be2710252878146bb43d2622fd62e0f, 3be27102528781508acff8d2b9c52119, 3be2710252878167957cf6825d481689 (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (23): bool, int, str, float, ALLOWED_TELEGRAM_USER_IDS(), DAILY_BRIEFING_ENABLED(), DAILY_BRIEFING_TIME(), EMAIL_FROM_ADDRESS() (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (13): bool, str, EmailService, Wrap the briefing content into a modern, responsive newsletter-style email conta, Service to handle formatting and delivering rich HTML email notifications and da, Send email via SMTP (Gmail, SendGrid, Brevo, Outlook, etc.)., Check if minimum required email credentials are configured., Send email via Resend REST API. (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (12): _, A(), B, C, D, ie, j(), le() (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (14): Image, generate_icon_image(), get_startup_shortcut_path(), Load configuration from disk with fallback to defaults., Save current or updated configuration to disk., Load cached tasks and project map for instant rendering., Save tasks and projects map to disk., Create or remove Windows startup shortcut. (+6 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (8): get_project_color(), Deterministically assign a color pair to a project name., Interactive card representing a single task., TaskCard, Test Suite for Notion Tasks Desktop Widget Verifies config persistence, cache ma, TestNotionTasksSync, TestWidgetManager, TestWidgetUIInitialization

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (5): Create task in Notion and update UI., Render task cards into the scrollable list., Optimistically update UI and sync new status to Notion., Any, str

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (4): NotionDesktopWidget, Hide main window and notify user in system tray., Save settings and cleanly exit., Main Windows Home Screen Widget Application.

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (13): always_on_top, auto_refresh_minutes, filter_mode, height, opacity, pinned_to_desktop, show_completed, start_with_windows (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.18
Nodes (6): main(), QuickAddTaskDialog, Notion Tasks - Modern Windows Desktop Widget A sleek, customizable desktop widge, Modal dialog for quickly adding a new task to Notion for today., Settings dialog for customizing widget behavior and appearance., SettingsDialog

## Knowledge Gaps
- **115 isolated node(s):** `float`, `int`, `bool`, `GenerateContentConfig`, `Any` (+110 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Path` connect `Community 10` to `Community 9`, `Community 4`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `NotionDesktopWidget` connect `Community 14` to `Community 16`, `Community 17`, `Community 11`, `Community 13`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `NotionDesktopWidget` (e.g. with `TestWidgetManager` and `TestNotionTasksSync`) actually correct?**
  _`NotionDesktopWidget` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `float`, `Service to handle formatting and delivering rich HTML email notifications and da`, `Check if minimum required email credentials are configured.` to the rest of the system?**
  _181 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09615384615384616 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11861861861861862 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._