"""
立花証券API価格データ取得サービス
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

from .session_manager import TachibanaSessionManager
from app.core.data_models import CurrentPriceData

logger = logging.getLogger(__name__)

@dataclass
class TachibanaPrice:
    """立花証券価格データ"""
    symbol: str
    current_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    previous_close: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    market_status: Optional[str] = None

class TachibanaePriceService:
    """立花証券価格データ取得サービス"""
    
    def __init__(self, session_manager: TachibanaSessionManager):
        self.session_manager = session_manager
        
    async def get_realtime_price(self, symbol: str) -> TachibanaPrice:
        """
        リアルタイム価格取得
        
        Args:
            symbol: 銘柄コード (例: "6723")
            
        Returns:
            TachibanaPrice: 価格データ
        """
        try:
            # 銘柄コード正規化 (.Tを除去)
            clean_symbol = symbol.replace('.T', '')
            
            # 価格取得パラメータ
            params = {
                'p_no': 1,  # 処理番号
                'symbol': clean_symbol,
                'gettype': 'snap'  # スナップショット取得
            }
            
            logger.info(f"立花証券リアルタイム価格取得開始: {symbol}")
            
            # APIリクエスト実行
            response = self.session_manager.make_request('price', params)
            
            # レスポンス解析
            price_data = self._parse_price_response(response, symbol)
            
            logger.info(f"立花証券価格取得完了: {symbol} = {price_data.current_price}円")
            
            return price_data
            
        except Exception as e:
            logger.error(f"立花証券価格取得エラー [{symbol}]: {str(e)}")
            raise
            
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, TachibanaPrice]:
        """
        複数銘柄の価格を同時取得
        
        Args:
            symbols: 銘柄コードリスト
            
        Returns:
            Dict[str, TachibanaPrice]: 銘柄別価格データ
        """
        try:
            # 最大120銘柄まで一度に取得可能
            if len(symbols) > 120:
                logger.warning(f"銘柄数制限: {len(symbols)} -> 120件に制限")
                symbols = symbols[:120]
                
            # 銘柄コード正規化
            clean_symbols = [s.replace('.T', '') for s in symbols]
            
            # バッチ価格取得パラメータ
            params = {
                'p_no': 2,  # バッチ取得処理番号
                'symbols': clean_symbols,
                'gettype': 'snap'
            }
            
            logger.info(f"立花証券バッチ価格取得開始: {len(symbols)}銘柄")
            
            # APIリクエスト実行
            response = self.session_manager.make_request('price', params)
            
            # レスポンス解析
            price_dict = self._parse_batch_price_response(response, symbols)
            
            logger.info(f"立花証券バッチ価格取得完了: {len(price_dict)}銘柄")
            
            return price_dict
            
        except Exception as e:
            logger.error(f"立花証券バッチ価格取得エラー: {str(e)}")
            raise
            
    async def get_historical_prices(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        履歴価格データ取得（日足）
        
        Args:
            symbol: 銘柄コード
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[Dict[str, Any]]: 履歴価格データ
        """
        try:
            clean_symbol = symbol.replace('.T', '')
            
            # 履歴データ取得パラメータ
            params = {
                'p_no': 3,  # 履歴取得処理番号
                'symbol': clean_symbol,
                'start_date': start_date.strftime('%Y%m%d'),
                'end_date': end_date.strftime('%Y%m%d'),
                'period': 'daily'
            }
            
            logger.info(f"立花証券履歴価格取得開始: {symbol} ({start_date} - {end_date})")
            
            # APIリクエスト実行
            response = self.session_manager.make_request('request', params)
            
            # レスポンス解析
            historical_data = self._parse_historical_response(response)
            
            logger.info(f"立花証券履歴価格取得完了: {symbol} {len(historical_data)}件")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"立花証券履歴価格取得エラー [{symbol}]: {str(e)}")
            raise
            
    def _parse_price_response(self, response: Dict[str, Any], symbol: str) -> TachibanaPrice:
        """
        価格レスポンス解析
        
        Args:
            response: APIレスポンス
            symbol: 銘柄コード
            
        Returns:
            TachibanaPrice: 解析済み価格データ
        """
        try:
            # レスポンス構造は立花証券API仕様に従って調整が必要
            # 以下は推定される構造での実装
            
            price_info = response.get('price_info', {})
            
            return TachibanaPrice(
                symbol=symbol,
                current_price=float(price_info.get('current_price', 0)),
                bid=self._safe_float(price_info.get('bid')),
                ask=self._safe_float(price_info.get('ask')),
                volume=self._safe_int(price_info.get('volume')),
                timestamp=datetime.now(),
                change=self._safe_float(price_info.get('change')),
                change_percent=self._safe_float(price_info.get('change_percent')),
                previous_close=self._safe_float(price_info.get('previous_close')),
                high=self._safe_float(price_info.get('high')),
                low=self._safe_float(price_info.get('low')),
                market_status=price_info.get('market_status', 'UNKNOWN')
            )
            
        except Exception as e:
            logger.error(f"価格レスポンス解析エラー: {str(e)}")
            # デフォルト価格データを返す
            return TachibanaPrice(
                symbol=symbol,
                current_price=0.0,
                timestamp=datetime.now()
            )
            
    def _parse_batch_price_response(
        self, 
        response: Dict[str, Any], 
        symbols: List[str]
    ) -> Dict[str, TachibanaPrice]:
        """
        バッチ価格レスポンス解析
        
        Args:
            response: APIレスポンス
            symbols: 銘柄コードリスト
            
        Returns:
            Dict[str, TachibanaPrice]: 銘柄別価格データ
        """
        try:
            price_dict = {}
            price_list = response.get('price_list', [])
            
            for i, price_info in enumerate(price_list):
                if i < len(symbols):
                    symbol = symbols[i]
                    price_dict[symbol] = TachibanaPrice(
                        symbol=symbol,
                        current_price=float(price_info.get('current_price', 0)),
                        bid=self._safe_float(price_info.get('bid')),
                        ask=self._safe_float(price_info.get('ask')),
                        volume=self._safe_int(price_info.get('volume')),
                        timestamp=datetime.now()
                    )
                    
            return price_dict
            
        except Exception as e:
            logger.error(f"バッチ価格レスポンス解析エラー: {str(e)}")
            return {}
            
    def _parse_historical_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        履歴データレスポンス解析
        
        Args:
            response: APIレスポンス
            
        Returns:
            List[Dict[str, Any]]: 履歴データ
        """
        try:
            historical_list = response.get('historical_data', [])
            processed_data = []
            
            for data_point in historical_list:
                processed_data.append({
                    'date': data_point.get('date'),
                    'open': self._safe_float(data_point.get('open')),
                    'high': self._safe_float(data_point.get('high')),
                    'low': self._safe_float(data_point.get('low')),
                    'close': self._safe_float(data_point.get('close')),
                    'volume': self._safe_int(data_point.get('volume'))
                })
                
            return processed_data
            
        except Exception as e:
            logger.error(f"履歴データレスポンス解析エラー: {str(e)}")
            return []
            
    def _safe_float(self, value: Any) -> Optional[float]:
        """安全なfloat変換"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
            
    def _safe_int(self, value: Any) -> Optional[int]:
        """安全なint変換"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None
            
    def to_current_price_data(self, tachibana_price: TachibanaPrice) -> CurrentPriceData:
        """
        立花証券価格データを共通フォーマットに変換
        
        Args:
            tachibana_price: 立花証券価格データ
            
        Returns:
            CurrentPriceData: 共通価格データフォーマット
        """
        return CurrentPriceData(
            symbol=tachibana_price.symbol,
            current_price=tachibana_price.current_price,
            price_change=tachibana_price.change or 0.0,
            price_change_percent=tachibana_price.change_percent or 0.0,
            volume=tachibana_price.volume or 0,
            market_cap=None,  # 立花証券APIでは提供されない場合
            pe_ratio=None,    # 立花証券APIでは提供されない場合
            dividend_yield=None  # 立花証券APIでは提供されない場合
        )