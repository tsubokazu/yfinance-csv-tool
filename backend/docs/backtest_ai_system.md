# バックテストAI判断システム 技術資料

## 概要

バックテスト実行時に各時刻でAI判断を行うシステムの詳細仕様と動作フローを説明する。

## システム構成

### 主要コンポーネント

1. **AITradingDecisionEngine** (`backend/app/services/ai/ai_trading_decision.py`)
   - AI判断システムの中核エンジン
   - LangGraphワークフローの実行制御
   - 効率化・継続性判断の管理

2. **Trading Agents** (`backend/app/services/ai/trading_agents.py`)
   - チャート分析エージェント
   - テクニカル指標分析エージェント  
   - 売買判断エージェント

3. **MinuteDecisionEngine** (`backend/app/services/minute_decision_engine.py`)
   - 各時刻での判断データパッケージ生成
   - 市場データ・テクニカル指標・チャート画像の統合

## データフロー

### 1. バックテスト実行時の処理フロー

```
バックテスト開始
    ↓
指定期間の各時刻でループ処理
    ↓
MinuteDecisionEngine.get_minute_decision_data()
    ↓
AITradingDecisionEngine.analyze_trading_decision()
    ↓
AI判断結果をバックテスト結果リストに追加
```

### 2. AI判断システム内部フロー

```
analyze_trading_decision()
    ↓
1. 効率化分析プラン取得 (continuity_engine)
    ↓
2. 継続性判断の実行
    ├─ 継続判断で十分 → 効率化された結果を返す
    └─ フル分析が必要 → 次へ
    ↓
3. 判断データパッケージの準備 (_prepare_initial_state)
    ├─ current_price
    ├─ technical_indicators  
    ├─ chart_images (パス情報)
    └─ market_context
    ↓
4. LangGraphワークフロー実行 (_workflow.invoke)
    ├─ chart_analyst_node (チャート分析)
    ├─ technical_analyst_node (テクニカル分析)
    └─ trading_decision_node (最終判断)
    ↓
5. 結果処理・構造化 (_process_workflow_result)
```

## 各時刻で生成されるデータ

### MinuteDecisionPackage の構成要素

1. **基本情報**
   - `symbol`: 銘柄コード (例: "6723.T")
   - `timestamp`: 判断時刻 (datetime)

2. **価格データ**
   - `current_price`: 現在価格情報
     - `current_price`: 価格
     - `price_change_percent`: 変化率
     - `volume`: 出来高

3. **テクニカル指標** (`technical_indicators`)
   ```python
   {
       "weekly": {...},    # 週足指標
       "daily": {...},     # 日足指標  
       "hourly_60": {...}, # 1時間足指標
       "minute_15": {...}, # 15分足指標
       "minute_5": {...},  # 5分足指標
       "minute_1": {...}   # 1分足指標
   }
   ```

4. **チャート画像** (`chart_images`)
   - 各時間足のチャート画像パス
   - **問題**: バックテスト時に画像パスが存在しないため警告が発生

5. **市場環境データ**
   - 市場時間情報
   - 全体的な市場状況

### テクニカル指標の詳細

各時間足で以下の指標を計算:

- **移動平均線**: SMA, EMA
- **VWAP**: 出来高加重平均価格
- **ボリンジャーバンド**: 上限・下限・中央線
- **ATR**: 平均真の値幅（ボラティリティ）
- **出来高プロファイル**: POC, Value Area

## AI エージェントとプロンプト

### 1. チャート分析エージェント

**役割**: チャート画像の視覚的分析

**プロンプト** (部分):
```
あなたはチャート分析の専門家です。

## 役割
- チャート画像から価格パターンを特定
- サポート・レジスタンスレベルの識別
- トレンドラインとチャートパターンの分析
- 視覚的な売買シグナルの生成

## 分析要素
1. **価格パターン**: ヘッドアンドショルダー、三角持ち合い等
2. **トレンドライン**: 上昇・下降・横ばいトレンド
3. **サポート・レジスタンス**: 重要な価格レベル
4. **出来高パターン**: 価格との関係性
```

**現在の問題**: チャート画像データが見つからないため、この分析がスキップされている

### 2. テクニカル指標分析エージェント

**役割**: 数値的なテクニカル指標分析

