import React, { useState } from 'react';
import { X, Settings as SettingsIcon, Sliders, RefreshCw, Power } from 'lucide-react';
import { WidgetConfig } from '../lib/types';

interface SettingsModalProps {
  config: WidgetConfig;
  onClose: () => void;
  onSaveConfig: (updates: Partial<WidgetConfig>) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  config,
  onClose,
  onSaveConfig,
}) => {
  const [theme, setTheme] = useState<WidgetConfig['theme']>(config.theme || 'light');
  const [autoRefresh, setAutoRefresh] = useState<number>(config.autoRefreshMinutes ?? 5);
  const [opacity, setOpacity] = useState<number>(config.opacity ?? 0.98);
  const [showCompleted, setShowCompleted] = useState<boolean>(config.showCompleted ?? true);
  const [startWithWindows, setStartWithWindows] = useState<boolean>(config.startWithWindows ?? false);
  const [saving, setSaving] = useState<boolean>(false);

  const handleSave = async () => {
    try {
      setSaving(true);
      await onSaveConfig({
        theme,
        autoRefreshMinutes: autoRefresh,
        opacity,
        showCompleted,
        startWithWindows,
      });
      onClose();
    } catch (err) {
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-sm bg-white rounded-xl border border-hairline shadow-notion-elevated overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-hairline bg-canvas-soft">
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-ink-muted" />
            <span className="text-[13px] font-bold text-ink">Widget Preferences</span>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-5 h-5 rounded-xs hover:bg-surface-hover text-ink-muted hover:text-ink"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-4 flex flex-col gap-3.5">
          {/* Auto Refresh */}
          <div>
            <label className="block text-[11px] font-bold text-ink mb-1 flex items-center gap-1">
              <RefreshCw className="w-3 h-3 text-ink-muted" />
              <span>Auto-Sync Interval</span>
            </label>
            <select
              value={autoRefresh}
              onChange={(e) => setAutoRefresh(Number(e.target.value))}
              className="w-full px-2 py-1.5 text-[11.5px] bg-canvas-soft border border-hairline rounded-xs text-ink focus:outline-none focus:border-primary focus:bg-white"
            >
              <option value={1}>Every 1 minute</option>
              <option value={3}>Every 3 minutes</option>
              <option value={5}>Every 5 minutes (Recommended)</option>
              <option value={15}>Every 15 minutes</option>
              <option value={0}>Manual refresh only</option>
            </select>
          </div>

          {/* Opacity Slider */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-bold text-ink flex items-center gap-1">
                <Sliders className="w-3 h-3 text-ink-muted" />
                <span>Window Opacity</span>
              </label>
              <span className="text-[10px] text-ink-muted">{Math.round(opacity * 100)}%</span>
            </div>
            <input
              type="range"
              min={0.6}
              max={1.0}
              step={0.02}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              className="w-full h-1.5 bg-canvas-soft rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>

          {/* Toggles */}
          <div className="flex flex-col gap-2 pt-2 border-t border-hairline">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
                className="w-3.5 h-3.5 rounded-xs accent-primary"
              />
              <span className="text-[11.5px] text-ink">Show Completed Tasks in Today view</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={startWithWindows}
                onChange={(e) => setStartWithWindows(e.target.checked)}
                className="w-3.5 h-3.5 rounded-xs accent-primary"
              />
              <span className="text-[11.5px] text-ink flex items-center gap-1">
                <Power className="w-3 h-3 text-sticker-green" />
                <span>Launch automatically on Windows startup</span>
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-hairline mt-1">
            <button
              onClick={onClose}
              className="notion-btn-press px-3 py-1.5 text-[12px] font-medium text-ink-secondary hover:bg-surface-hover rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="notion-btn-press px-4 py-1.5 text-[12px] font-semibold text-white bg-primary hover:bg-primary-active rounded-full shadow-sm transition-all"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
