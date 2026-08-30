import { contextBridge, ipcRenderer } from 'electron';
import { NotionTask, NotionProject, WidgetConfig, PagePreviewData } from './types';

export const electronAPI = {
  // Config
  getConfig: (): Promise<WidgetConfig> => ipcRenderer.invoke('get-config'),
  saveConfig: (updates: Partial<WidgetConfig>): Promise<WidgetConfig> =>
    ipcRenderer.invoke('save-config', updates),

  // Window Controls
  minimize: () => ipcRenderer.send('window-minimize'),
  close: () => ipcRenderer.send('window-close'),
  setAlwaysOnTop: (isTop: boolean) => ipcRenderer.send('window-set-topmost', isTop),

  // Notion API
  getProjects: (): Promise<NotionProject[]> => ipcRenderer.invoke('get-projects'),
  getTasks: (targetDate?: string): Promise<NotionTask[]> =>
    ipcRenderer.invoke('get-tasks', targetDate),
  updateTaskStatus: (taskId: string, newStatus: string): Promise<boolean> =>
    ipcRenderer.invoke('update-task-status', taskId, newStatus),
  createTask: (
    title: string,
    projectId?: string,
    priority?: string,
    doDate?: string
  ): Promise<NotionTask> =>
    ipcRenderer.invoke('create-task', title, projectId, priority, doDate),
  getPagePreview: (pageId: string): Promise<PagePreviewData> =>
    ipcRenderer.invoke('get-page-preview', pageId),
  openExternalUrl: (url: string) => ipcRenderer.send('open-external-url', url),

  // Listeners from Main / Tray
  onTriggerRefresh: (callback: () => void) => {
    const sub = () => callback();
    ipcRenderer.on('trigger-refresh', sub);
    return () => ipcRenderer.removeListener('trigger-refresh', sub);
  },
  onTriggerQuickAdd: (callback: () => void) => {
    const sub = () => callback();
    ipcRenderer.on('trigger-quick-add', sub);
    return () => ipcRenderer.removeListener('trigger-quick-add', sub);
  },
  onConfigUpdated: (callback: (cfg: Partial<WidgetConfig>) => void) => {
    const sub = (_: any, data: Partial<WidgetConfig>) => callback(data);
    ipcRenderer.on('config-updated', sub);
    return () => ipcRenderer.removeListener('config-updated', sub);
  },
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
