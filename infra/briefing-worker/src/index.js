const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function fetchWithTimeout(url, options = {}, timeoutMs = 70000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function wakeServer(appUrl) {
  const deadline = Date.now() + 4 * 60 * 1000;
  while (Date.now() < deadline) {
    try {
      const response = await fetchWithTimeout(`${appUrl}/api/health`, {
        headers: { Accept: 'application/json' },
      });
      if (response.ok && response.headers.get('content-type')?.includes('application/json')) {
        const health = await response.json();
        if (health.status === 'healthy' && health.database_ok === true) return;
      }
    } catch {
      // Render can reset the first connection while the free instance boots.
    }
    await sleep(10000);
  }
  throw new Error('Life Hub did not become healthy within four minutes');
}

async function triggerBriefing(appUrl, token) {
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetchWithTimeout(`${appUrl}/api/internal/briefings/daily`, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`,
        },
      }, 5 * 60 * 1000);
      if (response.ok && response.headers.get('content-type')?.includes('application/json')) {
        const result = await response.json();
        if (['completed', 'already_completed', 'in_progress'].includes(result.status)) return result;
      }
      lastError = new Error(`Briefing endpoint returned HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(attempt * 10000);
  }
  throw lastError || new Error('Briefing trigger failed');
}

export default {
  async scheduled(controller, env) {
    if (!env.APP_URL || !env.BRIEFING_TRIGGER_TOKEN) {
      throw new Error('APP_URL and BRIEFING_TRIGGER_TOKEN are required');
    }

    const appUrl = env.APP_URL.replace(/\/$/, '');
    await wakeServer(appUrl);

    // The cron starts at 05:58 Asia/Manila. Wait until 06:00 before dispatching.
    const targetTime = controller.scheduledTime + 2 * 60 * 1000;
    if (Date.now() < targetTime) await sleep(targetTime - Date.now());

    await triggerBriefing(appUrl, env.BRIEFING_TRIGGER_TOKEN);
  },
};
