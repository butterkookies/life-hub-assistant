import React from 'react';
import { Plus, X, MessageSquare, Trash2 } from 'lucide-react';
import { ConversationSummary } from '../types';

interface ConversationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export const ConversationDrawer: React.FC<ConversationDrawerProps> = ({
  isOpen,
  onClose,
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}) => {
  if (!isOpen) return null;

  const formatDate = (isoStr: string) => {
    try {
      const date = new Date(isoStr);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer content */}
      <div className="relative flex w-full max-w-xs flex-1 flex-col bg-notion-card border-r border-notion-border pt-safe shadow-2xl animate-in slide-in-from-left duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-notion-border px-4 py-3">
          <h2 className="text-sm font-semibold text-notion-text">Conversations</h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-notion-secondary hover:bg-notion-paper hover:text-notion-text"
            aria-label="Close conversation drawer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Action: New Conversation */}
        <div className="p-3">
          <button
            onClick={() => {
              onNew();
              onClose();
            }}
            className="flex w-full items-center justify-center space-x-2 rounded-xl bg-notion-blue px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-notion-blueHover active:scale-[0.98]"
          >
            <Plus className="h-4 w-4" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* List of Conversations */}
        <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1">
          {conversations.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs text-notion-secondary">
              No previous conversations yet.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <div
                  key={conv.id}
                  className={`group flex items-center justify-between rounded-xl px-3 py-2.5 transition-colors ${
                    isActive
                      ? 'bg-notion-paper font-medium text-notion-text border border-notion-border'
                      : 'text-notion-secondary hover:bg-notion-bg hover:text-notion-text'
                  }`}
                >
                  <button
                    onClick={() => {
                      onSelect(conv.id);
                      onClose();
                    }}
                    className="flex flex-1 items-start space-x-2.5 text-left overflow-hidden"
                  >
                    <MessageSquare className={`h-4 w-4 mt-0.5 shrink-0 ${isActive ? 'text-notion-blue' : 'text-notion-muted'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs truncate font-medium text-notion-text">
                        {conv.title}
                      </div>
                      <div className="text-[10px] text-notion-muted mt-0.5">
                        {formatDate(conv.updated_at)} · {conv.message_count} msgs
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this conversation?')) {
                        onDelete(conv.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-notion-muted hover:text-notion-red hover:bg-red-50 transition-opacity"
                    title="Delete conversation"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-notion-border p-3 text-center text-[11px] text-notion-muted pb-safe">
          Andrei’s Life Hub Assistant
        </div>
      </div>
    </div>
  );
};
