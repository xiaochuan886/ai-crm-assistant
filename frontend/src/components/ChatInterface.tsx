import React, { useRef, useEffect } from 'react';
import { ChatInterfaceProps } from '@/types';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* 聊天消息列表 */}
      <div className="flex-1 overflow-y-auto">
        <MessageList sessionId={sessionId} />
        <div ref={messagesEndRef} />
      </div>

      {/* 打字指示器 */}
      <TypingIndicator sessionId={sessionId} />

      {/* 消息输入框 */}
      <div className="border-t border-gray-200 bg-gray-50 p-4">
        <MessageInput sessionId={sessionId} onSendMessage={() => {
          // 消息发送后滚动到底部
          setTimeout(scrollToBottom, 100);
        }} />
      </div>
    </div>
  );
};