import { useEffect, useState, useCallback } from 'react';
import { api, ApiError } from '../lib/api';
import { ConversationSummary, Message, PendingScan } from '../types';

export function useConversations(enabled = true) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingScan, setPendingScan] = useState<PendingScan | null>(null);

  // Load conversations list
  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      const list = await api.conversations.list();
      setConversations(list);
      if (list.length > 0 && !activeId) {
        setActiveId(list[0].id);
      }
    } catch (err: any) {
      setError('Could not load conversations.');
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    if (enabled) {
      void loadConversations();
    } else {
      setConversations([]);
      setActiveId(null);
      setMessages([]);
      setPendingScan(null);
    }
  }, [enabled, loadConversations]);

  // Load active conversation messages
  const loadActiveMessages = useCallback(async (convId: string) => {
    try {
      setLoading(true);
      setError(null);
      const detail = await api.conversations.get(convId);
      setMessages(detail.messages);
    } catch (err: any) {
      setError('Could not load message history.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeId) {
      loadActiveMessages(activeId);
    } else {
      setMessages([]);
    }
  }, [activeId, loadActiveMessages]);

  const createConversation = async (title?: string) => {
    try {
      const conv = await api.conversations.create('notion', title);
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      setMessages([]);
      setPendingScan(null);
      return conv;
    } catch (err: any) {
      setError('Failed to create conversation.');
      return null;
    }
  };

  const deleteConversation = async (id: string) => {
    try {
      await api.conversations.delete(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) {
        const remaining = conversations.filter((c) => c.id !== id);
        if (remaining.length > 0) {
          setActiveId(remaining[0].id);
        } else {
          setActiveId(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      setError('Failed to delete conversation.');
    }
  };

  const sendMessage = async (content: string, retryClientMsgId?: string) => {
    if (!content.trim()) return;

    let targetConvId = activeId;
    if (!targetConvId) {
      const newConv = await createConversation();
      if (!newConv) return;
      targetConvId = newConv.id;
    }

    const clientMsgId = retryClientMsgId || `client-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

    // Optimistic User Message
    const optimisticMsg: Message = {
      id: `temp-${clientMsgId}`,
      conversation_id: targetConvId,
      role: 'user',
      content,
      status: 'completed',
      client_message_id: clientMsgId,
      attachments: [],
      created_at: new Date().toISOString(),
    };

    if (!retryClientMsgId) {
      setMessages((prev) => [...prev, optimisticMsg]);
    }

    setSending(true);
    setError(null);

    try {
      const reply = await api.messages.send(targetConvId, content, clientMsgId);
      setMessages((prev) => [...prev, reply]);
      // Refresh list to update message count / updated_at
      api.conversations.list().then(setConversations).catch(() => {});
    } catch (err: any) {
      const errMsg = err instanceof ApiError ? err.message : 'Failed to send message. Please retry.';
      setError(errMsg);
      // Append failed assistant bubble with retry option
      const failedReply: Message = {
        id: `failed-${Date.now()}`,
        conversation_id: targetConvId,
        role: 'assistant',
        content: `⚠️ ${errMsg}`,
        status: 'failed',
        error_message: errMsg,
        attachments: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, failedReply]);
    } finally {
      setSending(false);
    }
  };

  const uploadMedia = async (file: File, caption?: string) => {
    let targetConvId = activeId;
    if (!targetConvId) {
      const newConv = await createConversation();
      if (!newConv) return;
      targetConvId = newConv.id;
    }

    setSending(true);
    setError(null);

    try {
      const res = await api.media.upload(targetConvId, file, undefined, caption);
      if (res.type === 'voice' && res.message) {
        const assistantVoiceMsg = res.message;
        setMessages((prev) => [
          ...prev,
          {
            id: `temp-voice-${Date.now()}`,
            conversation_id: targetConvId!,
            role: 'user',
            content: '🎙️ [Voice note]',
            status: 'completed',
            attachments: [],
            created_at: new Date().toISOString(),
          },
          assistantVoiceMsg,
        ]);
      } else if (res.type === 'image') {
        if (res.action === 'saved' && res.message) {
          const imageMsg = res.message;
          setMessages((prev) => [...prev, imageMsg]);
        } else if (res.action === 'requires_confirmation' || res.action === 'conflict') {
          if (res.scan) {
            setPendingScan(res.scan);
          }
        } else if (res.message) {
          const generalImgMsg = res.message;
          setMessages((prev) => [...prev, generalImgMsg]);
        }
      }

      api.conversations.list().then(setConversations).catch(() => {});
    } catch (err: any) {
      const errMsg = err instanceof ApiError ? err.message : 'Media upload failed.';
      setError(errMsg);
    } finally {
      setSending(false);
    }
  };

  const confirmScan = async (token: string) => {
    setSending(true);
    setError(null);
    try {
      const res = await api.imageScans.confirm(token);
      setPendingScan(null);
      const scan = res.scan || {};
      const confirmationMsg: Message = {
        id: `scan-confirmed-${Date.now()}`,
        conversation_id: activeId || '',
        role: 'assistant',
        content: `✅ **Workout Saved to Notion**\n- Date: \`${scan.date || 'Today'}\`\n- Duration: \`${scan.duration_minutes} min\`\n- Distance: \`${scan.distance_km} km\`\n- Steps: \`${scan.steps}\`\n- Calories: \`${scan.calories_kcal} kcal\``,
        status: 'completed',
        attachments: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, confirmationMsg]);
    } catch (err: any) {
      setError(err.message || 'Could not confirm workout save.');
    } finally {
      setSending(false);
    }
  };

  const correctScan = async (token: string, text: string) => {
    setSending(true);
    setError(null);
    try {
      const updated = await api.imageScans.correct(token, text);
      setPendingScan(updated);
    } catch (err: any) {
      setError(err.message || 'Could not apply correction.');
    } finally {
      setSending(false);
    }
  };

  const cancelScan = async (token: string) => {
    try {
      await api.imageScans.cancel(token);
      setPendingScan(null);
    } catch {
      setPendingScan(null);
    }
  };

  return {
    conversations,
    activeId,
    messages,
    loading,
    sending,
    error,
    pendingScan,
    setActiveId,
    createConversation,
    deleteConversation,
    sendMessage,
    uploadMedia,
    confirmScan,
    correctScan,
    cancelScan,
    refreshConversations: loadConversations,
  };
}
