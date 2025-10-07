import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '@/types';

export class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.NODE_ENV === 'development'
        ? 'http://localhost:8000/api'
        : '/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  // 设置请求拦截器
  private setupInterceptors(): void {
    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        // 可以在这里添加token等认证信息
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        console.log('API Request:', config);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        console.log('API Response:', response);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);

        // 统一错误处理
        if (error.response) {
          // 服务器响应错误
          const { status } = error.response;
          switch (status) {
            case 401:
              // 未授权，跳转到登录页
              this.handleUnauthorized();
              break;
            case 403:
              // 权限不足
              console.error('Permission denied');
              break;
            case 404:
              // 资源不存在
              console.error('Resource not found');
              break;
            case 500:
              // 服务器错误
              console.error('Server error');
              break;
            default:
              console.error('HTTP Error:', status);
          }
        } else if (error.request) {
          // 请求发送失败
          console.error('Network Error:', error.message);
        } else {
          // 其他错误
          console.error('Error:', error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  // 处理未授权错误
  private handleUnauthorized(): void {
    // 清除本地存储的token
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // 可以在这里跳转到登录页
    // window.location.href = '/login';
  }

  // 通用GET请求
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.get<T>(url, config);
    return response.data as T;
  }

  // 通用POST请求
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.post<T>(url, data, config);
    return response.data as T;
  }

  // 通用PUT请求
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.put<T>(url, data, config);
    return response.data as T;
  }

  // 通用DELETE请求
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.delete<T>(url, config);
    return response.data as T;
  }

  // 创建会话
  async createSession(userId?: string): Promise<{ session_id: string }> {
    return this.post('/sessions/create', { user_id: userId });
  }

  // 获取会话信息
  async getSession(sessionId: string): Promise<any> {
    return this.get(`/sessions/${sessionId}`);
  }

  // 发送AI消息
  async sendAIMessage(sessionId: string, message: string): Promise<any> {
    return this.post('/chat/message', {
      session_id: sessionId,
      message: message,
    });
  }

  // 获取聊天历史
  async getChatHistory(sessionId: string): Promise<any[]> {
    return this.get(`/chat/history/${sessionId}`);
  }

  // CRM操作 - 创建客户
  async createCustomer(customerData: any): Promise<any> {
    return this.post('/crm/customer', customerData);
  }

  // CRM操作 - 搜索客户
  async searchCustomer(query: string): Promise<any[]> {
    return this.get(`/crm/customers/search`, { params: { q: query } });
  }

  // CRM操作 - 创建销售线索
  async createLead(leadData: any): Promise<any> {
    return this.post('/crm/lead', leadData);
  }

  // 健康检查
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }

  // 获取API状态
  async getApiStatus(): Promise<any> {
    return this.get('/status');
  }
}

// 创建单例实例
export const apiService = new ApiService();