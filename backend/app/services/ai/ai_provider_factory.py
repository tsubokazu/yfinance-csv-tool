"""
AI プロバイダーファクトリー

設定に基づいて適切なAIプロバイダーを生成・管理
"""

import os
from typing import Dict, Any, Optional
import logging

from .providers.base import AIProviderBase, AIProviderError
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """
    AIプロバイダーを生成・管理するファクトリークラス
    """
    
    # サポートされているプロバイダー
    SUPPORTED_PROVIDERS = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }
    
    # デフォルトモデル設定
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "gemini": "gemini-2.5-flash",
    }
    
    # 環境変数名のマッピング
    ENV_VAR_MAPPING = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    
    def __init__(self):
        self._provider_cache: Dict[str, AIProviderBase] = {}
    
    def create_provider(self, 
                       provider_name: str, 
                       model: Optional[str] = None,
                       api_key: Optional[str] = None,
                       **kwargs) -> AIProviderBase:
        """
        AIプロバイダーを作成
        
        Args:
            provider_name: プロバイダー名 ("openai", "gemini")
            model: モデル名（未指定の場合はデフォルトを使用）
            api_key: APIキー（未指定の場合は環境変数から取得）
            **kwargs: プロバイダー固有の追加設定
        
        Returns:
            AIProviderBase: 初期化されたプロバイダーインスタンス
        
        Raises:
            AIProviderError: プロバイダーの作成に失敗した場合
        """
        provider_name = provider_name.lower()
        
        # プロバイダーサポートチェック
        if provider_name not in self.SUPPORTED_PROVIDERS:
            raise AIProviderError(
                provider_name,
                f"サポートされていないプロバイダー: {provider_name}. "
                f"サポートされているプロバイダー: {list(self.SUPPORTED_PROVIDERS.keys())}"
            )
        
        # APIキーの取得
        if not api_key:
            env_var = self.ENV_VAR_MAPPING.get(provider_name)
            api_key = os.getenv(env_var)
            
            if not api_key:
                raise AIProviderError(
                    provider_name,
                    f"APIキーが見つかりません。環境変数 {env_var} を設定するか、"
                    f"api_key パラメータを指定してください。"
                )
        
        # モデルの決定
        if not model:
            model = self.DEFAULT_MODELS.get(provider_name)
        
        # キャッシュキーの生成
        cache_key = f"{provider_name}:{model}:{hash(api_key)}"
        
        # キャッシュから取得を試行
        if cache_key in self._provider_cache:
            cached_provider = self._provider_cache[cache_key]
            logger.info(f"キャッシュからプロバイダーを取得: {provider_name}:{model}")
            return cached_provider
        
        # プロバイダーの作成
        try:
            provider_class = self.SUPPORTED_PROVIDERS[provider_name]
            provider = provider_class(api_key=api_key, model=model, **kwargs)
            
            # 設定の妥当性を検証
            if not provider.validate_configuration():
                raise AIProviderError(provider_name, "プロバイダー設定の検証に失敗しました")
            
            # キャッシュに保存
            self._provider_cache[cache_key] = provider
            
            logger.info(f"新しいプロバイダーを作成: {provider_name}:{model}")
            return provider
            
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            else:
                raise AIProviderError(provider_name, f"プロバイダー作成エラー: {str(e)}", e)
    
    def get_default_provider(self, **kwargs) -> AIProviderBase:
        """
        デフォルトのAIプロバイダーを取得
        
        環境変数 AI_PROVIDER で指定されたプロバイダーを使用
        未指定の場合は openai を使用
        
        Args:
            **kwargs: プロバイダー固有の追加設定
        
        Returns:
            AIProviderBase: デフォルトプロバイダー
        """
        default_provider = os.getenv("AI_PROVIDER", "openai").lower()
        default_model = kwargs.pop("model", None) or os.getenv("AI_MODEL")
        
        return self.create_provider(
            provider_name=default_provider,
            model=default_model,
            **kwargs
        )
    
    def list_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        利用可能なプロバイダーとその情報を一覧表示
        
        Returns:
            Dict: プロバイダー情報の辞書
        """
        providers_info = {}
        
        for provider_name, provider_class in self.SUPPORTED_PROVIDERS.items():
            env_var = self.ENV_VAR_MAPPING.get(provider_name)
            api_key_available = bool(os.getenv(env_var))
            
            providers_info[provider_name] = {
                "class": provider_class.__name__,
                "default_model": self.DEFAULT_MODELS.get(provider_name),
                "env_var": env_var,
                "api_key_available": api_key_available,
                "supported_models": getattr(provider_class, 'SUPPORTED_MODELS', {})
            }
        
        return providers_info
    
    def clear_cache(self):
        """プロバイダーキャッシュをクリア"""
        self._provider_cache.clear()
        logger.info("プロバイダーキャッシュをクリアしました")
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        現在のプロバイダー状況を取得
        
        Returns:
            Dict: プロバイダー状況の詳細
        """
        status = {
            "cached_providers": len(self._provider_cache),
            "available_providers": list(self.SUPPORTED_PROVIDERS.keys()),
            "default_provider": os.getenv("AI_PROVIDER", "openai"),
            "api_keys_configured": {}
        }
        
        # APIキー設定状況
        for provider_name, env_var in self.ENV_VAR_MAPPING.items():
            status["api_keys_configured"][provider_name] = bool(os.getenv(env_var))
        
        return status


# グローバルファクトリーインスタンス
ai_factory = AIProviderFactory()


def get_ai_provider(provider_name: Optional[str] = None, 
                   model: Optional[str] = None,
                   **kwargs) -> AIProviderBase:
    """
    AIプロバイダーを取得する便利関数
    
    Args:
        provider_name: プロバイダー名（未指定の場合はデフォルト）
        model: モデル名
        **kwargs: プロバイダー固有の追加設定
    
    Returns:
        AIProviderBase: AIプロバイダーインスタンス
    """
    if provider_name:
        return ai_factory.create_provider(provider_name, model, **kwargs)
    else:
        if model:
            kwargs['model'] = model
        return ai_factory.get_default_provider(**kwargs)


def get_provider_info() -> Dict[str, Any]:
    """
    プロバイダー情報を取得する便利関数
    
    Returns:
        Dict: プロバイダー情報
    """
    return {
        "available": ai_factory.list_available_providers(),
        "status": ai_factory.get_provider_status()
    }