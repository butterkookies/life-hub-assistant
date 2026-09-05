import React, { useState } from 'react';
import { Eye, EyeOff, Lock, Sparkles, AlertCircle } from 'lucide-react';

interface LoginModalProps {
  onLogin: (password: string) => Promise<boolean>;
  error: string | null;
}

export const LoginModal: React.FC<LoginModalProps> = ({ onLogin, error }) => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim() || submitting) return;
    setSubmitting(true);
    await onLogin(password);
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-notion-bg px-4">
      <div className="w-full max-w-sm rounded-3xl border border-notion-border bg-notion-card p-6 sm:p-8 shadow-notion-float animate-in fade-in zoom-in-95 duration-200">
        {/* Logo and Greeting */}
        <div className="text-center mb-6">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-notion-blue text-white shadow-md mb-3">
            <Sparkles className="h-7 w-7" />
          </div>
          <h1 className="text-lg font-bold tracking-tight text-notion-text">
            Andrei’s Life Hub
          </h1>
          <p className="mt-1 text-xs text-notion-secondary">
            Personal Notion AI Assistant
          </p>
        </div>

        {/* Error alert */}
        {error && (
          <div className="mb-4 flex items-start space-x-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-red-600" />
            <div className="flex-1">{error}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-notion-secondary mb-1.5">
              Access Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                className="w-full rounded-xl border border-notion-border bg-white px-3.5 py-2.5 text-sm text-notion-text placeholder-notion-muted focus:border-notion-blue focus:outline-none focus:ring-1 focus:ring-notion-blue pr-10"
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-notion-muted hover:text-notion-text"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || !password.trim()}
            className="flex w-full items-center justify-center space-x-2 rounded-xl bg-notion-blue px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-notion-blueHover active:scale-[0.98] disabled:opacity-50 transition-all"
          >
            {submitting ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <Lock className="h-4 w-4" />
                <span>Unlock Assistant</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-[11px] text-notion-muted">
          Private single-user workspace. Secure cookie authentication.
        </div>
      </div>
    </div>
  );
};
