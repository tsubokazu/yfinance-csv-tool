'use client';

import { Menu, Bell, User } from 'lucide-react';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';

interface HeaderProps {
  onMenuClick: () => void;
  user?: {
    email?: string;
    name?: string;
  } | null;
}

export function Header({ onMenuClick, user }: HeaderProps) {
  const { isConnected, connectionError } = useWebSocketContext();

  return (
    <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      {/* Mobile menu button */}
      <button
        type="button"
        className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
        onClick={onMenuClick}
      >
        <Menu className="h-6 w-6" />
      </button>

      {/* Separator */}
      <div className="h-6 w-px bg-gray-200 lg:hidden" />

      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        {/* Page title or breadcrumb */}
        <div className="flex items-center">
          <h1 className="text-lg font-semibold text-gray-900">
            ダッシュボード
          </h1>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-x-4 lg:gap-x-6 ml-auto">
          {/* Connection status indicator */}
          <div className="flex items-center gap-x-2">
            <div 
              className={`h-2 w-2 rounded-full ${
                isConnected 
                  ? 'bg-green-400 animate-pulse' 
                  : connectionError
                  ? 'bg-red-400'
                  : 'bg-yellow-400'
              }`}
            ></div>
            <span className="text-sm text-gray-500">
              {isConnected 
                ? 'WebSocket接続中' 
                : connectionError 
                ? 'WebSocket接続エラー'
                : 'WebSocket接続待機中'
              }
            </span>
          </div>

          {/* Notifications */}
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500"
          >
            <Bell className="h-6 w-6" />
          </button>

          {/* Separator */}
          <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-200" />

          {/* Profile dropdown placeholder */}
          <div className="flex items-center gap-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500">
              <User className="h-5 w-5 text-white" />
            </div>
            <span className="hidden text-sm font-semibold leading-6 text-gray-900 lg:block">
              {user?.email || 'ユーザー'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}