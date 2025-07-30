'use client';

import { createContext, useContext, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';

interface WebSocketContextType {
  isConnected: boolean;
  connectionError: string | null;
  subscribeToSymbol: (symbol: string) => void;
  unsubscribeFromSymbol: (symbol: string) => void;
  requestAIDecision: (symbol: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const { isAuthenticated } = useAuth();
  
  const {
    isConnected,
    connectionError,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    requestAIDecision,
  } = useWebSocket({
    authenticated: true,
    autoConnect: true,
  });

  // Default subscriptions for dashboard
  useEffect(() => {
    if (isConnected && isAuthenticated) {
      // Subscribe to popular symbols by default
      const defaultSymbols = ['6723.T', '7203.T', '6758.T', '9984.T'];
      defaultSymbols.forEach(symbol => {
        subscribeToSymbol(symbol);
      });
    }
  }, [isConnected, isAuthenticated, subscribeToSymbol]);

  const contextValue: WebSocketContextType = {
    isConnected,
    connectionError,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    requestAIDecision,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}