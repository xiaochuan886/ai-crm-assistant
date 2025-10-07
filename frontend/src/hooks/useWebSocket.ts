import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService } from '@/services/websocket';
import { ConnectionStatus, WebSocketMessage } from '@/types';

export const useWebSocket = (sessionId: string | null) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [isTyping, setIsTyping] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // 连接WebSocket
  const connect = useCallback(async () => {
    if (!sessionId) {
      console.warn('No session ID provided for WebSocket connection');
      return;
    }

    try {
      await websocketService.connect(sessionId);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);

      // 自动重连逻辑
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        connect();
      }, 3000);
    }
  }, [sessionId]);

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    websocketService.disconnect();
  }, []);

  // 发送消息
  const sendMessage = useCallback((content: string) => {
    if (!sessionId) {
      throw new Error('No session ID available');
    }
    websocketService.sendMessage(content, sessionId);
  }, [sessionId]);

  // 发送打字状态
  const sendTypingStatus = useCallback((isTyping: boolean) => {
    if (!sessionId) {
      return;
    }
    websocketService.sendTypingStatus(isTyping, sessionId);
  }, [sessionId]);

  // 监听连接状态变化
  useEffect(() => {
    const handleConnectionStatus = (status: ConnectionStatus) => {
      setConnectionStatus(status);
    };

    websocketService.on('connection_status', handleConnectionStatus);

    return () => {
      websocketService.off('connection_status', handleConnectionStatus);
    };
  }, []);

  // 监听打字指示器
  useEffect(() => {
    const handleTyping = (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping);
    };

    websocketService.on('typing', handleTyping);

    return () => {
      websocketService.off('typing', handleTyping);
    };
  }, []);

  // 自动连接（不在卸载时全局断开，避免多组件互相影响）
  useEffect(() => {
    if (sessionId) {
      connect();
    }
    return () => {
      // 仅清理本 Hook 的副作用，不主动断开全局连接
    };
  }, [sessionId, connect]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    connectionStatus,
    isTyping,
    connect,
    disconnect,
    sendMessage,
    sendTypingStatus,
  };
};

// 监听特定WebSocket消息的hook
export const useWebSocketMessage = (
  messageType: string,
  callback: (message: WebSocketMessage) => void,
  deps: React.DependencyList = []
) => {
  useEffect(() => {
    const handleMessage = (message: WebSocketMessage) => {
      if (message.type === messageType) {
        callback(message);
      }
    };

    websocketService.on(messageType, handleMessage);

    return () => {
      websocketService.off(messageType, handleMessage);
    };
  }, deps);
};