export interface NotionTask {
  id: string;
  name: string;
  status: string; // 'Not started' | 'In progress' | 'Done'
  date?: string | null;
  priority?: string | null; // 'High' | 'Normal' | 'Low'
  projectId?: string | null;
  projectName?: string;
  url?: string | null;
  properties?: Record<string, any>;
}

export interface NotionProject {
  id: string;
  name: string;
}

export interface WidgetConfig {
  x: number;
  y: number;
  width: number;
  height: number;
  alwaysOnTop: boolean;
  theme: 'light' | 'dark' | 'system';
  opacity: number;
  autoRefreshMinutes: number;
  showCompleted: boolean;
  startWithWindows: boolean;
  filterMode: 'today' | 'active' | 'all';
}

export interface PageBlock {
  id: string;
  type: string;
  text: string;
  checked?: boolean;
}

export interface PagePreviewData {
  id: string;
  title: string;
  url?: string;
  blocks: PageBlock[];
}
