# 🎯 Phase 2.4 リアルタイムデータ統合・チャート実装 引き継ぎプロンプト

## 📋 現在の状況（2025年7月30日）

### ✅ 完了済み内容

**Phase 1.11: バックエンド完全実装済み**
- FastAPI + Supabase認証システム
- OpenAI GPT-4o AI判断システム (LangGraph 3エージェント)
- 立花証券API統合 (リアルタイム価格データ)
- WebSocketライブ配信システム
- ハイブリッドデータアーキテクチャ (yfinance + 立花証券)

**Phase 2.1: フロントエンド基盤セットアップ完了**
- Next.js 15.4.5 + React 19 + TypeScript
- TanStack Query v5.83 + Zustand v5.0.6 + Recharts v3.1
- 型安全なAPIクライアント・WebSocket管理システム

**Phase 2.2: 基本認証システム実装完了**
- LoginForm・RegisterForm・ログインページ(/login)
- Supabase認証統合・JWT管理
- 認証状態管理 (Zustand)

**Phase 2.3: メインダッシュボードレイアウト実装完了**
- 完全なダッシュボードレイアウト (/dashboard)
- レスポンシブナビゲーション (Sidebar, Header)
- メインコンテンツエリア (MarketOverview, WatchList, PriceDisplay, AIDecisionPanel)
- WebSocketリアルタイム基盤 (WebSocketProvider, 接続状態表示)
- 認証付きプロテクテッドルート実装

### 🚀 動作確認済み環境

- **フロントエンド**: http://localhost:3001/dashboard
- **バックエンドAPI**: http://localhost:8000/api/v1/*
- **WebSocket接続**: 準備完了・状態表示実装済み
- **認証フロー**: ログイン → ダッシュボード完全動作

## 🎯 Phase 2.4 実装目標

### 1. 実際のWebSocketデータ統合 (最優先)

**現在の状況**: WebSocket基盤は完成しているが、UIはダミーデータを表示中

**実装内容**:
- `WatchList` コンポーネントでリアルタイム価格更新
- `PriceDisplay` コンポーネントでリアルタイムデータ表示
- `MarketOverview` でリアルタイム市場データ統合
- WebSocketから受信したデータをZustand storeに保存・UIに反映

**技術詳細**:
```typescript
// すでに実装済みのWebSocketフック活用
const { subscribeToSymbol, unsubscribeFromSymbol } = useWebSocketContext();

// TradingStoreの価格データをコンポーネントで使用
const { prices, updatePrice } = useTradingStore();
```

### 2. リアルタイム価格チャート実装

**実装内容**:
- Rechartsを使用した価格チャート実装
- `PriceDisplay` コンポーネント内にチャート追加
- WebSocketから受信した価格データをチャートに反映
- 時系列データの蓄積・表示

**チャート仕様**:
- ローソク足チャート (OHLC)
- リアルタイム更新
- 時間軸切り替え (1分, 5分, 15分, 1時間)
- 出来高表示

### 3. AI判断APIの実際の連携

**現在の状況**: `AIDecisionPanel` はダミーデータを表示中

**実装内容**:
- バックエンドAI判断API (`/api/v1/trading/ai-decision`) との連携
- WebSocket経由でのAI判断リクエスト・結果受信
- AI判断結果のリアルタイム表示・更新
- 信頼度・戦略・判断根拠の動的更新

### 4. バックテスト結果表示機能

**実装内容**:
- バックテストAPI (`/api/v1/trading/ai-backtest`) との連携
- バックテスト結果チャート・グラフ表示
- 新しいページ `/dashboard/backtest` 作成
- パフォーマンス指標の可視化

### 5. 立花証券 vs yfinanceデータ切り替え機能

**実装内容**:
- データソース切り替えUI実装
- WebSocketでのデータソース指定
- 価格データの出所表示
- リアルタイム vs 履歴データの切り替え

## 🛠 実装方針・技術詳細

### WebSocketデータ統合

**既存の基盤活用**:
```typescript
// frontend/src/hooks/useWebSocket.ts - 既に実装済み
// frontend/src/lib/websocket.ts - WebSocketManager実装済み
// frontend/src/store/tradingStore.ts - 価格データ管理準備済み
```

