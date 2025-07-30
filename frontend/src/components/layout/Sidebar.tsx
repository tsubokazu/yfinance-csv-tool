'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import {
  TrendingUp,
  BarChart3,
  Wallet,
  Settings,
  LogOut,
  Home,
  Activity,
  Brain,
  X
} from 'lucide-react';

interface SidebarProps {
  onClose?: () => void;
}

const navigation = [
  { name: 'ダッシュボード', href: '/dashboard', icon: Home, current: true },
  { name: 'リアルタイム価格', href: '/dashboard/prices', icon: TrendingUp, current: false },
  { name: 'AI判断システム', href: '/dashboard/ai', icon: Brain, current: false },
  { name: 'バックテスト', href: '/dashboard/backtest', icon: BarChart3, current: false },
  { name: 'ポートフォリオ', href: '/dashboard/portfolio', icon: Wallet, current: false },
  { name: 'アクティビティ', href: '/dashboard/activity', icon: Activity, current: false },
];

export function Sidebar({ onClose }: SidebarProps) {
  const { logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
      {/* Close button for mobile */}
      {onClose && (
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <span className="text-lg font-semibold text-gray-900">Trading Platform</span>
          </div>
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={onClose}
          >
            <X className="h-6 w-6" />
          </button>
        </div>
      )}

      {/* Logo for desktop */}
      {!onClose && (
        <div className="flex h-16 shrink-0 items-center space-x-2">
          <TrendingUp className="h-8 w-8 text-blue-600" />
          <span className="text-lg font-semibold text-gray-900">Trading Platform</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <a
                    href={item.href}
                    className={`
                      group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                      ${item.current
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                      }
                    `}
                  >
                    <item.icon
                      className={`h-6 w-6 shrink-0 ${
                        item.current ? 'text-blue-600' : 'text-gray-400 group-hover:text-blue-600'
                      }`}
                    />
                    {item.name}
                  </a>
                </li>
              ))}
            </ul>
          </li>

          {/* Settings section */}
          <li className="mt-auto">
            <ul role="list" className="-mx-2 space-y-1">
              <li>
                <a
                  href="/dashboard/settings"
                  className="text-gray-700 hover:text-blue-600 hover:bg-gray-50 group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold"
                >
                  <Settings className="h-6 w-6 shrink-0 text-gray-400 group-hover:text-blue-600" />
                  設定
                </a>
              </li>
              <li>
                <button
                  onClick={handleLogout}
                  className="text-gray-700 hover:text-red-600 hover:bg-red-50 group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold w-full text-left"
                >
                  <LogOut className="h-6 w-6 shrink-0 text-gray-400 group-hover:text-red-600" />
                  ログアウト
                </button>
              </li>
            </ul>
          </li>
        </ul>
      </nav>
    </div>
  );
}