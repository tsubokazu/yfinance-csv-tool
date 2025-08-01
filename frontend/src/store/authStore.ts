import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserProfile, LoginRequest, RegisterRequest } from '@/types/auth';
import { apiClient } from '@/lib/api';

interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<void>;
  clearError: () => void;
  init: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      profile: null,
      isAuthenticated: false, // 初期値をfalseに設定し、init()で正確な状態を設定
      isLoading: true, // 初期化中はローディング状態を維持
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiClient.login({ email, password });
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          });
          
          // Fetch user profile after successful login
          try {
            await get().getCurrentUser();
          } catch (profileError) {
            console.warn('Failed to fetch user profile after login:', profileError);
          }
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiClient.register({ email, password });
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await apiClient.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            profile: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      getCurrentUser: async () => {
        const state = get();
        if (!state.isAuthenticated && !localStorage.getItem('auth-token')) return;
        
        set({ isLoading: true });
        try {
          const { user, profile } = await apiClient.getCurrentUser();
          set({
            user,
            profile,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          console.error('Failed to get current user:', error);
          if (error.response?.status === 401) {
            // Token is invalid, clear authentication state
            set({
              user: null,
              profile: null,
              isAuthenticated: false,
              isLoading: false,
            });
          } else {
            set({ isLoading: false });
          }
        }
      },

      clearError: () => set({ error: null }),
      
      // Initialize user data if token exists
      init: async () => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('auth-token');
          console.log('Auth Store Init - Token found:', !!token);
          
          if (token) {
            set({ isAuthenticated: true, isLoading: true });
            try {
              await get().getCurrentUser();
              console.log('Auth Store Init - User data loaded successfully');
              set({ isLoading: false }); // 成功時にローディング完了
            } catch (error) {
              console.error('Failed to initialize user data:', error);
              // トークンが無効な場合はクリア
              localStorage.removeItem('auth-token');
              set({ 
                isAuthenticated: false,
                user: null,
                profile: null,
                isLoading: false
              });
            }
          } else {
            set({ 
              isAuthenticated: false,
              user: null,
              profile: null,
              isLoading: false
            });
          }
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        profile: state.profile,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        console.log('Zustand onRehydrateStorage called');
        // ページロード時は必ずinit()を実行してトークンと状態を同期
        if (state && typeof window !== 'undefined') {
          setTimeout(() => {
            (state as any).init?.();
          }, 0);
        }
      },
    }
  )
);