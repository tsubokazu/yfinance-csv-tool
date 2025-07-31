'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { init } = useAuthStore();

  useEffect(() => {
    // アプリケーション起動時に認証状態を初期化
    init();
  }, [init]);

  return <>{children}</>;
}