**プロンプト**:
```
あなたはテクニカル指標分析の専門家です。

## 役割
- 各種テクニカル指標を詳細に分析
- 複数時間軸での指標の整合性を確認
- 明確な売買シグナルを生成
- リスク・リワード比率を評価

## 分析対象指標
1. **移動平均線**: ゴールデンクロス/デッドクロス、MA配列
2. **VWAP**: 価格とVWAPの関係、VWAP傾き
3. **ボリンジャーバンド**: バンド内位置、スクイーズ/エクスパンション
4. **ATR**: ボラティリティ水準と変化
5. **出来高プロファイル**: POC、Value Area、出来高分布

## 分析プロセス
1. **各時間軸分析**: 週足→日足→時間足→分足の順序で分析
2. **整合性確認**: 複数時間軸でのシグナル一致度確認
3. **強度評価**: シグナルの強さを定量的に評価
4. **タイミング判定**: エントリー/エグジットの最適タイミング
```

### 3. 売買判断エージェント

**役割**: 最終的な売買判断の決定

**プロンプト**:
```
あなたは総合的な売買判断を行うトレーディング専門家です。

## 役割
- チャート分析とテクニカル分析結果を統合
- 市場環境を考慮した最終判断
- 具体的なエントリー・エグジット戦略の提案
- リスク管理方針の策定

## 判断基準
1. **シグナル強度**: 複数分析結果の一致度
2. **市場環境**: 全体的な市場状況との整合性
3. **リスクリワード**: 想定損失と利益の比率
4. **時間軸整合性**: 短期・中期・長期の方向性
```

## OpenAI API 呼び出し

ログから確認される API 呼び出し:

```
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
```

各エージェントが以下のようにAPIを呼び出し:

1. **チャート分析**: 画像データ + プロンプト → GPT-4 Vision (予定)
2. **テクニカル分析**: テクニカル指標データ + プロンプト → GPT-4
3. **売買判断**: 統合分析結果 + プロンプト → GPT-4

## 効率化システム

### 継続性エンジン (TradingContinuityEngine)

前回の分析結果を活用して処理を効率化:

1. **キャッシュ機能**: チャート分析結果の時間軸別キャッシュ
2. **継続判断**: 前回判断からの継続性評価
3. **部分更新**: 必要な時間軸のみ再分析

**ログ例**:
```
INFO:app.services.efficiency.chart_analysis_cache:✅ hourly_60 チャート分析結果をキャッシュに保存
INFO:app.services.efficiency.chart_analysis_cache:♻️ weekly チャート分析をキャッシュから使用
```

## 出力結果の構造

AI判断の最終出力:

```python
{
    "trading_decision": "BUY|SELL|HOLD",
    "confidence_level": 0.85,  # 0.0-1.0
    "reasoning": [
        "テクニカル指標が強気シグナル",
        "ボリンジャーバンド下限からの反発"
    ],
    "strategy_used": "モメンタム戦略",
    "risk_factors": ["市場全体の下落リスク"],
    "entry_conditions": {
        "price_level": 1850,
        "stop_loss": 1800,
        "target_price": 1920
    },
    "analysis_efficiency": "full_analysis|continuity_based",
    "timestamp": "2025-07-30T10:00:00",
    "processing_time": "2025-08-01T15:50:18"
}
```

## 現在の問題と対処

### 1. チャート画像データ不足

**問題**: 
```
WARNING:app.services.ai.trading_agents:チャート画像データが見つかりません
```

**原因**: バックテスト時にチャート画像ファイルが生成されていない、またはパスが正しくない

**対処法**:
- チャート画像生成機能の確認
- バックテスト用チャート生成の実装
- 画像なしでも動作する fallback 機能の追加

### 2. 将来分析モジュール不足

**問題**:
```
WARNING:app.services.ai.ai_trading_decision:将来分析の追加に失敗: No module named 'trading_tools'
```

**原因**: `trading_tools` モジュールが見つからない

**対処法**:
- `trading_tools.py` の実装確認
- インポートパスの修正

## パフォーマンス情報

- **1判断あたりの処理時間**: 約0.5秒（推定）
- **API呼び出し回数**: 判断1回あたり最大3回（各エージェント）
- **効率化による削減**: キャッシュヒット時は約70%の処理時間短縮

## 今後の改善案

1. **チャート画像生成の安定化**
2. **エラーハンドリングの強化**  
3. **バックテスト専用モードの実装**
4. **レスポンス時間の最適化**
5. **判断精度の向上（モデル調整）**