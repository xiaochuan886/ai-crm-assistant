// WebSocket消息类型
export interface WebSocketMessage {
  type:
    | 'user_message'
    | 'ai_response'
    | 'status_update'
    | 'error'
    | 'typing'
    | 'message'
    | 'join_session';
  timestamp: string;
  session_id: string;
  data: {
    content?: string;
    action?: string;
    result?: any;
    error?: string;
    isTyping?: boolean;
    // 前端发送到后端时使用的下划线命名（后端期望字段）
    is_typing?: boolean;
  };
}

// 聊天消息类型
export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'ai';
  timestamp: string;
  isTyping?: boolean;
  status?: 'sending' | 'sent' | 'failed';
}

// WebSocket连接状态
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

// CRM操作类型
export interface CRMOperation {
  action: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
}

// 会话信息
export interface SessionInfo {
  id: string;
  userId?: string;
  createdAt: string;
  lastActivity: string;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 用户设置
export interface UserSettings {
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  notifications: boolean;
}

// 组件Props类型
export interface ChatInterfaceProps {
  sessionId: string;
}

export interface MessageListProps {
  sessionId: string;
}

export interface MessageInputProps {
  sessionId: string;
  onSendMessage: () => void;
}

export interface TypingIndicatorProps {
  sessionId: string;
}

export interface MessageBubbleProps {
  message: ChatMessage;
  onResend?: (messageId: string) => void;
}