import React, { useRef, useState, useEffect } from 'react';
import {
  Send,
  Mic,
  Camera,
  Paperclip,
  X,
  Check,
  AlertCircle
} from 'lucide-react';

import { useMediaRecorder } from '../hooks/useMediaRecorder';

interface MessageComposerProps {
  onSendMessage: (text: string) => void;
  onUploadMedia: (file: File, caption?: string) => void;
  disabled?: boolean;
  isOnline: boolean;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  onUploadMedia,
  disabled = false,
  isOnline,
}) => {
  const [text, setText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  const {
    isRecording,
    duration,
    error: micError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useMediaRecorder();

  // Auto-grow textarea
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
      // Send on Enter unless shift is pressed (on non-mobile)
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
      const file = new File([result.blob], `voice_${Date.now()}.${result.mimeType.includes('mp4') ? 'mp4' : 'webm'}`, {
        type: result.mimeType,
      });
      onUploadMedia(file);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className="sticky bottom-0 z-20 border-t border-notion-border bg-notion-bg/95 backdrop-blur-md px-3 sm:px-4 pt-3 pb-safe"
      style={{ paddingBottom: 'max(1.25rem, calc(0.75rem + env(safe-area-inset-bottom, 0px)))' }}
    >
      {/* Offline Warning Banner */}
      {!isOnline && (
        <div className="mb-2 flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-900">
          <span className="flex items-center">
            <AlertCircle className="mr-1.5 h-3.5 w-3.5 text-amber-600" />
            You are offline. Reconnect to send messages or execute Notion tasks.
          </span>
        </div>
      )}

      {/* Mic Error Notice */}
      {micError && (
        <div className="mb-2 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-3 py-1.5 text-xs text-red-900">
          <span>{micError}</span>
          <button onClick={() => cancelRecording()} className="p-0.5 text-red-700 hover:text-red-900">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Selected File / Image Preview */}
      {selectedFile && (
        <div className="mb-2 flex items-center space-x-2 rounded-xl border border-notion-border bg-notion-card p-2 shadow-sm max-w-sm">
          {filePreview ? (
            <img src={filePreview} alt="Upload preview" className="h-12 w-12 rounded-lg object-cover" />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-notion-paper text-notion-secondary">
              <Paperclip className="h-5 w-5" />
            </div>
          )}
          <div className="flex-1 min-w-0 text-xs">
            <p className="truncate font-medium text-notion-text">{selectedFile.name}</p>
            <p className="text-[10px] text-notion-secondary">
              {(selectedFile.size / 1024).toFixed(0)} KB
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedFile(null);
              setFilePreview(null);
            }}
            className="rounded-lg p-1.5 text-notion-secondary hover:bg-notion-paper hover:text-notion-text"
            title="Remove attachment"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Composer Input Area */}
      {isRecording ? (
        /* Voice Recording Active Bar */
        <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-red-50/70 px-4 py-2.5 shadow-sm">
          <div className="flex items-center space-x-2.5">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-600" />
            </span>
            <span className="text-sm font-semibold text-red-900">{formatTimer(duration)}</span>
            <span className="text-xs text-red-700 hidden sm:inline">Recording voice note...</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <button
              onClick={cancelRecording}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-notion-secondary border border-notion-border shadow-sm hover:text-notion-red transition-colors"
              title="Cancel recording"
              aria-label="Cancel recording"
            >
              <X className="h-4 w-4" />
            </button>
            <button
              onClick={handleFinishVoice}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-notion-blue text-white shadow-sm hover:bg-notion-blueHover transition-colors active:scale-95"
              title="Send voice note"
              aria-label="Send voice note"
            >
              <Check className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : (
        /* Standard Text & Media Composer */
        <div className="flex items-end space-x-1.5 sm:space-x-2">
          {/* Media Attachments Buttons */}
          <div className="flex items-center space-x-0.5 pb-1">
            {/* Camera Capture */}
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
              capture="environment"
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              type="button"
              onClick={() => cameraInputRef.current?.click()}
              disabled={disabled || !isOnline}
              className="flex h-10 w-10 items-center justify-center rounded-xl text-notion-secondary hover:bg-notion-paper hover:text-notion-text active:scale-95 disabled:opacity-40 transition-colors"
              title="Take photo"
              aria-label="Take photo"
            >
              <Camera className="h-5 w-5" />
            </button>

            {/* Photo Library / File Upload */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif,audio/*"
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled || !isOnline}
              className="flex h-10 w-10 items-center justify-center rounded-xl text-notion-secondary hover:bg-notion-paper hover:text-notion-text active:scale-95 disabled:opacity-40 transition-colors"
              title="Attach photo or audio"
              aria-label="Attach photo or audio"
            >
              <Paperclip className="h-5 w-5" />
            </button>

            {/* Voice Record Mic */}
            <button
              type="button"
              onClick={() => startRecording()}
              disabled={disabled || !isOnline}
              className="flex h-10 w-10 items-center justify-center rounded-xl text-notion-secondary hover:bg-notion-paper hover:text-notion-blue active:scale-95 disabled:opacity-40 transition-colors"
              title="Record voice note"
              aria-label="Record voice note"
            >
              <Mic className="h-5 w-5" />
            </button>
          </div>

          {/* Growing Textarea */}
          <div className="flex-1 min-w-0 rounded-2xl border border-notion-border bg-notion-card px-3 py-2 shadow-sm focus-within:border-notion-blue focus-within:ring-1 focus-within:ring-notion-blue transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={disabled ? 'Waiting for response...' : 'Ask Life Hub or log a workout...'}
              disabled={disabled || !isOnline}
              className="w-full resize-none bg-transparent text-sm text-notion-text placeholder-notion-muted focus:outline-none max-h-32"
            />
          </div>

          {/* Send Button */}
          <div className="pb-1">
            <button
              type="button"
              onClick={handleSend}
              disabled={disabled || !isOnline || (!text.trim() && !selectedFile)}
              className="flex h-10 w-10 items-center justify-center rounded-2xl bg-notion-blue text-white shadow-sm hover:bg-notion-blueHover active:scale-95 disabled:opacity-30 disabled:pointer-events-none transition-all"
              title="Send message"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
