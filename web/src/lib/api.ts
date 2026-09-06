import {
  Agent,
  ConversationSummary,
  Message,
  PendingScan,
  SessionState,
} from '../types';

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string = 'API_ERROR', status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

export type ServerStatus = 'checking' | 'waking' | 'ready' | 'offline' | 'unavailable';

let serverStatus: ServerStatus = 'checking';
let wakePromise: Promise<void> | null = null;
const statusListeners = new Set<(status: ServerStatus) => void>();

function setServerStatus(next: ServerStatus) {
  if (serverStatus === next) return;
  serverStatus = next;
  statusListeners.forEach((listener) => listener(next));
}

export function getServerStatus(): ServerStatus {
  return serverStatus;
}

export function subscribeServerStatus(listener: (status: ServerStatus) => void): () => void {
  statusListeners.add(listener);
  listener(serverStatus);
  return () => {
    statusListeners.delete(listener);
  };
}

const delay = (milliseconds: number) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function probeHealth(): Promise<boolean> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch('/api/health', {
      cache: 'no-store',
      credentials: 'include',
      signal: controller.signal,
    });
    if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) {
      return false;
    }
    const data = await response.json();
    return data.status === 'healthy' && data.database_ok === true;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function ensureServerReady(forceProbe = false): Promise<void> {
  if (!navigator.onLine) {
    setServerStatus('offline');
    throw new ApiError('You are offline. Reconnect to continue.', 'OFFLINE', 0);
  }
  if (!forceProbe && serverStatus === 'ready') return;
  if (wakePromise) return wakePromise;

  wakePromise = (async () => {
    setServerStatus('waking');
    const deadline = Date.now() + 90000;
    while (Date.now() < deadline) {
      if (!navigator.onLine) {
        setServerStatus('offline');
        throw new ApiError('You are offline. Reconnect to continue.', 'OFFLINE', 0);
      }
      if (await probeHealth()) {
        setServerStatus('ready');
        return;
      }
      await delay(3000);
    }
    setServerStatus('unavailable');
    throw new ApiError('Life Hub is taking longer than expected to wake. Tap Retry.', 'SERVER_UNAVAILABLE', 503);
  })().finally(() => {
    wakePromise = null;
  });

  return wakePromise;
}

interface RequestPolicy {
  retryMutation?: boolean;
}

async function request<T>(endpoint: string, options: RequestInit = {}, policy: RequestPolicy = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const headers = new Headers(options.headers || {});
  const method = (options.method || 'GET').toUpperCase();

  if (!isFormData && !headers.has('Content-Type') && options.method && options.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }

  // Ensure origin is included for CSRF validation
  const origin = window.location.origin;
  if (!headers.has('Origin')) {
    headers.set('Origin', origin);
  }

  await ensureServerReady(method !== 'GET');

  const attempts = method === 'GET' || policy.retryMutation ? 2 : 1;
  let res: Response | null = null;
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      res = await fetch(endpoint, {
        ...options,
        headers,
        credentials: 'include',
      });
      const transient = [502, 503, 504].includes(res.status);
      const isJson = res.headers.get('content-type')?.includes('application/json');
      if ((!isJson || transient) && attempt + 1 < attempts) {
        setServerStatus('waking');
        await delay(1500 * (attempt + 1));
        await ensureServerReady(true);
        continue;
      }
      break;
    } catch (error) {
      lastError = error;
      if (attempt + 1 >= attempts) break;
      setServerStatus(navigator.onLine ? 'waking' : 'offline');
      await delay(1500 * (attempt + 1));
      await ensureServerReady(true);
    }
  }

  if (!res) {
    setServerStatus(navigator.onLine ? 'unavailable' : 'offline');
    throw lastError instanceof ApiError
      ? lastError
      : new ApiError('Could not reach Life Hub. Please retry.', navigator.onLine ? 'SERVER_UNAVAILABLE' : 'OFFLINE', 0);
  }

  if (!res.ok) {
    let errCode = 'HTTP_ERROR';
    let errMsg = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      const detail = data.error || data.detail;
      if (detail) {
        errCode = detail.code || errCode;
        errMsg = detail.message || errMsg;
      }
    } catch {
      // Body not JSON
    }
    throw new ApiError(errMsg, errCode, res.status);
  }

  if (!res.headers.get('content-type')?.includes('application/json')) {
    setServerStatus('waking');
    throw new ApiError('Life Hub is still waking. Please retry.', 'SERVER_WAKING', 503);
  }

  setServerStatus('ready');
  return (await res.json()) as T;
}

