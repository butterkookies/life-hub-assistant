import React, { useRef, useState, useEffect } from 'react';
import {
  ArrowUp,
  Mic,
  Plus,
  X,
  Check,
  FileText,
} from 'lucide-react';
import { useMediaRecorder } from '../hooks/useMediaRecorder';

interface MessageComposerProps {
  onSendMessage: (text: string) => void;
  onUploadMedia: (file: File, caption?: string) => void;
  onOpenMediaSheet: () => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  cameraInputRef: React.RefObject<HTMLInputElement>;
  disabled?: boolean;
  isOnline: boolean;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  onUploadMedia,
  onOpenMediaSheet,
  fileInputRef,
  cameraInputRef,
  disabled = false,
  isOnline,
}) => {
  const [text, setText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const {
    isRecording,
    duration,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useMediaRecorder();

  // Auto-grow textarea up to 120px
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (disabled || !isOnline) return;

    if (selectedFile) {
      onUploadMedia(selectedFile, text.trim());
      setSelectedFile(null);
      setFilePreview(null);
      setText('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      return;
    }

    if (text.trim()) {
      onSendMessage(text.trim());
      setText('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (window.innerWidth > 640) {
        e.preventDefault();
        handleSend();
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setFilePreview(url);
      } else {
        setFilePreview(null);
      }
    }
  };

  const handleFinishVoice = async () => {
    const result = await stopRecording();
    if (result && result.blob) {
      const file = new File(
        [result.blob],
        `voice_${Date.now()}.${result.mimeType.includes('mp4') ? 'mp4' : 'webm'}`,
        { type: result.mimeType }
      );
      onUploadMedia(file);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const hasContent = text.trim().length > 0 || selectedFile !== null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-30 pointer-events-none pb-safe">
      <div className="max-w-2xl mx-auto px-3 sm:px-6 mb-3 sm:mb-5 pointer-events-auto">
        {/* Hidden native file inputs triggered by MediaBottomSheet */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*,audio/*,.pdf,.doc,.docx"
          className="hidden"
          onChange={handleFileChange}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Selected File Preview Float */}
        {selectedFile && (
          <div className="mb-2 flex items-center space-x-2 rounded-2xl border border-surface-border bg-surface-card/95 p-2 shadow-sm backdrop-blur-md animate-in fade-in slide-in-from-bottom-2">
            {filePreview ? (
              <img
                src={filePreview}
                alt="Upload preview"
                className="h-10 w-10 rounded-xl object-cover border border-surface-border"
              />
            ) : (
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-blueLight text-brand-blue">
                <FileText className="h-5 w-5" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-content-primary truncate">{selectedFile.name}</div>
              <div className="text-[10px] text-content-secondary">{(selectedFile.size / 1024).toFixed(1)} KB</div>
            </div>
            <button
              onClick={() => {
                setSelectedFile(null);
                setFilePreview(null);
              }}
              className="p-1 rounded-full text-content-muted hover:bg-surface-secondary hover:text-content-primary"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Recording Mode Pill */}
        {isRecording ? (
          <div className="flex items-center justify-between rounded-full border border-red-200 dark:border-red-900/40 bg-surface-card/95 px-4 py-3 shadow-composer-light dark:shadow-composer-dark backdrop-blur-xl">
            <div className="flex items-center space-x-3">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
              </span>
              <span className="text-xs font-medium text-red-600 dark:text-red-400">
                Recording audio {formatTimer(duration)}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={cancelRecording}
                className="flex h-8 w-8 items-center justify-center rounded-full text-content-muted hover:bg-surface-secondary hover:text-content-primary transition-colors"
                title="Cancel recording"
              >
                <X className="h-4 w-4" />
              </button>
              <button
                onClick={handleFinishVoice}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue text-white shadow-sm transition-transform active:scale-95"
                title="Send voice message"
              >
                <Check className="h-4 w-4" />
              </button>
            </div>
          </div>
        ) : (
          /* Normal Floating Pill Composer (Gemini iOS Style) */
          <div className="flex items-center rounded-full border border-surface-border bg-surface-elevated/95 px-2.5 py-1.5 shadow-composer-light dark:shadow-composer-dark backdrop-blur-xl transition-all focus-within:border-brand-blue/60 focus-within:ring-2 focus-within:ring-brand-blue/10">
            {/* Left: [+] Expander Button */}
            <button
              onClick={onOpenMediaSheet}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-secondary text-content-primary hover:bg-surface-secondary/80 active:scale-95 transition-all"
              title="Add photos, camera or actions"
              aria-label="Add media"
            >
              <Plus className="h-5 w-5 text-content-primary" />
            </button>

            {/* Center: Auto-resizing Text Input */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Life Hub..."
              disabled={disabled || !isOnline}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-content-primary placeholder-content-muted outline-none disabled:opacity-50"
              style={{ maxHeight: '120px' }}
            />

            {/* Right: Dynamic Mic / Send Action */}
            {hasContent ? (
              <button
                onClick={handleSend}
                disabled={disabled || !isOnline}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-blue text-white shadow-sm transition-all hover:bg-brand-blueHover active:scale-95 disabled:opacity-50"
                title="Send message"
                aria-label="Send message"
              >
                <ArrowUp className="h-4 w-4 stroke-[2.5]" />
              </button>
            ) : (
              <button
                onClick={startRecording}
                disabled={disabled || !isOnline}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-content-secondary hover:text-brand-blue hover:bg-surface-secondary transition-all active:scale-95 disabled:opacity-50"
                title="Record voice note"
                aria-label="Record voice note"
              >
                <Mic className="h-5 w-5" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
