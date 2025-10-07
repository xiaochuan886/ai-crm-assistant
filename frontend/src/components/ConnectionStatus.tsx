import React from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { ConnectionStatus } from '@/types';

const ConnectionStatusComponent: React.FC = () => {
  const { connectionStatus } = useWebSocket(null);

  const getStatusConfig = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return {
          text: '已连接',
          color: 'status-connected',
          textColor: 'text-green-600',
        };
      case 'connecting':
        return {
          text: '连接中...',
          color: 'status-connecting',
          textColor: 'text-yellow-600',
        };
      case 'disconnected':
        return {
          text: '连接断开',
          color: 'status-disconnected',
          textColor: 'text-red-600',
        };
      default:
        return {
          text: '未知状态',
          color: 'status-disconnected',
          textColor: 'text-gray-600',
        };
    }
  };

  const config = getStatusConfig(connectionStatus);

  return (
    <div className="flex items-center space-x-2">
      <div className={`status-indicator ${config.color}`}></div>
      <span className={`text-sm font-medium ${config.textColor}`}>
        {config.text}
      </span>
    </div>
  );
};

export { ConnectionStatusComponent as ConnectionStatus };