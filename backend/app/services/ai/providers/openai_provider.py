"""
OpenAI プロバイダー実装

OpenAI GPT モデル用のプロバイダークラス
"""

from typing import Dict, Any, List, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from .base import AIProviderBase, AIResponse, AIProviderError, ModelNotSupportedError

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProviderBase):
    """OpenAI GPTモデル用のプロバイダー"""
    
    # サポートされているモデル
    SUPPORTED_MODELS = {
        "gpt-4o": {"supports_vision": True, "max_tokens": 128000},
        "gpt-4": {"supports_vision": False, "max_tokens": 8192},
        "gpt-4-turbo": {"supports_vision": True, "max_tokens": 128000},
        "gpt-3.5-turbo": {"supports_vision": False, "max_tokens": 4096},
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs):
        """
        OpenAIプロバイダーの初期化
        
        Args:
            api_key: OpenAI APIキー
            model: 使用するGPTモデル
            **kwargs: 追加設定（temperature, max_tokensなど）
        """
        super().__init__(api_key, model, **kwargs)
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                "openai", 
                f"モデル '{model}' はサポートされていません。"
                f"サポートされているモデル: {list(self.SUPPORTED_MODELS.keys())}"
            )
        
        # OpenAI ChatLLMの初期化
        try:
            self.llm = ChatOpenAI(
                api_key=api_key,
                model=model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            logger.info(f"OpenAI ChatLLM初期化完了: {model}")
            
        except Exception as e:
            raise AIProviderError("openai", f"LLM初期化エラー: {str(e)}", e)
    
    def invoke(self, messages: List[Dict[str, Any]]) -> AIResponse:
        """
        メッセージを送信してOpenAI GPTから応答を取得
        
        Args:
            messages: チャット形式のメッセージリスト
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        try:
            # LangChainメッセージ形式に変換
            langchain_messages = self._convert_to_langchain_messages(messages)
            
            # OpenAI APIに送信
            response = self.llm.invoke(langchain_messages)
            
            # トークン使用量の取得（利用可能な場合）
            token_usage = None
            if hasattr(response, 'response_metadata') and response.response_metadata:
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    token_usage = {
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
            
            return AIResponse(
                content=response.content,
                model=self.model,
                provider="openai",
                token_usage=token_usage,
                metadata={
                    "response_metadata": getattr(response, 'response_metadata', {}),
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI API呼び出しエラー: {e}")
            raise AIProviderError("openai", f"API呼び出しエラー: {str(e)}", e)
    
    def invoke_with_system_prompt(self, system_prompt: str, user_message: str) -> AIResponse:
        """
        システムプロンプトとユーザーメッセージでOpenAIを呼び出し
        
        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.invoke(messages)
    
    def supports_vision(self) -> bool:
        """
        現在のモデルが画像解析をサポートしているかチェック
        
        Returns:
            bool: サポートしている場合True
        """
        return self.SUPPORTED_MODELS.get(self.model, {}).get("supports_vision", False)
    
    def invoke_with_images(self, text: str, image_data: List[str]) -> AIResponse:
        """
        画像付きでOpenAI GPT Vision APIを呼び出し
        
        Args:
            text: テキストメッセージ
            image_data: Base64エンコードされた画像データのリスト
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        if not self.supports_vision():
            raise AIProviderError(
                "openai", 
                f"モデル '{self.model}' はビジョン機能をサポートしていません"
            )
        
        try:
            # マルチモーダルメッセージを構築
            content_parts = [{"type": "text", "text": text}]
            
            for image_b64 in image_data:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                        "detail": "high"
                    }
                })
            
            message = HumanMessage(content=content_parts)
            response = self.llm.invoke([message])
            
            return AIResponse(
                content=response.content,
                model=self.model,
                provider="openai",
                token_usage=self._extract_token_usage(response),
                metadata={
                    "vision": True,
                    "image_count": len(image_data),
                    "response_metadata": getattr(response, 'response_metadata', {})
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI Vision API呼び出しエラー: {e}")
            raise AIProviderError("openai", f"Vision API呼び出しエラー: {str(e)}", e)
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List:
        """
        標準メッセージ形式をLangChainメッセージに変換
        
        Args:
            messages: 標準形式のメッセージリスト
        
        Returns:
            LangChainメッセージのリスト
        """
        langchain_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user or default
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    def _extract_token_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """
        OpenAIレスポンスからトークン使用量を抽出
        
        Args:
            response: OpenAIレスポンス
        
        Returns:
            トークン使用量の辞書またはNone
        """
        if hasattr(response, 'response_metadata') and response.response_metadata:
            usage = response.response_metadata.get('token_usage', {})
            if usage:
                return {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
        return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        モデル情報を取得
        
        Returns:
            Dict: モデルの詳細情報
        """
        model_info = self.SUPPORTED_MODELS.get(self.model, {})
        return {
            **super().get_provider_info(),
            "model_info": model_info,
            "supports_vision": self.supports_vision(),
            "max_model_tokens": model_info.get("max_tokens", 4000)
        }