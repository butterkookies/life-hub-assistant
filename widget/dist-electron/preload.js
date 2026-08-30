import { contextBridge as i, ipcRenderer as n } from "electron";
const s = {
  // Config
  getConfig: () => n.invoke("get-config"),
  saveConfig: (e) => n.invoke("save-config", e),
  // Window Controls
  minimize: () => n.send("window-minimize"),
  close: () => n.send("window-close"),
  setAlwaysOnTop: (e) => n.send("window-set-topmost", e),
  // Notion API
  getProjects: () => n.invoke("get-projects"),
  getTasks: (e) => n.invoke("get-tasks", e),
  updateTaskStatus: (e, t) => n.invoke("update-task-status", e, t),
  createTask: (e, t, o, r) => n.invoke("create-task", e, t, o, r),
  getPagePreview: (e) => n.invoke("get-page-preview", e),
  openExternalUrl: (e) => n.send("open-external-url", e),
  // Listeners from Main / Tray
  onTriggerRefresh: (e) => {
    const t = () => e();
    return n.on("trigger-refresh", t), () => n.removeListener("trigger-refresh", t);
  },
  onTriggerQuickAdd: (e) => {
    const t = () => e();
    return n.on("trigger-quick-add", t), () => n.removeListener("trigger-quick-add", t);
  },
  onConfigUpdated: (e) => {
    const t = (o, r) => e(r);
    return n.on("config-updated", t), () => n.removeListener("config-updated", t);
  }
};
i.exposeInMainWorld("electronAPI", s);
export {
  s as electronAPI
};
