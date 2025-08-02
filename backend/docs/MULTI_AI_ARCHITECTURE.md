# マルチAI対応アーキテクチャドキュメント

## 概要

本システムは、従来のOpenAI専用構成から、複数のAIプロバイダーに対応するマルチAI対応システムに拡張されました。現在はOpenAIとGoogle Geminiの両方をサポートしており、環境変数による動的な切り替えが可能です。

## システム構成

### アーキテクチャ概要

```
┌─────────────────────────────────────────────────┐
│                AI取引判断システム                    │
├─────────────────────────────────────────────────┤
│  trading_agents.py (LangChainベース)              │
│  ai_trading_decision.py (メインエンジン)           │
├─────────────────────────────────────────────────┤
│           AIプロバイダー抽象化レイヤー                │
│  ┌─────────────────────────────────────────────┐ │
│  │      ai_provider_factory.py                 │ │
│  │  - プロバイダー生成・管理                       │ │
│  │  - 環境変数ベース設定                          │ │
│  │  - キャッシュ機能                              │ │
│  └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│                プロバイダー実装                      │
│  ┌──────────────┐    ┌──────────────────────┐    │
│  │ OpenAIProvider │    │   GeminiProvider     │    │
│  │ - GPT-4o       │    │ - gemini-1.5-pro    │    │
│  │ - GPT-4        │    │ - gemini-1.5-flash  │    │
│  │ - GPT-3.5      │    │ - ビジョン対応        │    │
│  │ - ビジョン対応  │    │ - 大容量トークン      │    │
│  └──────────────┘    └──────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### 主要コンポーネント

#### 1. **抽象化基底クラス** (`providers/base.py`)
- `AIProviderBase`: 全プロバイダーの共通インターフェース
- `AIResponse`: 統一されたレスポンス形式
- エラーハンドリング用例外クラス

```python
@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### 2. **プロバイダーファクトリー** (`ai_provider_factory.py`)
- プロバイダーの動的生成・管理
- 環境変数ベースの設定
- インスタンスキャッシュ機能
- APIキーの自動検出

#### 3. **OpenAIプロバイダー** (`providers/openai_provider.py`)
- LangChain ChatOpenAIラッパー
- サポートモデル: GPT-4o, GPT-4, GPT-3.5-turbo
- ビジョン機能対応
- トークン使用量追跡

#### 4. **Geminiプロバイダー** (`providers/gemini_provider.py`)
- Google Generative AI SDK使用
- サポートモデル: gemini-1.5-pro, gemini-1.5-flash
- 大容量トークン対応（最大1M）
- 安全性設定とコンテンツフィルタリング

#### 5. **LangChainアダプター** (`langchain_adapter.py`)
- カスタムプロバイダーのLangChain互換化
- メッセージ形式の変換
- ビジョン機能のサポート

## 設定・使用方法

### 環境変数設定

```bash
# プロバイダー選択 (デフォルト: openai)
AI_PROVIDER=gemini

# APIキー設定
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# モデル指定（オプション）
AI_MODEL=gemini-1.5-pro
```

### 基本的な使用方法

```python
from app.services.ai.ai_provider_factory import get_ai_provider

# デフォルトプロバイダーを取得
ai_provider = get_ai_provider()

# 特定プロバイダーを指定
gemini_provider = get_ai_provider(provider_name="gemini")
openai_provider = get_ai_provider(provider_name="openai", model="gpt-4o")

# AIに質問
messages = [{"role": "user", "content": "株価分析をお願いします"}]
response = ai_provider.invoke(messages)
print(response.content)
```

### 取引判断システムでの使用

```python
from app.services.ai.ai_trading_decision import AITradingDecisionEngine

# AI取引判断エンジン（環境変数AI_PROVIDERに従ってプロバイダー選択）
ai_engine = AITradingDecisionEngine()
result = ai_engine.analyze_trading_decision(decision_package)
```

## サポートされているプロバイダー・モデル

### OpenAI
| モデル | ビジョン | 最大トークン | 用途 |
|--------|----------|-------------|------|
| gpt-4o | ✓ | 128,000 | 高精度分析 |
| gpt-4 | ✗ | 8,192 | 標準分析 |
| gpt-3.5-turbo | ✗ | 16,385 | 高速分析 |

### Google Gemini
| モデル | ビジョン | 最大トークン | 用途 |
|--------|----------|-------------|------|
| gemini-1.5-pro | ✓ | 1,048,576 | 高精度・大容量分析 |
| gemini-1.5-flash | ✓ | 1,048,576 | 高速・大容量分析 |

## 実装の詳細

### エラーハンドリング

```python
try:
    response = ai_provider.invoke(messages)
except AIProviderError as e:
    logger.error(f"プロバイダーエラー: {e}")
except ModelNotSupportedError as e:
    logger.error(f"モデル未サポート: {e}")
```

### プロバイダー情報の取得

```python
from app.services.ai.ai_provider_factory import get_provider_info

info = get_provider_info()
print(f"利用可能プロバイダー: {info['available']}")
print(f"現在の状態: {info['status']}")
```

### パフォーマンス最適化

- **プロバイダーキャッシュ**: 同一設定のプロバイダーを再利用
- **遅延初期化**: 必要時のみプロバイダーを作成
- **トークン効率**: プロバイダー固有の最適化設定

## テスト・検証

### バックテスト実行例

```bash
# Geminiを使用したバックテスト
AI_PROVIDER=gemini uv run python gemini_test_script.py

# OpenAIを使用したバックテスト  
AI_PROVIDER=openai uv run python tests/test_trading_decision.py
```

### 検証済みの機能

- ✅ プロバイダー間の切り替え
- ✅ 統一されたレスポンス形式
- ✅ エラーハンドリング
- ✅ トークン使用量追跡
- ✅ ビジョン機能（対応モデル）
- ✅ JSON構造化出力
- ✅ LangChain統合

## トラブルシューティング

### よくある問題

1. **APIキー未設定**
   ```
   ERROR: APIキーが見つかりません。環境変数 GEMINI_API_KEY を設定してください
   ```
   → `.env`ファイルに適切なAPIキーを設定

2. **プロバイダー未サポート**
   ```
   ERROR: サポートされていないプロバイダー: claude
   ```
   → `openai` または `gemini` を指定

3. **LangChain互換性問題**
   ```
   ERROR: 'MultiProviderLangChainAdapter' object has no attribute 'bind_tools'
   ```
   → 現在は基本的なinvoke()メソッドのみサポート

### デバッグ方法

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# プロバイダー状態の確認
from app.services.ai.ai_provider_factory import ai_factory
status = ai_factory.get_provider_status()
print(status)
```

## 今後の拡張予定

- **新プロバイダー追加**: Claude, Claude-2等のAnthropic製品
- **LangChain完全互換**: bind_tools, streaming等の高度な機能
- **パフォーマンス監視**: レスポンス時間、コスト追跡
- **A/Bテスト機能**: プロバイダー間の性能比較

## 変更履歴

### v1.0.0 (2025-08-02)
- マルチAI対応アーキテクチャの初期実装
- OpenAI + Gemini プロバイダー対応
- 環境変数ベースの設定システム
- 統一レスポンス形式の導入
- LangChain基本互換性の実装