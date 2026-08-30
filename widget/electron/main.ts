import { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, shell, globalShortcut, screen } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import { notionService } from './notion-client';
import { WidgetConfig } from './types';

import { fileURLToPath } from 'url';

const getDirname = () => {
  try {
    return path.dirname(fileURLToPath(import.meta.url));
  } catch {
    return process.cwd();
  }
};

const _dirname = getDirname();

// The built directory structure
process.env.DIST = path.join(_dirname, '../dist');
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public');

let win: BrowserWindow | null = null;
let tray: Tray | null = null;
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL'];

const CONFIG_PATH = path.join(app.getPath('userData'), 'widget_config.json');

const DEFAULT_CONFIG: WidgetConfig = {
  x: 100,
  y: 100,
  width: 420,
  height: 640,
  alwaysOnTop: false,
  theme: 'light',
  opacity: 0.98,
  autoRefreshMinutes: 5,
  showCompleted: true,
  startWithWindows: false,
  filterMode: 'today',
};

function loadConfig(): WidgetConfig {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const data = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      return { ...DEFAULT_CONFIG, ...data };
    }
  } catch (err) {
    console.error('Error loading config:', err);
  }
  return DEFAULT_CONFIG;
}

function saveConfig(cfg: Partial<WidgetConfig>) {
  try {
    const current = loadConfig();
    const updated = { ...current, ...cfg };
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(updated, null, 2), 'utf-8');
  } catch (err) {
    console.error('Error saving config:', err);
  }
}

function createTrayIcon(): Electron.NativeImage {
  const iconPaths = [
    path.join(_dirname, '../icon.png'),
    path.join(_dirname, '../../icon.png'),
    path.join(process.cwd(), 'icon.png'),
  ];
  for (const p of iconPaths) {
    if (fs.existsSync(p)) {
      const img = nativeImage.createFromPath(p);
      if (!img.isEmpty()) return img;
    }
  }
  return nativeImage.createEmpty();
}

function createWindow() {
  const config = loadConfig();

  // Validate screen coordinates to avoid opening off-screen
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenW, height: screenH } = primaryDisplay.workAreaSize;
  const width = Math.min(Math.max(config.width || 420, 360), 600);
  const height = Math.min(Math.max(config.height || 640, 480), 900);

  // Default to comfortable top-right on user screen
  let posX = config.x;
  let posY = config.y;
  if (!posX || posX <= 0 || posX > screenW - 100) posX = screenW - width - 60;
  if (!posY || posY <= 0 || posY > screenH - 100) posY = 60;

  const isFirstLaunch = !config.x || config.x <= 0;
  const trayIcon = createTrayIcon();

  win = new BrowserWindow({
    width: 430,
    height: 670,
    center: isFirstLaunch,
    x: isFirstLaunch ? undefined : config.x,
    y: isFirstLaunch ? undefined : config.y,
    minWidth: 360,
    minHeight: 480,
    maxWidth: 700,
    maxHeight: 1000,
    frame: false,
    transparent: true,
    hasShadow: true,
    alwaysOnTop: config.alwaysOnTop ?? true,
    resizable: true,
    skipTaskbar: false,
    show: true,
    icon: trayIcon,
    title: 'Notion Tasks Widget',
    webPreferences: {
      preload: path.join(_dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });


  win.show();
  win.restore();
  win.focus();
  win.moveTop();



  // Save window bounds on move / resize
  const saveBounds = () => {
    if (win && !win.isDestroyed()) {
      const bounds = win.getBounds();
      saveConfig({
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
      });
    }
  };

  win.on('moved', saveBounds);
  win.on('resized', saveBounds);

  const htmlPath = path.join(process.env.DIST as string, 'index.html');
  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(htmlPath);
  }

  win.webContents.on('did-finish-load', () => {
    console.log('Widget UI loaded successfully');
    win?.show();
    win?.focus();
  });

  win.webContents.on('did-fail-load', (_, errorCode, errorDescription) => {
    console.error('Failed to load widget UI:', errorCode, errorDescription);
  });
}

