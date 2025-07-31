'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { BacktestForm } from '@/components/backtest/BacktestForm';
import { BacktestResults } from '@/components/backtest/BacktestResults';
import { BacktestChart } from '@/components/backtest/BacktestChart';
import { useAuth } from '@/hooks/useAuth';

interface BacktestResult {
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
  }>;
}

export default function BacktestPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<{
    current: number;
    total: number;
    message: string;
  } | null>(null);
  const [authInitialized, setAuthInitialized] = useState(false);

  // 認証状態の初期化を監視
  useEffect(() => {
    if (!isLoading) {
      setAuthInitialized(true);
    }
  }, [isLoading]);

  const handleBacktestRun = async (params: {
    symbol: string;
    startDate: string;
    endDate: string;
    intervalMinutes: number;
    maxDecisions: number;
  }) => {
    setIsRunning(true);
    setError(null);
    setResults(null);
    setProgress(null);

    try {
      console.log('バックテスト開始:', params);
      console.log('認証状態デバッグ:', {
        isAuthenticated,
        isLoading,
        hasToken: !!localStorage.getItem('auth-token'),
        tokenValue: localStorage.getItem('auth-token')?.substring(0, 20) + '...'
      });
      
      // 推定実行時間を計算
      const totalMinutes = Math.ceil((new Date(params.endDate).getTime() - new Date(params.startDate).getTime()) / (1000 * 60));
      const estimatedDecisions = Math.min(Math.ceil(totalMinutes / params.intervalMinutes), params.maxDecisions);
      
      setProgress({
        current: 0,
        total: estimatedDecisions,
        message: 'バックテスト実行準備中...'
      });
      
      // 認証状態を確認（初期化完了まで待機）
      if (!authInitialized || isLoading) {
        throw new Error('認証状態を確認中です。しばらくお待ちください。');
      }
      
      if (!isAuthenticated) {
        throw new Error('認証が必要です。ログインしてください。');
      }
      
      const token = localStorage.getItem('auth-token');
      if (!token) {
        throw new Error('認証トークンが見つかりません。再度ログインしてください。');
      }

      setProgress({
        current: 0,
        total: estimatedDecisions,
        message: 'API接続中...'
      });

      // API呼び出し実装（直接バックエンドをテスト）
      const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${backendUrl}/trading/ai-backtest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`, // 認証トークンを追加
        },
        body: JSON.stringify({
          symbol: params.symbol,
          start_time: new Date(params.startDate).toISOString(),
          end_time: new Date(params.endDate).toISOString(),
          interval_minutes: params.intervalMinutes,
          max_decisions: params.maxDecisions,
        }),
      });

      console.log('API Response Status:', response.status);
      console.log('API Response Headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `API呼び出しエラー: ${response.status} ${response.statusText}`
        );
      }

      setProgress({
        current: Math.floor(estimatedDecisions * 0.8),
        total: estimatedDecisions,
        message: 'AI判断結果を処理中...'
      });

      const responseData = await response.json();
      const formattedResult: BacktestResult = {
        symbol: responseData.symbol,
        backtest_period: {
          start: responseData.backtest_period.start,
          end: responseData.backtest_period.end,
          interval_minutes: responseData.backtest_period.interval_minutes,
        },
        statistics: {
          total_decisions: responseData.statistics.total_decisions,
          buy_signals: responseData.statistics.buy_signals,
          sell_signals: responseData.statistics.sell_signals,
          hold_signals: responseData.statistics.hold_signals,
          average_confidence: responseData.statistics.average_confidence,
        },
        decisions: responseData.decisions.map((decision: any) => ({
          timestamp: decision.timestamp,
          price: decision.price,
          ai_decision: decision.ai_decision,
          confidence: decision.confidence,
          reasoning: decision.reasoning,
          analysis_efficiency: decision.analysis_efficiency,
        })),
      };
      
      setProgress({
        current: estimatedDecisions,
        total: estimatedDecisions,
        message: 'バックテスト完了！結果を表示中...'
      });

      // 少し遅延を入れて完了感を演出
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setResults(formattedResult);
    } catch (err) {
      console.error('バックテストエラー:', err);
      const errorMessage = err instanceof Error ? err.message : 'バックテストの実行に失敗しました';
      setError(errorMessage);
    } finally {
      setIsRunning(false);
      setProgress(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-3xl font-bold text-gray-900">バックテスト</h1>
          <p className="text-gray-600 mt-2">
            AI判断システムを使った過去データでの取引シミュレーション
          </p>
        </div>

        {/* Backtest Form */}
        <BacktestForm 
          onRun={handleBacktestRun}
          isRunning={isRunning || !authInitialized || isLoading}
        />

        {/* Auth Status Debug (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs">
            <h3 className="font-medium text-gray-900 mb-2">認証状態デバッグ</h3>
            <div className="space-y-1 text-gray-600">
              <p>isAuthenticated: {isAuthenticated.toString()}</p>
              <p>isLoading: {isLoading.toString()}</p>
              <p>authInitialized: {authInitialized.toString()}</p>
              <p>hasToken: {typeof window !== 'undefined' ? (!!localStorage.getItem('auth-token')).toString() : 'N/A'}</p>
            </div>
          </div>
        )}

        {/* Progress Display */}
        {progress && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center space-x-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-gray-900">バックテスト実行中</h3>
                  <span className="text-sm text-gray-600">
                    {progress.current}/{progress.total}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${Math.min((progress.current / progress.total) * 100, 100)}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-600 mt-2">{progress.message}</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Results Display */}
        {results && (
          <div className="space-y-6">
            <BacktestResults results={results} />
            <BacktestChart results={results} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}