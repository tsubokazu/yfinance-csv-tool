# 🎨 フロントエンド開発引き継ぎプロンプト

## 📋 現在の状況（2025年7月30日）

### ✅ バックエンド開発完了
**Phase 1.11: 立花証券API統合・WebSocketリアルタイム配信システム** が完全に実装済みです。

#### 🎯 完成済み主要機能
- ✅ **FastAPI + Supabase認証システム**: JWT認証完全統合
- ✅ **OpenAI GPT-4o AI判断システム**: LangGraph 3エージェント分析
- ✅ **立花証券API統合**: 真のリアルタイム価格データ取得
- ✅ **ハイブリッドデータアーキテクチャ**: yfinance（履歴）+ 立花証券（リアルタイム）
- ✅ **WebSocketライブ配信**: リアルタイム価格・AI判断結果配信
- ✅ **複数クライアント接続管理**: 認証付きプレミアム機能

## 🎯 フロントエンド開発目標

### React/Next.js ダッシュボード実装
以下の機能を持つ現代的なWebアプリケーションを構築します：

```bash
優先度1: コア機能
- ユーザー認証UI（ログイン・登録・プロファイル）
- WebSocketリアルタイム価格表示
- AI判断結果の可視化ダッシュボード
- バックテスト結果グラフ・チャート

優先度2: 高度機能
- 立花証券 vs yfinanceデータ切り替えUI
- 銘柄検索・ウォッチリスト管理
- ポートフォリオ管理画面
- レスポンシブデザイン（モバイル対応）
```

## 🔌 利用可能なAPI仕様

### 1. 認証エンドポイント
```typescript
// ユーザー登録
POST /api/v1/auth/register
Body: { email: string, password: string }
Response: { user: User, session: Session }

// ログイン
POST /api/v1/auth/login
Body: { email: string, password: string }
Response: { access_token: string, user: User }

// 現在ユーザー情報
GET /api/v1/auth/me
Headers: { Authorization: "Bearer <token>" }
Response: { user: User, profile?: UserProfile }
```

### 2. トレーディングデータAPI
```typescript
// 基本トレーディングデータ
POST /api/v1/trading/decision
Body: { symbol: string, timestamp: string }
Response: { 
  symbol: string,
  current_price: number,
  technical_indicators: TechnicalIndicators,
  market_data: MarketContext 
}

// AI判断（認証必須・プレミアム）
POST /api/v1/trading/ai-decision
Headers: { Authorization: "Bearer <token>" }
Body: { symbol: string, timestamp: string }
Response: {
  decision: "BUY" | "SELL" | "HOLD",
  confidence: number,
  strategy: string,
  reasoning: string,
  entry_conditions: string[]
}

// 連続バックテスト（認証必須・プレミアム）
POST /api/v1/trading/ai-backtest
Headers: { Authorization: "Bearer <token>" }
Body: { 
  symbol: string, 
  start_time: string,
  end_time: string,
  interval_minutes: number
}
Response: { results: BacktestResult[] }
```

### 3. WebSocketリアルタイム配信
```typescript
// 一般ライブ配信（認証不要）
WebSocket: ws://localhost:8000/api/v1/ws/live

// プレミアムライブ配信（認証必須）
WebSocket: ws://localhost:8000/api/v1/ws/live/authenticated?token=<jwt_token>

// メッセージ形式
Send: { type: "subscribe", symbol: "6723.T" }
Receive: {
  type: "price_update",
  symbol: "6723.T",
  current_price: 1234.5,
  price_change: -12.3,
  price_change_percent: -0.98,
  timestamp: "2025-07-30T10:30:00"
}

// AI判断リクエスト（認証済みのみ）
Send: { type: "ai_decision_request", symbol: "6723.T" }
Receive: {
  type: "ai_decision_result",
  symbol: "6723.T",
  decision_data: AIDecisionResult,
  timestamp: "2025-07-30T10:30:00"
}
```

## 🛠 推奨技術スタック

### フロントエンド
```bash
# 基本フレームワーク
- React 18 + Next.js 14 (App Router)
- TypeScript
- Tailwind CSS

# 状態管理・データフェッチ
- Zustand または Redux Toolkit
- TanStack Query (React Query)
- WebSocket用: native WebSocket API

# UI・チャート
- Recharts または Chart.js (価格チャート)
- Headless UI または Radix UI (コンポーネント)
- Lucide React (アイコン)

# 認証
- JWT トークン管理
- ローカルストレージ または Cookie
```

### 推奨プロジェクト構造
```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── login/
│   │   ├── dashboard/
│   │   └── layout.tsx
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
│   │   ├── auth.ts      # 認証ヘルパー
│   │   └── websocket.ts # WebSocket管理
│   ├── types/           # TypeScript型定義
│   │   ├── auth.ts
│   │   ├── trading.ts
│   │   └── api.ts
│   └── store/           # 状態管理
│       ├── authStore.ts
│       ├── tradingStore.ts
│       └── websocketStore.ts
├── public/
└── package.json
```

## 🚀 開発開始手順

