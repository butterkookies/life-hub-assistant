import React, { useEffect, useState } from 'react';
import { ExternalLink, Loader2, FileText, CheckSquare, Square } from 'lucide-react';
import { PagePreviewData } from '../lib/types';

interface TaskPreviewDrawerProps {
  taskId: string;
  taskName: string;
  url?: string | null;
  onOpenUrl: (url: string) => void;
  onClose: () => void;
}

export const TaskPreviewDrawer: React.FC<TaskPreviewDrawerProps> = ({
  taskId,
  taskName,
  url,
  onOpenUrl,
  onClose,
}) => {
  const [preview, setPreview] = useState<PagePreviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchPreview = async () => {
      if (!window.electronAPI) return;
      try {
        setLoading(true);
        const data = await window.electronAPI.getPagePreview(taskId);
        if (mounted) {
          setPreview(data);
          setLoading(false);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err?.message || 'Failed to load page preview');
          setLoading(false);
        }
      }
    };

    fetchPreview();
    return () => {
      mounted = false;
    };
  }, [taskId]);

  return (
    <div className="mt-2 p-2.5 bg-surface-subtle border border-hairline rounded-lg text-ink text-[12px] shadow-sm animate-in fade-in slide-in-from-top-1 duration-200">
      {/* Header with Title and Open Notion Link */}
      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-primary" />
          <span className="font-semibold text-ink text-[11px]">Page Notes & Preview</span>
        </div>
        {url && (
          <button
            onClick={() => onOpenUrl(url)}
            className="flex items-center gap-1 text-[10px] font-semibold text-primary hover:text-primary-active hover:underline"
          >
            <span>Open in Notion</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </button>
        )}
      </div>

      {/* Content Body */}
      {loading ? (
        <div className="flex items-center justify-center py-4 text-ink-faint gap-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
          <span className="text-[11px]">Loading page content...</span>
        </div>
      ) : error ? (
        <div className="text-ink-muted text-[11px] py-1 text-center italic">
          No written page content found.
        </div>
      ) : preview && preview.blocks.length > 0 ? (
        <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto pr-1">
          {preview.blocks.map((block) => {
            if (block.type === 'to_do') {
              return (
                <div key={block.id} className="flex items-start gap-1.5 text-[11px]">
                  {block.checked ? (
                    <CheckSquare className="w-3 h-3 text-sticker-green shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-3 h-3 text-ink-faint shrink-0 mt-0.5" />
                  )}
                  <span className={block.checked ? 'line-through text-ink-faint' : 'text-ink'}>
                    {block.text || 'Untitled task block'}
                  </span>
                </div>
              );
            }
            if (block.type.startsWith('heading')) {
              return (
                <div key={block.id} className="font-bold text-ink text-[12px] pt-1">
                  {block.text}
                </div>
              );
            }
            if (block.type === 'bulleted_list_item') {
              return (
                <div key={block.id} className="flex items-start gap-1.5 text-[11px]">
                  <span className="text-ink-muted text-[10px] mt-0.5">•</span>
                  <span>{block.text}</span>
                </div>
              );
            }
            return (
              <div key={block.id} className="text-ink-secondary text-[11px] leading-relaxed">
                {block.text}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-ink-faint text-[11px] py-2 text-center">
          Empty page body. Click "Open in Notion" to add notes.
        </div>
      )}
    </div>
  );
};
