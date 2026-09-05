import { useEffect, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { SessionState } from '../types';

export function useAuth() {
  const [session, setSession] = useState<SessionState>({
    authenticated: false,
    user: null,
    push_configured: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkSession = async () => {
    try {
      setLoading(true);
      const data = await api.auth.getSession();
      setSession(data);
      setError(null);
    } catch (err: any) {
      setSession({
        authenticated: false,
        user: null,
        push_configured: false,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkSession();
  }, []);

  const login = async (password: string) => {
    try {
      setError(null);
      await api.auth.login(password);
      await checkSession();
      return true;
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Login failed. Please try again.');
      }
      return false;
    }
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } finally {
      setSession({
        authenticated: false,
        user: null,
        push_configured: false,
      });
    }
  };

  return {
    session,
    loading,
    error,
    login,
    logout,
    refreshSession: checkSession,
  };
}
