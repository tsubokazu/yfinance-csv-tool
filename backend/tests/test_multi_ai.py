"""
マルチAI対応システムのテスト

OpenAIとGeminiの両プロバイダーが正常に動作することを確認
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.ai_provider_factory import get_ai_provider, get_provider_info
from app.services.ai.providers.base import AIProviderError
from app.services.ai.config import get_config_status
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_provider_info():
    """プロバイダー情報の取得テスト"""
    print("🔍 プロバイダー情報テスト")
    print("=" * 50)
    
    try:
        info = get_provider_info()
        print(f"✅ 利用可能プロバイダー: {list(info['available'].keys())}")
        
        for provider_name, provider_info in info['available'].items():
            print(f"📋 {provider_name}:")
            print(f"   - デフォルトモデル: {provider_info['default_model']}")
            print(f"   - APIキー設定: {provider_info['api_key_available']}")
            print(f"   - 環境変数: {provider_info['env_var']}")
        
        print(f"\n📊 現在の状況: {info['status']}")
        
    except Exception as e:
        print(f"❌ プロバイダー情報取得エラー: {e}")


def test_config_status():
    """設定状況の確認テスト"""
    print("\n⚙️ 設定状況テスト")
    print("=" * 50)
    
    try:
        status = get_config_status()
        print(f"📋 設定状況: {status['status']}")
        
        if status['status'] == 'OK':
            print(f"   - プロバイダー: {status['provider']}")
            print(f"   - モデル: {status['model']}")
            print(f"   - Temperature: {status['temperature']}")
            print(f"   - Max Tokens: {status['max_tokens']}")
            print(f"   - 設定有効: {status['is_valid']}")
        else:
            print(f"   - エラー: {status['error']}")
        
        print(f"\n🔑 環境変数状況:")
        for key, value in status['env_status'].items():
            print(f"   - {key}: {value}")
            
    except Exception as e:
        print(f"❌ 設定状況確認エラー: {e}")


def test_provider_creation(provider_name: str):
    """指定プロバイダーの作成テスト"""
    print(f"\n🚀 {provider_name} プロバイダー作成テスト")
    print("=" * 50)
    
    try:
        provider = get_ai_provider(provider_name=provider_name)
        print(f"✅ {provider_name} プロバイダー作成成功")
        
        info = provider.get_provider_info()
        print(f"📋 プロバイダー情報:")
        print(f"   - プロバイダー: {info['provider']}")
        print(f"   - モデル: {info['model']}")
        print(f"   - ビジョン対応: {info['supports_vision']}")
        print(f"   - Temperature: {info['temperature']}")
        print(f"   - Max Tokens: {info['max_tokens']}")
        
        return provider
        
    except AIProviderError as e:
        print(f"❌ {provider_name} プロバイダー作成エラー: {e}")
        return None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None


def test_simple_invoke(provider):
    """シンプルな呼び出しテスト"""
    if provider is None:
        print("❌ プロバイダーが利用できません")
        return
    
    print(f"\n💬 {provider.provider_name} シンプル呼び出しテスト")
    print("=" * 50)
    
    try:
        messages = [
            {"role": "user", "content": "こんにちは！簡単な挨拶をしてください。"}
        ]
        
        response = provider.invoke(messages)
        print(f"✅ 呼び出し成功")
        print(f"📝 応答: {response.content[:100]}...")
        print(f"🔧 モデル: {response.model}")
        print(f"🏭 プロバイダー: {response.provider}")
        
        if response.token_usage:
            print(f"📊 トークン使用量: {response.token_usage}")
        
    except Exception as e:
        print(f"❌ 呼び出しエラー: {e}")


def test_system_prompt(provider):
    """システムプロンプト呼び出しテスト"""
    if provider is None:
        print("❌ プロバイダーが利用できません")
        return
    
    print(f"\n🎯 {provider.provider_name} システムプロンプトテスト")
    print("=" * 50)
    
    try:
        system_prompt = "あなたは株式取引の専門家です。簡潔で正確な回答をしてください。"
        user_message = "日本株の取引で重要な指標を3つ教えてください。"
        
        response = provider.invoke_with_system_prompt(system_prompt, user_message)
        print(f"✅ システムプロンプト呼び出し成功")
        print(f"📝 応答: {response.content[:200]}...")
        
    except Exception as e:
        print(f"❌ システムプロンプト呼び出しエラー: {e}")


def test_vision_capability(provider):
    """ビジョン機能テスト"""
    if provider is None:
        print("❌ プロバイダーが利用できません")
        return
    
    print(f"\n👁️ {provider.provider_name} ビジョン機能テスト")
    print("=" * 50)
    
    if not provider.supports_vision():
        print(f"ℹ️ {provider.provider_name} はビジョン機能をサポートしていません")
        return
    
    print(f"✅ {provider.provider_name} はビジョン機能をサポートしています")
    # 実際の画像テストは簡単な例として省略
    print("ℹ️ 実際の画像テストは省略（Base64画像データが必要）")


def run_comprehensive_test():
    """包括的なテスト実行"""
    print("🧪 マルチAI対応システム 包括テスト")
    print("=" * 70)
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. プロバイダー情報テスト
    test_provider_info()
    
    # 2. 設定状況テスト
    test_config_status()
    
    # 3. 各プロバイダーのテスト
    providers_to_test = ["openai", "gemini"]
    
    for provider_name in providers_to_test:
        provider = test_provider_creation(provider_name)
        
        if provider:
            test_simple_invoke(provider)
            test_system_prompt(provider)
            test_vision_capability(provider)
    
    print("\n🎉 テスト完了")
    print("=" * 70)


def test_default_provider():
    """デフォルトプロバイダーテスト"""
    print("\n🔧 デフォルトプロバイダーテスト")
    print("=" * 50)
    
    try:
        provider = get_ai_provider()  # プロバイダー名を指定しない
        print(f"✅ デフォルトプロバイダー取得成功: {provider.provider_name}")
        
        # 簡単な呼び出しテスト
        test_simple_invoke(provider)
        
    except Exception as e:
        print(f"❌ デフォルトプロバイダーテスト失敗: {e}")


if __name__ == "__main__":
    # 環境変数の簡易チェック
    print("🔑 環境変数チェック:")
    ai_provider = os.getenv("AI_PROVIDER", "未設定")
    openai_key = "設定済み" if os.getenv("OPENAI_API_KEY") else "未設定"
    gemini_key = "設定済み" if os.getenv("GEMINI_API_KEY") else "未設定"
    
    print(f"   AI_PROVIDER: {ai_provider}")
    print(f"   OPENAI_API_KEY: {openai_key}")
    print(f"   GEMINI_API_KEY: {gemini_key}")
    print()
    
    # メインテスト実行
    run_comprehensive_test()
    
    # デフォルトプロバイダーテスト
    test_default_provider()