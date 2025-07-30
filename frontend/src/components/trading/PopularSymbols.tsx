'use client';

import { useState } from 'react';
import { TrendingUp, TrendingDown, Star, Building2 } from 'lucide-react';

interface PopularSymbol {
  symbol: string;
  name: string;
  sector: string;
  price?: number;
  change?: number;
  changePercent?: number;
  volume?: string;
}

const popularSymbols: PopularSymbol[] = [
  // 日本株主要銘柄
  { symbol: '6723.T', name: 'ルネサス エレクトロニクス', sector: '半導体' },
  { symbol: '7203.T', name: 'トヨタ自動車', sector: '自動車' },
  { symbol: '6758.T', name: 'ソニーグループ', sector: 'エレクトロニクス' },
  { symbol: '9984.T', name: 'ソフトバンクグループ', sector: '通信' },
  { symbol: '8306.T', name: '三菱UFJフィナンシャル・グループ', sector: '金融' },
  { symbol: '4689.T', name: 'Zホールディングス', sector: 'IT' },
  { symbol: '6954.T', name: 'ファナック', sector: '機械' },
  { symbol: '4063.T', name: '信越化学工業', sector: '化学' },
  { symbol: '6981.T', name: '村田製作所', sector: '電子部品' },
  { symbol: '9432.T', name: '日本電信電話', sector: '通信' },

  // 米国株主要銘柄
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'E-commerce' },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Automotive' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', sector: 'Semiconductors' },
  { symbol: 'META', name: 'Meta Platforms Inc.', sector: 'Social Media' },
  { symbol: 'NFLX', name: 'Netflix Inc.', sector: 'Entertainment' },
];

interface PopularSymbolsProps {
  onSymbolSelect: (symbol: string) => void;
  selectedSymbol?: string;
  className?: string;
}

export function PopularSymbols({ onSymbolSelect, selectedSymbol, className = '' }: PopularSymbolsProps) {
  const [activeTab, setActiveTab] = useState<'jp' | 'us'>('jp');

  const japaneseSymbols = popularSymbols.filter(s => s.symbol.endsWith('.T'));
  const usSymbols = popularSymbols.filter(s => !s.symbol.endsWith('.T'));

  const currentSymbols = activeTab === 'jp' ? japaneseSymbols : usSymbols;

  return (
    <div className={`bg-white rounded-lg shadow-sm ${className}`}>
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Star className="h-5 w-5 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900">人気銘柄</h3>
          </div>

          {/* タブ切り替え */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('jp')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                activeTab === 'jp'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              日本株
            </button>
            <button
              onClick={() => setActiveTab('us')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                activeTab === 'us'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              米国株
            </button>
          </div>
        </div>
      </div>

      {/* 銘柄リスト */}
      <div className="p-4">
        <div className="space-y-2">
          {currentSymbols.map((symbol) => (
            <button
              key={symbol.symbol}
              onClick={() => onSymbolSelect(symbol.symbol)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedSymbol === symbol.symbol
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <Building2 className="h-4 w-4 text-gray-400" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{symbol.symbol}</span>
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                          {symbol.sector}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{symbol.name}</p>
                    </div>
                  </div>
                </div>

                {/* 価格情報（今後追加予定） */}
                {symbol.price && (
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {activeTab === 'jp' ? '¥' : '$'}{symbol.price.toLocaleString()}
                    </div>
                    {symbol.change && (
                      <div className="flex items-center space-x-1">
                        {symbol.change > 0 ? (
                          <TrendingUp className="h-3 w-3 text-green-500" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-red-500" />
                        )}
                        <span
                          className={`text-xs ${
                            symbol.change > 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {symbol.change > 0 ? '+' : ''}{symbol.changePercent?.toFixed(2)}%
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}