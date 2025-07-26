# yfinance トレーディング データツール

yfinanceライブラリを使用した包括的な株価データ取得・分析ツールです。基本的なCSV出力から、バックテスト用のテクニカル分析データまで対応しています。

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

## インストール

```bash
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
├── main.py                    # CSV出力メインスクリプト
├── config.py                  # 設定管理
├── technical_indicators.py    # テクニカル指標計算エンジン
├── data_models.py            # データ構造定義
├── minute_decision_engine.py # バックテスト用データ生成エンジン
├── test_decision_engine.py   # テスト用スクリプト
├── requirements.txt          # 依存関係
├── README.md                 # このファイル
├── CLAUDE.md                 # Claude向け開発履歴
├── data/                     # CSV出力先
├── output/                   # JSON出力先
├── cache/                    # データキャッシュ
└── logs/                     # ログファイル
```

## ⚙️ 技術仕様

### 依存ライブラリ
- `yfinance`: Yahoo Finance API
- `pandas`: データ処理
- `numpy`: 数値計算
- `pandas-ta`: テクニカル分析
- `pytz`: タイムゾーン処理

### サポート指標
- **移動平均線**: SMA(5,9,20,50,200)
- **VWAP**: 日次・アンカーVWAP
- **ボリンジャーバンド**: 20期間±2σ
- **ATR**: 14期間平均真の値幅
- **出来高プロファイル**: POC, Value Area

## ⚠️ 注意事項

1. yfinanceは無料のAPIですが、利用制限がある場合があります
2. 1分足データは過去7日間程度しか取得できません
3. データの精度や完全性についてはyfinanceライブラリに依存します
4. 大量のデータを一度に取得すると時間がかかる場合があります
5. バックテスト機能は計算集約的なため、処理時間にご注意ください

## 🔧 エラー対処

- データが取得できない場合は、銘柄コードの書式を確認してください
- ネットワークエラーが発生する場合は、時間を置いてリトライしてください
- ログファイルでエラーの詳細を確認できます
- タイムゾーンエラーが発生する場合は、pytzライブラリが正しくインストールされているか確認してください