import React from 'react';
import {
  Image as ImageIcon,
  Camera,
  FileText,
  Dumbbell,
  Sun,
  PlusCircle,
  Search,
  X,
} from 'lucide-react';

interface MediaBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPhoto: () => void;
  onSelectCamera: () => void;
  onSelectFile?: () => void;
  onQuickAction?: (prompt: string) => void;
}

export const MediaBottomSheet: React.FC<MediaBottomSheetProps> = ({
  isOpen,
  onClose,
  onSelectPhoto,
  onSelectCamera,
  onSelectFile,
  onQuickAction,
}) => {
  if (!isOpen) return null;

  const quickTools = [
    {
      id: 'workout',
      title: 'Workout & Fitness Scan',
      description: 'Analyze treadmill or gym equipment display',
      icon: Dumbbell,
      action: () => onSelectCamera(),
    },
    {
      id: 'briefing',
      title: 'Morning Briefing',
      description: 'Generate daily schedule and priorities',
      icon: Sun,
      action: () => {
        onQuickAction?.('Create my morning briefing for today');
        onClose();
      },
    },
    {
      id: 'task',
      title: 'New Notion Task',
      description: 'Add a scheduled task to your workspace',
      icon: PlusCircle,
      action: () => {
        onQuickAction?.('Add a new task: ');
        onClose();
      },
    },
    {
      id: 'search',
      title: 'Search Workspace',
      description: 'Query notes, documents, and databases',
      icon: Search,
      action: () => {
        onQuickAction?.('Search my workspace for: ');
        onClose();
      },
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {/* Dimmed Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-Up Bottom Sheet */}
      <div
        className="relative w-full max-w-lg rounded-t-3xl border-t border-surface-border bg-surface-card p-4 pb-safe shadow-2xl transition-all duration-300 animate-in slide-in-from-bottom"
        style={{
          paddingBottom: 'max(1.75rem, calc(1rem + env(safe-area-inset-bottom, 0px)))',
        }}
      >
        {/* Grab Handle */}
        <div className="flex justify-center pb-2">
          <div className="h-1.5 w-12 rounded-full bg-content-muted/30" />
        </div>

        {/* Top Header */}
        <div className="flex items-center justify-between px-1 pb-3">
          <span className="text-sm font-semibold text-content-primary">Add to conversation</span>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-content-secondary hover:bg-surface-secondary active:scale-95"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Squircle Buttons Grid (Gemini iOS Style) */}
        <div className="grid grid-cols-3 gap-3 py-2">
          {/* Photos Button */}
          <button
            onClick={() => {
              onSelectPhoto();
              onClose();
            }}
            className="flex flex-col items-center justify-center rounded-2xl border border-surface-border bg-surface-secondary/70 p-4 transition-all hover:bg-surface-secondary active:scale-95 group"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-brand-blue group-hover:scale-105 transition-transform">
              <ImageIcon className="h-5 w-5" />
            </div>
            <span className="mt-2 text-xs font-medium text-content-primary">Photos</span>
          </button>

          {/* Camera Button */}
          <button
            onClick={() => {
              onSelectCamera();
              onClose();
            }}
            className="flex flex-col items-center justify-center rounded-2xl border border-surface-border bg-surface-secondary/70 p-4 transition-all hover:bg-surface-secondary active:scale-95 group"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 group-hover:scale-105 transition-transform">
              <Camera className="h-5 w-5" />
            </div>
            <span className="mt-2 text-xs font-medium text-content-primary">Camera</span>
          </button>

          {/* Document / File Button */}
          <button
            onClick={() => {
              onSelectFile ? onSelectFile() : onSelectPhoto();
              onClose();
            }}
            className="flex flex-col items-center justify-center rounded-2xl border border-surface-border bg-surface-secondary/70 p-4 transition-all hover:bg-surface-secondary active:scale-95 group"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600 group-hover:scale-105 transition-transform">
              <FileText className="h-5 w-5" />
            </div>
            <span className="mt-2 text-xs font-medium text-content-primary">Files</span>
          </button>
        </div>

        {/* Quick Tools List */}
        <div className="mt-3 divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-secondary/40 overflow-hidden">
          {quickTools.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={item.action}
                className="flex w-full items-center space-x-3 px-3.5 py-3 text-left transition-colors hover:bg-surface-secondary active:bg-surface-secondary/80"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-card text-brand-blue shadow-sm">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-content-primary truncate">{item.title}</div>
                  <div className="text-[11px] text-content-secondary truncate">{item.description}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
