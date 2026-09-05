import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from './hooks/useAuth';
import { useConversations } from './hooks/useConversations';
import { api } from './lib/api';
import { Agent } from './types';
import { Header } from './components/Header';
import { ConversationDrawer } from './components/ConversationDrawer';
import { ConversationTimeline } from './components/ConversationTimeline';
import { MessageComposer } from './components/MessageComposer';
import { MediaBottomSheet } from './components/MediaBottomSheet';
import { SettingsSheet } from './components/SettingsSheet';
import { LoginModal } from './components/LoginModal';
import { IosInstallGuide } from './components/IosInstallGuide';
import { PushNotificationModal } from './components/PushNotificationModal';
import { DesignKitView } from './components/DesignKitView';
import { Palette } from 'lucide-react';

export const App: React.FC = () => {
  const { session, loading: authLoading, error: authError, login, logout } = useAuth();
  const {
    conversations,
    activeId,
    messages,
    sending,
    pendingScan,
    setActiveId,
    createConversation,
    deleteConversation,
    sendMessage,
    uploadMedia,
    confirmScan,
    correctScan,
    cancelScan,
  } = useConversations();

  // Theme Management (Light mode default, with dark mode toggleable)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('life_hub_theme');
    return saved === 'dark' ? 'dark' : 'light';
  });

  // Dynamic Theme & Status Bar Synchronization (fixes top bar color mismatch)
  useEffect(() => {
    const isDark = theme === 'dark';
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Immediately synchronize iOS Safari / PWA status bar meta and canvas background
    const color = isDark ? '#090a0f' : '#f8f9fb';
    const themeMeta = document.getElementById('app-theme-color') || document.querySelector('meta[name="theme-color"]');
    if (themeMeta) {
      themeMeta.setAttribute('content', color);
    }
    document.documentElement.style.backgroundColor = color;
    document.body.style.backgroundColor = color;
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';

    localStorage.setItem('life_hub_theme', theme);

    // Synchronize custom ambient moving gradient if configured in Design Kit
    try {
      const savedGrad = localStorage.getItem('life_hub_custom_gradient');
      if (savedGrad) {
        const { gradColor1, gradColor2, gradColor3, gradSpeed, gradBlur } = JSON.parse(savedGrad);
        if (gradColor1) document.documentElement.style.setProperty('--gradient-glow-1', isDark ? `${gradColor1}40` : `${gradColor1}18`);
        if (gradColor2) document.documentElement.style.setProperty('--gradient-glow-2', isDark ? `${gradColor2}38` : `${gradColor2}14`);
        if (gradColor3) document.documentElement.style.setProperty('--gradient-glow-3', isDark ? `${gradColor3}30` : `${gradColor3}16`);
        if (gradSpeed) document.documentElement.style.setProperty('--gradient-speed', `${gradSpeed}s`);
        if (gradBlur) document.documentElement.style.setProperty('--gradient-blur', `${gradBlur}px`);
      }
    } catch {
      // Ignore parse error
    }
  }, [theme]);

  // Interactive Design Kit Studio State (?view=design-kit or hash #design-kit)
  const [isDesignKitView, setIsDesignKitView] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const params = new URLSearchParams(window.location.search);
    return params.get('view') === 'design-kit' || window.location.hash === '#design-kit';
  });

  const toggleDesignKitView = (active: boolean) => {
    setIsDesignKitView(active);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      if (active) {
        url.searchParams.set('view', 'design-kit');
      } else {
        url.searchParams.delete('view');
        if (url.hash === '#design-kit') url.hash = '';
      }
      window.history.replaceState({}, '', url.toString());
    }
  };

  const handleSendDesignKitFeedback = (feedbackText: string) => {
    toggleDesignKitView(false);
    sendMessage(feedbackText);
  };

  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'notion',
      name: 'Life Hub Notion AI',
      description: "Manages and queries Andrei's Notion workspace",
      capabilities: ['text', 'voice', 'image', 'tools', 'briefings'],
      status: 'available',
    },
  ]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('notion');

  // Drawer and Sheet States
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [mediaSheetOpen, setMediaSheetOpen] = useState(false);
  const [settingsSheetOpen, setSettingsSheetOpen] = useState(false);
  const [notifModalOpen, setNotifModalOpen] = useState(false);
  const [showInstallGuide, setShowInstallGuide] = useState(false);
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  // User Profile Photo State (persisted in localStorage)
  const [userPhoto, setUserPhoto] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('life_hub_user_avatar');
  });

  const handleUpdatePhoto = (photo: string | null) => {
    setUserPhoto(photo);
    if (photo) {
      localStorage.setItem('life_hub_user_avatar', photo);
    } else {
      localStorage.removeItem('life_hub_user_avatar');
    }
  };

  // Native input refs for media triggering
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  // Connectivity Listener
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch registered agents
  useEffect(() => {
    if (session.authenticated) {
      api.agents
        .list()
        .then((list) => {
          if (list.length > 0) setAgents(list);
        })
        .catch(() => {});
    }
  }, [session.authenticated]);

  // iOS Safari check for install banner prompt
  useEffect(() => {
    const isIos = typeof navigator !== 'undefined' && /iPhone|iPad|iPod/.test(navigator.userAgent);
    const isStandalone =
      typeof window !== 'undefined' &&
      ((window.navigator as any).standalone || window.matchMedia('(display-mode: standalone)').matches);
    const dismissed = localStorage.getItem('life_hub_install_dismissed');

    if (isIos && !isStandalone && !dismissed) {
      const timer = setTimeout(() => {
        setShowInstallGuide(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleDismissInstallGuide = () => {
    setShowInstallGuide(false);
    localStorage.setItem('life_hub_install_dismissed', 'true');
  };

  // 1. Loading screen
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-bg">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-blue border-t-transparent" />
          <span className="text-xs font-medium text-content-secondary">Loading Life Hub...</span>
        </div>
      </div>
    );
  }

  // 2. Authentication screen
  if (!session.authenticated) {
    return <LoginModal onLogin={login} error={authError} />;
  }

  // 3. Interactive Design Kit Studio
  if (isDesignKitView) {
    return (
      <DesignKitView
        onBackToChat={() => toggleDesignKitView(false)}
        onSendFeedbackToChat={handleSendDesignKitFeedback}
        activeAppTheme={theme}
        userPhoto={userPhoto}
        onUpdatePhoto={handleUpdatePhoto}
      />
    );
  }

  // 4. Main Assistant Interface (Gemini iOS Layout + Moving Blue Gradient)
  return (
    <div className="relative flex h-full flex-col bg-surface-bg text-content-primary overflow-hidden">
      {/* Ambient Moving Blue Gradient Canvas */}
      <div className="moving-gradient-canvas" aria-hidden="true" />

      {/* Floating Design Kit Quick Switch Pill */}
      <button
        onClick={() => toggleDesignKitView(true)}
        className="fixed bottom-24 right-3.5 sm:right-6 z-30 flex items-center space-x-1.5 rounded-full border border-surface-border bg-surface-card/90 px-3 py-1.5 text-xs font-semibold text-content-primary shadow-lg backdrop-blur-xl hover:bg-surface-secondary active:scale-95 transition-all"
        title="Open Interactive Design Kit Studio"
      >
        <Palette className="h-3.5 w-3.5 text-brand-blue" />
        <span>Design Kit</span>
      </button>

      {/* Gemini Minimal Top Bar */}
      <Header
        agents={agents}
        selectedAgentId={selectedAgentId}
        onSelectAgent={setSelectedAgentId}
        onNewConversation={() => createConversation()}
        onToggleDrawer={() => setDrawerOpen(true)}
        onOpenSettings={() => setSettingsSheetOpen(true)}
        isOnline={isOnline}
        userPhoto={userPhoto}
      />

      {/* Main Spacious Conversation Stream */}
      <main className="relative z-10 flex-1 overflow-hidden flex flex-col max-w-3xl w-full mx-auto">
        <ConversationTimeline
          messages={messages}
          sending={sending}
          pendingScan={pendingScan}
          onQuickAction={(prompt) => sendMessage(prompt)}
          onRetry={(content, clientMsgId) => sendMessage(content, clientMsgId)}
          onConfirmScan={confirmScan}
          onCorrectScan={correctScan}
          onCancelScan={cancelScan}
        />

        {/* Floating Pill Message Composer */}
        <MessageComposer
          onSendMessage={(content) => sendMessage(content)}
          onUploadMedia={(file, caption) => uploadMedia(file, caption)}
          onOpenMediaSheet={() => setMediaSheetOpen(true)}
          fileInputRef={fileInputRef as React.RefObject<HTMLInputElement>}
          cameraInputRef={cameraInputRef as React.RefObject<HTMLInputElement>}
          disabled={sending}
          isOnline={isOnline}
        />
      </main>

      {/* Slide-over Conversation Drawer (Gemini iOS Style) */}
      <ConversationDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => setActiveId(id)}
        onNew={() => createConversation()}
        onDelete={(id) => deleteConversation(id)}
        onOpenSettings={() => setSettingsSheetOpen(true)}
      />

      {/* iOS Media Bottom Sheet for [+] */}
      <MediaBottomSheet
        isOpen={mediaSheetOpen}
        onClose={() => setMediaSheetOpen(false)}
        onSelectPhoto={() => fileInputRef.current?.click()}
        onSelectCamera={() => cameraInputRef.current?.click()}
        onSelectFile={() => fileInputRef.current?.click()}
        onQuickAction={(prompt) => sendMessage(prompt)}
      />

      {/* iOS Settings Sheet (Image 2) */}
      <SettingsSheet
        isOpen={settingsSheetOpen}
        onClose={() => setSettingsSheetOpen(false)}
        theme={theme}
        onToggleTheme={(t) => setTheme(t)}
        onOpenNotifications={() => setNotifModalOpen(true)}
        onOpenDesignKit={() => toggleDesignKitView(true)}
        onLogout={logout}
        userPhoto={userPhoto}
        onUpdatePhoto={handleUpdatePhoto}
      />

      {/* Modals */}
      <PushNotificationModal
        isOpen={notifModalOpen}
        onClose={() => setNotifModalOpen(false)}
        vapidPublicKey={session.vapid_public_key}
      />

      <IosInstallGuide
        isOpen={showInstallGuide}
        onClose={handleDismissInstallGuide}
      />
    </div>
  );
};
