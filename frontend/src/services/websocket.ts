import { WebSocketMessage, ConnectionStatus } from '@/types';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Function[]> = new Map();
  private connectionStatus: ConnectionStatus = 'disconnected';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  constructor() {
    this.setupEventListeners();
  }

  // 连接WebSocket
  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 如果已存在连接或正在连接，避免重复建立
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
          console.log('WebSocket already connected/connecting');
          this.connectionStatus = this.ws.readyState === WebSocket.OPEN ? 'connected' : 'connecting';
          this.notifyConnectionStatus();
          if (this.ws.readyState === WebSocket.OPEN) {
            // 确保加入会话（幂等）
            this.joinSession(sessionId);
          }
          resolve();
          return;
        }

        this.connectionStatus = 'connecting';
        this.notifyConnectionStatus();

        const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss' : 'ws';
        const host = (typeof window !== 'undefined' ? window.location.hostname : 'localhost');
        const port = (import.meta as any)?.env?.VITE_API_PORT || '8000';
        const overrideHost = (import.meta as any)?.env?.VITE_API_HOST || host;
        const wsUrl = `${protocol}://${overrideHost}:${port}/ws/${sessionId}`;
        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.connectionStatus = 'connected';
          this.reconnectAttempts = 0;
          this.notifyConnectionStatus();
          this.joinSession(sessionId);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('Received message:', message);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.connectionStatus = 'disconnected';
          this.notifyConnectionStatus();
          this.attemptReconnect(sessionId);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.connectionStatus = 'disconnected';
          this.notifyConnectionStatus();
          reject(error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        this.connectionStatus = 'disconnected';
        this.notifyConnectionStatus();
        reject(error);
      }
    });
  }

  // 尝试重连
  private attemptReconnect(sessionId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

      this.reconnectTimeout = setTimeout(() => {
        if (this.connectionStatus === 'disconnected') {
          this.connect(sessionId).catch((error) => {
            console.error('Reconnection failed:', error);
          });
        }
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  // 加入会话
  private joinSession(sessionId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const joinMessage: WebSocketMessage = {
        type: 'join_session',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        data: {}
      };
      this.ws.send(JSON.stringify(joinMessage));
    }
  }

  // 发送消息
  sendMessage(content: string, sessionId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'message',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        data: { content }
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
      throw new Error('WebSocket not connected');
    }
  }

  // 发送打字状态
  sendTypingStatus(isTyping: boolean, sessionId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'typing',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        data: { is_typing: isTyping }
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  // 处理接收到的消息
  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'user_message':
      case 'ai_response':
      case 'error':
      case 'status_update':
        this.emit(message.type, message);
        break;
      case 'typing':
        this.emit('typing', message.data);
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  // 添加事件监听器
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  // 移除事件监听器
  off(event: string, callback: Function): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  // 触发事件
  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  // 通知连接状态变化
  private notifyConnectionStatus(): void {
    this.emit('connection_status', this.connectionStatus);
  }

  // 获取连接状态
  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  // 断开连接
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connectionStatus = 'disconnected';
      this.notifyConnectionStatus();
    }
  }

  // 设置事件监听器（用于调试）
  private setupEventListeners(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        console.log('Network online');
        if (this.connectionStatus === 'disconnected') {
          // 可以在这里实现自动重连逻辑
        }
      });

      window.addEventListener('offline', () => {
        console.log('Network offline');
        this.connectionStatus = 'disconnected';
        this.notifyConnectionStatus();
        this.disconnect();
      });
    }
  }
}

// 创建单例实例
export const websocketService = new WebSocketService();