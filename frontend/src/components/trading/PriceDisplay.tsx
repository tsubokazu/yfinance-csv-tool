'use client';

import { useState } from 'react';
import { Search, BarChart3, TrendingUp, TrendingDown, Clock } from 'lucide-react';

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
  const [priceData] = useState<PriceData>(samplePriceData);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header with search */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">価格表示</h2>
          <button className="flex items-center space-x-2 text-blue-600 hover:text-blue-700">
            <BarChart3 className="h-4 w-4" />
            <span className="text-sm font-medium">チャート表示</span>
          </button>
        </div>

        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="銘柄コードまたは銘柄名を入力 (例: 6723.T)"
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
          />
        </div>
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

        {/* Chart placeholder */}
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">価格チャート</h3>
          <p className="text-gray-600">
            WebSocketリアルタイム価格チャートは次のフェーズで実装予定です
          </p>
        </div>
      </div>
    </div>
  );
}