export const api = {
  auth: {
    login: (password: string) =>
      request<{ success: boolean; user: { id: string; username: string } }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password }),
      }),
    logout: () =>
      request<{ success: boolean }>('/api/auth/logout', {
        method: 'POST',
      }),
    getSession: () => request<SessionState>('/api/auth/session'),
  },

  agents: {
    list: () => request<Agent[]>('/api/agents'),
  },

  conversations: {
    list: () => request<ConversationSummary[]>('/api/conversations'),
    create: (agentId: string = 'notion', title?: string) =>
      request<ConversationSummary>('/api/conversations', {
        method: 'POST',
        body: JSON.stringify({ agent_id: agentId, title }),
      }),
    get: (id: string) =>
      request<{ conversation: ConversationSummary; messages: Message[] }>(`/api/conversations/${id}`),
    delete: (id: string) =>
      request<{ success: boolean }>(`/api/conversations/${id}`, {
        method: 'DELETE',
      }),
  },

  messages: {
    send: (conversationId: string, content: string, clientMessageId?: string, attachmentIds?: string[]) =>
      request<Message>(`/api/conversations/${conversationId}/messages`, {
        method: 'POST',
        body: JSON.stringify({
          content,
          client_message_id: clientMessageId,
          attachment_ids: attachmentIds,
        }),
      }, { retryMutation: Boolean(clientMessageId) }),
  },

  media: {
    upload: (conversationId: string, file: File, clientMessageId?: string, caption?: string) => {
      const formData = new FormData();
      formData.append('file', file);
      if (clientMessageId) formData.append('client_message_id', clientMessageId);
      if (caption) formData.append('caption', caption);

      return request<{
        type: 'voice' | 'image';
        action?: string;
        message?: Message;
        token?: string;
        scan?: PendingScan;
      }>(`/api/conversations/${conversationId}/attachments`, {
        method: 'POST',
        body: formData,
      });
    },
  },

  imageScans: {
    confirm: (token: string) =>
      request<any>(`/api/image-scans/${token}/confirm`, {
        method: 'POST',
      }),
    correct: (token: string, correctionText: string) =>
      request<PendingScan>(`/api/image-scans/${token}/correct`, {
        method: 'POST',
        body: JSON.stringify({ correction_text: correctionText }),
      }),
    cancel: (token: string) =>
      request<{ success: boolean }>(`/api/image-scans/${token}/cancel`, {
        method: 'POST',
      }),
  },

  notifications: {
    getStatus: () =>
      request<{ configured: boolean; subscribed: boolean; vapid_public_key?: string }>('/api/notifications/status'),
    getDeviceStatus: (endpoint: string) =>
      request<{ configured: boolean; subscribed: boolean; vapid_public_key?: string }>('/api/notifications/device-status', {
        method: 'POST',
        body: JSON.stringify({ endpoint }),
      }),
    subscribe: (subscription: PushSubscription) => {
      const p256dhKey = subscription.getKey('p256dh');
      const authKey = subscription.getKey('auth');
      const p256dh = p256dhKey ? btoa(String.fromCharCode(...new Uint8Array(p256dhKey))) : '';
      const auth = authKey ? btoa(String.fromCharCode(...new Uint8Array(authKey))) : '';

      return request<{ success: boolean }>('/api/notifications/subscribe', {
        method: 'POST',
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: { p256dh, auth },
          user_agent: navigator.userAgent,
        }),
      });
    },
    unsubscribe: (subscription: PushSubscription) =>
      request<{ success: boolean }>('/api/notifications/subscribe', {
        method: 'DELETE',
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: { p256dh: '', auth: '' },
        }),
      }),
    test: () =>
      request<{ success: boolean; delivered_devices: number }>('/api/notifications/test', {
        method: 'POST',
      }),
  },
};
