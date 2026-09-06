import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './styles/index.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Life Hub React Caught Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '540px', margin: '40px auto' }}>
          <h2 style={{ color: '#ef4444', fontSize: '1.2rem', fontWeight: 'bold' }}>Application Display Notice</h2>
          <p style={{ color: '#4b5563', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Life Hub encountered an issue loading components:
          </p>
          <pre style={{
            background: '#f3f4f6',
            padding: '1rem',
            borderRadius: '0.75rem',
            fontSize: '0.75rem',
            overflowX: 'auto',
            color: '#1f2937',
            whiteSpace: 'pre-wrap',
            marginTop: '0.75rem',
          }}>
            {this.state.error?.stack || this.state.error?.message}
          </pre>
          <button
            onClick={() => {
              if ('caches' in window) {
                caches.keys().then((names) => {
                  names.forEach((name) => caches.delete(name));
                });
              }
              localStorage.clear();
              window.location.reload();
            }}
            style={{
              marginTop: '1.25rem',
              padding: '0.6rem 1.2rem',
              background: '#1a73e8',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.75rem',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem',
            }}
          >
            Reset Cache & Reload App
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Global unhandled error hook to catch early script execution errors
window.addEventListener('error', (event) => {
  console.error('Global window error:', event.error || event.message);
  const root = document.getElementById('root');
  if (root && root.children.length === 0) {
    root.innerHTML = `
      <div style="padding: 24px; font-family: -apple-system, sans-serif; max-width: 500px; margin: 40px auto; text-align: center;">
        <h2 style="font-size: 1.1rem; color: #111827; font-weight: 600; margin-bottom: 8px;">Refreshing Life Hub...</h2>
        <p style="font-size: 0.85rem; color: #6b7280; margin-bottom: 16px;">Detected an update. Tap below to clear cached assets.</p>
        <button onclick="if('caches' in window){caches.keys().then(k=>k.forEach(n=>caches.delete(n)))}; localStorage.clear(); location.reload(true);" style="padding: 10px 18px; background: #1a73e8; color: #fff; border: none; border-radius: 12px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">
          Reload Fresh Version
        </button>
      </div>
    `;
  }
});

// Register Service Worker with instant activation
if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        reg.update();
        if (navigator.serviceWorker.controller) {
          let refreshing = false;
          navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (refreshing) return;
            refreshing = true;
            window.location.reload();
          });
        }
      })
      .catch((err) => {
        console.warn('ServiceWorker registration error:', err);
      });
  });
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
