"""
立花証券APIメインクライアント
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .session_manager import TachibanaSessionManager
from .price_service import TachibanaePriceService, TachibanaPrice
from app.core.config import settings
from app.core.data_models import CurrentPriceData

logger = logging.getLogger(__name__)

class TachibanaAPIClient:
    """立花証券APIメインクライアント"""
    
    def __init__(self):
        self.session_manager = TachibanaSessionManager()
        self.price_service = TachibanaePriceService(self.session_manager)
        self._is_connected = False
        
    async def connect(self, user_id: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        立花証券APIに接続
        
        Args:
            user_id: ユーザーID (省略時は環境変数から取得)
            password: パスワード (省略時は環境変数から取得)
            
        Returns:
            bool: 接続成功時True
        """
        try:
            # 認証情報取得
            user_id = user_id or settings.TACHIBANA_USER_ID
            password = password or settings.TACHIBANA_PASSWORD
            
            if not user_id or not password:
                raise ValueError("立花証券のユーザーID/パスワードが設定されていません")
            
            # ログイン実行
            success = self.session_manager.login(user_id, password)
            
            if success:
                self._is_connected = True
                logger.info("立花証券API接続完了")
            else:
                logger.error("立花証券API接続失敗")
                
            return success
            
        except Exception as e:
            logger.error(f"立花証券API接続エラー: {str(e)}")
            return False
            
    async def disconnect(self) -> bool:
        """
        立花証券APIから切断
        
        Returns:
            bool: 切断成功時True
        """
        try:
            success = self.session_manager.logout()
            self._is_connected = False
            logger.info("立花証券API切断完了")
            return success
            
        except Exception as e:
            logger.error(f"立花証券API切断エラー: {str(e)}")
            return False
            
    def is_connected(self) -> bool:
        """
        接続状態確認
        
        Returns:
            bool: 接続中の場合True
        """
        return self._is_connected and self.session_manager.is_logged_in()
        
    async def get_realtime_price(self, symbol: str) -> CurrentPriceData:
        """
        リアルタイム価格取得
        
        Args:
            symbol: 銘柄コード
            
        Returns:
            CurrentPriceData: 価格データ
        """
        try:
            if not self.is_connected():
                raise Exception("立花証券APIに接続していません")
                
            # 立花証券APIで価格取得
            tachibana_price = await self.price_service.get_realtime_price(symbol)
            
            # 共通フォーマットに変換
            current_price_data = self.price_service.to_current_price_data(tachibana_price)
            
            return current_price_data
            
        except Exception as e:
            logger.error(f"立花証券リアルタイム価格取得エラー [{symbol}]: {str(e)}")
            raise
            
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, CurrentPriceData]:
        """
        複数銘柄の価格取得
        
        Args:
            symbols: 銘柄コードリスト
            
        Returns:
            Dict[str, CurrentPriceData]: 銘柄別価格データ
        """
        try:
            if not self.is_connected():
                raise Exception("立花証券APIに接続していません")
                
            # 立花証券APIでバッチ価格取得
            tachibana_prices = await self.price_service.get_multiple_prices(symbols)
            
            # 共通フォーマットに変換
            price_data_dict = {}
            for symbol, tachibana_price in tachibana_prices.items():
                price_data_dict[symbol] = self.price_service.to_current_price_data(tachibana_price)
                
            return price_data_dict
            
        except Exception as e:
            logger.error(f"立花証券バッチ価格取得エラー: {str(e)}")
            raise
            
    async def stream_prices(self, symbols: List[str]):
        """
        価格データストリーミング（WebSocket用）
        
        Args:
            symbols: 監視する銘柄コード
            
        Yields:
            Dict[str, CurrentPriceData]: 更新された価格データ
        """
        try:
            if not self.is_connected():
                raise Exception("立花証券APIに接続していません")
                
            logger.info(f"立花証券価格ストリーミング開始: {symbols}")
            
            # 価格監視ループ
            while self.is_connected():
                try:
                    # 価格データ取得
                    price_data = await self.get_multiple_prices(symbols)
                    
                    # 更新をyield
                    yield price_data
                    
                    # 適切な間隔でポーリング（秒単位調整可能）
                    await asyncio.sleep(1.0)  # 1秒間隔
                    
                except Exception as e:
                    logger.error(f"価格ストリーミングエラー: {str(e)}")
                    await asyncio.sleep(5.0)  # エラー時は5秒待機
                    
        except Exception as e:
            logger.error(f"価格ストリーミング開始エラー: {str(e)}")
            raise
            
    async def get_market_status(self) -> Dict[str, Any]:
        """
        市場状態取得
        
        Returns:
            Dict[str, Any]: 市場状態情報
        """
        try:
            if not self.is_connected():
                raise Exception("立花証券APIに接続していません")
                
            # 市場状態取得パラメータ
            params = {
                'p_no': 10,  # 市場状態取得処理番号
            }
            
            response = self.session_manager.make_request('request', params)
            
            return {
                'is_market_open': response.get('is_market_open', False),
                'market_session': response.get('market_session', 'UNKNOWN'),
                'next_session_time': response.get('next_session_time'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"市場状態取得エラー: {str(e)}")
            # デフォルト値を返す
            return {
                'is_market_open': False,
                'market_session': 'UNKNOWN',
                'next_session_time': None,
                'timestamp': datetime.now().isoformat()
            }
            
    async def health_check(self) -> Dict[str, Any]:
        """
        立花証券APIヘルスチェック
        
        Returns:
            Dict[str, Any]: ヘルス状態
        """
        try:
            health_status = {
                'service': 'tachibana_api',
                'status': 'healthy' if self.is_connected() else 'disconnected',
                'demo_mode': settings.TACHIBANA_DEMO_MODE,
                'session_active': self.session_manager.is_logged_in(),
                'session_expiry': self.session_manager.session_expiry.isoformat() if self.session_manager.session_expiry else None,
                'timestamp': datetime.now().isoformat()
            }
            
            # 接続テスト
            if self.is_connected():
                market_status = await self.get_market_status()
                health_status['market_accessible'] = True
                health_status['market_status'] = market_status
            else:
                health_status['market_accessible'] = False
                
            return health_status
            
        except Exception as e:
            logger.error(f"立花証券APIヘルスチェックエラー: {str(e)}")
            return {
                'service': 'tachibana_api',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.disconnect()
        
    def __enter__(self):
        """同期コンテキストマネージャー開始"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同期コンテキストマネージャー終了"""
        asyncio.run(self.disconnect())