function setupTray() {
  const icon = createTrayIcon();
  tray = new Tray(icon);
  tray.setToolTip('Notion Tasks Desktop Widget (Click to Open)');

  const showAndFocus = () => {
    if (!win || win.isDestroyed()) {
      createWindow();
    } else {
      if (win.isMinimized()) win.restore();
      win.show();
      win.focus();
      win.moveTop();
      win.setAlwaysOnTop(true);
      setTimeout(() => {
        const cfg = loadConfig();
        if (win && !win.isDestroyed()) {
          win.setAlwaysOnTop(cfg.alwaysOnTop);
        }
      }, 500);
    }
  };

  const updateMenu = () => {
    const config = loadConfig();
    const contextMenu = Menu.buildFromTemplate([
      {
        label: '📋 Show Tasks Widget',
        click: showAndFocus,
      },
      {
        label: '🔄 Refresh Tasks Now',
        click: () => {
          showAndFocus();
          win?.webContents.send('trigger-refresh');
        },
      },
      {
        label: '➕ Add Task for Today...',
        click: () => {
          showAndFocus();
          win?.webContents.send('trigger-quick-add');
        },
      },
      { type: 'separator' },
      {
        label: '📌 Always on Top',
        type: 'checkbox',
        checked: config.alwaysOnTop,
        click: (item) => {
          const isTop = item.checked;
          win?.setAlwaysOnTop(isTop);
          saveConfig({ alwaysOnTop: isTop });
          win?.webContents.send('config-updated', { alwaysOnTop: isTop });
        },
      },
      {
        label: '🚀 Launch on Windows Startup',
        type: 'checkbox',
        checked: app.getLoginItemSettings().openAtLogin,
        click: (item) => {
          app.setLoginItemSettings({
            openAtLogin: item.checked,
            path: process.execPath,
          });
          saveConfig({ startWithWindows: item.checked });
        },
      },
      { type: 'separator' },
      {
        label: '❌ Exit Widget',
        click: () => {
          app.quit();
        },
      },
    ]);
    tray?.setContextMenu(contextMenu);
  };

  tray.on('click', showAndFocus);
  tray.on('double-click', showAndFocus);

  updateMenu();
}


function registerShortcuts() {
  const showOrToggle = () => {
    if (!win || win.isDestroyed()) {
      createWindow();
    } else {
      if (!win.isVisible() || win.isMinimized()) {
        win.restore();
        win.show();
        win.focus();
        win.moveTop();
      } else if (win.isFocused()) {
        win.minimize();
      } else {
        win.focus();
        win.moveTop();
      }
    }
  };

  try {
    globalShortcut.register('CommandOrControl+Shift+T', showOrToggle);
    console.log('Registered global shortcut: Ctrl+Shift+T');
  } catch (err) {
    console.error('Failed to register global shortcut:', err);
  }
}



// IPC Handlers
function setupIPC() {
  // Config
  ipcMain.handle('get-config', async () => {
    return loadConfig();
  });

  ipcMain.handle('save-config', async (_, updates: Partial<WidgetConfig>) => {
    saveConfig(updates);
    if (updates.alwaysOnTop !== undefined) {
      win?.setAlwaysOnTop(updates.alwaysOnTop);
    }
    if (updates.opacity !== undefined) {
      win?.setOpacity(updates.opacity);
    }
    if (updates.startWithWindows !== undefined) {
      app.setLoginItemSettings({
        openAtLogin: updates.startWithWindows,
        path: process.execPath,
      });
    }
    return loadConfig();
  });

  // Window Controls
  ipcMain.on('window-minimize', () => {
    win?.hide(); // Minimize directly to system tray
  });

  ipcMain.on('window-close', () => {
    win?.hide(); // Close minimizes to system tray
  });

  ipcMain.on('window-set-topmost', (_, isTop: boolean) => {
    win?.setAlwaysOnTop(isTop);
    saveConfig({ alwaysOnTop: isTop });
  });

  // Notion API
  ipcMain.handle('get-projects', async () => {
    return await notionService.getProjects();
  });

  ipcMain.handle('get-tasks', async (_, targetDate?: string) => {
    return await notionService.getTasks(targetDate);
  });

  ipcMain.handle('update-task-status', async (_, taskId: string, newStatus: string) => {
    return await notionService.updateTaskStatus(taskId, newStatus);
  });

  ipcMain.handle(
    'create-task',
    async (_, title: string, projectId?: string, priority?: string, doDate?: string) => {
      return await notionService.createTask(title, projectId, priority, doDate);
    }
  );

  ipcMain.handle('get-page-preview', async (_, pageId: string) => {
    return await notionService.getPagePreview(pageId);
  });

  ipcMain.on('open-external-url', (_, url: string) => {
    if (url) {
      shell.openExternal(url);
    }
  });
}

app.whenReady().then(() => {
  setupIPC();
  createWindow();
  setupTray();
  registerShortcuts();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Keep running in system tray unless explicitly exited
  }
});
