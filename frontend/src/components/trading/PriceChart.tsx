'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { apiClient } from '@/lib/api';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';

interface ChartData {
  timestamp: string;
  date: string;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface PriceChartProps {
  symbol: string;
  className?: string;
}

export function PriceChart({ symbol, className = '' }: PriceChartProps) {
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('1mo');
  const [interval, setInterval] = useState('1d');

  // チャートデータを取得する関数
  const fetchChartData = async (selectedSymbol: string, selectedPeriod: string, selectedInterval: string) => {
    console.log(`fetchChartData: 開始 - ${selectedSymbol}, ${selectedPeriod}, ${selectedInterval}`);
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getHistoricalData(selectedSymbol, selectedPeriod, selectedInterval);
      console.log('fetchChartData: 取得成功', response);
      console.log('chart_data length:', response.chart_data.length);
      setChartData(response.chart_data);
    } catch (err) {
      console.error('チャートデータ取得エラー:', err);
      setError('チャートデータの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 初回データ取得
  useEffect(() => {
    if (symbol) {
      console.log(`PriceChart: データ取得開始 - ${symbol}, ${period}, ${interval}`);
      fetchChartData(symbol, period, interval);
    }
  }, [symbol, period, interval]);

  // 価格変動の計算
  const priceChange = chartData.length >= 2 
    ? chartData[chartData.length - 1].close - chartData[chartData.length - 2].close 
    : 0;
  const priceChangePercent = chartData.length >= 2 
    ? ((priceChange / chartData[chartData.length - 2].close) * 100)
    : 0;

  // カスタムツールチップ
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="text-sm font-medium text-gray-900">{data.date}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm text-gray-600">
              終値: <span className="font-medium text-gray-900">¥{data.close.toLocaleString()}</span>
            </p>
            <p className="text-sm text-gray-600">
              始値: <span className="font-medium">¥{data.open.toLocaleString()}</span>
            </p>
            <p className="text-sm text-gray-600">
              高値: <span className="font-medium text-red-600">¥{data.high.toLocaleString()}</span>
            </p>
            <p className="text-sm text-gray-600">
              安値: <span className="font-medium text-blue-600">¥{data.low.toLocaleString()}</span>
            </p>
            <p className="text-sm text-gray-600">
              出来高: <span className="font-medium">{data.volume.toLocaleString()}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // 期間選択ボタン
  const periodOptions = [
    { value: '1d', label: '1日' },
    { value: '5d', label: '5日' },
    { value: '1mo', label: '1ヶ月' },
    { value: '3mo', label: '3ヶ月' },
    { value: '6mo', label: '6ヶ月' },
    { value: '1y', label: '1年' },
  ];

  const intervalOptions = [
    { value: '1d', label: '日' },
    { value: '1h', label: '時間' },
    { value: '15m', label: '15分' },
    { value: '5m', label: '5分' },
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm ${className}`}>
      {/* ヘッダー */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">価格チャート</h3>
              <p className="text-sm text-gray-600">{symbol}</p>
            </div>
          </div>

          {/* 価格変動表示 */}
          {chartData.length > 0 && (
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  ¥{chartData[chartData.length - 1]?.close.toLocaleString()}
                </div>
                <div className="flex items-center justify-end space-x-2">
                  {priceChange > 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      priceChange > 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePercent > 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 期間・間隔選択 */}
        <div className="mt-4 flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">期間:</span>
            <div className="flex space-x-1">
              {periodOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setPeriod(option.value)}
                  className={`px-3 py-1 text-xs rounded ${
                    period === option.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">間隔:</span>
            <div className="flex space-x-1">
              {intervalOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setInterval(option.value)}
                  className={`px-3 py-1 text-xs rounded ${
                    interval === option.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* チャート */}
      <div className="p-6">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">チャートデータ読み込み中...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Activity className="h-12 w-12 text-red-400 mx-auto mb-4" />
              <p className="text-red-600">{error}</p>
              <button
                onClick={() => fetchChartData(symbol, period, interval)}
                className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                再試行
              </button>
            </div>
          </div>
        )}

        {!loading && !error && chartData.length > 0 && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date"
                  stroke="#666"
                  fontSize={12}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return interval === '1d' 
                      ? date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })
                      : date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
                  }}
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  tickFormatter={(value) => `¥${value.toLocaleString()}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, stroke: '#2563eb', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {!loading && !error && chartData.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">チャートデータがありません</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}