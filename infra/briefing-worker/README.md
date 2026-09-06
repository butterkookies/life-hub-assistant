# Life Hub briefing trigger

This Cloudflare Worker wakes the free Render service at 05:58 Asia/Manila and calls the protected daily briefing endpoint at 06:00.

Deploy after creating the Render `BRIEFING_TRIGGER_TOKEN` secret:

```powershell
cd infra/briefing-worker
npx wrangler secret put BRIEFING_TRIGGER_TOKEN
npx wrangler deploy
```

Cron expressions use UTC. The configured `58 21 * * *` schedule corresponds to 05:58 the following day in Asia/Manila.
