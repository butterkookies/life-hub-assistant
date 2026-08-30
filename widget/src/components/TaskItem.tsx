import React, { useState } from 'react';
import { Check, Circle, ExternalLink, ChevronDown, ChevronUp, Flame } from 'lucide-react';
import { NotionTask } from '../lib/types';
import { getProjectSticker } from '../lib/notion-theme';
import { TaskPreviewDrawer } from './TaskPreviewDrawer';

interface TaskItemProps {
  task: NotionTask;
  onToggleStatus: (task: NotionTask, newStatus: string) => void;
  onOpenUrl: (url: string) => void;
}

export const TaskItem: React.FC<TaskItemProps> = ({
  task,
  onToggleStatus,
  onOpenUrl,
}) => {
  const [showPreview, setShowPreview] = useState<boolean>(false);
  const statusLower = (task.status || 'not started').toLowerCase();
  const isDone = statusLower === 'done';
  const isInProgress = statusLower === 'in progress' || statusLower === 'doing';
  const sticker = getProjectSticker(task.projectName);
  const isHighPriority = (task.priority || '').toLowerCase() === 'high';

  const handleCheckClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDone) {
      onToggleStatus(task, 'Not started');
    } else if (isInProgress) {
      onToggleStatus(task, 'Done');
    } else {
      onToggleStatus(task, 'Done');
    }
  };

  return (
    <div
      className={`group relative p-2.5 rounded-lg border transition-all ${
        isDone
          ? 'bg-canvas-soft border-hairline opacity-75'
          : 'bg-surface hover:bg-surface-hover border-hairline shadow-notion-soft'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        {/* 1. Left: Checkbox Button */}
        <button
          onClick={handleCheckClick}
          className={`notion-btn-press shrink-0 flex items-center justify-center w-5 h-5 mt-0.5 rounded-full border transition-all ${
            isDone
              ? 'bg-sticker-green border-sticker-green text-white'
              : isInProgress
              ? 'bg-[#fffbeb] border-sticker-orange text-sticker-orange'
              : 'bg-white border-hairline hover:border-primary text-transparent hover:text-ink-faint'
          }`}
          title={isDone ? 'Mark Incomplete' : 'Mark Done'}
        >
          {isDone ? (
            <Check className="w-3 h-3 stroke-[3]" />
          ) : isInProgress ? (
            <div className="w-2 h-2 rounded-full bg-sticker-orange" />
          ) : (
            <Check className="w-2.5 h-2.5 stroke-[2]" />
          )}
        </button>

        {/* 2. Middle: Task Title & Badges */}
        <div
          onClick={() => setShowPreview(!showPreview)}
          className="flex-1 cursor-pointer select-none"
        >
          <div
            className={`text-[12.5px] font-medium leading-snug transition-colors ${
              isDone ? 'line-through text-ink-faint' : 'text-ink'
            }`}
          >
            {task.name}
          </div>

          {/* Badges Row */}
          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
            {/* Project Sticker Pill */}
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[9.5px] font-semibold rounded-full border ${sticker.bg} ${sticker.text} ${sticker.border}`}
            >
              <span className={`w-1 h-1 rounded-full ${sticker.dot}`} />
              {task.projectName || 'Personal'}
            </span>

            {/* Status Pill */}
            <span
              className={`text-[9.5px] font-medium ${
                isDone
                  ? 'text-sticker-green font-semibold'
                  : isInProgress
                  ? 'text-sticker-orange font-semibold'
                  : 'text-ink-faint'
              }`}
            >
              {task.status || 'Not started'}
            </span>

            {/* High Priority Badge */}
            {isHighPriority && (
              <span className="inline-flex items-center gap-0.5 px-1 py-0.2 text-[9px] font-bold rounded-xs bg-[#fef2f2] text-[#dc2626] border border-[#fecaca]">
                <Flame className="w-2.5 h-2.5" />
                High
              </span>
            )}
          </div>
        </div>

        {/* 3. Right: Preview & Open Action Buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setShowPreview(!showPreview)}
            title={showPreview ? 'Hide notes preview' : 'View notes preview'}
            className="flex items-center justify-center w-5 h-5 rounded-xs hover:bg-white text-ink-faint hover:text-ink-secondary transition-colors"
          >
            {showPreview ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {task.url && (
            <button
              onClick={() => onOpenUrl(task.url!)}
              title="Open in Notion"
              className="flex items-center justify-center w-5 h-5 rounded-xs hover:bg-white text-ink-faint hover:text-primary transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Preview Drawer */}
      {showPreview && (
        <TaskPreviewDrawer
          taskId={task.id}
          taskName={task.name}
          url={task.url}
          onOpenUrl={onOpenUrl}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
};
