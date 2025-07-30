'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { AlertCircle, Mail, Lock, User } from 'lucide-react';

interface RegisterFormProps {
  onSwitchToLogin?: () => void;
}

export function RegisterForm({ onSwitchToLogin }: RegisterFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  
  const router = useRouter();
  const { register, isRegisterLoading, registerError, clearError } = useAuth();

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!email) {
      errors.email = 'メールアドレスは必須です';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = '有効なメールアドレスを入力してください';
    }

    if (!password) {
      errors.password = 'パスワードは必須です';
    } else if (password.length < 6) {
      errors.password = 'パスワードは6文字以上で入力してください';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'パスワード確認は必須です';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'パスワードが一致しません';
    }

    if (!fullName.trim()) {
      errors.fullName = '名前は必須です';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validateForm()) {
      return;
    }

    try {
      await register({ email, password });
      router.push('/dashboard');
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const errorMessage = registerError?.message || 
    (registerError as any)?.response?.data?.detail || 
    '登録に失敗しました';

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">新規登録</CardTitle>
        <CardDescription className="text-center">
          yfinance Trading Platformアカウントを作成
        </CardDescription>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {registerError && (
            <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="space-y-2">
            <div className="relative">
              <Input
                label="名前"
                type="text"
                placeholder="山田太郎"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                error={validationErrors.fullName}
                required
                disabled={isRegisterLoading}
                className="pl-10"
              />
              <User className="absolute left-3 top-8 h-4 w-4 text-gray-400" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Input
                label="メールアドレス"
                type="email"
                placeholder="your@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={validationErrors.email}
                required
                disabled={isRegisterLoading}
                className="pl-10"
              />
              <Mail className="absolute left-3 top-8 h-4 w-4 text-gray-400" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Input
                label="パスワード"
                type={showPassword ? 'text' : 'password'}
                placeholder="6文字以上のパスワード"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={validationErrors.password}
                required
                disabled={isRegisterLoading}
                className="pl-10"
              />
              <Lock className="absolute left-3 top-8 h-4 w-4 text-gray-400" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Input
                label="パスワード確認"
                type={showPassword ? 'text' : 'password'}
                placeholder="パスワードを再入力"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                error={validationErrors.confirmPassword}
                required
                disabled={isRegisterLoading}
                className="pl-10"
              />
              <Lock className="absolute left-3 top-8 h-4 w-4 text-gray-400" />
              <button
                type="button"
                className="absolute right-3 top-8 text-sm text-gray-500 hover:text-gray-700"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isRegisterLoading}
              >
                {showPassword ? '隠す' : '表示'}
              </button>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full"
            loading={isRegisterLoading}
            disabled={isRegisterLoading}
          >
            アカウント作成
          </Button>

          {onSwitchToLogin && (
            <div className="text-center text-sm text-gray-600">
              既にアカウントをお持ちの方は{' '}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-blue-600 hover:text-blue-500 font-medium"
                disabled={isRegisterLoading}
              >
                ログイン
              </button>
            </div>
          )}
        </CardFooter>
      </form>
    </Card>
  );
}