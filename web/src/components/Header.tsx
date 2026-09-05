import React, { useState } from 'react';
import {
  Menu,
  SquarePen,
  ChevronDown,
  WifiOff,
} from 'lucide-react';
import { Agent } from '../types';
import { MascotEntity } from './MascotEntity';

interface HeaderProps {
  agents: Agent[];
  selectedAgentId: string;
  onSelectAgent: (id: string) => void;
  onNewConversation: () => void;
  onToggleDrawer: () => void;
  onOpenSettings: () => void;
  isOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent,
  onNewConversation,
  onToggleDrawer,
  onOpenSettings,
  isOnline,
}) => {
  const [showAgentMenu, setShowAgentMenu] = useState(false);
  const currentAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-surface-borderSubtle bg-surface-bg/80 px-3 sm:px-4 py-2.5 backdrop-blur-md pt-safe">
      {/* Left: Drawer Toggle */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggleDrawer}
          className="flex h-10 w-10 items-center justify-center rounded-full text-content-primary transition-colors hover:bg-surface-secondary active:scale-95"
          title="Conversation history"
          aria-label="Open conversation history"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Center: Model / Assistant Dropdown Pill (Gemini iOS Style) */}
      <div className="relative">
        <button
          onClick={() => setShowAgentMenu(!showAgentMenu)}
          className="flex items-center space-x-2 rounded-full border border-surface-border bg-surface-card/80 px-3.5 py-1.5 text-xs font-semibold text-content-primary shadow-xs backdrop-blur-xs transition-all hover:bg-surface-secondary active:scale-98"
          aria-expanded={showAgentMenu}
          aria-haspopup="true"
        >
          <MascotEntity size="sm" />
          <span>{currentAgent?.name || 'Life Hub AI'}</span>
          <ChevronDown className="h-3 w-3 text-content-muted" />
        </button>

        {/* Dropdown Menu */}
        {showAgentMenu && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowAgentMenu(false)}
            />
            <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 rounded-2xl border border-surface-border bg-surface-card p-1.5 shadow-notion-float z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
                Select Assistant
              </div>
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    onSelectAgent(agent.id);
                    setShowAgentMenu(false);
                  }}
                  className={`flex w-full items-start space-x-2.5 rounded-xl px-3 py-2 text-left transition-colors ${
                    agent.id === selectedAgentId
                      ? 'bg-brand-blueLight text-brand-blue font-medium'
                      : 'text-content-primary hover:bg-surface-secondary'
                  }`}
                >
                  <MascotEntity size="sm" className="mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold truncate">{agent.name}</div>
                    <div className="text-[11px] text-content-secondary line-clamp-1">
                      {agent.description}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Right: New Chat & User Avatar */}
      <div className="flex items-center space-x-2">
        {/* Offline Warning if any */}
        {!isOnline && (
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-950/50"
            title="You are currently offline"
          >
            <WifiOff className="h-4 w-4" />
          </div>
        )}

        {/* New Chat Button */}
        <button
          onClick={onNewConversation}
          className="flex h-10 w-10 items-center justify-center rounded-full text-content-primary transition-colors hover:bg-surface-secondary active:scale-95"
          title="New conversation"
          aria-label="New conversation"
        >
          <SquarePen className="h-5 w-5" />
        </button>

        {/* Profile Avatar -> Opens SettingsSheet */}
        <button
          onClick={onOpenSettings}
          className="relative flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-cyan text-white text-xs font-bold shadow-sm transition-transform hover:scale-105 active:scale-95 ring-2 ring-transparent focus:ring-brand-blue"
          title="Settings & Profile"
          aria-label="Settings and Profile"
        >
          <span>AJ</span>
          <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-surface-bg bg-emerald-500" />
        </button>
      </div>
    </header>
  );
};
