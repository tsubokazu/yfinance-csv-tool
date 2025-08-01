'use client';

import { useState, useEffect } from 'react';
import { Play, Settings, Calendar, Clock, TrendingUp } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { SymbolSearchInput } from '@/components/trading/SymbolSearchInput';

interface BacktestFormProps {
  onRun: (params: {
    symbol: string;
    startDate: string;
    endDate: string;
    intervalMinutes: number;
    maxDecisions: number;
  }) => void;
  isRunning: boolean;
}

export function BacktestForm({ onRun, isRunning }: BacktestFormProps) {
  const [symbol, setSymbol] = useState('6723.T');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('15:00');
  const [intervalMinutes, setIntervalMinutes] = useState(60);
  const [maxDecisions, setMaxDecisions] = useState(50);

  // デフォルト値をクライアントサイドで設定（Hydrationエラー回避）
  useEffect(() => {
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    setStartDate(weekAgo.toISOString().split('T')[0]);
    setEndDate(today.toISOString().split('T')[0]);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // 日付と時刻を組み合わせてISOString形式に変換
    const startDateTime = `${startDate}T${startTime}:00`;
    const endDateTime = `${endDate}T${endTime}:00`;
    
    onRun({
      symbol,
      startDate: startDateTime,
      endDate: endDateTime,
      intervalMinutes,
      maxDecisions,
    });
  };

  const handleSymbolSelect = (selectedSymbol: string) => {
    setSymbol(selectedSymbol);
  };

  const intervalOptions = [
    { value: 1, label: '1分' },
    { value: 5, label: '5分' },
    { value: 15, label: '15分' },
    { value: 30, label: '30分' },
    { value: 60, label: '1時間' },
    { value: 240, label: '4時間' },
  ];

  const maxDecisionOptions = [
    { value: 20, label: '20回' },
    { value: 50, label: '50回' },
    { value: 100, label: '100回' },
    { value: 200, label: '200回' },
    { value: 500, label: '500回' },
  ];

  // 期間プリセット
  const periodPresets = [
    {
      label: '今日',
      getValue: () => {
        const today = new Date().toISOString().split('T')[0];
        return { startDate: today, endDate: today };
      }
    },
    {
      label: '過去3日',
      getValue: () => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 3);
        return {
          startDate: start.toISOString().split('T')[0],
          endDate: end.toISOString().split('T')[0]
        };
      }
    },
    {
      label: '過去1週間',
      getValue: () => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 7);
        return {
          startDate: start.toISOString().split('T')[0],
          endDate: end.toISOString().split('T')[0]
        };
      }
    },
    {
      label: '過去1ヶ月',
      getValue: () => {
        const end = new Date();
        const start = new Date();
        start.setMonth(start.getMonth() - 1);
        return {
          startDate: start.toISOString().split('T')[0],
          endDate: end.toISOString().split('T')[0]
        };
      }
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Settings className="h-6 w-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">バックテスト設定</h2>
            <p className="text-sm text-gray-600">
              シミュレーション実行のパラメータを設定してください
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-6">
        <div className="space-y-6">
          {/* Symbol Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              銘柄選択
            </label>
            <SymbolSearchInput
              value={symbol}
              onChange={setSymbol}
              onSelect={handleSymbolSelect}
              disabled={isRunning}
              placeholder="銘柄コードを入力 (例: 6723.T, AAPL)"
            />
          </div>

          {/* Period Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="inline h-4 w-4 mr-1" />
              期間プリセット
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
              {periodPresets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => {
                    const { startDate: newStart, endDate: newEnd } = preset.getValue();
                    setStartDate(newStart);
                    setEndDate(newEnd);
                  }}
                  disabled={isRunning}
                  className={`px-3 py-2 text-sm rounded-md border transition-colors bg-white text-gray-700 border-gray-300 hover:bg-gray-50 ${
                    isRunning ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Input
                label="開始日"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isRunning}
                required
              />
            </div>
            <div>
              <Input
                label="終了日"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isRunning}
                required
              />
            </div>
          </div>

          {/* Time Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Input
                label="開始時刻"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                disabled={isRunning}
                required
              />
            </div>
            <div>
              <Input
                label="終了時刻"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                disabled={isRunning}
                required
              />
            </div>
          </div>

          {/* Interval Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Clock className="inline h-4 w-4 mr-1" />
              判断間隔
            </label>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
              {intervalOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setIntervalMinutes(option.value)}
                  disabled={isRunning}
                  className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                    intervalMinutes === option.value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <p>AI判断を実行する時間間隔を選択してください</p>
              <p className="mt-1">
                選択中: <span className="font-medium text-blue-600">{intervalMinutes}分間隔</span>
                {(() => {
                  const totalMinutes = Math.ceil((new Date(`${endDate}T${endTime}`).getTime() - new Date(`${startDate}T${startTime}`).getTime()) / (1000 * 60));
                  const estimatedDecisions = Math.min(Math.ceil(totalMinutes / intervalMinutes), maxDecisions);
                  return ` (推定判断回数: 約${estimatedDecisions}回)`;
                })()}
              </p>
            </div>
          </div>

          {/* Max Decisions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <TrendingUp className="inline h-4 w-4 mr-1" />
              最大判断回数
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {maxDecisionOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setMaxDecisions(option.value)}
                  disabled={isRunning}
                  className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                    maxDecisions === option.value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <p>バックテスト期間中の最大AI判断回数を設定してください</p>
              <p className="mt-1">
                実行制限: 選択した間隔と期間で決まる自然な判断回数と、ここで設定した上限のいずれか小さい方で実行されます
              </p>
            </div>
          </div>

          {/* Run Button */}
          <div className="pt-4 border-t border-gray-200">
            <button
              type="submit"
              disabled={isRunning}
              className={`w-full flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                isRunning
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isRunning ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>バックテスト実行中...</span>
                </>
              ) : (
                <>
                  <Play className="h-5 w-5" />
                  <span>バックテスト実行</span>
                </>
              )}
            </button>
          </div>

          {/* Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <Calendar className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">バックテストについて</h4>
                <div className="text-sm text-blue-800 mt-2 space-y-1">
                  <p>• 過去の価格データを使用してAI判断システムの性能をテストします</p>
                  <p>• 実際の取引は行われません（シミュレーションのみ）</p>
                  <p>• 指定した間隔でAI判断を実行し、統計情報とチャートで結果を表示します</p>
                  <p>• 結果は参考情報として利用してください</p>
                </div>
                {(() => {
                  const totalMinutes = Math.ceil((new Date(`${endDate}T${endTime}`).getTime() - new Date(`${startDate}T${startTime}`).getTime()) / (1000 * 60));
                  const estimatedDecisions = Math.min(Math.ceil(totalMinutes / intervalMinutes), maxDecisions);
                  const estimatedTime = Math.ceil(estimatedDecisions * 0.5); // 1判断あたり約0.5秒と仮定
                  
                  return (
                    <div className="mt-3 p-2 bg-blue-100 rounded text-xs">
                      <strong>実行予測:</strong> 約{estimatedDecisions}回の判断、実行時間約{estimatedTime}秒
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}