"""
AI プロバイダー基底クラス

全AIプロバイダーの共通インターフェースを定義
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """AI応答の標準化されたデータクラス"""
    content: str
    model: str
    provider: str
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIProviderBase(ABC):
    """
    AIプロバイダーの基底クラス
    
    全てのAIプロバイダーがこのインターフェースを実装する必要がある
    """
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """
        基底クラスの初期化
        
        Args:
            api_key: APIキー
            model: 使用するモデル名
            **kwargs: プロバイダー固有の設定
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()
        
        # 共通設定
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4000)
        
        logger.info(f"初期化完了: {self.provider_name} - {model}")
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, Any]]) -> AIResponse:
        """
        メッセージを送信してAI応答を取得
        
        Args:
            messages: チャット形式のメッセージリスト
                     [{"role": "user", "content": "..."}, ...]
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        pass
    
    @abstractmethod
    def invoke_with_system_prompt(self, system_prompt: str, user_message: str) -> AIResponse:
        """
        システムプロンプトとユーザーメッセージで呼び出し
        
        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """
        画像解析機能をサポートしているかどうか
        
        Returns:
            bool: サポートしている場合True
        """
        pass
    
    @abstractmethod
    def invoke_with_images(self, text: str, image_data: List[str]) -> AIResponse:
        """
        画像付きでAIを呼び出し（ビジョン機能）
        
        Args:
            text: テキストメッセージ
            image_data: Base64エンコードされた画像データのリスト
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        
        Raises:
            NotImplementedError: プロバイダーがビジョン機能をサポートしていない場合
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        プロバイダー情報を取得
        
        Returns:
            Dict: プロバイダーの詳細情報
        """
        return {
            "provider": self.provider_name,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "supports_vision": self.supports_vision(),
            "config": self.config
        }
    
    def _format_messages_for_provider(self, messages: List[Dict[str, Any]]) -> Any:
        """
        プロバイダー固有のメッセージ形式に変換
        
        子クラスで必要に応じてオーバーライド
        
        Args:
            messages: 標準形式のメッセージリスト
        
        Returns:
            プロバイダー固有のメッセージ形式
        """
        return messages
    
    def _extract_token_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """
        レスポンスからトークン使用量を抽出
        
        子クラスで必要に応じてオーバーライド
        
        Args:
            response: プロバイダー固有のレスポンス
        
        Returns:
            トークン使用量の辞書またはNone
        """
        return None
    
    def validate_configuration(self) -> bool:
        """
        設定の妥当性を検証
        
        Returns:
            bool: 設定が有効な場合True
        """
        if not self.api_key:
            logger.error(f"{self.provider_name}: APIキーが設定されていません")
            return False
        
        if not self.model:
            logger.error(f"{self.provider_name}: モデルが指定されていません")
            return False
        
        return True


class AIProviderError(Exception):
    """AIプロバイダー関連のエラー"""
    
    def __init__(self, provider: str, message: str, original_error: Optional[Exception] = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")


class ModelNotSupportedError(AIProviderError):
    """サポートされていないモデルエラー"""
    pass


class VisionNotSupportedError(AIProviderError):
    """ビジョン機能がサポートされていないエラー"""
    pass