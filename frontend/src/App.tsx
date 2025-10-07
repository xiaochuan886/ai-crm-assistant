import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChatInterface } from '@/components/ChatInterface';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { LoadingScreen } from '@/components/LoadingScreen';
import { apiService } from '@/services/api';
import { SessionInfo } from '@/types';

function App() {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // 创建或获取会话
  const {
    data: session,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['session'],
    queryFn: async () => {
      console.log('Starting session creation...');

      // 尝试从localStorage获取现有会话
      const existingSessionId = localStorage.getItem('crm_session_id');
      console.log('Existing session ID:', existingSessionId);

      if (existingSessionId) {
        try {
          console.log('Trying to get existing session:', existingSessionId);
          const session = await apiService.getSession(existingSessionId);
          console.log('Got existing session:', session);
          return session;
        } catch (error) {
          console.warn('Failed to get existing session, creating new one:', error);
          localStorage.removeItem('crm_session_id');
        }
      }

      // 创建新会话
      console.log('Creating new session...');
      const newSession = await apiService.createSession();
      console.log('Created new session:', newSession);
      localStorage.setItem('crm_session_id', newSession.session_id);
      return newSession;
    },
    retry: 1,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });

  useEffect(() => {
    console.log('Session changed:', session);
    if (session) {
      const sessionInfo = {
        id: session.session_id,
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
      };
      console.log('Setting session info:', sessionInfo);
      setSessionInfo(sessionInfo);
      setIsInitializing(false);
    }
  }, [session]);

  // 处理重试
  const handleRetry = () => {
    refetch();
  };

  // 处理重新连接
  const handleReconnect = () => {
    localStorage.removeItem('crm_session_id');
    refetch();
  };

  // 如果正在加载，显示加载屏幕
  if (isLoading || isInitializing) {
    return <LoadingScreen />;
  }

  // 如果有错误，显示错误屏幕
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">连接失败</h2>
          <p className="text-gray-600 mb-6">
            无法连接到AI CRM助手服务。请检查网络连接或稍后重试。
          </p>
          <div className="space-y-3">
            <button
              onClick={handleRetry}
              className="w-full btn-primary"
            >
              重试连接
            </button>
            <button
              onClick={handleReconnect}
              className="w-full btn-secondary"
            >
              重新开始
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 主应用界面
  if (!sessionInfo?.id) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 头部 */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">AI CRM助手</h1>
              <p className="text-sm text-gray-500">智能客户管理助手</p>
            </div>
          </div>
          <ConnectionStatus />
        </div>
      </header>

      {/* 主要内容 */}
      <main className="flex-1 flex flex-col">
        <ChatInterface sessionId={sessionInfo.id} />
      </main>
    </div>
  );
}

export default App;