**実装手順**:
1. `useTradingStore` の価格データをコンポーネントで使用
2. WebSocket接続後、自動的にデフォルト銘柄を購読
3. 受信した価格データをリアルタイムでUI更新

### チャート実装 (Recharts使用)

**推奨コンポーネント構造**:
```typescript
// components/charts/PriceChart.tsx
interface PriceChartProps {
  symbol: string;
  data: PriceData[];
  timeframe: '1m' | '5m' | '15m' | '1h';
}

// components/charts/CandlestickChart.tsx - ローソク足
// components/charts/VolumeChart.tsx - 出来高
```

### API連携強化

**必要なAPI統合**:
- `POST /api/v1/trading/ai-decision` - AI判断取得
- `POST /api/v1/trading/ai-backtest` - バックテスト実行
- WebSocket `ai_decision_request` - リアルタイムAI判断

## 📁 実装予定ファイル構造

```
frontend/src/
├── app/
│   └── dashboard/
│       ├── backtest/
│       │   └── page.tsx              # バックテスト結果ページ
│       ├── charts/
│       │   └── page.tsx              # チャート専用ページ
│       └── settings/
│           └── page.tsx              # 設定ページ
├── components/
│   ├── charts/
│   │   ├── PriceChart.tsx           # メイン価格チャート
│   │   ├── CandlestickChart.tsx     # ローソク足チャート
│   │   ├── VolumeChart.tsx          # 出来高チャート
│   │   └── BacktestResultChart.tsx  # バックテスト結果
│   ├── trading/
│   │   ├── DataSourceSwitcher.tsx   # データソース切り替え
│   │   ├── TimeframeSwitcher.tsx    # 時間軸切り替え
│   │   └── RealTimePriceDisplay.tsx # リアルタイム価格
│   └── backtest/
│       ├── BacktestForm.tsx         # バックテスト設定
│       ├── BacktestResults.tsx      # 結果表示
│       └── PerformanceMetrics.tsx   # パフォーマンス指標
├── hooks/
│   ├── useRealTimePrice.ts          # リアルタイム価格管理
│   ├── useAIDecision.ts            # AI判断管理
│   └── useBacktest.ts              # バックテスト管理
└── types/
    ├── chart.ts                     # チャート関連型
    └── backtest.ts                  # バックテスト関連型
```

## 🎬 開発開始プロンプト

```
yfinance Trading Platform のフロントエンド開発 Phase 2.4 を開始します。

📋 現在の状況:
- ✅ Phase 1.11: バックエンド完全実装済み（立花証券API統合・WebSocketリアルタイム配信）
- ✅ Phase 2.1: フロントエンド基盤セットアップ完了
- ✅ Phase 2.2: 基本認証システム実装完了 (2025-07-30)
- ✅ Phase 2.3: メインダッシュボードレイアウト実装完了 (2025-07-30)
- 🚀 フロントエンド完全動作確認済み: http://localhost:3001/dashboard (ダッシュボード完成)
- 🔗 WebSocketリアルタイム基盤準備完了: 接続状態表示・デフォルト銘柄購読
- 作業ディレクトリ: /Users/kazusa/Develop/daytraid/daytraid/yfinance-csv-tool/

🎯 Phase 2.4 目標:
リアルタイムデータ統合・チャート実装
- 実際のWebSocketデータとUI連携
- リアルタイム価格チャート実装（Recharts使用）
- AI判断APIの実際の連携・動作確認
- バックテスト結果表示機能
- 立花証券 vs yfinanceデータ切り替け機能

詳細は FRONTEND_HANDOVER.md と docs/PHASE_2_4_HANDOVER.md を参照してください。
実際のWebSocketデータ統合から始めましょう！
```

## 📚 参考ドキュメント

- **API仕様書**: http://localhost:8000/docs（Swagger UI）
- **WebSocket動作確認**: `/api/v1/ws/websocket/status`
- **メインドキュメント**: `FRONTEND_HANDOVER.md`
- **バックエンド実装詳細**: `docs/CLAUDE.md`
- **認証システム**: `backend/app/core/auth.py`
- **WebSocket実装**: `backend/app/api/v1/endpoints/websocket.py`

---

**重要**: Phase 2.4では「見た目の完成」から「実際のデータ連携」に移行します。バックエンドAPIとの完全統合が最優先課題です。