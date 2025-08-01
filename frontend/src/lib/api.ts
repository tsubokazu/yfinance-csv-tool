import axios, { AxiosInstance, AxiosError } from 'axios';
import { AuthResponse, LoginRequest, RegisterRequest, User, UserProfile } from '@/types/auth';
import { TradingData, AIDecisionResult, BacktestResult } from '@/types/trading';
import { HealthResponse, WebSocketStatus } from '@/types/api';

class APIClient {
  private instance: AxiosInstance;

  constructor() {
    this.instance = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1', // プロキシ経由
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.instance.interceptors.request.use((config) => {
      const token = this.getToken();
      console.log('API Request Interceptor:', {
        url: config.url,
        hasToken: !!token,
        tokenPrefix: token ? token.substring(0, 20) + '...' : 'None'
      });
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.instance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.log('API Response Error:', {
          status: error.response?.status,
          data: error.response?.data,
          url: error.config?.url
        });
        
        if (error.response?.status === 401) {
          console.log('401 Unauthorized - Clearing token and redirecting');
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    // Supabaseトークンを使用
    return localStorage.getItem('auth-token');
  }

  private setToken(token: string): void {
    localStorage.setItem('auth-token', token);
  }

  private clearToken(): void {
    localStorage.removeItem('auth-token');
  }

  // Auth endpoints
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.instance.post<any>('/auth/register', data);
    this.setToken(response.data.access_token);
    return {
      user: response.data.user,
      session: {
        access_token: response.data.access_token,
        refresh_token: '', // バックエンドから提供されていない
        expires_in: 3600,
        token_type: response.data.token_type,
        user: response.data.user
      }
    };
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.instance.post<any>('/auth/login', data);
    // バックエンドから返されたSupabaseアクセストークンを保存
    this.setToken(response.data.access_token);
    return {
      user: response.data.user,
      session: {
        access_token: response.data.access_token,
        refresh_token: '', // バックエンドから提供されていない
        expires_in: 3600,
        token_type: response.data.token_type,
        user: response.data.user
      }
    };
  }

  async getCurrentUser(): Promise<{ user: User; profile?: UserProfile }> {
    const response = await this.instance.get<User>('/auth/me');
    return { user: response.data };
  }

  async logout(): Promise<void> {
    try {
      await this.instance.post('/auth/logout');
    } finally {
      this.clearToken();
    }
  }

  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response = await this.instance.get<HealthResponse>('/health');
    return response.data;
  }

  // WebSocket status
  async getWebSocketStatus(): Promise<WebSocketStatus> {
    const response = await this.instance.get<WebSocketStatus>('/ws/websocket/status');
    return response.data;
  }

  // Trading endpoints
  async getTradingDecision(symbol: string, timestamp: string): Promise<TradingData> {
    const response = await this.instance.post<TradingData>('/trading/decision', {
      symbol,
      timestamp,
    });
    return response.data;
  }

  async getAIDecision(symbol: string, timestamp: string): Promise<AIDecisionResult> {
    const response = await this.instance.post<AIDecisionResult>('/trading/ai-decision', {
      symbol,
      timestamp,
    });
    return response.data;
  }

  async runBacktest(
    symbol: string,
    startTime: string,
    endTime: string,
    intervalMinutes: number
  ): Promise<{ results: BacktestResult[] }> {
    const response = await this.instance.post<{ results: BacktestResult[] }>('/trading/ai-backtest', {
      symbol,
      start_time: startTime,
      end_time: endTime,
      interval_minutes: intervalMinutes,
    });
    return response.data;
  }

  async getHistoricalData(
    symbol: string,
    period: string = '1mo',
    interval: string = '1d'
  ): Promise<{
    symbol: string;
    period: string;
    interval: string;
    data_points: number;
    chart_data: Array<{
      timestamp: string;
      date: string;
      time: string;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
    }>;
    user_authenticated: boolean;
  }> {
    const response = await this.instance.post('/trading/historical', {
      symbol,
      period,
      interval,
    });
    return response.data;
  }
}

export const apiClient = new APIClient();