# AIプロバイダー使用ガイド

## 概要

このドキュメントでは、マルチAI対応システムの具体的な使用方法と設定について説明します。

## クイックスタート

### 1. 環境設定

`.env`ファイルに以下を追加：

```bash
# 使用したいプロバイダーを指定
AI_PROVIDER=gemini  # または openai

# 必要なAPIキーを設定
OPENAI_API_KEY=sk-proj-your-openai-key
GEMINI_API_KEY=your-gemini-api-key

# オプション: 特定モデルを指定
AI_MODEL=gemini-1.5-pro
```

### 2. 基本的な使用方法

```python
from app.services.ai.ai_provider_factory import get_ai_provider

# AIプロバイダーを取得
ai = get_ai_provider()

# 取引分析の実行
messages = [
    {"role": "user", "content": "6723.Tの株価分析をお願いします"}
]

response = ai.invoke(messages)
print(f"AI判断: {response.content}")
print(f"使用モデル: {response.model}")
print(f"トークン使用量: {response.token_usage}")
```

## プロバイダー別の特徴と使い分け

### OpenAI GPT-4o
**適用場面:**
- 精密な財務分析
- 複雑な市場状況の解釈
- ビジョン機能を使った チャート分析

**特徴:**
- 高い分析精度
- ビジョン機能対応
- 豊富な金融知識

```python
openai_provider = get_ai_provider(provider_name="openai", model="gpt-4o")
```

### Google Gemini 1.5 Pro
**適用場面:**
- 大量データの一括分析
- 長期トレンド分析
- コスト効率重視の運用

**特徴:**
- 大容量トークン（1M）
- 高速レスポンス
- コストパフォーマンス

```python
gemini_provider = get_ai_provider(provider_name="gemini", model="gemini-1.5-pro")
```

## 実践例

### 1. 取引判断システムでの使用

```python
from app.services.ai.ai_trading_decision import AITradingDecisionEngine
from app.services.minute_decision_engine import MinuteDecisionEngine
from datetime import datetime

# データ取得
engine = MinuteDecisionEngine()
decision_package = engine.get_minute_decision_data('6723.T', datetime.now())

# AI分析（環境変数AI_PROVIDERに従って自動選択）
ai_engine = AITradingDecisionEngine()
result = ai_engine.analyze_trading_decision(decision_package)

print(f"判断: {result['final_decision']}")
print(f"信頼度: {result['confidence_level']}")
```

### 2. プロバイダー比較分析

```python
import asyncio
from app.services.ai.ai_provider_factory import get_ai_provider

async def compare_providers(prompt):
    """複数プロバイダーで同じ質問を分析"""
    
    providers = {
        'openai': get_ai_provider(provider_name="openai"),
        'gemini': get_ai_provider(provider_name="gemini")
    }
    
    results = {}
    
    for name, provider in providers.items():
        response = provider.invoke([{"role": "user", "content": prompt}])
        results[name] = {
            'decision': response.content,
            'model': response.model,
            'tokens': response.token_usage
        }
    
    return results

# 使用例
prompt = "ルネサス株の短期投資判断をBUY/SELL/HOLDで教えてください"
comparison = await compare_providers(prompt)
```

### 3. エラーハンドリング付きの実装

```python
from app.services.ai.ai_provider_factory import get_ai_provider
from app.services.ai.providers.base import AIProviderError, ModelNotSupportedError

def safe_ai_analysis(symbol, provider_name=None):
    """安全なAI分析実行"""
    
    try:
        # プロバイダー取得
        ai = get_ai_provider(provider_name=provider_name)
        
        # 分析実行
        messages = [{"role": "user", "content": f"{symbol}の分析をお願いします"}]
        response = ai.invoke(messages)
        
        return {
            'success': True,
            'result': response.content,
            'provider': response.provider,
            'model': response.model
        }
        
    except AIProviderError as e:
        return {
            'success': False,
            'error': f"プロバイダーエラー: {e}",
            'fallback': 'openai'  # フォールバック先
        }
        
    except ModelNotSupportedError as e:
        return {
            'success': False,
            'error': f"モデル未サポート: {e}",
            'supported_models': ai.get_supported_models()
        }
```

