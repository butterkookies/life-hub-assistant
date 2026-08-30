const { contextBridge, ipcRenderer } = require('electron');

const electronAPI = {
  // Config
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (updates) => ipcRenderer.invoke('save-config', updates),

  // Window Controls
  minimize: () => ipcRenderer.send('window-minimize'),
  close: () => ipcRenderer.send('window-close'),
  setAlwaysOnTop: (isTop) => ipcRenderer.send('window-set-topmost', isTop),

  // Notion API
  getProjects: () => ipcRenderer.invoke('get-projects'),
  getTasks: (targetDate) => ipcRenderer.invoke('get-tasks', targetDate),
  updateTaskStatus: (taskId, newStatus) =>
    ipcRenderer.invoke('update-task-status', taskId, newStatus),
  createTask: (title, projectId, priority, doDate) =>
    ipcRenderer.invoke('create-task', title, projectId, priority, doDate),
  getPagePreview: (pageId) => ipcRenderer.invoke('get-page-preview', pageId),
  openExternalUrl: (url) => ipcRenderer.send('open-external-url', url),

  // Listeners from Main / Tray
  onTriggerRefresh: (callback) => {
    const sub = () => callback();
    ipcRenderer.on('trigger-refresh', sub);
    return () => ipcRenderer.removeListener('trigger-refresh', sub);
  },
  onTriggerQuickAdd: (callback) => {
    const sub = () => callback();
    ipcRenderer.on('trigger-quick-add', sub);
    return () => ipcRenderer.removeListener('trigger-quick-add', sub);
  },
  onConfigUpdated: (callback) => {
    const sub = (_, data) => callback(data);
    ipcRenderer.on('config-updated', sub);
    return () => ipcRenderer.removeListener('config-updated', sub);
  },
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
