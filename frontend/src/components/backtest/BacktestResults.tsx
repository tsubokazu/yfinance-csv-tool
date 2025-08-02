'use client';

import { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Clock, BarChart3, ChevronDown, ChevronRight, Eye, BarChart2, Activity } from 'lucide-react';

interface BacktestResultsProps {
  results: {
    symbol: string;
    backtest_period: {
      start: string;
      end: string;
      interval_minutes: number;
    };
    statistics: {
      total_decisions: number;
      buy_signals: number;
      sell_signals: number;
      hold_signals: number;
      average_confidence: number;
    };
    decisions: Array<{
      timestamp: string;
      price: number;
      ai_decision: 'BUY' | 'SELL' | 'HOLD';
      confidence: number;
      reasoning: string[];
      analysis_efficiency: string;
      detailed_analysis?: {
        chart_analysis?: {
          decision: 'BUY' | 'SELL' | 'HOLD';
          confidence: number;
          reasoning: string[];
        };
        technical_analysis?: {
          decision: 'BUY' | 'SELL' | 'HOLD';
          confidence: number;
          reasoning: string[];
        };
        integrated_analysis?: {
          decision: 'BUY' | 'SELL' | 'HOLD';
          confidence: number;
          reasoning: string[];
        };
      };
    }>;
  };
}

