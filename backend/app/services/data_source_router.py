"""
データソースルーター
yfinanceと立花証券APIのハイブリッド利用を管理
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, time
from enum import Enum
import asyncio

from app.core.data_models import CurrentPriceData, MinuteDecisionPackage
from app.services.minute_decision_engine import MinuteDecisionEngine
from app.services.tachibana import TachibanaAPIClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """データソース種別"""
    YFINANCE = "yfinance"
    TACHIBANA = "tachibana"
    AUTO = "auto"

class DataSourceRouter:
    """
    データソースルーター
    
    yfinanceとTachibana APIを自動選択して最適なデータを提供
    """
    
    def __init__(self):
        """初期化"""
        self.yfinance_engine = MinuteDecisionEngine()
        self.tachibana_client = TachibanaAPIClient()
        self._tachibana_connected = False
        
        logger.info("データソースルーター初期化完了")
        
    async def initialize(self) -> bool:
        """
        ルーター初期化（立花証券API接続試行）
        
        Returns:
            bool: 初期化成功時True
        """
        try:
            # 立花証券API接続試行
            if settings.TACHIBANA_USER_ID and settings.TACHIBANA_PASSWORD:
                logger.info("立花証券API接続を試行中...")
                self._tachibana_connected = await self.tachibana_client.connect()
                
                if self._tachibana_connected:
                    logger.info("✅ 立花証券API接続成功 - リアルタイムデータ利用可能")
                else:
                    logger.warning("⚠️ 立花証券API接続失敗 - yfinanceのみ利用")
            else:
                logger.info("立花証券認証情報未設定 - yfinanceのみ利用")
                
            return True
            
        except Exception as e:
            logger.error(f"データソースルーター初期化エラー: {str(e)}")
            return False
            
    async def get_current_price(
        self, 
        symbol: str, 
        source: DataSource = DataSource.AUTO
    ) -> CurrentPriceData:
        """
        現在価格取得
        
        Args:
            symbol: 銘柄コード
            source: データソース指定
            
        Returns:
            CurrentPriceData: 現在価格データ
        """
        try:
            selected_source = self._select_optimal_source(source)
            
            logger.info(f"価格取得開始: {symbol} (ソース: {selected_source.value})")
            
            if selected_source == DataSource.TACHIBANA and self._tachibana_connected:
                return await self._get_tachibana_price(symbol)
            else:
                return await self._get_yfinance_price(symbol)
                
        except Exception as e:
            logger.error(f"価格取得エラー [{symbol}]: {str(e)}")
            # フォールバック: yfinanceで再試行
            if selected_source != DataSource.YFINANCE:
                logger.info(f"yfinanceにフォールバック: {symbol}")
                return await self._get_yfinance_price(symbol)
            raise
            
    async def get_trading_data(
        self,
        symbol: str,
        timestamp: datetime,
        source: DataSource = DataSource.AUTO
    ) -> MinuteDecisionPackage:
        """
        包括的トレーディングデータ取得
        
        Args:
            symbol: 銘柄コード
            timestamp: 判断時刻
            source: データソース指定
            
        Returns:
            MinuteDecisionPackage: 判断データパッケージ
        """
        try:
            selected_source = self._select_optimal_source(source)
            
            logger.info(f"トレーディングデータ取得開始: {symbol} at {timestamp} (ソース: {selected_source.value})")
            
            if selected_source == DataSource.TACHIBANA and self._tachibana_connected:
                # 立花証券API + yfinance混合モード
                return await self._get_hybrid_trading_data(symbol, timestamp)
            else:
                # yfinanceのみモード
                return self.yfinance_engine.get_minute_decision_data(symbol, timestamp)
                
        except Exception as e:
            logger.error(f"トレーディングデータ取得エラー [{symbol}]: {str(e)}")
            # フォールバック: yfinanceのみ
            logger.info(f"yfinanceにフォールバック: {symbol}")
            return self.yfinance_engine.get_minute_decision_data(symbol, timestamp)
            
    async def get_multiple_prices(
        self,
        symbols: List[str],
        source: DataSource = DataSource.AUTO
    ) -> Dict[str, CurrentPriceData]:
        """
        複数銘柄価格取得
        
        Args:
            symbols: 銘柄コードリスト
            source: データソース指定
            
        Returns:
            Dict[str, CurrentPriceData]: 銘柄別価格データ
        """
        try:
            selected_source = self._select_optimal_source(source)
            
            logger.info(f"複数銘柄価格取得開始: {len(symbols)}銘柄 (ソース: {selected_source.value})")
            
            if selected_source == DataSource.TACHIBANA and self._tachibana_connected:
                return await self.tachibana_client.get_multiple_prices(symbols)
            else:
                return await self._get_yfinance_multiple_prices(symbols)
                
        except Exception as e:
            logger.error(f"複数銘柄価格取得エラー: {str(e)}")
            # フォールバック: yfinance
            return await self._get_yfinance_multiple_prices(symbols)
            
    def _select_optimal_source(self, source: DataSource) -> DataSource:
        """
        最適なデータソース選択
        
        Args:
            source: 指定されたソース
            
        Returns:
            DataSource: 選択されたソース
        """
        if source != DataSource.AUTO:
            return source
            
        # 自動選択ロジック
        if self._is_market_hours() and self._tachibana_connected:
            return DataSource.TACHIBANA
        else:
            return DataSource.YFINANCE
            
    def _is_market_hours(self) -> bool:
        """
        市場時間判定
        
        Returns:
            bool: 市場時間内の場合True
        """
        now = datetime.now()
        current_time = now.time()
        
        # 日本市場時間（平日 9:00-15:00）
        market_open = time(9, 0)
        market_close = time(15, 0)
        
        is_weekday = now.weekday() < 5  # 月-金
        is_market_time = market_open <= current_time <= market_close
        
        return is_weekday and is_market_time
        
    async def _get_tachibana_price(self, symbol: str) -> CurrentPriceData:
        """立花証券APIから価格取得"""
        return await self.tachibana_client.get_realtime_price(symbol)
        
    async def _get_yfinance_price(self, symbol: str) -> CurrentPriceData:
        """yfinanceから価格取得"""
        # yfinanceエンジンを使用して現在のデータを取得
        import asyncio
        from datetime import datetime
        
        loop = asyncio.get_event_loop()
        
        # MinuteDecisionEngineから基本データを取得
        decision_data = await loop.run_in_executor(
            None,
            self.yfinance_engine.get_minute_decision_data,
            symbol,
            datetime.now()
        )
        
        return decision_data.current_price
        
    async def _get_yfinance_multiple_prices(self, symbols: List[str]) -> Dict[str, CurrentPriceData]:
        """yfinanceから複数銘柄価格取得"""
        price_dict = {}
        
        # 並列処理で複数銘柄取得
        tasks = [self._get_yfinance_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"yfinance価格取得エラー [{symbol}]: {str(result)}")
            else:
                price_dict[symbol] = result
                
        return price_dict
        
    async def _get_hybrid_trading_data(
        self, 
        symbol: str, 
        timestamp: datetime
    ) -> MinuteDecisionPackage:
        """
        ハイブリッドトレーディングデータ取得
        
        立花証券のリアルタイム価格 + yfinanceの分析データ
        """
        try:
            # yfinanceベースの分析データ取得
            base_data = self.yfinance_engine.get_minute_decision_data(symbol, timestamp)
            
            # 立花証券からリアルタイム価格取得して上書き
            try:
                realtime_price = await self.tachibana_client.get_realtime_price(symbol)
                base_data.current_price = realtime_price
                logger.info(f"ハイブリッドデータ取得完了: {symbol} (リアルタイム価格: {realtime_price.current_price}円)")
            except Exception as e:
                logger.warning(f"立花証券価格取得失敗、yfinance価格を使用: {str(e)}")
                
            return base_data
            
        except Exception as e:
            logger.error(f"ハイブリッドデータ取得エラー: {str(e)}")
            raise
            
    async def get_data_source_status(self) -> Dict[str, Any]:
        """
        データソース状態取得
        
        Returns:
            Dict[str, Any]: データソース状態情報
        """
        try:
            yfinance_status = {
                "available": True,
                "type": "historical_delayed",
                "delay_minutes": 15
            }
            
            tachibana_status = {
                "available": self._tachibana_connected,
                "type": "realtime" if self._tachibana_connected else "unavailable",
                "delay_minutes": 0 if self._tachibana_connected else None
            }
            
            if self._tachibana_connected:
                health = await self.tachibana_client.health_check()
                tachibana_status.update(health)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "market_hours": self._is_market_hours(),
                "sources": {
                    "yfinance": yfinance_status,
                    "tachibana": tachibana_status
                },
                "recommended_source": self._select_optimal_source(DataSource.AUTO).value
            }
            
        except Exception as e:
            logger.error(f"データソース状態取得エラー: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "sources": {
                    "yfinance": {"available": True, "type": "fallback"},
                    "tachibana": {"available": False, "type": "error"}
                }
            }
            
    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self._tachibana_connected:
                await self.tachibana_client.disconnect()
                self._tachibana_connected = False
            logger.info("データソースルーター クリーンアップ完了")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {str(e)}")
            
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.cleanup()