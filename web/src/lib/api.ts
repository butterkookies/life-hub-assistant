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

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const headers = new Headers(options.headers || {});

  if (!isFormData && !headers.has('Content-Type') && options.method && options.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }

  // Ensure origin is included for CSRF validation
  const origin = window.location.origin;
  if (!headers.has('Origin')) {
    headers.set('Origin', origin);
  }

  const res = await fetch(endpoint, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!res.ok) {
    let errCode = 'HTTP_ERROR';
    let errMsg = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data.error) {
        errCode = data.error.code || errCode;
        errMsg = data.error.message || errMsg;
      }
    } catch {
      // Body not JSON
    }
    throw new ApiError(errMsg, errCode, res.status);
  }

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
      }),
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
