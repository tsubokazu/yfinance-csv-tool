# 🚀 Next.js + FastAPI フルスタック トレーディング プラットフォーム

**Phase 11 完了** | Next.js 15.4.5 + React 19.1 + FastAPI + AI + WebSocket リアルタイム

## 🎯 プロジェクト概要

yfinanceライブラリとリアルタイムAPI統合による包括的な株価分析から、AI売買判断、WebSocketライブ配信まで対応した次世代トレーディング分析プラットフォームです。フロントエンドからバックエンドまで完全統合されたフルスタック実装が完了しています。

### 🎨 フロントエンド機能（Phase 11 新規完了）
- ⚡ **Next.js 15.4.5 + React 19.1** - 最新フレームワークによる高性能SPA
- 🔐 **Supabase認証システム** - JWT認証・ログイン・認証ガード完全実装
- 📊 **リアルタイムチャート表示** - Recharts による美しい株価可視化
- 🎯 **バックテスト機能UI** - 期間・間隔設定と結果表示システム
- 📡 **WebSocketリアルタイム通信** - 価格・AI判断のライブ更新
- 🎨 **レスポンシブデザイン** - TailwindCSS による美しいUI/UX
- 🛡️ **認証ガード機能** - 未ログイン時の自動リダイレクト

### 📡 WebSocketリアルタイム機能
- ⚡ **価格ライブストリーミング** - リアルタイム株価データ配信
- 🤖 **AI判断ライブ実行** - リアルタイムAI分析と即座配信
- 🔗 **マルチクライアント対応** - 複数接続の同時管理
- 🔐 **認証済み配信** - JWT認証によるセキュアな通信
- 🔄 **自動再接続機能** - ネットワーク障害時の自動復旧

### 🔄 ハイブリッドデータシステム
- 🏢 **立花証券API統合** - 真のリアルタイム価格データ取得
- 📊 **yfinance統合** - 履歴データ・テクニカル分析用
- 🤖 **データソース自動選択** - 市場時間に応じた最適なデータ源選択
- ⚡ **フォールバック機能** - API障害時の自動切り替え

### 🚀 革新的効率化システム
- ⚡ **50-150倍の処理速度向上**
- 💰 **API費用90%削減**
- 📝 **コンテキスト使用量80%削減**
- 🎯 **将来エントリー条件自動生成**
- 🔄 **判断継続性エンジン**
- 📊 **時間軸別インテリジェントキャッシュ**

---

## 📁 ファイル構成

### 🔧 **コアエンジン**
| ファイル | 役割 | 重要度 |
|---------|------|-------|
| `main.py` | 基本CSV出力エンジン | ⭐⭐⭐ |
| `minute_decision_engine.py` | バックテスト用データ生成エンジン | ⭐⭐⭐ |
| `backtest_runner.py` | **メイン実行ファイル**（AI統合済み） | ⭐⭐⭐⭐⭐ |

### 🤖 **AI判断システム**
| ファイル | 役割 | 重要度 |
|---------|------|-------|
| `ai_trading_decision.py` | LangGraphワークフローエンジン + 効率化統合 | ⭐⭐⭐⭐⭐ |
| `trading_agents.py` | 3つの専門エージェント定義 | ⭐⭐⭐⭐ |
| `trading_tools.py` | エージェント用ツール群 + 戦略ロジック | ⭐⭐⭐⭐ |

### ⚡ **効率化システム（新規）**
| ファイル | 役割 | 重要度 |
|---------|------|-------|
| `chart_analysis_cache.py` | **時間軸別インテリジェントキャッシュ** | ⭐⭐⭐⭐⭐ |
| `trading_continuity_engine.py` | **判断継続性エンジン** | ⭐⭐⭐⭐⭐ |
| `timeframe_chart_analyzer.py` | 時間軸特化分析システム | ⭐⭐⭐⭐ |
| `test_efficiency_system.py` | 効率化システムテスト・検証 | ⭐⭐⭐ |

### 📊 **データ・チャート**
| ファイル | 役割 | 重要度 |
|---------|------|-------|
| `technical_indicators.py` | テクニカル指標計算ロジック | ⭐⭐⭐ |
| `data_models.py` | データ構造定義 | ⭐⭐⭐ |
| `config.py` | 設定管理 | ⭐⭐ |
| `chart_generator.py` | チャート画像生成 | ⭐⭐ |
| `market_data_engine.py` | 市場環境データ取得 | ⭐⭐ |

### 🧪 **テスト・例**
| ファイル | 役割 | 重要度 |
|---------|------|-------|
| `test_integration.py` | 統合テストスクリプト | ⭐⭐ |
| `test_decision_engine.py` | 判断エンジンテスト | ⭐⭐ |

## 🎯 主要機能

