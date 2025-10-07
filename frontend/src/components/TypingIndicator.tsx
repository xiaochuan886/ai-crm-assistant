import React from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { TypingIndicatorProps } from '@/types';

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ sessionId }) => {
  const { isTyping } = useWebSocket(sessionId);

  if (!isTyping) {
    return null;
  }

  return (
    <div className="px-4 py-2">
      <div className="flex items-center space-x-2">
        <div className="message-bubble message-ai">
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
        <span className="text-sm text-gray-500">AI助手正在输入...</span>
      </div>
    </div>
  );
};