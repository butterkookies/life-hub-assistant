import React, { useState } from 'react';
import {
  MessageSquarePlus,
  PanelLeft,
  Bell,
  LogOut,
  Sparkles,
  WifiOff,
  ChevronDown
} from 'lucide-react';

import { Agent } from '../types';

interface HeaderProps {
  agents: Agent[];
  selectedAgentId: string;
  onSelectAgent: (id: string) => void;
  onNewConversation: () => void;
  onToggleDrawer: () => void;
  onOpenNotifications: () => void;
  onLogout: () => void;
  isOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent,
  onNewConversation,
  onToggleDrawer,
  onOpenNotifications,
  onLogout,
  isOnline,
}) => {
  const [showAgentMenu, setShowAgentMenu] = useState(false);
  const currentAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-notion-border bg-notion-bg/95 px-3 py-2.5 backdrop-blur-md pt-safe">
      <div className="flex items-center space-x-2">
        {/* Drawer Toggle */}
        <button
          onClick={onToggleDrawer}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-notion-secondary transition-colors hover:bg-notion-paper hover:text-notion-text active:scale-95"
          title="Conversation history"
          aria-label="Open conversation history"
        >
          <PanelLeft className="h-5 w-5" />
        </button>

        {/* App Title & Agent Selector */}
        <div className="relative">
          <button
            onClick={() => setShowAgentMenu(!showAgentMenu)}
            className="flex items-center space-x-1.5 rounded-lg px-2 py-1 text-left font-semibold text-notion-text transition-colors hover:bg-notion-paper"
            aria-expanded={showAgentMenu}
            aria-haspopup="true"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-notion-blue text-white shadow-sm">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-notion-text leading-tight">
                Life Hub
              </span>
              <span className="text-[11px] font-normal text-notion-secondary flex items-center">
                {currentAgent?.name || 'Assistant'}
                <ChevronDown className="ml-1 h-3 w-3" />
              </span>
            </div>
          </button>

          {/* Agent Dropdown */}
          {showAgentMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowAgentMenu(false)}
              />
              <div className="absolute left-0 top-full mt-1.5 w-64 rounded-xl border border-notion-border bg-notion-card p-1.5 shadow-notion-float z-50 animate-in fade-in zoom-in-95 duration-100">
                <div className="px-2.5 py-1.5 text-[11px] font-medium uppercase tracking-wider text-notion-muted">
                  Select Assistant
                </div>
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => {
                      onSelectAgent(agent.id);
                      setShowAgentMenu(false);
                    }}
                    className={`flex w-full items-start space-x-2 rounded-lg px-2.5 py-2 text-left transition-colors ${
                      agent.id === selectedAgentId
                        ? 'bg-notion-blueLight text-notion-blue font-medium'
                        : 'text-notion-text hover:bg-notion-paper'
                    }`}
                  >
                    <div className="mt-0.5">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-semibold">{agent.name}</div>
                      <div className="text-[11px] text-notion-secondary line-clamp-1">
                        {agent.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-1 sm:space-x-1.5">
        {/* Connectivity Status Pill */}
        <div
          className={`flex items-center space-x-1 rounded-full px-2 py-0.5 text-[11px] font-medium border ${
            isOnline
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border-amber-200 bg-amber-50 text-amber-700'
          }`}
          title={isOnline ? 'Connected to Life Hub API' : 'Operating in Offline Mode'}
        >
          {isOnline ? (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="hidden sm:inline">Online</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3 w-3" />
              <span>Offline</span>
            </>
          )}
        </div>

        {/* New Chat */}
        <button
          onClick={onNewConversation}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-notion-secondary transition-colors hover:bg-notion-paper hover:text-notion-text active:scale-95"
          title="New conversation"
          aria-label="Start new conversation"
        >
          <MessageSquarePlus className="h-5 w-5" />
        </button>

        {/* Notifications Modal */}
        <button
          onClick={onOpenNotifications}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-notion-secondary transition-colors hover:bg-notion-paper hover:text-notion-text active:scale-95"
          title="Notifications & Briefings"
          aria-label="Open notifications settings"
        >
          <Bell className="h-5 w-5" />
        </button>

        {/* Logout */}
        <button
          onClick={onLogout}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-notion-secondary transition-colors hover:bg-notion-paper hover:text-notion-red active:scale-95"
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
};
