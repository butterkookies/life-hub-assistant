export interface User {
  id: string;
  username: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'available' | 'busy' | 'offline';
}

export interface ConversationSummary {
  id: string;
  agent_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Attachment {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  url?: string;
}

export interface PendingScan {
  token: string;
  filename: string;
  date: string;
  metrics: {
    duration_minutes?: number;
    distance_km?: number;
    steps?: number;
    calories_kcal?: number;
    speed_kmh?: number;
    heart_rate_bpm?: number;
    trax_program?: string;
    workout_type?: string;
  };
  confidence: number;
  uncertain_fields: string[];
  conflicts?: Record<string, [any, any]>;
  validation_errors: string[];
  can_save: boolean;
  awaiting_correction: boolean;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  status: 'pending' | 'completed' | 'failed';
  client_message_id?: string;
  tool_activity?: Array<Record<string, any>>;
  attachments: Attachment[];
  created_at: string;
  error_message?: string;
  pending_scan?: PendingScan;
}

export interface SessionState {
  authenticated: boolean;
  user: User | null;
  push_configured: boolean;
  vapid_public_key?: string;
}