export function BacktestResults({ results }: BacktestResultsProps) {
  const { symbol, backtest_period, statistics, decisions } = results;
  const [expandedDecisions, setExpandedDecisions] = useState<Set<number>>(new Set());

  // デバッグ：決定データをコンソールに出力
  console.log('BacktestResults - decisions data:', decisions);
  console.log('BacktestResults - decisions with detailed_analysis:', 
    decisions.filter(d => d.detailed_analysis).length);
  
  // 各決定の詳細分析データをチェック
  decisions.forEach((decision, index) => {
    if (decision.detailed_analysis) {
      console.log(`Decision ${index} has detailed_analysis:`, decision.detailed_analysis);
    }
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return 'text-green-600 bg-green-50';
      case 'SELL':
        return 'text-red-600 bg-red-50';
      case 'HOLD':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return <TrendingUp className="h-4 w-4" />;
      case 'SELL':
        return <TrendingDown className="h-4 w-4" />;
      case 'HOLD':
        return <Minus className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  const toggleDecisionExpansion = (index: number) => {
    const newExpanded = new Set(expandedDecisions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedDecisions(newExpanded);
  };

  const getAnalysisIcon = (type: 'chart' | 'technical' | 'integrated') => {
    switch (type) {
      case 'chart':
        return <Eye className="h-4 w-4" />;
      case 'technical':
        return <BarChart2 className="h-4 w-4" />;
      case 'integrated':
        return <Activity className="h-4 w-4" />;
    }
  };

  const getAnalysisLabel = (type: 'chart' | 'technical' | 'integrated') => {
    switch (type) {
      case 'chart':
        return 'チャート画像分析';
      case 'technical':
        return 'テクニカル指標分析';
      case 'integrated':
        return '統合分析';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">バックテスト結果</h2>
              <p className="text-sm text-gray-600">
                {symbol} | {formatDate(backtest_period.start)} 〜 {formatDate(backtest_period.end)}
              </p>
            </div>
          </div>
          <div className="text-right space-y-1">
            <div className="text-sm text-gray-600">判断間隔</div>
            <div className="font-medium text-gray-900">
              {backtest_period.interval_minutes < 60 
                ? `${backtest_period.interval_minutes}分` 
                : `${backtest_period.interval_minutes / 60}時間`}
            </div>
            <div className="text-xs text-gray-500">
              実行期間: {(() => {
                const start = new Date(backtest_period.start);
                const end = new Date(backtest_period.end);
                const diffHours = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60));
                return diffHours < 24 ? `${diffHours}時間` : `${Math.ceil(diffHours / 24)}日`;
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2">
            <Target className="h-5 w-5 text-blue-600" />
            <div className="text-sm text-gray-600">総判断回数</div>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-2">
            {statistics.total_decisions}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <div className="text-sm text-gray-600">買いシグナル</div>
          </div>
          <div className="text-2xl font-bold text-green-600 mt-2">
            {statistics.buy_signals}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((statistics.buy_signals / statistics.total_decisions) * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2">
            <TrendingDown className="h-5 w-5 text-red-600" />
            <div className="text-sm text-gray-600">売りシグナル</div>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-2">
            {statistics.sell_signals}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((statistics.sell_signals / statistics.total_decisions) * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2">
            <Minus className="h-5 w-5 text-gray-600" />
            <div className="text-sm text-gray-600">様子見</div>
          </div>
          <div className="text-2xl font-bold text-gray-600 mt-2">
            {statistics.hold_signals}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((statistics.hold_signals / statistics.total_decisions) * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-purple-600" />
            <div className="text-sm text-gray-600">平均信頼度</div>
          </div>
          <div className="text-2xl font-bold text-purple-600 mt-2">
            {(statistics.average_confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Decision History */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">判断履歴</h3>
          <p className="text-sm text-gray-600 mt-1">
            時系列でのAI判断と価格推移
          </p>
        </div>

        <div className="p-6">
          <div className="space-y-3">
            {decisions.map((decision, index) => (
              <div key={index} className="bg-gray-50 rounded-lg">
                <div 
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => toggleDecisionExpansion(index)}
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <div className={`p-2 rounded-full ${getDecisionColor(decision.ai_decision)}`}>
                        {getDecisionIcon(decision.ai_decision)}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">
                          {decision.ai_decision}
                        </div>
                        <div className="text-sm text-gray-600">
                          信頼度: {(decision.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-600">
                      <div className="font-medium">¥{decision.price.toLocaleString()}</div>
                      <div>{formatDateTime(decision.timestamp)}</div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right max-w-xs">
                      <div className="text-sm text-gray-600">
                        {decision.reasoning.join(', ')}
                      </div>
                    </div>
                    
                    {/* 常に展開ボタンを表示し、詳細分析データの有無を示す */}
                    <div className="flex items-center space-x-2">
                      {expandedDecisions.has(index) ? (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                      <div className={`text-xs font-medium ${
                        decision.detailed_analysis 
                          ? 'text-blue-600' 
                          : 'text-gray-400'
                      }`}>
                        詳細分析{decision.detailed_analysis ? '' : '（なし）'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detailed Analysis Section */}
                {expandedDecisions.has(index) && (
                  <div className="border-t border-gray-200 p-4 bg-white">
                    {decision.detailed_analysis ? (
                      <div className="space-y-4">
                        {['chart', 'technical', 'integrated'].map((analysisType) => {
                          const key = `${analysisType}_analysis` as keyof typeof decision.detailed_analysis;
                          const analysis = decision.detailed_analysis?.[key];
                          
                          if (!analysis) return null;

                          return (
                            <div key={analysisType} className="border border-gray-200 rounded-lg p-3">
                              <div className="flex items-center space-x-2 mb-2">
                                {getAnalysisIcon(analysisType as 'chart' | 'technical' | 'integrated')}
                                <h4 className="font-medium text-gray-900">
                                  {getAnalysisLabel(analysisType as 'chart' | 'technical' | 'integrated')}
                                </h4>
                              </div>
                              
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                  <div className="text-xs text-gray-500 mb-1">判断</div>
                                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded text-sm ${getDecisionColor(analysis.decision)}`}>
                                    {getDecisionIcon(analysis.decision)}
                                    <span>{analysis.decision}</span>
                                  </div>
                                </div>
                                
                                <div>
                                  <div className="text-xs text-gray-500 mb-1">信頼度</div>
                                  <div className="text-sm font-medium">
                                    {(analysis.confidence * 100).toFixed(1)}%
                                  </div>
                                </div>
                                
                                <div>
                                  <div className="text-xs text-gray-500 mb-1">理由</div>
                                  <div className="text-sm text-gray-700">
                                    {analysis.reasoning.join(', ')}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-4 text-gray-500">
                        詳細分析データがありません
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}