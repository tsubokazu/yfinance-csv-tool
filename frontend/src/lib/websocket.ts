import { WebSocketMessage, PriceUpdate, AIDecisionResult } from '@/types/trading';

export type WebSocketEventCallback = (data: any) => void;
export type WebSocketErrorCallback = (error: Event) => void;
export type WebSocketStatusCallback = (connected: boolean) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private authenticated: boolean = false;
  private subscriptions: Set<string> = new Set();
  private eventHandlers: Map<string, WebSocketEventCallback[]> = new Map();
  private onStatusChange?: WebSocketStatusCallback;
  private onError?: WebSocketErrorCallback;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(authenticated = false) {
    this.authenticated = authenticated;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.getWebSocketUrl();
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.onStatusChange?.(true);
          
          // Re-subscribe to previous subscriptions
          this.subscriptions.forEach(symbol => {
            this.subscribeToSymbol(symbol);
          });
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.onStatusChange?.(false);
          this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.onError?.(error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.subscriptions.clear();
    this.eventHandlers.clear();
  }

  private getWebSocketUrl(): string {
    const baseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000/api/v1/ws';
    const endpoint = this.authenticated ? '/live/authenticated' : '/live';
    
    if (this.authenticated) {
      const token = localStorage.getItem('access_token');
      return `${baseUrl}${endpoint}?token=${token}`;
    }
    
    return `${baseUrl}${endpoint}`;
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data) as WebSocketMessage;
      
      switch (message.type) {
        case 'price_update':
          this.emitEvent('price_update', message as PriceUpdate);
          this.emitEvent(`price_update:${message.symbol}`, message as PriceUpdate);
          break;
        case 'ai_decision_result':
          this.emitEvent('ai_decision_result', message.decision_data);
          this.emitEvent(`ai_decision_result:${message.symbol}`, message.decision_data);
          break;
        default:
          this.emitEvent('message', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private emitEvent(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.forEach(handler => handler(data));
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectTimer = setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts + 1})`);
      this.reconnectAttempts++;
      this.connect().catch(console.error);
    }, delay);
  }

  subscribeToSymbol(symbol: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return;
    }

    this.subscriptions.add(symbol);
    const message: WebSocketMessage = {
      type: 'subscribe',
      symbol,
    };

    this.ws.send(JSON.stringify(message));
  }

  unsubscribeFromSymbol(symbol: string): void {
    this.subscriptions.delete(symbol);
    // Note: Backend might not support unsubscribe, but we remove from local subscriptions
  }

  requestAIDecision(symbol: string): void {
    if (!this.authenticated) {
      console.warn('AI decision requests require authentication');
      return;
    }

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return;
    }

    const message: WebSocketMessage = {
      type: 'ai_decision_request',
      symbol,
    };

    this.ws.send(JSON.stringify(message));
  }

  addEventListener(eventType: string, callback: WebSocketEventCallback): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    
    this.eventHandlers.get(eventType)!.push(callback);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(callback);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  setStatusChangeHandler(callback: WebSocketStatusCallback): void {
    this.onStatusChange = callback;
  }

  setErrorHandler(callback: WebSocketErrorCallback): void {
    this.onError = callback;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}