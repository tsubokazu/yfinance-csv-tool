'use client';

import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

const marketData = [
  {
    name: '日経平均',
    value: '38,720.47',
    change: '+156.22',
    changePercent: '+0.41%',
    isPositive: true,
  },
  {
    name: 'TOPIX',
    value: '2,697.58',
    change: '+8.94',
    changePercent: '+0.33%',
    isPositive: true,
  },
  {
    name: 'マザーズ',
    value: '1,024.33',
    change: '-5.67',
    changePercent: '-0.55%',
    isPositive: false,
  },
  {
    name: 'JASDAQ',
    value: '164.78',
    change: '+1.23',
    changePercent: '+0.75%',
    isPositive: true,
  },
];

export function MarketOverview() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">市場概況</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Activity className="h-4 w-4" />
          <span>リアルタイム更新</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {marketData.map((market) => (
          <div
            key={market.name}
            className="relative bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">{market.name}</h3>
              {market.isPositive ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
            </div>
            
            <div className="space-y-1">
              <div className="text-2xl font-bold text-gray-900">
                {market.value}
              </div>
              <div className="flex items-center space-x-2">
                <span
                  className={`text-sm font-medium ${
                    market.isPositive ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {market.change}
                </span>
                <span
                  className={`text-sm ${
                    market.isPositive ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  ({market.changePercent})
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Market Status */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">東京証券取引所: 開場中</span>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            最終更新: {new Date().toLocaleTimeString('ja-JP')}
          </div>
        </div>
      </div>
    </div>
  );
}