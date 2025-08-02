"""
マルチAI対応デモスクリプト

OpenAIとGeminiの切り替え方法と基本的な使用方法を示すデモ
"""

import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.ai_provider_factory import get_ai_provider
from app.services.ai.config import get_config_status


def demo_provider_switching():
    """プロバイダー切り替えデモ"""
    print("🔄 プロバイダー切り替えデモ")
    print("=" * 50)
    
    # 投資関連の質問
    investment_question = "日本の半導体株への投資について、現在の市場環境での注意点を3つ教えてください。"
    
    providers = ["openai", "gemini"]
    
    for provider_name in providers:
        print(f"\n🤖 {provider_name.upper()} の回答:")
        print("-" * 30)
        
        try:
            # プロバイダーを指定して作成
            provider = get_ai_provider(provider_name=provider_name)
            
            # 質問を送信
            messages = [{"role": "user", "content": investment_question}]
            response = provider.invoke(messages)
            
            print(f"モデル: {response.model}")
            print(f"回答: {response.content[:300]}...")
            
            if response.token_usage:
                print(f"トークン使用量: {response.token_usage}")
                
        except Exception as e:
            print(f"❌ {provider_name} エラー: {e}")


def demo_system_prompt_comparison():
    """システムプロンプト比較デモ"""
    print("\n🎯 システムプロンプト比較デモ")
    print("=" * 50)
    
    system_prompt = """
あなたは20年の経験を持つプロの株式アナリストです。
以下の特徴で回答してください：
- 具体的なデータに基づいた分析
- リスクとリターンの両面を考慮
- 簡潔で実践的なアドバイス
"""
    
    user_question = "6723.T（ルネサスエレクトロニクス）の今後1ヶ月の見通しを教えてください。"
    
    providers = ["openai", "gemini"]
    
    for provider_name in providers:
        print(f"\n🎨 {provider_name.upper()} (システムプロンプト適用):")
        print("-" * 40)
        
        try:
            provider = get_ai_provider(provider_name=provider_name)
            response = provider.invoke_with_system_prompt(system_prompt, user_question)
            
            print(f"回答: {response.content[:400]}...")
            
        except Exception as e:
            print(f"❌ {provider_name} エラー: {e}")


def demo_environment_configuration():
    """環境設定デモ"""
    print("\n⚙️ 環境設定デモ")
    print("=" * 50)
    
    print("現在の設定状況:")
    status = get_config_status()
    
    if status['status'] == 'OK':
        print(f"✅ 有効なプロバイダー: {status['provider']}")
        print(f"   モデル: {status['model']}")
        print(f"   設定: temperature={status['temperature']}, max_tokens={status['max_tokens']}")
    else:
        print(f"❌ 設定エラー: {status['error']}")
    
    print("\n📝 設定変更方法:")
    print("環境変数で設定を変更できます：")
    print("   export AI_PROVIDER=openai      # OpenAIを使用")
    print("   export AI_PROVIDER=gemini      # Geminiを使用")
    print("   export AI_MODEL=gpt-4o         # OpenAIモデル指定")
    print("   export AI_MODEL=gemini-1.5-pro # Geminiモデル指定")
    print("   export AI_TEMPERATURE=0.1      # Temperature設定")
    print("   export AI_MAX_TOKENS=4000      # Max Tokens設定")


def demo_trading_analysis():
    """取引分析デモ"""
    print("\n📊 取引分析デモ")
    print("=" * 50)
    
    # 市場データ（サンプル）
    market_context = {
        "symbol": "6723.T",
        "current_price": 2850,
        "price_change": "+1.2%",
        "volume": "1,200,000",
        "technical_signals": "RSI: 65, MACD: 上向き, BB: 中央付近"
    }
    
    analysis_prompt = f"""
以下の市場データを分析して、簡潔な投資判断を提供してください：

銘柄: {market_context['symbol']}
現在価格: ¥{market_context['current_price']}
価格変動: {market_context['price_change']}
出来高: {market_context['volume']}
テクニカル指標: {market_context['technical_signals']}

BUY/SELL/HOLDの判断と理由を30秒で読める長さで回答してください。
"""
    
    try:
        # デフォルトプロバイダーで分析
        provider = get_ai_provider()
        print(f"使用プロバイダー: {provider.provider_name} - {provider.model}")
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = provider.invoke(messages)
        
        print(f"\n投資判断:")
        print(response.content)
        
    except Exception as e:
        print(f"❌ 取引分析エラー: {e}")


def main():
    """メインデモ実行"""
    print("🚀 マルチAI対応システム デモ")
    print("=" * 60)
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. プロバイダー切り替えデモ
    demo_provider_switching()
    
    # 2. システムプロンプト比較デモ
    demo_system_prompt_comparison()
    
    # 3. 環境設定デモ
    demo_environment_configuration()
    
    # 4. 取引分析デモ
    demo_trading_analysis()
    
    print("\n🎉 デモ完了")
    print("=" * 60)
    print("\n💡 使用方法のヒント:")
    print("1. 環境変数でプロバイダーを切り替え可能")
    print("2. 既存コードは最小限の変更で対応")
    print("3. エラーハンドリングとログが自動化")
    print("4. ビジョン機能も統一インターフェースで利用可能")


if __name__ == "__main__":
    main()