import React from 'react';
import { MessageBubbleProps } from '@/types';

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onResend }) => {
  const isUser = message.type === 'user';
  const isFailed = message.status === 'failed';
  const isSending = message.status === 'sending';

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } else {
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`message-bubble ${isUser ? 'message-user' : 'message-ai'} ${
        isFailed ? 'bg-red-100 border-red-300 text-red-800' : ''
      }`}>
        {/* 消息内容 */}
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* 消息状态和时间 */}
        <div className={`flex items-center space-x-2 mt-1 text-xs ${
          isUser ? 'text-primary-100' : 'text-gray-500'
        }`}>
          <span>{formatTime(message.timestamp)}</span>

          {/* 用户消息状态指示器 */}
          {isUser && (
            <div className="flex items-center space-x-1">
              {isSending && (
                <div className="animate-spin rounded-full h-3 w-3 border border-current border-t-transparent"></div>
              )}
              {isFailed && (
                <button
                  onClick={() => onResend?.(message.id)}
                  className="hover:text-red-600 transition-colors"
                  title="重新发送"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              )}
              {!isSending && !isFailed && (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};