### 1. CSV出力機能
- 銘柄指定による株価データ取得
- 複数時間足対応（1分足、5分足、15分足、60分足、日足、週足）
- 期間指定またはperiod指定
- CSV形式でのデータ出力
- 対話式モードとコマンドラインモード

### 2. 🚀 バックテスト用データ生成機能（NEW）
- **時刻・銘柄指定**でのリアルタイム判断データ生成
- **6時間軸のテクニカル指標**を一括計算
- **JSON形式**での構造化データ出力
- AI判断システム向けデータパッケージ対応

### 3. ⚡ 複数銘柄バッチ処理機能（NEW）
- **複数銘柄の並列処理**で高速データ生成
- **市場環境データ**付きの総合分析
- **CSV・JSON形式**でのサマリー出力
- バックテスト・スクリーニング用途に最適

### 4. 📊 チャート画像生成機能（NEW）
- **6時間軸チャート**の自動生成（週足、日足、60分足、15分足、5分足、1分足）
- **テクニカル指標付きチャート**（移動平均、VWAP、ボリンジャーバンド等）
- **バックテスト対応**（指定時刻でのスナップショット）
- **AI判断システム**向けの高品質チャート画像

## 🚀 クイックスタート

### プロジェクト実行（推奨方法）

```bash
# 全体プロジェクト実行（フロントエンド + バックエンド）
just run-all

# または個別実行
just run-frontend    # Next.js フロントエンド (port 3000)
just run-backend     # FastAPI バックエンド (port 8000)

# ポート使用中の場合は自動的にプロセスを終了してから起動
```

### アクセスURL
- **フロントエンド**: http://localhost:3000
- **API ドキュメント**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/api/v1/ws/live

### 初回セットアップ

```bash
# 依存関係インストール
just install-all

# またはそれぞれ個別に
cd frontend && npm install
cd backend && pip install -r requirements.txt
```

## インストール

### CLI版（レガシー）

```bash
# 基本機能
pip install -r requirements.txt

# チャート生成機能（オプション）
pip install matplotlib mplfinance
```

### Web API版（推奨）

```bash
cd backend
pip install -r requirements.txt
```

## 使用方法

### 1. CSV出力機能

#### 対話式モード

```bash
python main.py --interactive
```

または

```bash
python main.py
```

#### コマンドラインモード

```bash
# AAPL（Apple）の全時間足データを1ヶ月分取得
python main.py --symbol AAPL

# 特定の時間足のみ取得
python main.py --symbol AAPL --intervals 1d 1wk

# 期間指定
python main.py --symbol AAPL --period 3mo

# 日付範囲指定
python main.py --symbol AAPL --start 2024-01-01 --end 2024-01-31

# 日本株の例：トヨタ自動車（7203）
python main.py --symbol 7203.T --intervals 1d 1wk
```

### 2. 🚀 バックテスト用データ生成

#### 基本的な使用方法

```bash
# ルネサス（6723.T）の現在時刻での判断データを生成
python test_decision_engine.py --symbol 6723.T

# 特定時刻でのデータ生成
python test_decision_engine.py --symbol 7203.T --datetime "2025-07-25 14:30"

# 米国株の例
python test_decision_engine.py --symbol AAPL --datetime "2025-07-25 09:30"
```

### 3. ⚡ 複数銘柄バッチ処理

#### サンプルファイル作成

```bash
# サンプル銘柄リストファイルを作成
python batch_decision_engine.py --create-sample
```

#### バッチ処理実行

```bash
# 銘柄リストファイルから一括処理
python batch_decision_engine.py --symbols-file sample_symbols.txt

# 銘柄を直接指定
python batch_decision_engine.py --symbols 7203.T 6723.T 9984.T

# 並列処理数を指定（デフォルト3）
python batch_decision_engine.py --symbols-file sample_symbols.txt --workers 5

# 特定時刻でのバッチ処理
python batch_decision_engine.py --symbols-file sample_symbols.txt --datetime "2025-07-25 14:30"
```

### 4. 📊 チャート画像生成

#### 軽量チャート生成（推奨）

```bash
# 現在時刻でのチャート生成
python test_integrated_charts.py --symbol 7203.T

# 特定時刻でのチャート生成  
python test_integrated_charts.py --symbol 7203.T --datetime "2025-07-25 11:00"

# バックテスト用（指定時刻でのスナップショット）
python test_integrated_charts.py --symbol 7203.T --datetime "2025-07-25 10:30" --backtest
```

#### 単体チャート生成テスト

```bash
# 軽量チャート（matplotlib使用）
python test_simple_chart.py --symbol 6723.T --datetime "2025-07-25 14:30"

# バックテストモード
python test_simple_chart.py --symbol 6723.T --datetime "2025-07-25 10:30" --backtest
```

#### バッチ処理出力

