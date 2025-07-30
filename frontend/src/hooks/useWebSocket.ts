import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketManager, WebSocketEventCallback } from '@/lib/websocket';
import { useTradingStore } from '@/store/tradingStore';
import { useAuthStore } from '@/store/authStore';
import { PriceUpdate, AIDecisionResult } from '@/types/trading';

interface UseWebSocketOptions {
  authenticated?: boolean;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { authenticated = false, autoConnect = true } = options;
  
  const wsRef = useRef<WebSocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const { isAuthenticated } = useAuthStore();
  const {
    updatePrice,
    updateAIDecision,
    setWebSocketConnection,
    addSubscription,
    removeSubscription,
  } = useTradingStore();

  // Initialize WebSocket manager
  useEffect(() => {
    const shouldUseAuth = authenticated && isAuthenticated;
    wsRef.current = new WebSocketManager(shouldUseAuth);

    // Set up event handlers
    wsRef.current.setStatusChangeHandler((connected) => {
      setIsConnected(connected);
      setWebSocketConnection(connected);
      if (connected) {
        setConnectionError(null);
      }
    });

    wsRef.current.setErrorHandler((error) => {
      console.error('WebSocket error:', error);
      setConnectionError('Connection error occurred');
    });

    // Price update handler
    wsRef.current.addEventListener('price_update', (data: PriceUpdate) => {
      updatePrice(data);
    });

    // AI decision handler
    wsRef.current.addEventListener('ai_decision_result', (data: AIDecisionResult) => {
      updateAIDecision(data);
    });

    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, [authenticated, isAuthenticated, updatePrice, updateAIDecision, setWebSocketConnection]);

  // Auto connect
  useEffect(() => {
    if (autoConnect && wsRef.current && !isConnected) {
      const shouldConnect = !authenticated || (authenticated && isAuthenticated);
      if (shouldConnect) {
        connect();
      }
    }
  }, [autoConnect, authenticated, isAuthenticated, isConnected]);

  const connect = useCallback(async () => {
    if (!wsRef.current) return;

    try {
      await wsRef.current.connect();
      setConnectionError(null);
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setConnectionError('Failed to connect');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }
  }, []);

  const subscribeToSymbol = useCallback((symbol: string) => {
    if (wsRef.current && isConnected) {
      wsRef.current.subscribeToSymbol(symbol);
      addSubscription(symbol);
    }
  }, [isConnected, addSubscription]);

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (wsRef.current) {
      wsRef.current.unsubscribeFromSymbol(symbol);
      removeSubscription(symbol);
    }
  }, [removeSubscription]);

  const requestAIDecision = useCallback((symbol: string) => {
    if (wsRef.current && isConnected && (authenticated ? isAuthenticated : true)) {
      wsRef.current.requestAIDecision(symbol);
    }
  }, [isConnected, authenticated, isAuthenticated]);

  const addEventListener = useCallback((eventType: string, callback: WebSocketEventCallback) => {
    if (wsRef.current) {
      return wsRef.current.addEventListener(eventType, callback);
    }
    return () => {};
  }, []);

  return {
    // State
    isConnected,
    connectionError,
    wsManager: wsRef.current,

    // Actions
    connect,
    disconnect,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    requestAIDecision,
    addEventListener,
  };
}