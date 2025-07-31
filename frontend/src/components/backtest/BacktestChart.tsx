'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Dot } from 'recharts';
import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface BacktestChartProps {
  results: {
    symbol: string;
    decisions: Array<{
      timestamp: string;
      price: number;
      ai_decision: 'BUY' | 'SELL' | 'HOLD';
      confidence: number;
      reasoning: string[];
    }>;
  };
}

export function BacktestChart({ results }: BacktestChartProps) {
  const { symbol, decisions } = results;

  // チャート用データに変換
  const chartData = decisions.map((decision, index) => ({
    index: index + 1,
    timestamp: decision.timestamp,
    price: decision.price,
    decision: decision.ai_decision,
    confidence: decision.confidence,
    date: new Date(decision.timestamp).toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
  }));

  // 価格範囲の計算
  const prices = decisions.map(d => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1;

  // カスタムドットコンポーネント
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload) return null;

    const decision = payload.decision;
    let fill = '#6B7280'; // デフォルト (HOLD)
    
    if (decision === 'BUY') fill = '#10B981';
    else if (decision === 'SELL') fill = '#EF4444';

    return (
      <Dot 
        cx={cx} 
        cy={cy} 
        r={6} 
        fill={fill} 
        stroke="#ffffff" 
        strokeWidth={2}
      />
    );
  };

  // カスタムツールチップ
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="text-sm font-medium text-gray-900">{data.date}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm text-gray-600">
              価格: <span className="font-medium text-gray-900">¥{data.price.toLocaleString()}</span>
            </p>
            <p className="text-sm text-gray-600">
              AI判断: <span className={`font-medium ${
                data.decision === 'BUY' ? 'text-green-600' :
                data.decision === 'SELL' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {data.decision}
              </span>
            </p>
            <p className="text-sm text-gray-600">
              信頼度: <span className="font-medium">{(data.confidence * 100).toFixed(1)}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">価格推移とAI判断</h3>
              <p className="text-sm text-gray-600">{symbol} のバックテスト結果</p>
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-600">BUY</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600">SELL</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-gray-500"></div>
              <span className="text-gray-600">HOLD</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date"
                stroke="#666"
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                stroke="#666"
                fontSize={12}
                tickFormatter={(value) => `¥${value.toLocaleString()}`}
                domain={[minPrice - padding, maxPrice + padding]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#2563eb"
                strokeWidth={2}
                dot={<CustomDot />}
                activeDot={{ r: 8, stroke: '#2563eb', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary */}
      <div className="p-6 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <div>
              <div className="text-sm text-gray-600">買いシグナル</div>
              <div className="font-medium text-gray-900">
                {decisions.filter(d => d.ai_decision === 'BUY').length}回
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <TrendingDown className="h-5 w-5 text-red-600" />
            <div>
              <div className="text-sm text-gray-600">売りシグナル</div>
              <div className="font-medium text-gray-900">
                {decisions.filter(d => d.ai_decision === 'SELL').length}回
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Minus className="h-5 w-5 text-gray-600" />
            <div>
              <div className="text-sm text-gray-600">様子見</div>
              <div className="font-medium text-gray-900">
                {decisions.filter(d => d.ai_decision === 'HOLD').length}回
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}