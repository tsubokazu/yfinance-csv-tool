import { create } from 'zustand';
import { PriceUpdate, AIDecisionResult, TradingData } from '@/types/trading';

interface TradingState {
  // Price data
  priceData: Map<string, PriceUpdate>;
  aiDecisions: Map<string, AIDecisionResult>;
  tradingData: Map<string, TradingData>;
  
  // UI state
  selectedSymbol: string | null;
  watchlist: string[];
  
  // WebSocket state
  isConnected: boolean;
  subscribedSymbols: Set<string>;
  
  // Actions
  updatePrice: (priceUpdate: PriceUpdate) => void;
  updateAIDecision: (aiDecision: AIDecisionResult) => void;
  updateTradingData: (symbol: string, data: TradingData) => void;
  setSelectedSymbol: (symbol: string) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  setWebSocketConnection: (connected: boolean) => void;
  addSubscription: (symbol: string) => void;
  removeSubscription: (symbol: string) => void;
  clearData: () => void;
  
  // Getters
  getPriceData: (symbol: string) => PriceUpdate | undefined;
  getAIDecision: (symbol: string) => AIDecisionResult | undefined;
  getTradingData: (symbol: string) => TradingData | undefined;
}

export const useTradingStore = create<TradingState>((set, get) => ({
  // Initial state
  priceData: new Map(),
  aiDecisions: new Map(),
  tradingData: new Map(),
  selectedSymbol: null,
  watchlist: ['6723.T', '7203.T', '9984.T'], // Default Japanese stocks
  isConnected: false,
  subscribedSymbols: new Set(),

  // Actions
  updatePrice: (priceUpdate: PriceUpdate) => {
    set((state) => {
      const newPriceData = new Map(state.priceData);
      newPriceData.set(priceUpdate.symbol, priceUpdate);
      return { priceData: newPriceData };
    });
  },

  updateAIDecision: (aiDecision: AIDecisionResult) => {
    set((state) => {
      const newAIDecisions = new Map(state.aiDecisions);
      newAIDecisions.set(aiDecision.symbol, aiDecision);
      return { aiDecisions: newAIDecisions };
    });
  },

  updateTradingData: (symbol: string, data: TradingData) => {
    set((state) => {
      const newTradingData = new Map(state.tradingData);
      newTradingData.set(symbol, data);
      return { tradingData: newTradingData };
    });
  },

  setSelectedSymbol: (symbol: string) => {
    set({ selectedSymbol: symbol });
  },

  addToWatchlist: (symbol: string) => {
    set((state) => {
      if (!state.watchlist.includes(symbol)) {
        return { watchlist: [...state.watchlist, symbol] };
      }
      return state;
    });
  },

  removeFromWatchlist: (symbol: string) => {
    set((state) => ({
      watchlist: state.watchlist.filter(s => s !== symbol),
    }));
  },

  setWebSocketConnection: (connected: boolean) => {
    set({ isConnected: connected });
  },

  addSubscription: (symbol: string) => {
    set((state) => {
      const newSubscribedSymbols = new Set(state.subscribedSymbols);
      newSubscribedSymbols.add(symbol);
      return { subscribedSymbols: newSubscribedSymbols };
    });
  },

  removeSubscription: (symbol: string) => {
    set((state) => {
      const newSubscribedSymbols = new Set(state.subscribedSymbols);
      newSubscribedSymbols.delete(symbol);
      return { subscribedSymbols: newSubscribedSymbols };
    });
  },

  clearData: () => {
    set({
      priceData: new Map(),
      aiDecisions: new Map(),
      tradingData: new Map(),
      selectedSymbol: null,
      subscribedSymbols: new Set(),
    });
  },

  // Getters
  getPriceData: (symbol: string) => {
    return get().priceData.get(symbol);
  },

  getAIDecision: (symbol: string) => {
    return get().aiDecisions.get(symbol);
  },

  getTradingData: (symbol: string) => {
    return get().tradingData.get(symbol);
  },
}));