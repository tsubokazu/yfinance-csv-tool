"""
LangChain アダプター

カスタムAIプロバイダーをLangChainエコシステムで使用するためのアダプター
"""

from typing import Any, List, Optional, Dict
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

from .providers.base import AIProviderBase, AIResponse

logger = logging.getLogger(__name__)


class MultiProviderLangChainAdapter(Runnable):
    """
    カスタムAIプロバイダーをLangChain対応にするアダプター
    
    LangChainのエージェントやチェーンで使用できるようにするためのラッパークラス
    Runnableを継承してLangGraph互換性を提供
    """
    
    def __init__(self, ai_provider: AIProviderBase):
        """
        アダプターの初期化
        
        Args:
            ai_provider: カスタムAIプロバイダーインスタンス
        """
        super().__init__()
        self.ai_provider = ai_provider
        self.provider_name = ai_provider.provider_name
        self.model_name = ai_provider.model
    

    
    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs) -> AIMessage:
        """
        Runnableインターフェースの実装 - メッセージを送信してAI応答を取得
        
        Args:
            input: 入力データ（メッセージリストまたは単一メッセージ）
            config: Runnable設定
            **kwargs: 追加引数
        
        Returns:
            AIMessage: LangChain AIMessageオブジェクト
        """
        try:
            # 入力をメッセージリストに正規化
            if isinstance(input, list):
                messages = input
            elif isinstance(input, str):
                messages = [HumanMessage(content=input)]
            elif hasattr(input, 'content'):
                messages = [input]
            else:
                messages = [HumanMessage(content=str(input))]
            
            # LangChainメッセージを標準形式に変換
            standard_messages = self._convert_langchain_to_standard(messages)
            
            # AIプロバイダーで処理
            ai_response: AIResponse = self.ai_provider.invoke(standard_messages)
            
            # LangChain AIMessageとして返す
            return AIMessage(
                content=ai_response.content,
                additional_kwargs={
                    "provider": ai_response.provider,
                    "model": ai_response.model,
                    "token_usage": ai_response.token_usage,
                    "metadata": ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"LangChainアダプター呼び出しエラー: {e}")
            raise
    
    def _convert_langchain_to_standard(self, langchain_messages: List[Any]) -> List[Dict[str, Any]]:
        """
        LangChainメッセージを標準形式に変換
        
        Args:
            langchain_messages: LangChainメッセージのリスト
        
        Returns:
            標準形式のメッセージリスト
        """
        standard_messages = []
        
        for msg in langchain_messages:
            if isinstance(msg, HumanMessage):
                standard_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                standard_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                standard_messages.append({"role": "system", "content": msg.content})
            else:
                # 文字列や辞書の場合の処理
                if isinstance(msg, str):
                    standard_messages.append({"role": "user", "content": msg})
                elif isinstance(msg, dict):
                    standard_messages.append(msg)
                else:
                    logger.warning(f"未知のメッセージタイプ: {type(msg)}")
                    standard_messages.append({"role": "user", "content": str(msg)})
        
        return standard_messages
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """LangChain識別パラメータ"""
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "provider_info": self.ai_provider.get_provider_info()
        }
    
    def get_num_tokens(self, text: str) -> int:
        """
        テキストのトークン数を概算
        
        Args:
            text: 対象テキスト
        
        Returns:
            概算トークン数
        """
        # 簡易的な概算（より正確な実装が必要な場合は各プロバイダーのトークンカウンターを使用）
        return len(text.split()) * 1.3  # 単語数の1.3倍を概算とする
    
    def supports_vision(self) -> bool:
        """ビジョン機能のサポート状況"""
        return self.ai_provider.supports_vision()
    
    def invoke_with_images(self, text: str, image_data: List[str]) -> AIMessage:
        """
        画像付きでAIを呼び出し（ビジョン機能）
        
        Args:
            text: テキストメッセージ
            image_data: Base64エンコードされた画像データのリスト
        
        Returns:
            AIMessage: LangChain AIMessageオブジェクト
        """
        try:
            ai_response: AIResponse = self.ai_provider.invoke_with_images(text, image_data)
            
            return AIMessage(
                content=ai_response.content,
                additional_kwargs={
                    "provider": ai_response.provider,
                    "model": ai_response.model,
                    "token_usage": ai_response.token_usage,
                    "metadata": ai_response.metadata,
                    "vision": True
                }
            )
            
        except Exception as e:
            logger.error(f"LangChainアダプター画像呼び出しエラー: {e}")
            raise
    
    def bind_tools(self, tools: List[Any], **kwargs) -> "MultiProviderLangChainAdapter":
        """
        ツールをバインド（LangGraph互換性のため）
        
        Args:
            tools: バインドするツールのリスト
            **kwargs: 追加のバインド引数
        
        Returns:
            ツールがバインドされたアダプターインスタンス
        """
        # ツール情報を保存
        self._bound_tools = tools
        self._bind_kwargs = kwargs
        
        # LangGraphでの動作のため、自分自身を返す
        return self
    
    def get_bound_tools(self) -> List[Any]:
        """バインドされたツールを取得"""
        return getattr(self, '_bound_tools', [])
    
    def with_structured_output(self, schema, **kwargs):
        """構造化出力サポート（LangChain互換性のため）"""
        # 構造化出力設定を保存
        self._output_schema = schema
        self._output_kwargs = kwargs
        return self


def create_langchain_llm(ai_provider: AIProviderBase) -> MultiProviderLangChainAdapter:
    """
    AIプロバイダーからLangChain対応LLMを作成
    
    Args:
        ai_provider: AIプロバイダーインスタンス
    
    Returns:
        LangChain対応のLLMアダプター
    """
    return MultiProviderLangChainAdapter(ai_provider)