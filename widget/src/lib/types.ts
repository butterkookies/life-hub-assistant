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

export interface IElectronAPI {
  getConfig: () => Promise<WidgetConfig>;
  saveConfig: (updates: Partial<WidgetConfig>) => Promise<WidgetConfig>;
  minimize: () => void;
  close: () => void;
  setAlwaysOnTop: (isTop: boolean) => void;
  getProjects: () => Promise<NotionProject[]>;
  getTasks: (targetDate?: string) => Promise<NotionTask[]>;
  updateTaskStatus: (taskId: string, newStatus: string) => Promise<boolean>;
  createTask: (
    title: string,
    projectId?: string,
    priority?: string,
    doDate?: string
  ) => Promise<NotionTask>;
  getPagePreview: (pageId: string) => Promise<PagePreviewData>;
  openExternalUrl: (url: string) => void;
  onTriggerRefresh: (callback: () => void) => () => void;
  onTriggerQuickAdd: (callback: () => void) => () => void;
  onConfigUpdated: (callback: (cfg: Partial<WidgetConfig>) => void) => () => void;
}

declare global {
  interface Window {
    electronAPI?: IElectronAPI;
  }
}
