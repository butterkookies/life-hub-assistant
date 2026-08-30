import React, { useState } from 'react';
import { Plus, CornerDownLeft, Loader2 } from 'lucide-react';
import { NotionProject } from '../lib/types';

interface InlineTaskAddProps {
  projects: NotionProject[];
  defaultProjectId: string | null;
  onAddTask: (title: string, projectId?: string) => Promise<void>;
}

export const InlineTaskAdd: React.FC<InlineTaskAddProps> = ({
  projects,
  defaultProjectId,
  onAddTask,
}) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>(defaultProjectId || '');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle || isSubmitting) return;

    try {
      setIsSubmitting(true);
      await onAddTask(cleanTitle, selectedProjectId || undefined);
      setTitle('');
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to inline create task:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setTitle('');
    }
  };

  if (!isEditing) {
    return (
      <button
        onClick={() => setIsEditing(true)}
        className="w-full flex items-center gap-2 px-3 py-2 mt-1 rounded-lg border border-dashed border-hairline hover:border-primary/40 hover:bg-white/60 text-ink-muted hover:text-primary text-[12px] font-medium transition-all select-none"
      >
        <Plus className="w-3.5 h-3.5" />
        <span>New task...</span>
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="p-2 mt-1 bg-white border border-primary/30 rounded-lg shadow-sm flex flex-col gap-1.5"
    >
      <div className="flex items-center gap-1.5">
        <input
          autoFocus
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type task title and press Enter..."
          className="flex-1 text-[12px] text-ink placeholder:text-ink-faint focus:outline-none bg-transparent"
        />
        <button
          type="submit"
          disabled={!title.trim() || isSubmitting}
          className="flex items-center justify-center w-5 h-5 rounded-xs bg-primary hover:bg-primary-active text-white disabled:opacity-40 transition-colors"
        >
          {isSubmitting ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <CornerDownLeft className="w-3 h-3" />
          )}
        </button>
      </div>

      {/* Project Selector Mini Dropdown */}
      {projects.length > 0 && (
        <div className="flex items-center justify-between pt-1 border-t border-hairline">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="text-[10px] text-ink-secondary bg-transparent focus:outline-none max-w-[180px] truncate"
          >
            <option value="">(No Project / Personal)</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                📁 {p.name}
              </option>
            ))}
          </select>
          <span className="text-[10px] text-ink-faint">Esc to cancel</span>
        </div>
      )}
    </form>
  );
};
