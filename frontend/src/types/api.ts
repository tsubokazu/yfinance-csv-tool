export interface APIError {
  detail: string;
  code?: string;
  type?: string;
}

export interface APIResponse<T = any> {
  data?: T;
  error?: APIError;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface WebSocketStatus {
  timestamp: string;
  active_connections: number;
  authenticated_users: number;
  streaming_symbols: string[];
  is_streaming: boolean;
  data_router_status: {
    timestamp: string;
    market_hours: boolean;
    sources: {
      yfinance: {
        available: boolean;
        type: string;
        delay_minutes: number;
      };
      tachibana: {
        available: boolean;
        type: string;
        delay_minutes?: number;
      };
    };
    recommended_source: string;
  };
}