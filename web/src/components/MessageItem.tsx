import React, { useState } from 'react';
import { Bot, User, Copy, Check, RotateCcw, AlertTriangle, FileText, Image as ImageIcon } from 'lucide-react';
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

  return (
    <div className={`flex w-full space-x-3 px-3 sm:px-4 py-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-xl bg-notion-blue text-white shadow-sm mt-0.5">
          <Bot className="h-4 w-4" />
        </div>
      )}

      {/* Message Bubble & Content */}
      <div className={`flex flex-col max-w-[88%] sm:max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`relative rounded-2xl px-4 py-3 text-sm shadow-sm transition-all ${
            isUser
              ? 'bg-notion-card text-notion-text border border-notion-border rounded-br-sm'
              : isFailed
              ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-sm'
              : 'bg-notion-card text-notion-text border border-notion-border rounded-bl-sm'
          }`}
        >
          {/* Attachments if any */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1.5">
              {message.attachments.map((att) => (
                <a
                  key={att.id}
                  href={att.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 rounded-lg border border-notion-border bg-notion-bg px-2.5 py-1 text-xs text-notion-secondary hover:text-notion-blue transition-colors"
                >
                  {att.mime_type.startsWith('image/') ? (
                    <ImageIcon className="h-3.5 w-3.5 text-blue-500" />
                  ) : (
                    <FileText className="h-3.5 w-3.5 text-orange-500" />
                  )}
                  <span className="truncate max-w-[140px] font-medium">{att.filename}</span>
                </a>
              ))}
            </div>
          )}

          {/* Render Markdown for assistant or clean text for user */}
          {isUser ? (
            <div className="whitespace-pre-wrap break-words leading-relaxed text-notion-text">
              {message.content}
            </div>
          ) : (
            <div
              className="notion-prose leading-relaxed break-words"
              dangerouslySetInnerHTML={{ __html: renderMarkdownSafe(message.content) }}
            />
          )}

          {/* Failed Message Alert & Retry */}
          {isFailed && (
            <div className="mt-2.5 flex items-center justify-between border-t border-red-200 pt-2 text-xs">
              <span className="flex items-center text-red-700 font-medium">
                <AlertTriangle className="mr-1 h-3.5 w-3.5" />
                Delivery failed
              </span>
              {onRetry && (
                <button
                  onClick={() => onRetry(message.content, message.client_message_id)}
                  className="flex items-center space-x-1 rounded-md px-2 py-0.5 font-medium text-red-800 hover:bg-red-100 transition-colors"
                >
                  <RotateCcw className="h-3 w-3" />
                  <span>Retry</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Footer info: time & copy */}
        <div className="flex items-center space-x-2 mt-1 px-1 text-[11px] text-notion-muted">
          <span>{formatTime(message.created_at)}</span>
          {!isUser && (
            <button
              onClick={handleCopy}
              className="hover:text-notion-text transition-colors p-0.5 rounded"
              title="Copy text"
              aria-label="Copy message text"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            </button>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-xl bg-notion-paper border border-notion-border text-notion-secondary shadow-sm mt-0.5">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
};
