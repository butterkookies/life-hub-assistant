import React from 'react';
import { Plus, RefreshCw, Pin, Settings as SettingsIcon, Minus, X, CheckSquare } from 'lucide-react';
import { formatTodayHeader } from '../lib/notion-theme';

interface HeaderProps {
  isSyncing: boolean;
  alwaysOnTop: boolean;
  onRefresh: () => void;
  onQuickAdd: () => void;
  onTogglePin: () => void;
  onOpenSettings: () => void;
  onMinimize: () => void;
  onClose: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isSyncing,
  alwaysOnTop,
  onRefresh,
  onQuickAdd,
  onTogglePin,
  onOpenSettings,
  onMinimize,
  onClose,
}) => {
  return (
    <div className="app-drag-region flex items-center justify-between px-3.5 py-2.5 bg-canvas border-b border-hairline rounded-t-2xl select-none">
      {/* Left: Brand Icon & Title & Date */}
      <div className="flex items-center gap-2.5">
        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary text-white shadow-sm">
          <CheckSquare className="w-4 h-4" />
        </div>
        <div className="flex flex-col">
          <span className="text-[14px] font-bold text-ink tracking-tight leading-none">
            Daily Tasks
          </span>
          <span className="text-[11px] font-medium text-ink-muted leading-tight mt-0.5">
            {formatTodayHeader()}
          </span>
        </div>
      </div>

      {/* Right: Window & Action Controls */}
      <div className="app-no-drag flex items-center gap-1">
        {/* + Add Task Button */}
        <button
          onClick={onQuickAdd}
          title="Add task for today"
          className="notion-btn-press flex items-center justify-center w-6 h-6 rounded-md bg-primary hover:bg-primary-active text-white transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>

        {/* 🔄 Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isSyncing}
          title="Refresh tasks from Notion"
          className="notion-btn-press flex items-center justify-center w-6 h-6 rounded-md hover:bg-surface-hover text-ink-secondary hover:text-ink transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-primary' : ''}`} />
        </button>

        {/* 📌 Pin / Always on Top Toggle */}
        <button
          onClick={onTogglePin}
          title={alwaysOnTop ? 'Pinned on top (Click to unpin)' : 'Pin on top'}
          className={`notion-btn-press flex items-center justify-center w-6 h-6 rounded-md transition-colors ${
            alwaysOnTop
              ? 'bg-primary-subtle text-primary font-bold'
              : 'hover:bg-surface-hover text-ink-secondary hover:text-ink'
          }`}
        >
          <Pin className="w-3.5 h-3.5" />
        </button>

        {/* ⚙️ Settings Button */}
        <button
          onClick={onOpenSettings}
          title="Widget Settings"
          className="notion-btn-press flex items-center justify-center w-6 h-6 rounded-md hover:bg-surface-hover text-ink-secondary hover:text-ink transition-colors"
        >
          <SettingsIcon className="w-3.5 h-3.5" />
        </button>

        {/* — Minimize Button */}
        <button
          onClick={onMinimize}
          title="Minimize to System Tray"
          className="notion-btn-press flex items-center justify-center w-6 h-6 rounded-md hover:bg-surface-hover text-ink-secondary hover:text-ink transition-colors"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>

        {/* ✕ Close Button */}
        <button
          onClick={onClose}
          title="Close to Tray"
          className="notion-btn-press flex items-center justify-center w-6 h-6 rounded-md hover:bg-[#fee2e2] text-ink-secondary hover:text-[#dc2626] transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
