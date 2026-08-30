import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { Header } from './components/Header';
import { DailyProgress } from './components/DailyProgress';
import { FilterBar } from './components/FilterBar';
import { TaskItem } from './components/TaskItem';
import { InlineTaskAdd } from './components/InlineTaskAdd';
import { QuickAddModal } from './components/QuickAddModal';
import { SettingsModal } from './components/SettingsModal';
import { NotionTask, NotionProject, WidgetConfig } from './lib/types';
import { Loader2, CheckCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [tasks, setTasks] = useState<NotionTask[]>([]);
  const [projects, setProjects] = useState<NotionProject[]>([]);
  const [config, setConfig] = useState<WidgetConfig>({
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
  });

  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [filterMode, setFilterMode] = useState<'today' | 'active' | 'all'>('today');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [showQuickAdd, setShowQuickAdd] = useState<boolean>(false);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('Ready');

  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);

  // Fetch projects and tasks
  const fetchData = useCallback(async () => {
    if (!window.electronAPI) return;
    try {
      setIsSyncing(true);
      setStatusMessage('Syncing with Notion...');

      const [projs, fetchedTasks, loadedConfig] = await Promise.all([
        window.electronAPI.getProjects(),
        window.electronAPI.getTasks(todayStr),
        window.electronAPI.getConfig(),
      ]);

      setProjects(projs);
      setTasks(fetchedTasks);
      if (loadedConfig) {
        setConfig(loadedConfig);
        setFilterMode(loadedConfig.filterMode || 'today');
      }

      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setStatusMessage(`Synced at ${timeStr}`);
    } catch (err) {
      console.error('Error loading data:', err);
      setStatusMessage('Offline / Sync error');
    } finally {
      setIsSyncing(false);
    }
  }, [todayStr]);

  // Initial load and tray event subscriptions
  useEffect(() => {
    fetchData();

    if (!window.electronAPI) return;

    const unregRefresh = window.electronAPI.onTriggerRefresh(() => {
      fetchData();
    });

    const unregQuickAdd = window.electronAPI.onTriggerQuickAdd(() => {
      setShowQuickAdd(true);
    });

    const unregConfig = window.electronAPI.onConfigUpdated((newCfg) => {
      setConfig((prev) => ({ ...prev, ...newCfg }));
    });

    return () => {
      unregRefresh();
      unregQuickAdd();
      unregConfig();
    };
  }, [fetchData]);

  // Auto-refresh interval
  useEffect(() => {
    const mins = config.autoRefreshMinutes;
    if (mins > 0) {
      const ms = mins * 60 * 1000;
      const interval = setInterval(() => {
        fetchData();
      }, ms);
      return () => clearInterval(interval);
    }
  }, [config.autoRefreshMinutes, fetchData]);

  // Keyboard Shortcuts (Ctrl+N, Ctrl+R, Esc)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        setShowQuickAdd(true);
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        fetchData();
      } else if (e.key === 'Escape') {
        setShowQuickAdd(false);
        setShowSettings(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [fetchData]);

  // Optimistic Status Toggle
  const handleToggleStatus = async (task: NotionTask, newStatus: string) => {
    const prevStatus = task.status;
    // Optimistically update
    setTasks((current) =>
      current.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t))
    );
    setStatusMessage(`Updating '${task.name.slice(0, 15)}...'`);

    try {
      if (window.electronAPI) {
        await window.electronAPI.updateTaskStatus(task.id, newStatus);
        setStatusMessage(`Saved to Notion`);
      }
    } catch (err) {
      console.error('Status toggle failed:', err);
      // Revert on error
      setTasks((current) =>
        current.map((t) => (t.id === task.id ? { ...t, status: prevStatus } : t))
      );
      setStatusMessage('Sync failed - reverted');
    }
  };

  // Add Task
  const handleCreateTask = async (
    title: string,
    projectId?: string,
    priority?: string,
    doDate?: string
  ) => {
    if (!window.electronAPI) return;
    setStatusMessage(`Creating '${title.slice(0, 15)}...'`);
    try {
      const created = await window.electronAPI.createTask(
        title,
        projectId,
        priority,
        doDate || todayStr
      );
      setTasks((prev) => [created, ...prev]);
      setStatusMessage('Created task in Notion');
    } catch (err) {
      console.error('Failed to create task:', err);
      setStatusMessage('Failed to create task');
      throw err;
    }
  };

  // Open External URL in Notion / Browser
  const handleOpenUrl = (url: string) => {
    if (window.electronAPI) {
      window.electronAPI.openExternalUrl(url);
    } else {
      window.open(url, '_blank');
    }
  };

  // Window Controls
  const handleMinimize = () => {
    window.electronAPI?.minimize();
  };

  const handleClose = () => {
    window.electronAPI?.close();
  };

  const handleTogglePin = async () => {
    const nextVal = !config.alwaysOnTop;
    setConfig((prev) => ({ ...prev, alwaysOnTop: nextVal }));
    if (window.electronAPI) {
      await window.electronAPI.saveConfig({ alwaysOnTop: nextVal });
    }
  };

  const handleSaveConfig = async (updates: Partial<WidgetConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
    if (window.electronAPI) {
      await window.electronAPI.saveConfig(updates);
    }
  };

  const handleFilterModeChange = (mode: 'today' | 'active' | 'all') => {
    setFilterMode(mode);
    if (window.electronAPI) {
      window.electronAPI.saveConfig({ filterMode: mode });
    }
  };

  // Filter and Sort Tasks
  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const isDone = (t.status || '').toLowerCase() === 'done';

      // 1. Filter Mode
      if (filterMode === 'today') {
        if (!config.showCompleted && isDone) return false;
      } else if (filterMode === 'active') {
        if (isDone) return false;
      }

      // 2. Project Filter
      if (selectedProjectId && t.projectId !== selectedProjectId) {
        return false;
      }

      // 3. Search Query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = t.name.toLowerCase().includes(query);
        const matchesProject = (t.projectName || '').toLowerCase().includes(query);
        if (!matchesName && !matchesProject) return false;
      }

      return true;
    });
  }, [tasks, filterMode, selectedProjectId, searchQuery, config.showCompleted]);

  // Sort Tasks: In Progress (0) -> Not Started (1) -> Done (2)
  const sortedTasks = useMemo(() => {
    return [...filteredTasks].sort((a, b) => {
      const statusScore = (s: string) => {
        const lower = s.toLowerCase();
        if (lower === 'in progress' || lower === 'doing') return 0;
        if (lower === 'not started') return 1;
        return 2;
      };
      return statusScore(a.status || '') - statusScore(b.status || '');
    });
  }, [filteredTasks]);

  // Metrics for Today
  const totalCount = tasks.length;
  const completedCount = tasks.filter((t) => (t.status || '').toLowerCase() === 'done').length;

  return (
    <div className="flex flex-col h-screen w-screen bg-canvas-soft border border-hairline/80 rounded-2xl shadow-2xl overflow-hidden select-none">
      {/* 1. Draggable Header */}
      <Header
        isSyncing={isSyncing}
        alwaysOnTop={config.alwaysOnTop}
        onRefresh={fetchData}
        onQuickAdd={() => setShowQuickAdd(true)}
        onTogglePin={handleTogglePin}
        onOpenSettings={() => setShowSettings(true)}
        onMinimize={handleMinimize}
        onClose={handleClose}
      />

      {/* 2. Daily Metric Progress Bar */}
      <DailyProgress total={totalCount} completed={completedCount} />

      {/* 3. Filter Bar & Search */}
      <FilterBar
        filterMode={filterMode}
        searchQuery={searchQuery}
        selectedProjectId={selectedProjectId}
        projects={projects}
        onFilterModeChange={handleFilterModeChange}
        onSearchChange={setSearchQuery}
        onProjectSelect={setSelectedProjectId}
      />

      {/* 4. Scrollable Task List */}
      <div className="flex-1 overflow-y-auto px-3 py-1.5 flex flex-col gap-1.5">
        {sortedTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-ink-muted">
            {totalCount > 0 && completedCount === totalCount ? (
              <>
                <CheckCircle className="w-8 h-8 text-sticker-green mb-2" />
                <span className="text-[13px] font-bold text-ink">All tasks completed for today!</span>
                <span className="text-[11px] text-ink-faint mt-0.5">Enjoy the rest of your day.</span>
              </>
            ) : (
              <>
                <span className="text-[13px] font-semibold text-ink">No tasks match this filter.</span>
                <span className="text-[11px] text-ink-faint mt-0.5">
                  Click below to create a new task.
                </span>
              </>
            )}
          </div>
        ) : (
          sortedTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggleStatus={handleToggleStatus}
              onOpenUrl={handleOpenUrl}
            />
          ))
        )}

        {/* 5. Inline Add Task Row */}
        <InlineTaskAdd
          projects={projects}
          defaultProjectId={selectedProjectId}
          onAddTask={(title, pId) => handleCreateTask(title, pId)}
        />
      </div>

      {/* 6. Footer Status Bar */}
      <div className="px-3 py-1.5 bg-canvas border-t border-hairline flex items-center justify-between text-[10.5px] text-ink-faint">
        <div className="flex items-center gap-1.5">
          {isSyncing && <Loader2 className="w-3 h-3 animate-spin text-primary" />}
          <span>{statusMessage}</span>
        </div>
        <button
          onClick={() => handleOpenUrl('https://www.notion.so')}
          className="text-primary hover:text-primary-active hover:underline font-medium"
        >
          Open Notion ↗
        </button>
      </div>

      {/* Modals */}
      {showQuickAdd && (
        <QuickAddModal
          projects={projects}
          defaultProjectId={selectedProjectId}
          onClose={() => setShowQuickAdd(false)}
          onCreateTask={handleCreateTask}
        />
      )}

      {showSettings && (
        <SettingsModal
          config={config}
          onClose={() => setShowSettings(false)}
          onSaveConfig={handleSaveConfig}
        />
      )}
    </div>
  );
};
