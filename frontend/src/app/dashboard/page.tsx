'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { PriceDisplay } from '@/components/trading/PriceDisplay';
import { WatchList } from '@/components/trading/WatchList';
import { AIDecisionPanel } from '@/components/trading/AIDecisionPanel';
import { MarketOverview } from '@/components/trading/MarketOverview';

export default function DashboardPage() {
  const { isAuthenticated, user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">認証確認中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-3xl font-bold text-gray-900">
            yfinance Trading Platform
          </h1>
          <p className="text-gray-600 mt-2">
            リアルタイムトレーディングダッシュボード
          </p>
        </div>

        {/* Market Overview */}
        <MarketOverview />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Watch List */}
          <div className="lg:col-span-1">
            <WatchList />
          </div>

          {/* Price Display */}
          <div className="lg:col-span-2">
            <PriceDisplay />
          </div>
        </div>

        {/* AI Decision Panel */}
        <AIDecisionPanel />
      </div>
    </DashboardLayout>
  );
}