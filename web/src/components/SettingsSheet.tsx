import React, { useState } from 'react';
import {
  Sun,
  Moon,
  Bell,
  Sparkles,
  Database,
  LogOut,
  ChevronRight,
  RotateCcw,
  Palette,
  Loader2,
} from 'lucide-react';

interface SettingsSheetProps {
  isOpen: boolean;
  onClose: () => void;
  theme: 'light' | 'dark';
  onToggleTheme: (theme: 'light' | 'dark') => void;
  onOpenNotifications: () => void;
  onOpenDesignKit?: () => void;
  onLogout: () => void;
  userEmail?: string;
  userName?: string;
}

export const SettingsSheet: React.FC<SettingsSheetProps> = ({
  isOpen,
  onClose,
  theme,
  onToggleTheme,
  onOpenNotifications,
  onOpenDesignKit,
  onLogout,
  userEmail = 'geronimojoan002@gmail.com',
  userName = 'Geronimo, Andrei John P.',
}) => {
  const [clearing, setClearing] = useState(false);

  const handleHardRefresh = async () => {
    setClearing(true);
    try {
      if ('caches' in window) {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
      }
      if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        for (const reg of registrations) {
          await reg.update();
        }
      }
    } catch (err) {
      console.warn('Cache clear error:', err);
    }
    // Hard reload
    window.location.reload();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Dimming Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-200 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* iOS Modal Sheet (Bottom sheet on mobile, rounded card on desktop) */}
      <div className="relative flex h-[92vh] sm:h-auto sm:max-h-[88vh] w-full max-w-md flex-col rounded-t-[32px] sm:rounded-3xl bg-surface-bg border-t sm:border border-surface-border shadow-2xl overflow-hidden animate-in slide-in-from-bottom sm:zoom-in-95 duration-200">
        {/* iOS Grab Handle (Mobile only) */}
        <div className="mx-auto mt-2.5 mb-1 h-1 w-9 rounded-full bg-content-muted/30 sm:hidden shrink-0" />

        {/* Navigation Bar */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-3.5 bg-surface-bg/85 backdrop-blur-xl">
          <h2 className="text-[17px] font-semibold text-content-primary tracking-tight">
            Settings
          </h2>
          <button
            onClick={onClose}
            className="text-[17px] font-semibold text-brand-blue hover:text-brand-blueHover active:opacity-60 transition-opacity"
          >
            Done
          </button>
        </div>

        {/* Scrollable Grouped Content */}
        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-6 pb-safe no-scrollbar">
          {/* Apple ID Style User Profile Row */}
          <div className="rounded-2xl border border-surface-border bg-surface-card p-4 shadow-2xs transition-transform">
            <div className="flex items-center space-x-3.5">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-indigo text-white font-semibold text-lg shadow-xs shrink-0 select-none">
                <span>AJ</span>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-[16px] font-semibold text-content-primary tracking-tight truncate">
                  {userName}
                </h3>
                <p className="text-[13px] text-content-secondary truncate">{userEmail}</p>
                <div className="mt-1 flex items-center space-x-1.5 text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Workspace Connected</span>
                </div>
              </div>
            </div>
          </div>

          {/* Group: Appearance (Cupertino Segmented Control) */}
          <div>
            <div className="px-3 pb-1.5 text-[12px] font-semibold uppercase tracking-wider text-content-muted">
              Appearance
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card p-1.5 shadow-2xs">
              <div className="flex rounded-xl bg-surface-secondary/70 p-1">
                <button
                  onClick={() => onToggleTheme('light')}
                  className={`flex flex-1 items-center justify-center space-x-2 rounded-lg py-2.5 text-[13px] font-medium transition-all active:scale-[0.98] ${
                    theme === 'light'
                      ? 'bg-surface-card text-content-primary shadow-xs font-semibold'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  <Sun className="h-4 w-4 text-amber-500" />
                  <span>Light</span>
                </button>
                <button
                  onClick={() => onToggleTheme('dark')}
                  className={`flex flex-1 items-center justify-center space-x-2 rounded-lg py-2.5 text-[13px] font-medium transition-all active:scale-[0.98] ${
                    theme === 'dark'
                      ? 'bg-surface-card text-content-primary shadow-xs font-semibold'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  <Moon className="h-4 w-4 text-indigo-400" />
                  <span>Dark</span>
                </button>
              </div>
            </div>
          </div>

          {/* Group: Workspace & AI Engine (Grouped Inset List) */}
          <div>
            <div className="px-3 pb-1.5 text-[12px] font-semibold uppercase tracking-wider text-content-muted">
              Workspace & AI
            </div>
            <div className="divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-card shadow-2xs overflow-hidden">
              {/* Notion Row */}
              <div className="flex items-center justify-between p-3.5">
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500 text-white shadow-2xs shrink-0">
                    <Database className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">Notion Workspace</div>
                    <div className="text-[12px] text-content-secondary">Official Integration Active</div>
                  </div>
                </div>
                <span className="rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/50 dark:border-emerald-800/50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                  Synced
                </span>
              </div>

              {/* Gemini Intelligence Row */}
              <div className="flex items-center justify-between p-3.5">
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500 text-white shadow-2xs shrink-0">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">Gemini 2.5 Flash</div>
                    <div className="text-[12px] text-content-secondary">Multimodal Vision & OCR</div>
                  </div>
                </div>
                <span className="text-[12px] font-medium text-content-muted">Ready</span>
              </div>
            </div>
          </div>

          {/* Group: Notifications & Automations */}
          <div>
            <div className="px-3 pb-1.5 text-[12px] font-semibold uppercase tracking-wider text-content-muted">
              Automation & Alerts
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card shadow-2xs overflow-hidden">
              <button
                onClick={() => {
                  onOpenNotifications();
                  onClose();
                }}
                className="flex w-full items-center justify-between p-3.5 text-left hover:bg-surface-secondary/50 active:bg-surface-secondary/70 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500 text-white shadow-2xs shrink-0">
                    <Bell className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">Daily Briefing & Web Push</div>
                    <div className="text-[12px] text-content-secondary">06:00 AM (PHT) schedule delivery</div>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-content-muted/70" />
              </button>
            </div>
          </div>

          {/* Group: System & Tools */}
          <div>
            <div className="px-3 pb-1.5 text-[12px] font-semibold uppercase tracking-wider text-content-muted">
              System & Tools
            </div>
            <div className="divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-card shadow-2xs overflow-hidden">
              {/* Hard Refresh Row */}
              <button
                onClick={handleHardRefresh}
                disabled={clearing}
                className="flex w-full items-center justify-between p-3.5 text-left hover:bg-surface-secondary/50 active:bg-surface-secondary/70 transition-colors disabled:opacity-60"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500 text-white shadow-2xs shrink-0">
                    {clearing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RotateCcw className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">
                      {clearing ? 'Clearing Cache & Reloading...' : 'Force Reload & Clear Cache'}
                    </div>
                    <div className="text-[12px] text-content-secondary">
                      Bypasses Service Worker and reloads fresh app
                    </div>
                  </div>
                </div>
                <span className="text-[12px] font-semibold text-brand-blue">
                  {clearing ? 'Reloading' : 'Reload'}
                </span>
              </button>

              {/* Design Kit Studio Shortcut */}
              {onOpenDesignKit && (
                <button
                  onClick={() => {
                    onOpenDesignKit();
                    onClose();
                  }}
                  className="flex w-full items-center justify-between p-3.5 text-left hover:bg-surface-secondary/50 active:bg-surface-secondary/70 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500 text-white shadow-2xs shrink-0">
                      <Palette className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-[14px] font-medium text-content-primary">
                        Design Kit & UI Studio
                      </div>
                      <div className="text-[12px] text-content-secondary">
                        Interactive sandbox, property tweakers & review
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-content-muted/70" />
                </button>
              )}
            </div>
          </div>

          {/* Group: Account Sign Out */}
          <div>
            <div className="px-3 pb-1.5 text-[12px] font-semibold uppercase tracking-wider text-content-muted">
              Account
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card shadow-2xs overflow-hidden">
              <button
                onClick={onLogout}
                className="flex w-full items-center justify-center space-x-2 p-3.5 text-[15px] font-semibold text-red-600 dark:text-red-400 hover:bg-red-50/50 dark:hover:bg-red-950/20 active:bg-red-100/50 active:scale-[0.99] transition-all"
              >
                <LogOut className="h-4 w-4" />
                <span>Log Out</span>
              </button>
            </div>
          </div>

          {/* iOS System Footnote */}
          <div className="text-center text-[11px] text-content-muted pt-2 pb-4">
            Life Hub Assistant • iOS Native Design System
          </div>
        </div>
      </div>
    </div>
  );
};
