import React, { useEffect, useRef, useState } from 'react';
import {
  Calendar,
  PlusCircle,
  Search,
  Sun,
  Dumbbell,
  ArrowUpRight,
} from 'lucide-react';
import { Message, PendingScan } from '../types';
import { MessageItem } from './MessageItem';
import { PendingScanCard } from './PendingScanCard';
import { MascotEntity } from './MascotEntity';

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

const GREETINGS = [
  'Your move, Andrei!',
  'Ready to conquer the day, Andrei?',
  'What are we building today, Andrei?',
  'All systems go, Andrei.',
  'Let’s make things happen, Andrei.',
  'How can I help you thrive today, Andrei?',
];

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

  // Pick a dynamic greeting on initial load
  const [greeting] = useState<string>(() => {
    const randomIndex = Math.floor(Math.random() * GREETINGS.length);
    return GREETINGS[randomIndex];
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, sending, pendingScan]);

  const quickActions = [
    { label: "What's on my schedule today?", icon: Calendar, prompt: "What's on my schedule and tasks for today?" },
    { label: "Add a task to Notion", icon: PlusCircle, prompt: "Add a new task: " },
    { label: "Search my workspace & notes", icon: Search, prompt: "Search my workspace for: " },
    { label: "Generate morning briefing", icon: Sun, prompt: "Create my morning briefing for today" },
    { label: "Log workout & fitness", icon: Dumbbell, prompt: "Log a workout: " },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-6 pb-36 no-scrollbar">
      {messages.length === 0 ? (
        /* Empty / Hero State (Gemini iOS Layout) */
        <div className="flex flex-col justify-center min-h-[70vh] max-w-xl mx-auto px-2">
          {/* Centered Wobbly Mascot Entity */}
          <div className="flex flex-col items-center justify-center my-6">
            <MascotEntity size="xl" state="idle" />
            <h1 className="mt-6 text-2xl sm:text-3xl font-bold tracking-tight text-content-primary text-center">
              {greeting}
            </h1>
          </div>

          {/* Left-Aligned Quick Actions (No pills, clean icon + phrase) */}
          <div className="mt-8 space-y-2">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-content-muted px-2 mb-3">
              Suggested Prompts
            </div>
            {quickActions.map((action, i) => {
              const Icon = action.icon;
              return (
                <button
                  key={i}
                  onClick={() => onQuickAction(action.prompt)}
                  className="group flex w-full items-center justify-between rounded-xl px-3.5 py-3 text-left transition-all hover:bg-surface-secondary/70 active:scale-[0.99]"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className="text-brand-blue group-hover:scale-110 transition-transform">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="text-sm font-medium text-content-primary group-hover:text-brand-blue transition-colors">
                      {action.label}
                    </span>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-content-muted opacity-0 group-hover:opacity-100 group-hover:text-brand-blue transition-all" />
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        /* Message Stream */
        <div className="space-y-6 max-w-2xl mx-auto">
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} onRetry={onRetry} />
          ))}

          {/* Pending Workout Scan Confirmation Card */}
          {pendingScan && (
            <div className="py-2">
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
            <div className="flex items-center space-x-3.5 py-3 text-xs text-content-secondary">
              <MascotEntity size="sm" state="thinking" />
              <div className="flex items-center space-x-1.5 font-medium">
                <span>Life Hub is thinking</span>
                <span className="flex space-x-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
              </div>
            </div>
          )}

          <div ref={bottomRef} className="h-4" />
        </div>
      )}
    </div>
  );
};
