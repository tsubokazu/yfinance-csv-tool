'use client';

import { useState } from 'react';
import { Plus, Star, TrendingUp, TrendingDown } from 'lucide-react';

interface WatchListItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
}

const watchListData: WatchListItem[] = [
  {
    symbol: '6723.T',
    name: 'ルネサス',
    price: 1234.5,
    change: 23.5,
    changePercent: 1.94,
    volume: '2.3M',
  },
  {
    symbol: '7203.T',
    name: 'トヨタ',
    price: 2847.0,
    change: -15.0,
    changePercent: -0.52,
    volume: '5.1M',
  },
  {
    symbol: '6758.T',
    name: 'ソニーG',
    price: 12650.0,
    change: 125.0,
    changePercent: 1.00,
    volume: '890K',
  },
  {
    symbol: '9984.T',
    name: 'ソフトバンク',
    price: 6534.0,
    change: -234.0,
    changePercent: -3.46,
    volume: '1.2M',
  },
];

export function WatchList() {
  const [watchList, setWatchList] = useState<WatchListItem[]>(watchListData);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">ウォッチリスト</h2>
          <button className="flex items-center space-x-2 text-blue-600 hover:text-blue-700">
            <Plus className="h-4 w-4" />
            <span className="text-sm font-medium">追加</span>
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {watchList.map((item) => (
          <div
            key={item.symbol}
            className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900">{item.symbol}</span>
                      <span className="text-sm text-gray-500">{item.name}</span>
                    </div>
                    <div className="text-sm text-gray-500">出来高: {item.volume}</div>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-lg font-semibold text-gray-900">
                  ¥{item.price.toLocaleString()}
                </div>
                <div className="flex items-center justify-end space-x-1">
                  {item.change > 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      item.change > 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {item.change > 0 ? '+' : ''}{item.change}
                  </span>
                  <span
                    className={`text-sm ${
                      item.change > 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    ({item.changePercent > 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-gray-50 rounded-b-lg">
        <button className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium">
          すべて表示
        </button>
      </div>
    </div>
  );
}