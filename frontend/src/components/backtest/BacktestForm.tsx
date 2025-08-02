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
    aiModel: string;
    aiProvider: string;
  }) => void;
  isRunning: boolean;
}

export function BacktestForm({ onRun, isRunning }: BacktestFormProps) {
  const [symbol, setSymbol] = useState('6723.T');
  const [startDateTime, setStartDateTime] = useState('');
  const [endDateTime, setEndDateTime] = useState('');
  const [intervalMinutes, setIntervalMinutes] = useState(60);
  const [maxDecisions, setMaxDecisions] = useState(50);
  const [aiModel, setAiModel] = useState('simple');
  const [aiProvider, setAiProvider] = useState('gemini');

  // デフォルト値をクライアントサイドで設定（Hydrationエラー回避）
  useEffect(() => {
    const now = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    // 取引時間に設定（9:00-15:00）
    weekAgo.setHours(9, 0, 0, 0);
    now.setHours(15, 0, 0, 0);
    
    setStartDateTime(weekAgo.toISOString().slice(0, 16));
    setEndDateTime(now.toISOString().slice(0, 16));
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
      // 日時入力をJSTとして扱い、バックエンドに直接送信
      // datetime-localはローカルタイムゾーンで解釈されるため、JSTとして扱う
      console.log('日時送信:', {
        original_start: startDateTime,
        original_end: endDateTime,
        timezone_info: 'JSTとしてバックエンドに送信',
        local_tz_offset: new Date().getTimezoneOffset()
      });

      onRun({
        symbol,
        startDate: startDateTime, // ISO文字列として直接送信
        endDate: endDateTime,     // ISO文字列として直接送信
        intervalMinutes,
        maxDecisions,
        aiModel,
        aiProvider,
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

  // AI モデル選択肢
  const aiModelOptions = [
    { value: 'simple', label: 'シンプル判断' },
    { value: 'integrated', label: '統合分析' },
    { value: 'chart', label: 'チャート画像分析' },
    { value: 'technical', label: 'テクニカル指標' },
  ];

  // 期間プリセット
  const periodPresets = [
    {
      label: '今日',
      getValue: () => {
        const today = new Date();
        const start = new Date(today);
        start.setHours(9, 0, 0, 0);
        const end = new Date(today);
        end.setHours(15, 0, 0, 0);
        return { 
          startDateTime: start.toISOString().slice(0, 16), 
          endDateTime: end.toISOString().slice(0, 16) 
        };
      }
    },
    {
      label: '過去3日',
      getValue: () => {
        const end = new Date();
        end.setHours(15, 0, 0, 0);
        const start = new Date();
        start.setDate(start.getDate() - 3);
        start.setHours(9, 0, 0, 0);
        return {
          startDateTime: start.toISOString().slice(0, 16),
          endDateTime: end.toISOString().slice(0, 16)
        };
      }
    },
    {
      label: '過去1週間',
      getValue: () => {
        const end = new Date();
        end.setHours(15, 0, 0, 0);
        const start = new Date();
        start.setDate(start.getDate() - 7);
        start.setHours(9, 0, 0, 0);
        return {
          startDateTime: start.toISOString().slice(0, 16),
          endDateTime: end.toISOString().slice(0, 16)
        };
      }
    },
    {
      label: '過去1ヶ月',
      getValue: () => {
        const end = new Date();
        end.setHours(15, 0, 0, 0);
        const start = new Date();
        start.setMonth(start.getMonth() - 1);
        start.setHours(9, 0, 0, 0);
        return {
          startDateTime: start.toISOString().slice(0, 16),
          endDateTime: end.toISOString().slice(0, 16)
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

          {/* AI Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              使用AIモデル
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {aiModelOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setAiModel(option.value)}
                  disabled={isRunning}
                  className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                    aiModel === option.value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <p>
                選択中: <span className="font-medium text-blue-600">
                  {aiModelOptions.find(opt => opt.value === aiModel)?.label || 'シンプル判断'}
                </span>
              </p>
              <p className="mt-1">
                {aiModel === 'simple' && 'チャート画像のみの基本的な判断'}
                {aiModel === 'integrated' && 'チャート画像、テクニカル指標、統合分析による総合判断'}
                {aiModel === 'chart' && 'チャート画像分析に特化した判断'}
                {aiModel === 'technical' && 'テクニカル指標分析に特化した判断'}
              </p>
            </div>
          </div>

          {/* AI Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              使用AIプロバイダー
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setAiProvider('openai')}
                disabled={isRunning}
                className={`px-4 py-3 text-sm rounded-md border transition-colors ${
                  aiProvider === 'openai'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="text-center">
                  <div className="font-medium">OpenAI GPT-4</div>
                  <div className="text-xs mt-1 opacity-75">
                    高精度分析（コスト高）
                  </div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setAiProvider('gemini')}
                disabled={isRunning}
                className={`px-4 py-3 text-sm rounded-md border transition-colors ${
                  aiProvider === 'gemini'
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="text-center">
                  <div className="font-medium">Gemini 2.5 Flash</div>
                  <div className="text-xs mt-1 opacity-75">
                    高速・効率的分析（コスト低）
                  </div>
                </div>
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <p>
                選択中: <span className="font-medium text-green-600">
                  {aiProvider === 'openai' ? 'OpenAI GPT-4' : 'Gemini 2.5 Flash'}
                </span>
              </p>
              <p className="mt-1">
                {aiProvider === 'openai' && 'OpenAI GPT-4を使用した高精度なAI分析。詳細な推論能力と高い精度を提供しますが、コストが高めです。'}
                {aiProvider === 'gemini' && 'Google Gemini 2.5 Flashを使用した高速で効率的なAI分析。バランスの取れた性能とコスト性能を提供します。'}
              </p>
            </div>
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
                    const { startDateTime: newStart, endDateTime: newEnd } = preset.getValue();
                    setStartDateTime(newStart);
                    setEndDateTime(newEnd);
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

          {/* Date and Time Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Input
                label="開始日時"
                type="datetime-local"
                value={startDateTime}
                onChange={(e) => setStartDateTime(e.target.value)}
                disabled={isRunning}
                required
              />
            </div>
            <div>
              <Input
                label="終了日時"
                type="datetime-local"
                value={endDateTime}
                onChange={(e) => setEndDateTime(e.target.value)}
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
                  if (!startDateTime || !endDateTime) return '';
                  const totalMinutes = Math.ceil((new Date(endDateTime).getTime() - new Date(startDateTime).getTime()) / (1000 * 60));
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
                  if (!startDateTime || !endDateTime) return null;
                  const totalMinutes = Math.ceil((new Date(endDateTime).getTime() - new Date(startDateTime).getTime()) / (1000 * 60));
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