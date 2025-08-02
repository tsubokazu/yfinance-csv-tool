"""
Google Gemini プロバイダー実装

Google Gemini モデル用のプロバイダークラス
"""

from typing import Dict, Any, List, Optional
import logging
import base64

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import AIProviderBase, AIResponse, AIProviderError, ModelNotSupportedError, VisionNotSupportedError

logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderBase):
    """Google Gemini モデル用のプロバイダー"""
    
    # サポートされているモデル
    SUPPORTED_MODELS = {
        "gemini-1.5-pro": {"supports_vision": True, "max_tokens": 1048576},
        "gemini-1.5-flash": {"supports_vision": True, "max_tokens": 1048576},
        "gemini-pro": {"supports_vision": False, "max_tokens": 32768},
        "gemini-pro-vision": {"supports_vision": True, "max_tokens": 32768},
    }
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", **kwargs):
        """
        Geminiプロバイダーの初期化
        
        Args:
            api_key: Google AI Studio APIキー
            model: 使用するGeminiモデル
            **kwargs: 追加設定（temperature, max_tokensなど）
        """
        if not GEMINI_AVAILABLE:
            raise AIProviderError(
                "gemini", 
                "google-generativeai パッケージがインストールされていません。"
                "pip install google-generativeai でインストールしてください。"
            )
        
        super().__init__(api_key, model, **kwargs)
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                "gemini", 
                f"モデル '{model}' はサポートされていません。"
                f"サポートされているモデル: {list(self.SUPPORTED_MODELS.keys())}"
            )
        
        # Gemini APIの初期化
        try:
            genai.configure(api_key=api_key)
            
            # 安全性設定（必要に応じて調整）
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # 生成設定
            self.generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 64),
            }
            
            # モデルの初期化
            self.model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            logger.info(f"Gemini model初期化完了: {model}")
            
        except Exception as e:
            raise AIProviderError("gemini", f"モデル初期化エラー: {str(e)}", e)
    
    def invoke(self, messages: List[Dict[str, Any]]) -> AIResponse:
        """
        メッセージを送信してGeminiから応答を取得
        
        Args:
            messages: チャット形式のメッセージリスト
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        try:
            # Gemini用のプロンプトに変換
            prompt = self._convert_messages_to_prompt(messages)
            
            # Gemini APIに送信
            response = self.model_instance.generate_content(prompt)
            
            # セーフティフィルターでブロックされた場合の処理
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 1:  # STOP = 1
                    logger.warning(f"Gemini応答がフィルターされました: {candidate.finish_reason}")
            
            # トークン使用量の取得（利用可能な場合）
            token_usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                token_usage = {
                    'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                    'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                    'total_tokens': getattr(usage, 'total_token_count', 0)
                }
            
            return AIResponse(
                content=response.text,
                model=self.model,
                provider="gemini",
                token_usage=token_usage,
                metadata={
                    "generation_config": self.generation_config,
                    "safety_settings": str(self.safety_settings),
                    "finish_reason": getattr(response.candidates[0], 'finish_reason', None) if hasattr(response, 'candidates') and response.candidates else None
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini API呼び出しエラー: {e}")
            raise AIProviderError("gemini", f"API呼び出しエラー: {str(e)}", e)
    
    def invoke_with_system_prompt(self, system_prompt: str, user_message: str) -> AIResponse:
        """
        システムプロンプトとユーザーメッセージでGeminiを呼び出し
        
        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        # Geminiではシステムプロンプトを先頭に含めてユーザーメッセージとして送信
        combined_prompt = f"システム指示:\n{system_prompt}\n\nユーザー:\n{user_message}"
        
        messages = [{"role": "user", "content": combined_prompt}]
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
        画像付きでGemini Vision APIを呼び出し
        
        Args:
            text: テキストメッセージ
            image_data: Base64エンコードされた画像データのリスト
        
        Returns:
            AIResponse: 標準化された応答オブジェクト
        """
        if not self.supports_vision():
            raise VisionNotSupportedError(
                "gemini", 
                f"モデル '{self.model}' はビジョン機能をサポートしていません"
            )
        
        try:
            # マルチモーダルコンテンツを構築
            content_parts = [text]
            
            for image_b64 in image_data:
                # Base64デコードして画像データに変換
                image_bytes = base64.b64decode(image_b64)
                
                # Gemini用の画像オブジェクトを作成
                image_part = {
                    "mime_type": "image/png",  # 必要に応じて他の形式も対応
                    "data": image_bytes
                }
                content_parts.append(image_part)
            
            # Gemini APIに送信
            response = self.model_instance.generate_content(content_parts)
            
            return AIResponse(
                content=response.text,
                model=self.model,
                provider="gemini",
                token_usage=self._extract_token_usage(response),
                metadata={
                    "vision": True,
                    "image_count": len(image_data),
                    "generation_config": self.generation_config
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini Vision API呼び出しエラー: {e}")
            raise AIProviderError("gemini", f"Vision API呼び出しエラー: {str(e)}", e)
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        標準メッセージ形式をGemini用プロンプトに変換
        
        Args:
            messages: 標準形式のメッセージリスト
        
        Returns:
            Gemini用の統合プロンプト
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"システム指示:\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"アシスタント:\n{content}")
            else:  # user or default
                prompt_parts.append(f"ユーザー:\n{content}")
        
        return "\n\n".join(prompt_parts)
    
    def _extract_token_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """
        Geminiレスポンスからトークン使用量を抽出
        
        Args:
            response: Geminiレスポンス
        
        Returns:
            トークン使用量の辞書またはNone
        """
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            return {
                'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                'total_tokens': getattr(usage, 'total_token_count', 0)
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
            "max_model_tokens": model_info.get("max_tokens", 32768),
            "generation_config": self.generation_config,
            "safety_settings_enabled": True
        }