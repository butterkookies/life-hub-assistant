import React, { useState } from 'react';
import { X, Sparkles, Loader2, Calendar, Folder, Flame } from 'lucide-react';
import { NotionProject } from '../lib/types';

interface QuickAddModalProps {
  projects: NotionProject[];
  defaultProjectId: string | null;
  onClose: () => void;
  onCreateTask: (
    title: string,
    projectId?: string,
    priority?: string,
    doDate?: string
  ) => Promise<void>;
}

export const QuickAddModal: React.FC<QuickAddModalProps> = ({
  projects,
  defaultProjectId,
  onClose,
  onCreateTask,
}) => {
  const todayStr = new Date().toISOString().split('T')[0];
  const [title, setTitle] = useState<string>('');
  const [projectId, setProjectId] = useState<string>(defaultProjectId || '');
  const [priority, setPriority] = useState<string>('Normal');
  const [doDate, setDoDate] = useState<string>(todayStr);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle || loading) return;

    try {
      setLoading(true);
      await onCreateTask(cleanTitle, projectId || undefined, priority, doDate);
      onClose();
    } catch (err) {
      console.error('Task creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-sm bg-white rounded-xl border border-hairline shadow-notion-elevated overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-hairline bg-canvas-soft">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-[13px] font-bold text-ink">New Task for Today</span>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-5 h-5 rounded-xs hover:bg-surface-hover text-ink-muted hover:text-ink"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-3">
          {/* Task Name */}
          <div>
            <label className="block text-[11px] font-bold text-ink mb-1">Task Title</label>
            <input
              autoFocus
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be accomplished?"
              className="w-full px-2.5 py-1.5 text-[12px] bg-canvas-soft border border-hairline rounded-xs text-ink placeholder:text-ink-faint focus:outline-none focus:border-primary focus:bg-white transition-all"
            />
          </div>

          {/* Project Selector */}
          <div>
            <label className="block text-[11px] font-bold text-ink mb-1 flex items-center gap-1">
              <Folder className="w-3 h-3 text-ink-muted" />
              <span>Project</span>
            </label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full px-2 py-1.5 text-[11.5px] bg-canvas-soft border border-hairline rounded-xs text-ink focus:outline-none focus:border-primary focus:bg-white"
            >
              <option value="">(No Project / Personal)</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority & Date Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[11px] font-bold text-ink mb-1 flex items-center gap-1">
                <Flame className="w-3 h-3 text-ink-muted" />
                <span>Priority</span>
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-2 py-1.5 text-[11.5px] bg-canvas-soft border border-hairline rounded-xs text-ink focus:outline-none focus:border-primary focus:bg-white"
              >
                <option value="Normal">Normal</option>
                <option value="High">🔥 High</option>
                <option value="Low">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-ink mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-ink-muted" />
                <span>Do Date</span>
              </label>
              <input
                type="date"
                value={doDate}
                onChange={(e) => setDoDate(e.target.value)}
                className="w-full px-2 py-1 text-[11.5px] bg-canvas-soft border border-hairline rounded-xs text-ink focus:outline-none focus:border-primary focus:bg-white"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-hairline mt-1">
            <button
              type="button"
              onClick={onClose}
              className="notion-btn-press px-3 py-1.5 text-[12px] font-medium text-ink-secondary hover:bg-surface-hover rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || loading}
              className="notion-btn-press flex items-center gap-1.5 px-4 py-1.5 text-[12px] font-semibold text-white bg-primary hover:bg-primary-active disabled:opacity-40 rounded-full shadow-sm transition-all"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Create Task</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
