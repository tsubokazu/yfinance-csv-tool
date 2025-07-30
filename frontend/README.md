# 📊 yfinance Trading Platform - Frontend

React/Next.js製のWebSocketリアルタイム対応トレーディングダッシュボード

## 🎯 概要

バックエンド（FastAPI + Supabase + OpenAI GPT-4o + 立花証券API + WebSocket）と統合されたモダンなWebアプリケーション。リアルタイム価格配信、AI判断結果の可視化、バックテスト機能を提供。

## 🛠 技術スタック

### コアフレームワーク
- **Next.js 15.4.5** (App Router) + **React 19** + **TypeScript**
- **Tailwind CSS v4** - スタイリング

### 状態管理・データフェッチング
- **TanStack Query v5.83** - サーバーサイドデータ管理
- **Zustand v5.0.6** - 軽量クライアント状態管理

### データ可視化・UI
- **Recharts v3.1** - React特化チャートライブラリ
- **Lucide React** - アイコン
- **Headless UI** - アクセシブルコンポーネント

### 通信
- **Native WebSocket API** - リアルタイム通信
- **Axios** - HTTP クライアント

## 📁 プロジェクト構造

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── login/        # ログインページ
│   │   ├── dashboard/    # ダッシュボード
│   │   └── layout.tsx    # ルートレイアウト
│   ├── components/       # 再利用可能コンポーネント
│   │   ├── ui/          # 基本UIコンポーネント
│   │   ├── charts/      # チャート関連
│   │   └── auth/        # 認証関連
│   ├── hooks/           # カスタムフック
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   └── useTrading.ts
│   ├── lib/             # ユーティリティ
│   │   ├── api.ts       # API クライアント
│   │   └── websocket.ts # WebSocket管理
│   ├── types/           # TypeScript型定義
│   │   ├── auth.ts
│   │   ├── trading.ts
│   │   └── api.ts
│   └── store/           # 状態管理
│       ├── authStore.ts
│       └── tradingStore.ts
├── public/
└── package.json
```

## 🚀 セットアップ・起動

### 前提条件
- Node.js 18+ 
- npm
- バックエンドサーバーが起動済み（http://localhost:8000）

### インストール・起動
```bash
# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev

# 本番ビルド
npm run build
npm start

# リント
npm run lint
```

アプリケーション: http://localhost:3000

## 🔌 API統合

### 利用可能なエンドポイント

#### 認証
- `POST /api/v1/auth/register` - ユーザー登録
- `POST /api/v1/auth/login` - ログイン  
- `GET /api/v1/auth/me` - 現在ユーザー情報

#### トレーディングデータ
- `POST /api/v1/trading/decision` - 基本トレーディングデータ
- `POST /api/v1/trading/ai-decision` - AI判断（認証必須）
- `POST /api/v1/trading/ai-backtest` - バックテスト（認証必須）

#### WebSocketリアルタイム配信
- `ws://localhost:8000/api/v1/ws/live` - 一般ライブ配信
- `ws://localhost:8000/api/v1/ws/live/authenticated?token=<jwt>` - プレミアム配信

## 🎨 主要機能

### 優先度1: コア機能
- ✅ ユーザー認証UI（ログイン・登録・プロファイル）
- ✅ WebSocketリアルタイム価格表示
- 🔄 AI判断結果の可視化ダッシュボード
- 🔄 バックテスト結果グラフ・チャート

### 優先度2: 高度機能  
- 🔄 立花証券 vs yfinanceデータ切り替えUI
- 🔄 銘柄検索・ウォッチリスト管理
- 🔄 ポートフォリオ管理画面
- 🔄 レスポンシブデザイン（モバイル対応）

## 🔧 環境変数

`.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_APP_NAME=yfinance Trading Platform
```

## 📊 状態管理

### 認証ストア (`useAuthStore`)
- ユーザー情報・認証状態
- ログイン・ログアウト・登録機能
- JWT トークン管理

### トレーディングストア (`useTradingStore`) 
- リアルタイム価格データ
- AI判断結果
- ウォッチリスト・選択銘柄
- WebSocket接続状態

## 🔌 WebSocket統合

```typescript
// 基本使用例
const wsManager = new WebSocketManager(authenticated);
await wsManager.connect();

// 価格更新購読
wsManager.subscribeToSymbol('6723.T');
wsManager.addEventListener('price_update:6723.T', (data) => {
  console.log('Price update:', data);
});

// AI判断リクエスト（認証必須）
wsManager.requestAIDecision('6723.T');
```

## 🧪 開発状況

**Phase 2.1 完了**: フロントエンド基盤セットアップ

- ✅ Next.js 15 + 最新技術スタック統合
- ✅ 型安全なAPIクライアント・WebSocket管理
- ✅ Zustand状態管理システム  
- ✅ 推奨プロジェクト構造実装
- 🔄 基本認証システム実装中

**Next Steps**: 認証UI→WebSocketリアルタイム通信→AI判断ダッシュボード

## 🔗 関連ドキュメント

- [バックエンドドキュメント](../backend/README.md)
- [API仕様書](http://localhost:8000/docs) - Swagger UI  
- [フロントエンド引き継ぎ仕様](../FRONTEND_HANDOVER.md)