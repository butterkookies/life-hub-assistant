import React, { useEffect, useRef } from 'react';
import { Sparkles, Calendar, PlusCircle, Search, Sun, Dumbbell } from 'lucide-react';
import { Message, PendingScan } from '../types';
import { MessageItem } from './MessageItem';
import { PendingScanCard } from './PendingScanCard';

interface ConversationTimelineProps {
  messages: Message[];
  sending: boolean;
  pendingScan: PendingScan | null;
  onQuickAction: (actionText: string) => void;
  onRetry: (content: string, clientMsgId?: string) => void;
  onConfirmScan: (token: string) => void;
  onCorrectScan: (token: string, text: string) => void;
  onCancelScan: (token: string) => void;
}

export const ConversationTimeline: React.FC<ConversationTimelineProps> = ({
  messages,
  sending,
  pendingScan,
  onQuickAction,
  onRetry,
  onConfirmScan,
  onCorrectScan,
  onCancelScan,
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, sending, pendingScan]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning, Andrei ☀️';
    if (hour >= 12 && hour < 17) return 'Good afternoon, Andrei 🌤️';
    return 'Good evening, Andrei 🌙';
  };

  const quickActions = [
    { label: "What's on my schedule today?", icon: Calendar, prompt: "What's on my schedule and tasks for today?" },
    { label: "Add a task", icon: PlusCircle, prompt: "Add a new task: " },
    { label: "Search my notes", icon: Search, prompt: "Search my workspace for: " },
    { label: "Morning briefing", icon: Sun, prompt: "Create my morning briefing for today" },
    { label: "Log workout", icon: Dumbbell, prompt: "Log a workout: " },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-1 sm:px-2 py-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 max-w-md mx-auto">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-notion-blue text-white shadow-sm mb-3.5">
            <Sparkles className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-bold text-notion-text">{getGreeting()}</h2>
          <p className="mt-1 text-xs text-notion-secondary max-w-xs leading-relaxed">
            I'm your Notion Life Hub Assistant. Ask me about your schedule, projects, health logs, or record a voice note.
          </p>

          {/* Quick Action Chips */}
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {quickActions.map((action, i) => {
              const Icon = action.icon;
              return (
                <button
                  key={i}
                  onClick={() => onQuickAction(action.prompt)}
                  className="flex items-center space-x-1.5 rounded-xl border border-notion-border bg-notion-card px-3.5 py-2 text-xs font-medium text-notion-text shadow-sm hover:border-notion-blue hover:text-notion-blue hover:bg-notion-blueLight/50 transition-all active:scale-95"
                >
                  <Icon className="h-3.5 w-3.5 text-notion-blue" />
                  <span>{action.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="space-y-1">
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} onRetry={onRetry} />
          ))}

          {/* Pending Workout Scan Confirmation Card */}
          {pendingScan && (
            <div className="px-3 sm:px-4">
              <PendingScanCard
                scan={pendingScan}
                onConfirm={onConfirmScan}
                onCorrect={onCorrectScan}
                onCancel={onCancelScan}
                disabled={sending}
              />
            </div>
          )}

          {/* Thinking / Working Indicator */}
          {sending && (
            <div className="flex items-center space-x-3 px-3 sm:px-4 py-3 text-xs text-notion-secondary animate-pulse">
              <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-notion-blue text-white shadow-sm">
                <Sparkles className="h-3.5 w-3.5 animate-spin" />
              </div>
              <div className="flex items-center space-x-1.5">
                <span>Working in Notion...</span>
                <span className="flex space-x-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-notion-secondary animate-bounce [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-notion-secondary animate-bounce [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-notion-secondary animate-bounce" />
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} className="h-6" />
        </div>
      )}
    </div>
  );
};
