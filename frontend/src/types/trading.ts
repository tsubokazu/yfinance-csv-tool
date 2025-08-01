export interface TechnicalIndicators {
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger: {
    upper: number;
    middle: number;
    lower: number;
  };
  sma_20: number;
  ema_12: number;
  ema_26: number;
}

export interface MarketContext {
  volume: number;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
}

export interface TradingData {
  symbol: string;
  current_price: number;
  price_change?: number;
  price_change_percent?: number;
  volume?: number;
  technical_indicators: TechnicalIndicators;
  market_data: MarketContext;
  timestamp: string;
}

export interface AIDecisionResult {
  symbol: string;
  decision: "BUY" | "SELL" | "HOLD";
  confidence: number;
  strategy: string;
  reasoning: string;
  entry_conditions: string[];
  timestamp: string;
}

export interface BacktestResult {
  timestamp: string;
  symbol: string;
  price: number;
  decision: "BUY" | "SELL" | "HOLD";
  confidence: number;
  pnl?: number;
  cumulative_pnl?: number;
}

export interface PriceUpdate {
  type: "price_update";
  symbol: string;
  current_price: number;
  price_change: number;
  price_change_percent: number;
  timestamp: string;
}

export interface WebSocketMessage {
  type: "subscribe" | "ai_decision_request" | "price_update" | "ai_decision_result" | "price_update_error" | "connection_established";
  symbol?: string;
  decision_data?: AIDecisionResult;
  error?: string;
  [key: string]: any;
}