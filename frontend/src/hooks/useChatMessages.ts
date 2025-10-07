import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ChatMessage } from '@/types';
import { apiService } from '@/services/api';
import { useWebSocketMessage } from './useWebSocket';

export const useChatMessages = (sessionId: string) => {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // 获取聊天历史
  const {
    data: history = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: () => apiService.getChatHistory(sessionId),
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  // 发送消息的mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        content,
        type: 'user',
        timestamp: new Date().toISOString(),
        status: 'sending',
      };

      // 先添加到本地状态
      setMessages(prev => [...prev, userMessage]);

      try {
        // 发送到API
        const response = await apiService.sendAIMessage(sessionId, content);

        // 更新用户消息状态为已发送
        setMessages(prev =>
          prev.map(msg =>
            msg.id === userMessage.id
              ? { ...msg, status: 'sent' as const }
              : msg
          )
        );

        return response;
      } catch (error) {
        // 更新用户消息状态为失败
        setMessages(prev =>
          prev.map(msg =>
            msg.id === userMessage.id
              ? { ...msg, status: 'failed' as const }
              : msg
          )
        );
        throw error;
      }
    },
    onSuccess: () => {
      // 发送成功后，可能需要刷新聊天历史
      queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] });
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
    },
  });

  // 监听WebSocket消息
  useWebSocketMessage('ai_response', (message) => {
    if (message.session_id === sessionId && message.data.content) {
      const aiMessage: ChatMessage = {
        id: `ai_${Date.now()}`,
        content: message.data.content,
        type: 'ai',
        timestamp: message.timestamp,
      };

      setMessages(prev => [...prev, aiMessage]);
    }
  }, [sessionId]);

  useWebSocketMessage('user_message', (message) => {
    if (message.session_id === sessionId && message.data.content) {
      // 确保用户消息在状态中（可能是其他标签页发送的）
      const existingMessage = messages.find(
        msg => msg.content === message.data.content && msg.type === 'user'
      );

      if (!existingMessage) {
        const userMessage: ChatMessage = {
          id: `user_${Date.now()}`,
          content: message.data.content,
          type: 'user',
          timestamp: message.timestamp,
          status: 'sent',
        };

        setMessages(prev => [...prev, userMessage]);
      }
    }
  }, [sessionId, messages]);

  // 监听错误消息
  useWebSocketMessage('error', (message) => {
    if (message.session_id === sessionId && message.data.error) {
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content: `错误: ${message.data.error}`,
        type: 'ai',
        timestamp: message.timestamp,
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  }, [sessionId]);

  // 初始化时加载历史消息
  useEffect(() => {
    if (history.length > 0) {
      const formattedHistory: ChatMessage[] = history.map((item: any) => ({
        id: item.id || `history_${item.timestamp}`,
        content: item.content,
        type: item.type,
        timestamp: item.timestamp,
      }));

      setMessages(formattedHistory);
    }
  }, [history]);

  // 发送消息的函数
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) {
      return;
    }

    try {
      await sendMessageMutation.mutateAsync(content.trim());
    } catch (error) {
      console.error('Failed to send message:', error);
      // 这里可以添加错误提示
    }
  }, [sendMessageMutation]);

  // 重发消息的函数
  const resendMessage = useCallback(async (messageId: string) => {
    const message = messages.find(msg => msg.id === messageId);
    if (message && message.type === 'user') {
      // 移除失败的消息
      setMessages(prev => prev.filter(msg => msg.id !== messageId));
      // 重新发送
      await sendMessage(message.content);
    }
  }, [messages, sendMessage]);

  // 清除消息的函数
  const clearMessages = useCallback(() => {
    setMessages([]);
    queryClient.setQueryData(['chatHistory', sessionId], []);
  }, [sessionId, queryClient]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    resendMessage,
    clearMessages,
    isSending: sendMessageMutation.isPending,
  };
};