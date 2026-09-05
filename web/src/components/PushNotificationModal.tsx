import React, { useEffect, useState } from 'react';
import { Bell, BellOff, X, Send, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';


interface PushNotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  vapidPublicKey?: string;
}

export const PushNotificationModal: React.FC<PushNotificationModalProps> = ({
  isOpen,
  onClose,
  vapidPublicKey,
}) => {
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [configured, setConfigured] = useState(false);
  const [publicKey, setPublicKey] = useState(vapidPublicKey);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPushSupported = typeof window !== 'undefined' && window.isSecureContext && 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
  const isIos = typeof navigator !== 'undefined' && (/iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1));
  const isStandalone = typeof window !== 'undefined' && ((window.navigator as Navigator & { standalone?: boolean }).standalone || window.matchMedia('(display-mode: standalone)').matches);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    setChecking(true);
    setError(null);
    setTestResult(null);
    setSubscribed(false);
    setConfigured(false);
    const refresh = async () => {
      try {
        const status = await api.notifications.getStatus();
        const registration = isPushSupported ? await navigator.serviceWorker.getRegistration() : undefined;
        const subscription = registration ? await registration.pushManager.getSubscription() : null;
        const deviceStatus = subscription ? await api.notifications.getDeviceStatus(subscription.endpoint) : null;
        if (!cancelled) {
          setConfigured(status.configured);
          setPublicKey(status.vapid_public_key);
          setSubscribed(Boolean(deviceStatus?.subscribed && Notification.permission === 'granted'));
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not check this device. Close and reopen notifications to retry.');
      } finally {
        if (!cancelled) setChecking(false);
      }
    };
    void refresh();
    return () => { cancelled = true; };
  }, [isOpen, isPushSupported]);

  if (!isOpen) return null;

  const readyWorker = async (): Promise<ServiceWorkerRegistration> => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([
        navigator.serviceWorker.ready,
        new Promise<never>((_, reject) => {
          timer = setTimeout(() => reject(new Error('Notification setup is still loading. Reload the app and try again.')), 10000);
        }),
      ]);
    } finally {
      clearTimeout(timer);
    }
  };

  const urlBase64ToUint8Array = (base64String: string) => {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  };

  const handleSubscribe = async () => {
    setError(null);
    setTestResult(null);
    setLoading(true);

    try {
      if (!isPushSupported) {
        throw new Error('Web Push is not supported on this browser.');
      }

      if (!configured || !publicKey) {
        throw new Error('Push notifications are not configured on this server yet.');
      }

      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        throw new Error(permission === 'denied'
          ? 'Notifications are blocked. Allow them in your browser or device notification settings, then try again.'
          : 'Permission was not granted. Tap Enable again when you are ready.');
      }

      const reg = await readyWorker();
      const sub = await reg.pushManager.getSubscription() || await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });

      await api.notifications.subscribe(sub);
      setSubscribed(true);
      setTestResult('✅ Notifications enabled successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to subscribe to push notifications.');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setError(null);
    setLoading(true);
    try {
      const reg = await readyWorker();
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await api.notifications.unsubscribe(sub);
        await sub.unsubscribe();
      }
      setSubscribed(false);
      setTestResult('Notifications disabled.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable notifications.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendTest = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);
    try {
      const res = await api.notifications.test();
      if (!res.success || res.delivered_devices === 0) {
        throw new Error('No test notifications were sent. Enable this device again, or check the server push settings.');
      }
      setTestResult(`Test sent to ${res.delivered_devices} device(s). Check your notifications.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test dispatch failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <div role="dialog" aria-modal="true" aria-labelledby="push-notification-title" className="w-full max-w-sm rounded-3xl border border-notion-border bg-notion-card p-6 shadow-notion-float animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-3 border-b border-notion-borderSubtle">
          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-notion-blueLight text-notion-blue">
              <Bell className="h-4 w-4" />
            </div>
            <h3 id="push-notification-title" className="text-sm font-semibold text-notion-text">Web Push & Briefings</h3>
          </div>
          <button onClick={onClose} aria-label="Close notifications" className="p-1 rounded-lg text-notion-secondary hover:bg-notion-paper">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-3.5 text-xs text-notion-text">
          <p className="text-notion-secondary leading-relaxed">
            Receive morning briefings on your device. Enable notifications separately on your computer and iPhone.
          </p>

          {isIos && !isStandalone && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-900 flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
              <span>
                <strong>iOS Notice:</strong> Apple requires adding Life Hub to your Home Screen before Safari enables Web Push notifications.
              </span>
            </div>
          )}

          {!isPushSupported && !(isIos && !isStandalone) && (
            <p className="text-notion-secondary">Open the HTTPS app in a browser that supports push notifications, such as Chrome, Edge, or Safari.</p>
          )}
          {!checking && !configured && (
            <p className="text-notion-secondary">Push notifications need to be configured on the server before this device can subscribe.</p>
          )}

          {error && (
            <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-800">
              {error}
            </div>
          )}

          {testResult && (
            <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-2.5 text-xs text-emerald-800">
              {testResult}
            </div>
          )}

          <div className="rounded-2xl bg-notion-bg p-3.5 border border-notion-borderSubtle space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-notion-text">This Device</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${subscribed ? 'bg-emerald-100 text-emerald-800' : 'bg-notion-paper text-notion-secondary'}`}>
                {checking ? 'Checking…' : subscribed ? 'Active' : 'Disabled'}
              </span>
            </div>
            <p className="text-[11px] text-notion-muted">
              Scheduled daily morning briefings run automatically at 6:00 AM (Asia/Manila time).
            </p>
          </div>

          <div className="space-y-2 pt-2">
            {subscribed ? (
              <>
                <button
                  onClick={handleSendTest}
                  disabled={loading}
                  className="w-full flex items-center justify-center space-x-1.5 rounded-xl border border-notion-border bg-notion-card py-2 text-xs font-semibold text-notion-text hover:bg-notion-paper transition-colors"
                >
                  <Send className="h-3.5 w-3.5 text-notion-blue" />
                  <span>Send Test Notification</span>
                </button>
                <button
                  onClick={handleUnsubscribe}
                  disabled={loading}
                  className="w-full flex items-center justify-center space-x-1.5 rounded-xl py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <BellOff className="h-3.5 w-3.5" />
                  <span>Disable Notifications</span>
                </button>
              </>
            ) : (
              <button
                onClick={handleSubscribe}
                disabled={loading || checking || !configured || !isPushSupported || Boolean(isIos && !isStandalone)}
                className="w-full flex items-center justify-center space-x-1.5 rounded-xl bg-notion-blue py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-notion-blueHover transition-colors disabled:opacity-50"
              >
                <Bell className="h-4 w-4" />
                <span>Enable Push Notifications</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