**個別JSONファイル**: 各銘柄の詳細判断データ
**サマリーCSV**: 全銘柄の主要指標をまとめたスプレッドシート
**バッチ結果JSON**: 処理結果の統計情報

```csv
symbol,company_name,current_price,price_change,price_change_percent,volume_ratio,ma20_1d,ma50_1d,atr14,vwap_60m
7203.T,トヨタ自動車,2775.5,-69.0,-2.43,0.006,2545.7,2586.09,72.7,2670.8
6723.T,ルネサスエレクトロニクス,1834.0,-83.0,-4.33,0.009,1871.1,1857.78,79.9,1882.6
```

#### 生成されるデータ

**6時間軸のテクニカル指標:**
- **週足**: MA20/50/200, 出来高プロファイル
- **日足**: MA20/50/200, ATR14, 出来高プロファイル
- **60分足**: MA20/50, VWAP, ボリンジャーバンド
- **15分足**: MA9/20, VWAP
- **5分足**: MA5/21, VWAP
- **1分足**: MA5/9, VWAP

**出力例:**
```json
{
  "timestamp": "2025-07-26T12:24:00",
  "symbol": "6723.T",
  "current_price": {
    "current_price": 1834.0,
    "price_change": -83.0,
    "price_change_percent": -4.33,
    "today_high": 2014.0,
    "today_low": 1794.0
  },
  "technical_indicators": {
    "weekly": {"moving_averages": {"ma20": 1876.3}},
    "daily": {"atr14": 79.9},
    "hourly_60": {"vwap": {"daily": 1882.6}},
    "minute_15": {"moving_averages": {"ma9": 1821.9}},
    "minute_5": {"moving_averages": {"ma5": 1831.6}},
    "minute_1": {"moving_averages": {"ma5": 1832.5}}
  }
}
```

### パラメータ

- `--symbol, -s`: 銘柄コード（例: AAPL, 7203.T）
- `--intervals, -i`: 時間足（1m, 5m, 15m, 60m, 1d, 1wk）複数選択可能
- `--period, -p`: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
- `--start`: 開始日（YYYY-MM-DD形式）
- `--end`: 終了日（YYYY-MM-DD形式）
- `--interactive`: 対話式モード

## 出力

### CSV出力
CSVファイルは `data/` ディレクトリに以下の形式で保存されます：

```
{銘柄コード}_{時間足}_{開始日}_{終了日}.csv
```

例: `AAPL_1d_2024-01-01_2024-01-31.csv`

### バックテスト用JSON出力
JSONファイルは `output/` ディレクトリに以下の形式で保存されます：

```
decision_data_{銘柄コード}_{YYYYMMDD_HHMMSS}.json
```

例: `decision_data_6723.T_20250726_122400.json`

### CSVファイルの構造

| カラム | 説明 |
|--------|------|
| Date | 日時 |
| Open | 始値 |
| High | 高値 |
| Low | 安値 |
| Close | 終値 |
| Volume | 出来高 |
| Adj Close | 調整後終値 |

## ログ

実行ログは `logs/` ディレクトリに日付別で保存されます：

```
logs/yfinance_tool_YYYYMMDD.log
```

## 対応銘柄

yfinanceライブラリが対応するすべての銘柄に対応しています：

- 米国株：AAPL, MSFT, GOOGL など
- 日本株：7203.T, 9984.T など（.T サフィックス）
- その他の市場：各市場のサフィックスを使用

## 📁 プロジェクト構成

```
yfinance-csv-tool/
├── frontend/                 # Next.js フロントエンド (Phase 11)
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   │   ├── api/        # API Routes (開発中)
│   │   │   ├── login/      # ログイン画面
│   │   │   └── dashboard/   # メインダッシュボード
│   │   │       └── backtest/ # バックテスト機能
│   │   ├── components/      # Reactコンポーネント
│   │   │   ├── auth/       # 認証関連コンポーネント
│   │   │   ├── backtest/   # バックテスト機能
│   │   │   ├── charts/     # チャート表示
│   │   │   ├── providers/  # Context Providers
│   │   │   └── ui/         # UIコンポーネント
│   │   ├── hooks/          # カスタムHooks
│   │   ├── lib/            # ユーティリティ・設定
│   │   └── types/          # TypeScript型定義
│   ├── package.json        # Node.js依存関係
│   └── next.config.ts     # Next.js設定
├── backend/                  # FastAPI バックエンドAPI
│   ├── app/
│   │   ├── api/v1/         # APIエンドポイント
│   │   │   └── endpoints/  # 各機能エンドポイント
│   │   │       ├── auth.py      # 認証API
│   │   │       ├── trading.py   # トレーディングAPI
│   │   │       └── websocket.py # WebSocket API
│   │   ├── core/           # コア機能
│   │   │   ├── auth.py     # 認証システム
│   │   │   ├── config.py   # 設定管理
│   │   │   └── data_models.py # データ構造
│   │   ├── services/       # ビジネスロジック
│   │   │   ├── ai/        # AI判断システム
│   │   │   ├── efficiency/ # 効率化システム
│   │   │   ├── data_source_router.py # ハイブリッドデータ
│   │   │   └── minute_decision_engine.py # 判断エンジン
│   │   └── main.py        # FastAPIエントリーポイント
│   └── requirements.txt   # Python依存関係
├── justfile                 # プロジェクト実行コマンド (Phase 11)
├── docs/                   # ドキュメント
│   └── CLAUDE.md         # 開発履歴・技術仕様
├── .gitignore            # Git除外設定
└── README.md             # このファイル
```