### 1. 環境セットアップ
```bash
# フロントエンド用ディレクトリ作成
cd /Users/kazusa/Develop/daytraid/daytraid/yfinance-csv-tool/
mkdir frontend && cd frontend

# Next.js プロジェクト初期化
npx create-next-app@latest . --typescript --tailwind --app

# 必要パッケージインストール
npm install @tanstack/react-query zustand recharts
npm install lucide-react @headlessui/react
npm install axios ws @types/ws
```

### 2. バックエンド起動確認
```bash
cd ../backend
uvicorn app.main:app --reload --port 8000

# API動作確認
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ws/websocket/status
```

### 3. 基本認証システム実装
```typescript
// lib/api.ts - API クライアント基盤
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// hooks/useAuth.ts - 認証フック
export const useAuth = () => {
  // JWT トークン管理
  // ログイン・ログアウト機能
  // ユーザー状態管理
};

// hooks/useWebSocket.ts - WebSocket フック  
export const useWebSocket = (authenticated = false) => {
  // WebSocket接続管理
  // メッセージ送受信
  // 自動再接続
};
```

## 💡 重要な実装ポイント

### 1. WebSocketリアルタイム更新
```typescript
// リアルタイム価格表示の例
const PriceDisplay = ({ symbol }: { symbol: string }) => {
  const { subscribe, data } = useWebSocket();
  
  useEffect(() => {
    subscribe(symbol);
  }, [symbol]);
  
  return (
    <div className="price-card">
      <h3>{symbol}</h3>
      <span className="price">{data?.current_price}</span>
      <span className={data?.price_change > 0 ? 'text-green' : 'text-red'}>
        {data?.price_change_percent}%
      </span>
    </div>
  );
};
```

### 2. AI判断結果の可視化
```typescript
// AI判断ダッシュボードの例
const AIDecisionDashboard = () => {
  const { data: aiDecision } = useAIDecision(symbol);
  
  return (
    <div className="ai-dashboard">
      <DecisionBadge decision={aiDecision.decision} />
      <ConfidenceChart confidence={aiDecision.confidence} />
      <ReasoningText reasoning={aiDecision.reasoning} />
      <EntryConditionsList conditions={aiDecision.entry_conditions} />
    </div>
  );
};
```

## 🔧 開発環境設定

### 環境変数（.env.local）
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_APP_NAME=yfinance Trading Platform
```

## 📊 Git状態

現在の状況:
- ✅ Phase 1.11 完了コミット済み（ローカル）
- ✅ **Phase 2.1 完了**: フロントエンド基盤セットアップ完了 (2025-07-30)
- ✅ **Phase 2.2 完了**: 基本認証システム実装完了 (2025-07-30)
- ⚠️ プッシュ時にGitHubセキュリティで過去のAPIキー検出
- 📝 対応: https://github.com/tsubokazu/yfinance-csv-tool/security/secret-scanning/unblock-secret/30YRrQ8PXzJqi7aFUoaAwqPHMBS でシークレット許可が必要

**Phase 2.2 実装完了内容:**
- Next.js 15.4.5 + React 19 + TypeScript プロジェクト完全セットアップ
- TanStack Query v5.83 + Zustand v5.0.6 + Recharts v3.1 統合
- 型安全なAPIクライアント・WebSocket管理システム実装
- 認証・トレーディング用Zustand状態管理ストア実装
- **基本認証UI完成**: LoginForm・RegisterForm・ログインページ(/login)
- **フロントエンド動作確認**: http://localhost:3000 正常起動・バックエンドAPI連携確認
- **Supabase認証統合**: バックエンド認証エンドポイント動作確認済み

## 💬 次のセッション開始プロンプト

```
yfinance Trading Platform のフロントエンド開発 Phase 2.3 を開始します。

📋 現在の状況:
- ✅ Phase 1.11: バックエンド完全実装済み（立花証券API統合・WebSocketリアルタイム配信）
- ✅ Phase 2.1: フロントエンド基盤セットアップ完了
- ✅ Phase 2.2: 基本認証システム実装完了 (2025-07-30)
- 🚀 フロントエンド動作確認済み: http://localhost:3000/login (認証UI完成)
- 🔗 バックエンドAPI連携確認済み: http://localhost:8000/api/v1/auth/* 
- 作業ディレクトリ: /Users/kazusa/Develop/daytraid/daytraid/yfinance-csv-tool/

🎯 Phase 2.3 目標:
メインダッシュボードレイアウト実装
- 認証後のダッシュボード画面(/dashboard)作成
- ナビゲーション・サイドバー・メインコンテンツエリア
- WebSocketリアルタイム通信準備
- 価格表示・ウォッチリスト基礎UI

詳細は FRONTEND_HANDOVER.md を参照してください。メインダッシュボードから始めましょう！
```

## 📚 参考ドキュメント

- **API仕様書**: http://localhost:8000/docs（Swagger UI）
- **WebSocket動作確認**: `/api/v1/ws/websocket/status`
- **バックエンド実装詳細**: `docs/CLAUDE.md`
- **認証システム**: `backend/app/core/auth.py`
- **WebSocket実装**: `backend/app/api/v1/endpoints/websocket.py`