"""
市場環境データ取得エンジン
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

from app.core.data_models import MarketContext, MarketStatus, IndexData

logger = logging.getLogger(__name__)

class MarketDataEngine:
    """市場環境データ取得エンジン"""
    
    def __init__(self):
        # 主要指数・先物・為替のティッカーシンボル
        self.symbols = {
            'indices': {
                'nikkei225': '^N225',
                'topix': '1306.T',  # TOPIX連動型上場投信
                'mothers': '2516.T',  # 東証マザーズETF 
                'sp500': '^GSPC',
                'nasdaq': '^IXIC',
                'dow': '^DJI'
            },
            'futures': {
                'nikkei225_future': '1321.T',  # 日経225連動型上場投信（代替）
                'sp500_future': 'ES=F'
            },
            'forex': {
                'usdjpy': 'USDJPY=X',
                'eurjpy': 'EURJPY=X',
                'gbpjpy': 'GBPJPY=X'
            }
        }
        
        # セクター情報（日本の主要セクター）
        self.japanese_sectors = {
            '輸送用機器': ['7203.T', '7267.T', '7201.T'],  # トヨタ、ホンダ、日産
            '電気機器': ['6758.T', '6861.T', '6723.T'],    # ソニー、キーエンス、ルネサス
            'サービス業': ['4755.T', '2432.T', '4385.T'],   # 楽天、DeNA、メルカリ
            '情報・通信業': ['9984.T', '4689.T', '3659.T'], # SBG、ヤフー、ネクソン
            '医薬品': ['4568.T', '4523.T', '4502.T'],       # 第一三共、エーザイ、武田
            'その他金融業': ['8306.T', '8316.T', '8411.T'], # 三菱UFJ、三井住友、みずほ
        }
        
        # キャッシュ
        self._cache = {}
        self._cache_expiry = {}
    
    def get_market_context(self, timestamp: datetime) -> MarketContext:
        """
        市場環境データを取得
        
        Args:
            timestamp: 取得時刻
            
        Returns:
            MarketContext: 市場環境データ
        """
        logger.info(f"市場環境データ取得開始: {timestamp}")
        
        try:
            # 指数データ取得
            indices_data = self._get_indices_data()
            
            # 先物データ取得
            futures_data = self._get_futures_data()
            
            # 為替データ取得
            forex_data = self._get_forex_data()
            
            # セクター情報取得
            sector_data = self._get_sector_data()
            
            market_context = MarketContext(
                indices=indices_data,
                futures=futures_data,
                forex=forex_data,
                sector=sector_data
            )
            
            logger.info("市場環境データ取得完了")
            return market_context
            
        except Exception as e:
            logger.error(f"市場環境データ取得エラー: {str(e)}")
            # エラー時はデフォルト値を返す
            return self._get_default_market_context()
    
    def _get_indices_data(self) -> Dict[str, IndexData]:
        """指数データを取得"""
        indices_data = {}
        
        for index_name, symbol in self.symbols['indices'].items():
            try:
                if self._is_cache_valid(f"index_{symbol}"):
                    data = self._cache[f"index_{symbol}"]
                else:
                    ticker = yf.Ticker(symbol)
                    # 過去2日分のデータを取得して変化率を計算
                    data = ticker.history(period='2d', interval='1d')
                    if not data.empty:
                        self._cache[f"index_{symbol}"] = data
                        self._cache_expiry[f"index_{symbol}"] = datetime.now() + timedelta(minutes=5)
                
                if not data.empty and len(data) >= 2:
                    current_price = float(data['Close'].iloc[-1])
                    prev_price = float(data['Close'].iloc[-2])
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100 if prev_price != 0 else 0.0
                    
                    indices_data[index_name] = IndexData(
                        price=current_price,
                        change=change,
                        change_percent=change_percent
                    )
                else:
                    logger.warning(f"指数データ取得失敗: {symbol}")
                    indices_data[index_name] = IndexData(price=0, change=0, change_percent=0)
                    
            except Exception as e:
                logger.warning(f"指数データエラー {symbol}: {str(e)}")
                indices_data[index_name] = IndexData(price=0, change=0, change_percent=0)
        
        return indices_data
    
    def _get_futures_data(self) -> Dict[str, IndexData]:
        """先物データを取得"""
        futures_data = {}
        
        for future_name, symbol in self.symbols['futures'].items():
            try:
                if self._is_cache_valid(f"future_{symbol}"):
                    data = self._cache[f"future_{symbol}"]
                else:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='2d', interval='1d')
                    if not data.empty:
                        self._cache[f"future_{symbol}"] = data
                        self._cache_expiry[f"future_{symbol}"] = datetime.now() + timedelta(minutes=5)
            
                if not data.empty and len(data) >= 2:
                    current_price = float(data['Close'].iloc[-1])
                    prev_price = float(data['Close'].iloc[-2])
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100 if prev_price != 0 else 0.0
                    
                    futures_data[future_name] = IndexData(
                        price=current_price,
                        change=change,
                        change_percent=change_percent
                    )
                else:
                    logger.warning(f"先物データ取得失敗: {symbol}")
                    futures_data[future_name] = IndexData(price=0, change=0, change_percent=0)
                    
            except Exception as e:
                logger.warning(f"先物データエラー {symbol}: {str(e)}")
                futures_data[future_name] = IndexData(price=0, change=0, change_percent=0)
        
        return futures_data
    
    def _get_forex_data(self) -> Dict[str, IndexData]:
        """為替データを取得"""
        forex_data = {}
        
        for forex_name, symbol in self.symbols['forex'].items():
            try:
                if self._is_cache_valid(f"forex_{symbol}"):
                    data = self._cache[f"forex_{symbol}"]
                else:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='2d', interval='1d')
                    if not data.empty:
                        self._cache[f"forex_{symbol}"] = data
                        self._cache_expiry[f"forex_{symbol}"] = datetime.now() + timedelta(minutes=5)
                
                if not data.empty and len(data) >= 2:
                    current_rate = float(data['Close'].iloc[-1])
                    prev_rate = float(data['Close'].iloc[-2])
                    change = current_rate - prev_rate
                    change_percent = (change / prev_rate) * 100 if prev_rate != 0 else 0.0
                    
                    forex_data[forex_name] = IndexData(
                        price=current_rate,
                        change=change,
                        change_percent=change_percent
                    )
                else:
                    logger.warning(f"為替データ取得失敗: {symbol}")
                    forex_data[forex_name] = IndexData(price=0, change=0, change_percent=0)
                    
            except Exception as e:
                logger.warning(f"為替データエラー {symbol}: {str(e)}")
                forex_data[forex_name] = IndexData(price=0, change=0, change_percent=0)
        
        return forex_data
    
    def _get_sector_data(self) -> Dict[str, any]:
        """セクター情報を取得"""
        try:
            # 簡易セクター分析（代表銘柄の平均パフォーマンス）
            sector_performance = {}
            
            for sector_name, symbols in self.japanese_sectors.items():
                performances = []
                
                for symbol in symbols:
                    try:
                        if self._is_cache_valid(f"sector_{symbol}"):
                            data = self._cache[f"sector_{symbol}"]
                        else:
                            ticker = yf.Ticker(symbol)
                            data = ticker.history(period='2d', interval='1d')
                            if not data.empty:
                                self._cache[f"sector_{symbol}"] = data
                                self._cache_expiry[f"sector_{symbol}"] = datetime.now() + timedelta(minutes=5)
                        
                        if not data.empty and len(data) >= 2:
                            current_price = float(data['Close'].iloc[-1])
                            prev_price = float(data['Close'].iloc[-2])
                            change_percent = ((current_price - prev_price) / prev_price) * 100
                            performances.append(change_percent)
                            
                    except Exception as e:
                        logger.warning(f"セクター銘柄データエラー {symbol}: {str(e)}")
                        continue
                
                if performances:
                    avg_performance = np.mean(performances)
                    sector_performance[sector_name] = avg_performance
                else:
                    sector_performance[sector_name] = 0.0
            
            # パフォーマンス順にランク付け
            sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
            
            # 最もパフォーマンスの良いセクターを返す
            if sorted_sectors:
                best_sector, best_performance = sorted_sectors[0]
                rank = 1
            else:
                best_sector, best_performance, rank = "不明", 0.0, 1
            
            return {
                'name': best_sector,
                'performance': best_performance,
                'rank': rank,
                'all_sectors': dict(sorted_sectors)
            }
            
        except Exception as e:
            logger.error(f"セクターデータ取得エラー: {str(e)}")
            return {
                'name': "不明",
                'performance': 0.0,
                'rank': 1,
                'all_sectors': {}
            }
    
    def get_market_status(self, timestamp: datetime) -> MarketStatus:
        """
        市場状態を取得
        
        Args:
            timestamp: 現在時刻
            
        Returns:
            MarketStatus: 市場状態
        """
        try:
            # 日本時間での市場セッション判定
            jst_time = timestamp
            if timestamp.tzinfo is not None:
                import pytz
                jst = pytz.timezone('Asia/Tokyo')
                jst_time = timestamp.astimezone(jst).replace(tzinfo=None)
            
            hour = jst_time.hour
            minute = jst_time.minute
            
            # 市場セッション判定
            if hour < 9:
                session = "PRE_MARKET"
                next_event = "MORNING_START"
                time_to_next = (9 - hour) * 60 - minute
            elif hour == 9 and minute < 30:
                session = "MORNING"
                next_event = "MORNING_ACTIVE"
                time_to_next = 30 - minute
            elif hour < 11 or (hour == 11 and minute < 30):
                session = "MORNING"
                next_event = "LUNCH_BREAK"
                time_to_next = (11 - hour) * 60 + (30 - minute)
            elif hour < 12 or (hour == 12 and minute < 30):
                session = "LUNCH_BREAK"
                next_event = "AFTERNOON_START"
                time_to_next = (12 - hour) * 60 + (30 - minute)
            elif hour < 15:
                session = "AFTERNOON"
                next_event = "MARKET_CLOSE"
                time_to_next = (15 - hour) * 60 - minute
            else:
                session = "AFTER_HOURS"
                next_event = "NEXT_DAY_PREMARKET"
                # 翌日9時まで
                time_to_next = (24 - hour + 9) * 60 - minute
            
            # 簡易地合い判定（日経225の変化率ベース）
            market_sentiment = self._determine_market_sentiment()
            
            return MarketStatus(
                current_time=timestamp,
                session=session,
                time_to_next_event=max(0, time_to_next * 60),  # 秒に変換
                next_event=next_event,
                market_sentiment=market_sentiment
            )
            
        except Exception as e:
            logger.error(f"市場状態判定エラー: {str(e)}")
            # デフォルト値を返す
            return MarketStatus(
                current_time=timestamp,
                session="UNKNOWN",
                time_to_next_event=0,
                next_event="UNKNOWN",
                market_sentiment={
                    'direction': 'NEUTRAL',
                    'strength': 0.5,
                    'change_time': timestamp,
                    'duration': 0
                }
            )
    
    def _determine_market_sentiment(self) -> Dict[str, any]:
        """市場地合いを判定"""
        try:
            # 日経225の変化率で簡易判定
            nikkei_data = self._get_indices_data().get('nikkei225')
            if not nikkei_data:
                return {
                    'direction': 'NEUTRAL',
                    'strength': 0.5,
                    'change_time': datetime.now(),
                    'duration': 0
                }
            
            change_percent = nikkei_data.change_percent
            
            # 地合い判定ロジック
            if change_percent > 1.0:
                direction = 'BULLISH'
                strength = min(0.9, 0.5 + abs(change_percent) / 10)
            elif change_percent < -1.0:
                direction = 'BEARISH'
                strength = min(0.9, 0.5 + abs(change_percent) / 10)
            else:
                direction = 'NEUTRAL'
                strength = 0.5
            
            return {
                'direction': direction,
                'strength': strength,
                'change_time': datetime.now(),
                'duration': 30  # 仮の継続時間（分）
            }
            
        except Exception as e:
            logger.error(f"地合い判定エラー: {str(e)}")
            return {
                'direction': 'NEUTRAL',
                'strength': 0.5,
                'change_time': datetime.now(),
                'duration': 0
            }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """キャッシュの有効性をチェック"""
        if cache_key not in self._cache:
            return False
        
        expiry_time = self._cache_expiry.get(cache_key)
        if not expiry_time or datetime.now() > expiry_time:
            # 期限切れの場合はキャッシュを削除
            if cache_key in self._cache:
                del self._cache[cache_key]
            if cache_key in self._cache_expiry:
                del self._cache_expiry[cache_key]
            return False
        
        return True
    
    def _get_default_market_context(self) -> MarketContext:
        """デフォルトの市場環境データを返す"""
        default_index = IndexData(price=0, change=0, change_percent=0)
        
        return MarketContext(
            indices={
                'nikkei225': default_index,
                'topix': default_index,
                'mothers': default_index
            },
            futures={
                'nikkei225_future': default_index
            },
            forex={
                'usdjpy': default_index
            },
            sector={
                'name': '不明',
                'performance': 0.0,
                'rank': 1
            }
        )