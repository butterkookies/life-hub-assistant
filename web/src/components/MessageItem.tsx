import React, { useState } from 'react';
import {
  Copy,
  Check,
  RotateCcw,
  AlertTriangle,
  FileText,
  Image as ImageIcon,
} from 'lucide-react';
import { Message } from '../types';
import { renderMarkdownSafe } from '../lib/sanitize';

interface MessageItemProps {
  message: Message;
  onRetry?: (content: string, clientMsgId?: string) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, onRetry }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isFailed = message.status === 'failed';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  // User Message: Clean pill bubble on the right
  if (isUser) {
    return (
      <div className="flex w-full justify-end py-1">
        <div className="flex flex-col items-end max-w-[85%] sm:max-w-[75%]">
          {/* Attachments if any */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mb-2 flex flex-wrap justify-end gap-1.5">
              {message.attachments.map((att) => (
                <a
                  key={att.id}
                  href={att.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 rounded-xl border border-surface-border bg-surface-card px-3 py-1.5 text-xs text-content-secondary hover:text-brand-blue transition-colors shadow-xs"
                >
                  {att.mime_type.startsWith('image/') ? (
                    <ImageIcon className="h-3.5 w-3.5 text-brand-blue" />
                  ) : (
                    <FileText className="h-3.5 w-3.5 text-brand-indigo" />
                  )}
                  <span className="truncate max-w-[140px] font-medium">{att.filename}</span>
                </a>
              ))}
            </div>
          )}

          <div className="rounded-3xl rounded-br-sm border border-surface-border bg-surface-secondary/90 px-4 py-2.5 text-sm text-content-primary shadow-xs">
            <div className="whitespace-pre-wrap break-words leading-relaxed">{message.content}</div>
          </div>
          <span className="mt-1 text-[10px] text-content-muted px-2">{formatTime(message.created_at)}</span>
        </div>
      </div>
    );
  }

  // Assistant Message: Borderless Gemini stream layout (spacious, full-width, zero wasted indent)
  return (
    <div className="flex w-full flex-col py-2.5">
      {/* Attachments if any */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {message.attachments.map((att) => (
            <a
              key={att.id}
              href={att.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 rounded-xl border border-surface-border bg-surface-card px-3 py-2 text-xs text-content-secondary hover:text-brand-blue transition-colors shadow-xs"
            >
              {att.mime_type.startsWith('image/') ? (
                <ImageIcon className="h-4 w-4 text-brand-blue" />
              ) : (
                <FileText className="h-4 w-4 text-brand-indigo" />
              )}
              <span className="truncate max-w-[160px] font-medium">{att.filename}</span>
            </a>
          ))}
        </div>
      )}

      {/* Render Rich Markdown with full width */}
      <div
        className="prose-gemini break-words leading-relaxed w-full"
        dangerouslySetInnerHTML={{ __html: renderMarkdownSafe(message.content) }}
      />

      {/* Delivery failure / retry banner */}
      {isFailed && (
        <div className="mt-3 flex items-center justify-between rounded-xl border border-red-200 dark:border-red-900/30 bg-red-50/70 dark:bg-red-950/30 p-2.5 text-xs text-red-700 dark:text-red-400">
          <span className="flex items-center font-medium">
            <AlertTriangle className="mr-1.5 h-4 w-4 text-red-500" />
            Delivery failed
          </span>
          {onRetry && (
            <button
              onClick={() => onRetry(message.content, message.client_message_id)}
              className="flex items-center space-x-1 rounded-lg px-2.5 py-1 font-semibold text-red-800 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors active:scale-95"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}

      {/* Message Actions Footer (Copy button & subtle timestamp) */}
      {!isFailed && (
        <div className="mt-2.5 flex items-center space-x-3 text-content-muted">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 rounded-lg px-2 py-1 text-[11px] font-medium hover:bg-surface-secondary hover:text-content-primary transition-colors active:scale-95"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-emerald-500 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
          <span className="text-[10px] select-none opacity-70">
            {formatTime(message.created_at)}
          </span>
        </div>
      )}
    </div>
  );
};
