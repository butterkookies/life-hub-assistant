import React from 'react';
import {
  Sun,
  Moon,
  Bell,
  Sparkles,
  Database,
  LogOut,
  Check,
} from 'lucide-react';
import { MascotEntity } from './MascotEntity';

interface SettingsSheetProps {
  isOpen: boolean;
  onClose: () => void;
  theme: 'light' | 'dark';
  onToggleTheme: (theme: 'light' | 'dark') => void;
  onOpenNotifications: () => void;
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
  onLogout,
  userEmail = 'geronimojoan002@gmail.com',
  userName = 'Geronimo, Andrei John P.',
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Card (Full screen on mobile, rounded card on desktop) */}
      <div className="relative flex h-full w-full max-w-lg flex-col bg-surface-bg sm:h-auto sm:max-h-[90vh] sm:rounded-3xl sm:border sm:border-surface-border shadow-2xl overflow-hidden animate-in slide-in-from-bottom sm:zoom-in-95 duration-200">
        {/* Navigation Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-surface-border bg-surface-card/90 px-4 py-3.5 backdrop-blur-md pt-safe">
          <span className="text-base font-semibold text-content-primary">Settings</span>
          <button
            onClick={onClose}
            className="text-sm font-semibold text-brand-blue hover:text-brand-blueHover active:scale-95"
          >
            Done
          </button>
        </div>

        {/* Scrollable Settings Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-safe">
          {/* User Profile Card */}
          <div className="flex items-center space-x-3.5 rounded-2xl border border-surface-border bg-surface-card p-4 shadow-sm">
            <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-cyan text-white font-bold text-lg shadow-md shrink-0">
              <MascotEntity size="sm" className="absolute -bottom-1 -right-1" />
              <span>AJ</span>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-content-primary truncate">{userName}</h3>
              <p className="text-xs text-content-secondary truncate">{userEmail}</p>
              <div className="mt-1 flex items-center space-x-1.5 text-[11px] text-emerald-600 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>Active Life Hub Session</span>
              </div>
            </div>
          </div>

          {/* Group 1: Appearance & Theme */}
          <div className="rounded-2xl border border-surface-border bg-surface-card overflow-hidden shadow-sm">
            <div className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-content-muted bg-surface-secondary/50">
              Appearance
            </div>
            <div className="p-3">
              <div className="grid grid-cols-2 gap-2.5">
                {/* Light Mode Tile */}
                <button
                  onClick={() => onToggleTheme('light')}
                  className={`flex items-center space-x-3 rounded-xl border p-3 text-left transition-all ${
                    theme === 'light'
                      ? 'border-brand-blue bg-brand-blueLight/60 text-brand-blue shadow-sm'
                      : 'border-surface-border bg-surface-secondary/50 text-content-secondary hover:bg-surface-secondary'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${theme === 'light' ? 'bg-white shadow-xs' : 'bg-surface-card'}`}>
                    <Sun className="h-4 w-4 text-amber-500" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold">Light Mode</div>
                    <div className="text-[10px] opacity-75">Clean & spacious</div>
                  </div>
                  {theme === 'light' && <Check className="h-4 w-4" />}
                </button>

                {/* Dark Mode Tile */}
                <button
                  onClick={() => onToggleTheme('dark')}
                  className={`flex items-center space-x-3 rounded-xl border p-3 text-left transition-all ${
                    theme === 'dark'
                      ? 'border-brand-blue bg-brand-blueLight/60 text-brand-blue shadow-sm'
                      : 'border-surface-border bg-surface-secondary/50 text-content-secondary hover:bg-surface-secondary'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${theme === 'dark' ? 'bg-white/10 shadow-xs' : 'bg-surface-card'}`}>
                    <Moon className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold">Dark Mode</div>
                    <div className="text-[10px] opacity-75">Luminous OLED</div>
                  </div>
                  {theme === 'dark' && <Check className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Group 2: Notion Integration & Assistant */}
          <div className="divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-card shadow-sm overflow-hidden">
            <div className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-content-muted bg-surface-secondary/50">
              Workspace & AI
            </div>

            <div className="flex items-center justify-between p-3.5">
              <div className="flex items-center space-x-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-brand-blue">
                  <Database className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-content-primary">Notion Workspace</div>
                  <div className="text-[11px] text-content-secondary">Connected via official Integration</div>
                </div>
              </div>
              <span className="rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:text-emerald-400">
                Connected
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5">
              <div className="flex items-center space-x-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-content-primary">Gemini 2.5 Flash</div>
                  <div className="text-[11px] text-content-secondary">Multimodal intelligence & OCR active</div>
                </div>
              </div>
              <span className="text-[11px] font-medium text-content-muted">Active</span>
            </div>
          </div>

          {/* Group 3: Notifications & Briefings */}
          <div className="divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-card shadow-sm overflow-hidden">
            <div className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-content-muted bg-surface-secondary/50">
              Automation & Alerts
            </div>

            <button
              onClick={() => {
                onOpenNotifications();
                onClose();
              }}
              className="flex w-full items-center justify-between p-3.5 text-left hover:bg-surface-secondary/50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
                  <Bell className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-content-primary">Daily Briefing & Web Push</div>
                  <div className="text-[11px] text-content-secondary">06:00 AM (PHT) schedule delivery</div>
                </div>
              </div>
              <span className="text-xs font-semibold text-brand-blue">Configure &rarr;</span>
            </button>
          </div>

          {/* Group 4: Log Out */}
          <div className="pt-2">
            <button
              onClick={onLogout}
              className="flex w-full items-center justify-center space-x-2 rounded-2xl border border-red-200 dark:border-red-900/30 bg-red-50/50 dark:bg-red-950/20 p-3.5 text-xs font-semibold text-red-600 dark:text-red-400 transition-colors hover:bg-red-100/50 active:scale-[0.98]"
            >
              <LogOut className="h-4 w-4" />
              <span>Log out of Life Hub</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
