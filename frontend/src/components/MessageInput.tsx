import React, { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { MessageInputProps } from '@/types';

export const MessageInput: React.FC<MessageInputProps> = ({ sessionId, onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, sendTypingStatus, connectionStatus } = useWebSocket(sessionId);

  // 自动调整文本框高度
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  // 发送消息
  const handleSend = async () => {
    if (!message.trim() || connectionStatus !== 'connected') {
      return;
    }

    try {
      await sendMessage(message.trim());
      setMessage('');
      onSendMessage();
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  // 处理输入变化
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // 发送打字状态
    if (e.target.value.trim()) {
      sendTypingStatus(true);
    } else {
      sendTypingStatus(false);
    }
  };

  // 处理焦点事件
  const handleBlur = () => {
    sendTypingStatus(false);
  };

  const isConnected = connectionStatus === 'connected';
  const placeholder = isConnected ? '输入消息...' : '正在连接...';
  const buttonDisabled = !message.trim() || !isConnected;

  return (
    <div className="flex items-end space-x-3">
      {/* 文本输入框 */}
      <div className="flex-1">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          placeholder={placeholder}
          disabled={!isConnected}
          className="chat-input"
          rows={1}
          style={{
            minHeight: '48px',
            maxHeight: '120px',
            resize: 'none',
          }}
        />
      </div>

      {/* 发送按钮 */}
      <button
        onClick={handleSend}
        disabled={buttonDisabled}
        className={`
          btn-primary px-4 py-3
          ${buttonDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary-600'}
          transition-all duration-200
          flex items-center justify-center
          min-w-[48px] h-[48px]
        `}
        title="发送消息 (Enter)"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>

      {/* 连接状态指示 */}
      {!isConnected && (
        <div className="text-sm text-red-500 mr-2">
          连接断开
        </div>
      )}
    </div>
  );
};