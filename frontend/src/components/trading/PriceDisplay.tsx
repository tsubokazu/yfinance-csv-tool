'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Clock, Star } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { PriceChart } from './PriceChart';
import { SymbolSearchInput } from './SymbolSearchInput';
import { PopularSymbols } from './PopularSymbols';

interface PriceData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  open: number;
  volume: string;
  lastUpdate: string;
}

const samplePriceData: PriceData = {
  symbol: '6723.T',
  name: 'ルネサス エレクトロニクス',
  price: 1234.5,
  change: 23.5,
  changePercent: 1.94,
  high: 1245.0,
  low: 1205.0,
  open: 1211.0,
  volume: '2,345,678',
  lastUpdate: new Date().toLocaleTimeString('ja-JP'),
};

export function PriceDisplay() {
  const [selectedSymbol, setSelectedSymbol] = useState('6723.T');
  const [searchValue, setSearchValue] = useState('6723.T');
  const [priceData, setPriceData] = useState<PriceData>(samplePriceData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showChart, setShowChart] = useState(true);
  const [showPopular, setShowPopular] = useState(false);

  // yfinanceデータを取得する関数
  const fetchPriceData = async (symbol: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getTradingDecision(
        symbol,
        new Date().toISOString()
      );
      
      const data = response;
      
      // APIレスポンスをPriceDataフォーマットに変換
      const newPriceData: PriceData = {
        symbol: data.symbol,
        name: getSymbolName(data.symbol),
        price: data.current_price,
        change: data.price_change || 0,
        changePercent: data.price_change_percent || 0,
        high: data.current_price + Math.abs((data.price_change || 0) * 0.5), // 仮想的な高値
        low: data.current_price - Math.abs((data.price_change || 0) * 0.3), // 仮想的な安値  
        open: data.current_price - (data.price_change || 0), // 仮想的な始値
        volume: data.volume?.toLocaleString() || 'N/A',
        lastUpdate: new Date().toLocaleTimeString('ja-JP'),
      };
      
      setPriceData(newPriceData);
    } catch (err) {
      console.error('価格データ取得エラー:', err);
      setError('価格データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 銘柄名を取得（シンプルなマッピング）
  const getSymbolName = (symbol: string) => {
    const nameMap: { [key: string]: string } = {
      '6723.T': 'ルネサス エレクトロニクス',
      '7203.T': 'トヨタ自動車',
      '6758.T': 'ソニーグループ',
      '9984.T': 'ソフトバンクグループ',
    };
    return nameMap[symbol] || symbol;
  };

  // 初回データ取得
  useEffect(() => {
    fetchPriceData(selectedSymbol);
  }, []);

  // 検索値変更時の処理
  const handleSearchChange = (value: string) => {
    setSearchValue(value);
  };

  // 銘柄選択時の処理
  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    setSearchValue(symbol);
    fetchPriceData(symbol);
    setShowPopular(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header with search */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">価格表示</h2>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setShowPopular(!showPopular)}
              className="flex items-center space-x-2 text-yellow-600 hover:text-yellow-700"
            >
              <Star className="h-4 w-4" />
              <span className="text-sm font-medium">
                {showPopular ? '人気銘柄非表示' : '人気銘柄表示'}
              </span>
            </button>
            <button 
              onClick={() => setShowChart(!showChart)}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-700"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="text-sm font-medium">
                {showChart ? 'チャート非表示' : 'チャート表示'}
              </span>
            </button>
          </div>
        </div>

        {/* Enhanced Search bar */}
        <SymbolSearchInput
          value={searchValue}
          onChange={handleSearchChange}
          onSelect={handleSymbolSelect}
          loading={loading}
          disabled={loading}
        />

        {/* エラー表示 */}
        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Price data */}
      <div className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">{priceData.symbol}</h3>
              <p className="text-lg text-gray-600">{priceData.name}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-gray-900">
                ¥{priceData.price.toLocaleString()}
              </div>
              <div className="flex items-center justify-end space-x-2">
                {priceData.change > 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-500" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-500" />
                )}
                <span
                  className={`text-lg font-semibold ${
                    priceData.change > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {priceData.change > 0 ? '+' : ''}{priceData.change}
                </span>
                <span
                  className={`text-lg ${
                    priceData.change > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  ({priceData.changePercent > 0 ? '+' : ''}{priceData.changePercent}%)
                </span>
              </div>
            </div>
          </div>

          {/* Last update */}
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock className="h-4 w-4" />
            <span>最終更新: {priceData.lastUpdate}</span>
          </div>
        </div>

        {/* Price details grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">始値</div>
            <div className="text-lg font-semibold text-gray-900">
              ¥{priceData.open.toLocaleString()}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">高値</div>
            <div className="text-lg font-semibold text-red-600">
              ¥{priceData.high.toLocaleString()}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">安値</div>
            <div className="text-lg font-semibold text-blue-600">
              ¥{priceData.low.toLocaleString()}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">出来高</div>
            <div className="text-lg font-semibold text-gray-900">
              {priceData.volume}
            </div>
          </div>
        </div>

        {/* Popular Symbols */}
        {showPopular && (
          <div className="mb-6">
            <PopularSymbols 
              onSymbolSelect={handleSymbolSelect}
              selectedSymbol={selectedSymbol}
            />
          </div>
        )}

        {/* Price Chart */}
        {showChart && (
          <PriceChart symbol={priceData.symbol} />
        )}
      </div>
    </div>
  );
}