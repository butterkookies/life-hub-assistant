import React, { useEffect, useState } from 'react';
import { useAuth } from './hooks/useAuth';
import { useConversations } from './hooks/useConversations';
import { api } from './lib/api';
import { Agent } from './types';
import { Header } from './components/Header';
import { ConversationDrawer } from './components/ConversationDrawer';
import { ConversationTimeline } from './components/ConversationTimeline';
import { MessageComposer } from './components/MessageComposer';
import { LoginModal } from './components/LoginModal';
import { IosInstallGuide } from './components/IosInstallGuide';
import { PushNotificationModal } from './components/PushNotificationModal';

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

  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'notion',
      name: 'Life Hub Assistant',
      description: "Manages and queries Andrei's Notion workspace",
      capabilities: ['text', 'voice', 'image', 'tools', 'briefings'],
      status: 'available',
    },
  ]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('notion');

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifModalOpen, setNotifModalOpen] = useState(false);
  const [showInstallGuide, setShowInstallGuide] = useState(false);
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

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
      api.agents.list().then((list) => {
        if (list.length > 0) setAgents(list);
      }).catch(() => {});
    }
  }, [session.authenticated]);

  // iOS Safari check for install banner prompt
  useEffect(() => {
    const isIos = typeof navigator !== 'undefined' && /iPhone|iPad|iPod/.test(navigator.userAgent);
    const isStandalone = typeof window !== 'undefined' && ((window.navigator as any).standalone || window.matchMedia('(display-mode: standalone)').matches);
    const dismissed = localStorage.getItem('life_hub_install_dismissed');

    if (isIos && !isStandalone && !dismissed) {
      // Prompt install guide after 2 seconds
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
      <div className="flex min-h-screen items-center justify-center bg-notion-bg">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-notion-blue border-t-transparent" />
          <span className="text-xs font-medium text-notion-secondary">Loading Life Hub...</span>
        </div>
      </div>
    );
  }

  // 2. Authentication screen
  if (!session.authenticated) {
    return <LoginModal onLogin={login} error={authError} />;
  }

  // 3. Main Assistant Interface
  return (
    <div className="flex h-full flex-col bg-notion-bg text-notion-text overflow-hidden">
      {/* Header */}
      <Header
        agents={agents}
        selectedAgentId={selectedAgentId}
        onSelectAgent={setSelectedAgentId}
        onNewConversation={() => createConversation()}
        onToggleDrawer={() => setDrawerOpen(true)}
        onOpenNotifications={() => setNotifModalOpen(true)}
        onLogout={logout}
        isOnline={isOnline}
      />

      {/* Main Conversation Stream */}
      <main className="flex-1 overflow-hidden flex flex-col max-w-3xl w-full mx-auto">
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

        {/* Sticky Message Composer */}
        <MessageComposer
          onSendMessage={(content) => sendMessage(content)}
          onUploadMedia={(file, caption) => uploadMedia(file, caption)}
          disabled={sending}
          isOnline={isOnline}
        />
      </main>

      {/* Slide-over Conversation Drawer */}
      <ConversationDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => setActiveId(id)}
        onNew={() => createConversation()}
        onDelete={(id) => deleteConversation(id)}
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
