"""
AI設定管理

AIプロバイダーに関する設定の管理と検証
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIProviderConfig:
    """AIプロバイダー設定データクラス"""
    provider: str
    model: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 4000
    additional_config: Optional[Dict[str, Any]] = None


class AIConfigManager:
    """AI設定マネージャー"""
    
    # デフォルト設定
    DEFAULT_CONFIGS = {
        "openai": {
            "model": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 4000
        },
        "gemini": {
            "model": "gemini-1.5-pro",
            "temperature": 0.1,
            "max_tokens": 4000,
            "top_p": 0.95,
            "top_k": 64
        }
    }
    
    # 環境変数マッピング
    ENV_VARS = {
        "provider": "AI_PROVIDER",
        "model": "AI_MODEL",
        "temperature": "AI_TEMPERATURE",
        "max_tokens": "AI_MAX_TOKENS",
        "openai_api_key": "OPENAI_API_KEY",
        "gemini_api_key": "GEMINI_API_KEY"
    }
    
    def __init__(self):
        self._config_cache: Optional[AIProviderConfig] = None
    
    def get_config(self, force_reload: bool = False) -> AIProviderConfig:
        """
        現在のAI設定を取得
        
        Args:
            force_reload: キャッシュを無視して再読み込み
        
        Returns:
            AIProviderConfig: AI設定
        """
        if self._config_cache is None or force_reload:
            self._config_cache = self._load_config()
        
        return self._config_cache
    
    def _load_config(self) -> AIProviderConfig:
        """設定を環境変数から読み込み"""
        
        # プロバイダーの決定
        provider = os.getenv(self.ENV_VARS["provider"], "openai").lower()
        
        # デフォルト設定の取得
        default_config = self.DEFAULT_CONFIGS.get(provider, self.DEFAULT_CONFIGS["openai"])
        
        # モデルの決定
        model = os.getenv(self.ENV_VARS["model"], default_config["model"])
        
        # APIキーの取得
        if provider == "openai":
            api_key = os.getenv(self.ENV_VARS["openai_api_key"])
        elif provider == "gemini":
            api_key = os.getenv(self.ENV_VARS["gemini_api_key"])
        else:
            api_key = None
        
        if not api_key:
            raise ValueError(f"{provider} のAPIキーが設定されていません")
        
        # その他の設定
        temperature = float(os.getenv(self.ENV_VARS["temperature"], default_config["temperature"]))
        max_tokens = int(os.getenv(self.ENV_VARS["max_tokens"], default_config["max_tokens"]))
        
        # プロバイダー固有の追加設定
        additional_config = {}
        if provider == "gemini":
            additional_config.update({
                "top_p": default_config.get("top_p", 0.95),
                "top_k": default_config.get("top_k", 64)
            })
        
        config = AIProviderConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            additional_config=additional_config
        )
        
        logger.info(f"AI設定読み込み完了: {provider}:{model}")
        return config
    
    def validate_config(self, config: Optional[AIProviderConfig] = None) -> bool:
        """
        設定の妥当性を検証
        
        Args:
            config: 検証する設定（Noneの場合は現在の設定）
        
        Returns:
            bool: 設定が有効な場合True
        """
        if config is None:
            try:
                config = self.get_config()
            except Exception as e:
                logger.error(f"設定取得エラー: {e}")
                return False
        
        # 必須フィールドのチェック
        if not config.provider:
            logger.error("プロバイダーが指定されていません")
            return False
        
        if not config.model:
            logger.error("モデルが指定されていません")
            return False
        
        if not config.api_key:
            logger.error("APIキーが指定されていません")
            return False
        
        # 数値範囲のチェック
        if not (0.0 <= config.temperature <= 2.0):
            logger.error(f"temperatureの値が無効です: {config.temperature}")
            return False
        
        if config.max_tokens <= 0:
            logger.error(f"max_tokensの値が無効です: {config.max_tokens}")
            return False
        
        logger.info(f"設定検証完了: {config.provider}:{config.model}")
        return True
    
    def get_env_status(self) -> Dict[str, Any]:
        """
        環境変数の設定状況を取得
        
        Returns:
            Dict: 環境変数の状況
        """
        status = {}
        
        for key, env_var in self.ENV_VARS.items():
            value = os.getenv(env_var)
            if "api_key" in key:
                # APIキーはマスク表示
                status[key] = "設定済み" if value else "未設定"
            else:
                status[key] = value if value else "未設定"
        
        return status
    
    def set_provider_config(self, 
                           provider: str, 
                           model: Optional[str] = None,
                           **kwargs) -> None:
        """
        プロバイダー設定を更新（ランタイム）
        
        Args:
            provider: プロバイダー名
            model: モデル名
            **kwargs: その他の設定
        """
        # 環境変数を更新
        os.environ[self.ENV_VARS["provider"]] = provider
        
        if model:
            os.environ[self.ENV_VARS["model"]] = model
        
        # その他の設定を更新
        for key, value in kwargs.items():
            if key in ["temperature", "max_tokens"] and hasattr(self.ENV_VARS, key):
                os.environ[self.ENV_VARS[key]] = str(value)
        
        # キャッシュをクリア
        self._config_cache = None
        
        logger.info(f"プロバイダー設定更新: {provider}:{model}")
    
    def reset_cache(self):
        """設定キャッシュをリセット"""
        self._config_cache = None
        logger.info("AI設定キャッシュをリセットしました")


# グローバル設定マネージャーインスタンス
config_manager = AIConfigManager()


def get_ai_config() -> AIProviderConfig:
    """
    現在のAI設定を取得する便利関数
    
    Returns:
        AIProviderConfig: 現在のAI設定
    """
    return config_manager.get_config()


def validate_ai_config() -> bool:
    """
    現在のAI設定の妥当性を検証する便利関数
    
    Returns:
        bool: 設定が有効な場合True
    """
    return config_manager.validate_config()


def get_config_status() -> Dict[str, Any]:
    """
    AI設定の状況を取得する便利関数
    
    Returns:
        Dict: 設定状況の詳細
    """
    try:
        config = config_manager.get_config()
        return {
            "status": "OK",
            "provider": config.provider,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "env_status": config_manager.get_env_status(),
            "is_valid": config_manager.validate_config(config)
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "env_status": config_manager.get_env_status(),
            "is_valid": False
        }