## ⚙️ 技術仕様

### フロントエンド技術スタック (Phase 11)
```typescript
// 主要フレームワーク・ライブラリ
- Next.js 15.4.5        # React フレームワーク
- React 19.1.0          # UIライブラリ
- TypeScript 5.6.3      # 型安全性
- TailwindCSS 4.0       # CSSフレームワーク
- Recharts 3.1.0        # チャートライブラリ
- Zustand 5.0.6         # 状態管理
- TanStack Query 5.83.0 # データフェッチ
- Axios 1.11.0          # HTTP通信
- WebSocket (ws 8.18.3) # リアルタイム通信
```

### バックエンド技術スタック
```python
# 主要フレームワーク・ライブラリ
- FastAPI              # Web API フレームワーク
- Uvicorn              # ASGI サーバー
- yfinance             # Yahoo Finance API
- pandas + numpy       # データ処理・数値計算
- pandas-ta            # テクニカル分析
- pytz                 # タイムゾーン処理
- Supabase (supabase-py) # 認証・データベース
- OpenAI API           # AI判断システム
- LangGraph            # AI ワークフロー
- WebSockets           # リアルタイム通信
```

### サポート指標
- **移動平均線**: SMA(5,9,20,50,200)
- **VWAP**: 日次・アンカーVWAP
- **ボリンジャーバンド**: 20期間±2σ
- **ATR**: 14期間平均真の値幅
- **出来高プロファイル**: POC, Value Area

### API統合
- **立花証券API**: リアルタイム価格データ取得
- **yfinance API**: 履歴データ・テクニカル分析
- **Supabase**: ユーザー認証・データベース
- **OpenAI GPT-4o**: AI売買判断システム
- **WebSocket**: リアルタイム双方向通信

## 🎯 主要機能

### 🎨 フロントエンド機能
- **認証システム**: Supabase JWT認証によるログイン・ログアウト
- **ダッシュボード**: リアルタイム株価表示・チャート可視化
- **バックテスト機能**: 期間・間隔設定によるAI判断バックテスト
- **レスポンシブデザイン**: デスクトップ・モバイル対応
- **リアルタイム通信**: WebSocketによる価格・AI判断ライブ更新

### 🤖 バックエンド機能
- **AI売買判断**: OpenAI GPT-4o + LangGraphによる3エージェント分析
- **効率化システム**: 50-150倍高速化・API費用90%削減
- **WebSocketサーバー**: マルチクライアント対応リアルタイム配信
- **ハイブリッドデータ**: 立花証券API + yfinance自動選択
- **認証API**: Supabase統合によるセキュアなユーザー管理

### 📊 データ機能
- **6時間軸分析**: 1分足〜週足の包括的テクニカル分析
- **リアルタイム価格**: 立花証券APIによる真のリアルタイム価格
- **AI戦略**: コンフルエンス・トレンド・平均回帰・慎重HOLD
- **バックテスト**: 任意期間でのAI判断シミュレーション

## ⚠️ 注意事項

1. **API制限**: yfinanceとOpenAI APIには利用制限があります
2. **データ期間**: 1分足データは過去7-8日分のみ取得可能
3. **処理時間**: AI判断・バックテスト機能は計算集約的です
4. **認証**: 一部機能はSupabase認証が必要です
5. **リアルタイム機能**: WebSocket接続が必要です

## 🔧 トラブルシューティング

### よくある問題と解決策

```bash
# ポート使用中エラー
just kill-port 3000  # または 8000

# 依存関係エラー
just install-all

# 認証エラー
# Supabaseプロジェクト設定を確認してください

# WebSocket接続エラー
# バックエンドが起動していることを確認してください
```

### ログファイル確認
```bash
# フロントエンド: ブラウザの開発者ツール > Console
# バックエンド: ターミナル出力 + logs/ディレクトリ
```

## 📚 関連ドキュメント

- [開発履歴・技術仕様](docs/CLAUDE.md) - 詳細な実装仕様と開発履歴
- [API ドキュメント](http://localhost:8000/docs) - FastAPI自動生成ドキュメント