## 環境別設定例

### 開発環境
```bash
# 開発ではコスト効率重視
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash
```

### ステージング環境
```bash
# 本番同等でテスト
AI_PROVIDER=openai
AI_MODEL=gpt-4o
```

### 本番環境
```bash
# 精度とコストのバランス
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
```

## パフォーマンス最適化

### 1. プロバイダーキャッシュの活用

```python
from app.services.ai.ai_provider_factory import ai_factory

# キャッシュ状態確認
status = ai_factory.get_provider_status()
print(f"キャッシュされたプロバイダー数: {status['cached_providers']}")

# キャッシュクリア（必要時）
ai_factory.clear_cache()
```

### 2. トークン使用量の監視

```python
def monitor_token_usage(ai_provider, messages):
    """トークン使用量を監視"""
    
    response = ai_provider.invoke(messages)
    
    if response.token_usage:
        usage = response.token_usage
        print(f"入力トークン: {usage.get('input_tokens', 0)}")
        print(f"出力トークン: {usage.get('output_tokens', 0)}")
        print(f"総トークン: {usage.get('total_tokens', 0)}")
    
    return response
```

### 3. バッチ処理での効率化

```python
def batch_analysis(symbols, provider_name=None):
    """複数銘柄の一括分析"""
    
    ai = get_ai_provider(provider_name=provider_name)
    results = {}
    
    # 一括でプロンプト生成
    batch_prompt = f"""
    以下の銘柄について、それぞれ投資判断を行ってください：
    {', '.join(symbols)}
    
    各銘柄について以下の形式で回答：
    - 銘柄コード: 判断(BUY/SELL/HOLD)
    """
    
    response = ai.invoke([{"role": "user", "content": batch_prompt}])
    
    return {
        'batch_result': response.content,
        'token_efficiency': len(symbols) / response.token_usage.get('total_tokens', 1)
    }
```

## デバッグ・監視

### 1. ログ設定

```python
import logging

# AIプロバイダー関連のログを有効化
logging.getLogger('app.services.ai').setLevel(logging.DEBUG)

# 使用例
ai = get_ai_provider()  # DEBUG: プロバイダー作成ログが出力される
```

### 2. プロバイダー状態の確認

```python
from app.services.ai.ai_provider_factory import get_provider_info

def check_system_status():
    """システム状態の確認"""
    
    info = get_provider_info()
    
    print("=== AIプロバイダー状態 ===")
    print(f"デフォルトプロバイダー: {info['status']['default_provider']}")
    print(f"設定済みAPIキー: {info['status']['api_keys_configured']}")
    
    print("\n=== 利用可能プロバイダー ===")
    for name, details in info['available'].items():
        print(f"{name}:")
        print(f"  モデル: {details['default_model']}")
        print(f"  APIキー: {'✓' if details['api_key_available'] else '✗'}")

check_system_status()
```

## トラブルシューティング

### よくある問題と解決方法

1. **APIキー設定問題**
```bash
# 環境変数の確認
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY

# .envファイルの確認
cat .env | grep API_KEY
```

2. **プロバイダー切り替え問題**
```python
# 明示的なプロバイダー指定で検証
openai_test = get_ai_provider(provider_name="openai")
gemini_test = get_ai_provider(provider_name="gemini")

print(f"OpenAI: {openai_test.provider_name}")
print(f"Gemini: {gemini_test.provider_name}")
```

3. **レスポンス形式問題**
```python
# レスポンス内容の詳細確認
response = ai.invoke(messages)
print(f"Content type: {type(response.content)}")
print(f"Content length: {len(response.content)}")
print(f"Has token usage: {response.token_usage is not None}")
```

## ベストプラクティス

1. **環境変数での設定管理**
2. **エラーハンドリングの実装**
3. **トークン使用量の監視**
4. **プロバイダー固有の特徴を活用**
5. **定期的なキャッシュクリア**
6. **ログレベルの適切な設定**