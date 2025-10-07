import React from 'react';
import { useChatMessages } from '@/hooks/useChatMessages';
import { MessageBubble } from './MessageBubble';
import { MessageListProps } from '@/types';

export const MessageList: React.FC<MessageListProps> = ({ sessionId }) => {
  const { messages, isLoading, error, resendMessage } = useChatMessages(sessionId);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-2"></div>
          <p>加载聊天记录...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-600 mb-2">加载消息失败</p>
          <button
            onClick={() => window.location.reload()}
            className="text-primary-600 hover:text-primary-700 text-sm"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">开始对话</h3>
          <p className="text-gray-500 text-sm">
            你好！我是AI CRM助手，可以帮助你管理客户、销售线索等。有什么可以帮助你的吗？
          </p>
          <div className="mt-4 space-y-2">
            <div className="bg-gray-50 rounded-lg p-3 text-left">
              <p className="text-sm text-gray-700 mb-1">💡 试试说：</p>
              <div className="space-y-1 text-xs text-gray-600">
                <p>• 创建一个新客户</p>
                <p>• 查找客户信息</p>
                <p>• 创建销售线索</p>
                <p>• 今天的日程安排</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onResend={message.status === 'failed' ? resendMessage : undefined}
        />
      ))}
    </div>
  );
};