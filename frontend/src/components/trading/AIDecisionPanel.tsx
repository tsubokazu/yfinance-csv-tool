'use client';

import { useState } from 'react';
import { Brain, TrendingUp, TrendingDown, AlertCircle, Target } from 'lucide-react';

interface AIDecision {
  symbol: string;
  decision: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  strategy: string;
  reasoning: string;
  entryConditions: string[];
  timestamp: string;
}

const sampleAIDecision: AIDecision = {
  symbol: '6723.T',
  decision: 'BUY',
  confidence: 85,
  strategy: 'モメンタム戦略',
  reasoning: '技術的指標が強気のシグナルを示しており、出来高の増加と共に上昇トレンドが継続する可能性が高い。RSIは買われ過ぎ水準には達しておらず、MACDも買いシグナルを示している。',
  entryConditions: [
    '現在価格付近での買い推奨',
    'ストップロス: ¥1,180 (-4.4%)',
    'ターゲット1: ¥1,280 (+3.7%)',
    'ターゲット2: ¥1,320 (+6.9%)',
  ],
  timestamp: new Date().toLocaleString('ja-JP'),
};

export function AIDecisionPanel() {
  const [aiDecision] = useState<AIDecision>(sampleAIDecision);
  const [isLoading, setIsLoading] = useState(false);

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'SELL':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'HOLD':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return <TrendingUp className="h-5 w-5" />;
      case 'SELL':
        return <TrendingDown className="h-5 w-5" />;
      case 'HOLD':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <Brain className="h-5 w-5" />;
    }
  };

  const handleRequestAIDecision = async () => {
    setIsLoading(true);
    // Simulate API call delay
    setTimeout(() => {
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">AI判断システム</h2>
          </div>
          <button
            onClick={handleRequestAIDecision}
            disabled={isLoading}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Target className="h-4 w-4" />
            )}
            <span>{isLoading ? '分析中...' : 'AI判断実行'}</span>
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Decision summary */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <span className="text-lg font-medium text-gray-900">{aiDecision.symbol}</span>
              <div
                className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getDecisionColor(
                  aiDecision.decision
                )}`}
              >
                {getDecisionIcon(aiDecision.decision)}
                <span className="font-semibold">{aiDecision.decision}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">信頼度</div>
              <div className="text-2xl font-bold text-gray-900">{aiDecision.confidence}%</div>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>戦略: {aiDecision.strategy}</span>
            <span>•</span>
            <span>更新: {aiDecision.timestamp}</span>
          </div>
        </div>

        {/* Confidence meter */}
        <div className="mb-6">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>信頼度</span>
            <span>{aiDecision.confidence}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                aiDecision.confidence >= 80
                  ? 'bg-green-500'
                  : aiDecision.confidence >= 60
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${aiDecision.confidence}%` }}
            ></div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">判断根拠</h3>
          <p className="text-gray-700 leading-relaxed">{aiDecision.reasoning}</p>
        </div>

        {/* Entry conditions */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">エントリー条件</h3>
          <ul className="space-y-2">
            {aiDecision.entryConditions.map((condition, index) => (
              <li key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                </div>
                <span className="text-gray-700">{condition}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-yellow-50 border-t border-yellow-200 px-6 py-4">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium">免責事項</p>
            <p>
              AI判断は参考情報であり、投資を推奨するものではありません。
              投資判断は自己責任で行ってください。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}