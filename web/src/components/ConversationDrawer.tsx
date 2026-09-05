import React, { useState } from 'react';
import {
  Plus,
  X,
  MessageSquare,
  Trash2,
  Search,
  Settings,
} from 'lucide-react';
import { ConversationSummary } from '../types';
import { MascotEntity } from './MascotEntity';

interface ConversationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onOpenSettings: () => void;
  userName?: string;
}

export const ConversationDrawer: React.FC<ConversationDrawerProps> = ({
  isOpen,
  onClose,
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onOpenSettings,
  userName = 'Geronimo, Andrei John P.',
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

  const formatDate = (isoStr: string) => {
    try {
      const date = new Date(isoStr);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '';
    }
  };

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel (Gemini iOS Style) */}
      <div className="relative flex w-full max-w-xs sm:max-w-sm flex-1 flex-col bg-surface-card border-r border-surface-border pt-safe shadow-2xl animate-in slide-in-from-left duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-borderSubtle">
          <div className="flex items-center space-x-2">
            <MascotEntity size="sm" />
            <span className="text-sm font-semibold text-content-primary">Life Hub</span>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-content-secondary hover:bg-surface-secondary active:scale-95 transition-colors"
            aria-label="Close conversation drawer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Top Action: + New Chat Pill (Image 1 Style) */}
        <div className="p-3">
          <button
            onClick={() => {
              onNew();
              onClose();
            }}
            className="flex w-full items-center justify-center space-x-2 rounded-full bg-surface-secondary px-4 py-3 text-sm font-medium text-content-primary shadow-xs transition-all hover:bg-surface-border active:scale-[0.98]"
          >
            <Plus className="h-4 w-4 text-brand-blue" />
            <span>New chat</span>
          </button>
        </div>

        {/* Search Chats Input */}
        <div className="px-3 pb-2">
          <div className="relative flex items-center">
            <Search className="absolute left-3.5 h-3.5 w-3.5 text-content-muted pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats"
              className="w-full rounded-full border border-surface-border bg-surface-bg pl-9 pr-3.5 py-2 text-xs text-content-primary placeholder-content-muted outline-none focus:border-brand-blue"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 text-content-muted hover:text-content-primary"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Recents Section */}
        <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
            Recents
          </div>

          {filteredConversations.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs text-content-muted">
              {searchQuery ? 'No matching conversations.' : 'No previous conversations yet.'}
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <div
                  key={conv.id}
                  className={`group flex items-center justify-between rounded-xl px-3 py-2.5 transition-colors ${
                    isActive
                      ? 'bg-brand-blueLight/60 dark:bg-brand-blueLight/20 font-medium text-brand-blue'
                      : 'text-content-secondary hover:bg-surface-secondary hover:text-content-primary'
                  }`}
                >
                  <button
                    onClick={() => {
                      onSelect(conv.id);
                      onClose();
                    }}
                    className="flex flex-1 items-center space-x-2.5 text-left overflow-hidden"
                  >
                    <MessageSquare className={`h-4 w-4 shrink-0 ${isActive ? 'text-brand-blue' : 'text-content-muted'}`} />
                    <span className="text-xs truncate font-medium text-content-primary flex-1">
                      {conv.title}
                    </span>
                    <span className="text-[10px] text-content-muted shrink-0">
                      {formatDate(conv.updated_at)}
                    </span>
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this conversation?')) {
                        onDelete(conv.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-content-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition-opacity ml-1"
                    title="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Bottom Sticky User Profile Bar (Gemini iOS Image 1) */}
        <div className="border-t border-surface-border p-3 pb-safe bg-surface-card/90 backdrop-blur-md">
          <div className="flex items-center justify-between rounded-xl p-1.5 hover:bg-surface-secondary/70 transition-colors">
            <button
              onClick={() => {
                onOpenSettings();
                onClose();
              }}
              className="flex items-center space-x-2.5 flex-1 min-w-0 text-left"
            >
              <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-cyan text-white text-xs font-bold shrink-0">
                <span>AJ</span>
                <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-emerald-500 border-2 border-surface-card" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-content-primary truncate">{userName}</div>
                <div className="text-[10px] text-content-muted truncate">Life Hub Assistant</div>
              </div>
            </button>

            <button
              onClick={() => {
                onOpenSettings();
                onClose();
              }}
              className="p-2 rounded-full text-content-muted hover:text-content-primary hover:bg-surface-border transition-colors"
              title="Open settings"
            >
              <Settings className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
