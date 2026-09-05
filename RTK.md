# RTK and workspace conventions

This file supplies the local instructions referenced by `@RTK.md` for Life Hub Assistant.

## Compact command output

RTK is a CLI proxy that reduces command output. Prefer it for supported commands when the summary retains the evidence needed for the task:

- `rtk git status` for repository status.
- `rtk git diff` for a compact change review.
- `rtk npm run build` from `web/` for the frontend build.
- `rtk gain` to inspect recorded output savings when requested.

Use `rtk --help` or subcommand help to check supported syntax. Use native commands when RTK is unavailable, changes command behavior, or hides necessary diagnostics. Read full source and diffs when correctness depends on details. Do not install tools or change global hooks merely to enable RTK.

Use `rg` and `rg --files` for focused searches. On Windows, use PowerShell and literal paths for filesystem operations.

## Project context

- Read `ONBOARDING.md` for architecture, `DESIGN_SYSTEM.md` for UI conventions, and `README.md` for setup. Resolve stale documentation against the actual code and configuration.
- The primary app is a mobile-first React/TypeScript PWA in `web/`, backed by Python/FastAPI in `server/` and integrations with Gemini and Notion.
- Preserve the Apple/iOS design direction, light and dark theme readability, safe areas, and PWA behavior. Check whether component changes also affect the Design Kit preview.
- Keep edits scoped to the requested work and preserve existing user changes.
- Do not expose `.env` contents, credentials, private conversation data, or uploads in command output or commits.

## Validation

- Frontend build: run `npm run build` from `web/` (or the RTK equivalent above).
- Backend tests: run `python -m pytest tests -v` from the project root for backend changes, using the project's configured Python environment.
- Run checks appropriate to the change. Documentation-only edits do not require an application build or test run.
- Report what was actually verified. Treat historical test counts and deployment claims as context until checked.
