"""
毎分判断データ生成エンジン
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import concurrent.futures
import time

from technical_indicators import TechnicalIndicators
from market_data_engine import MarketDataEngine
from data_models import (
    MinuteDecisionPackage, CurrentPriceData, TimeframeIndicators,
    WeeklyIndicators, DailyIndicators, HourlyIndicators, MinuteIndicators,
    MovingAverageData, VWAPData, BollingerBandData, VolumeProfileData,
    MarketContext, MarketStatus,
    TIMEFRAME_CONFIG
)

logger = logging.getLogger(__name__)

class MinuteDecisionEngine:
    """毎分判断データ生成エンジン"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.tech_indicators = TechnicalIndicators()
        self.market_engine = MarketDataEngine()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # データキャッシュ
        self._data_cache = {}
        self._cache_expiry = {}
    
    def get_minute_decision_data(self, symbol: str, timestamp: datetime) -> MinuteDecisionPackage:
        """
        指定時刻における銘柄の全判断材料を取得
        
        Args:
            symbol: 銘柄コード (例: "7203.T")
            timestamp: 判断時刻
        
        Returns:
            MinuteDecisionPackage: 全判断データパッケージ
        """
        logger.info(f"判断データ生成開始: {symbol} at {timestamp}")
        
        try:
            # 各時間軸のデータを取得
            timeframe_data = self._get_all_timeframe_data(symbol, timestamp)
            
            # 現在価格データを生成
            current_price = self._generate_current_price_data(symbol, timestamp, timeframe_data)
            
            # テクニカル指標を計算
            technical_indicators = self._calculate_all_indicators(timeframe_data, timestamp)
            
            # 市場環境データを取得
            market_context = self.market_engine.get_market_context(timestamp)
            market_status = self.market_engine.get_market_status(timestamp)
            
            # データパッケージを作成
            package = MinuteDecisionPackage(
                timestamp=timestamp,
                symbol=symbol,
                current_price=current_price,
                technical_indicators=technical_indicators,
                market_context=market_context,
                market_status=market_status
            )
            
            logger.info(f"判断データ生成完了: {symbol}")
            return package
            
        except Exception as e:
            logger.error(f"判断データ生成エラー: {symbol} - {str(e)}")
            raise
    
    def get_multiple_decisions(self, symbols: List[str], timestamp: datetime, 
                             max_workers: int = 3) -> Dict[str, Optional[MinuteDecisionPackage]]:
        """
        複数銘柄の判断データを並列取得
        
        Args:
            symbols: 銘柄コードリスト
            timestamp: 判断時刻
            max_workers: 最大並列処理数
        
        Returns:
            Dict[str, MinuteDecisionPackage]: 銘柄別判断データ
        """
        logger.info(f"複数銘柄データ生成開始: {len(symbols)}銘柄")
        start_time = time.time()
        
        results = {}
        
        # 並列処理で複数銘柄を処理
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 各銘柄の処理を並列実行
            future_to_symbol = {
                executor.submit(self._safe_get_decision_data, symbol, timestamp): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results[symbol] = result
                    if result:
                        logger.info(f"処理完了: {symbol}")
                    else:
                        logger.warning(f"処理失敗: {symbol}")
                except Exception as e:
                    logger.error(f"処理エラー: {symbol} - {str(e)}")
                    results[symbol] = None
        
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results.values() if r is not None)
        
        logger.info(f"複数銘柄データ生成完了: {success_count}/{len(symbols)}銘柄 ({elapsed_time:.1f}秒)")
        
        return results
    
    def _safe_get_decision_data(self, symbol: str, timestamp: datetime) -> Optional[MinuteDecisionPackage]:
        """
        安全な判断データ取得（エラー処理付き）
        
        Args:
            symbol: 銘柄コード
            timestamp: 判断時刻
        
        Returns:
            MinuteDecisionPackage or None: 判断データ（エラー時はNone）
        """
        try:
            return self.get_minute_decision_data(symbol, timestamp)
        except Exception as e:
            logger.error(f"安全処理エラー: {symbol} - {str(e)}")
            return None
    
    def save_multiple_results(self, results: Dict[str, Optional[MinuteDecisionPackage]], 
                            output_dir: str = "output") -> List[str]:
        """
        複数銘柄の結果をファイル保存
        
        Args:
            results: 複数銘柄の判断データ
            output_dir: 出力ディレクトリ
        
        Returns:
            List[str]: 保存されたファイルパスのリスト
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for symbol, package in results.items():
            if package is None:
                logger.warning(f"データなしのためスキップ: {symbol}")
                continue
            
            try:
                filename = f"decision_data_{symbol}_{package.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                filepath = output_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(package.to_json())
                
                saved_files.append(str(filepath))
                logger.info(f"ファイル保存完了: {filepath}")
                
            except Exception as e:
                logger.error(f"ファイル保存エラー: {symbol} - {str(e)}")
        
        return saved_files
    
    def _get_all_timeframe_data(self, symbol: str, timestamp: datetime) -> Dict[str, pd.DataFrame]:
        """全時間軸のデータを取得"""
        timeframe_data = {}
        
        for timeframe, config in TIMEFRAME_CONFIG.items():
            try:
                data = self._get_timeframe_data(
                    symbol, 
                    config['interval'], 
                    config['lookback_bars'],
                    timestamp
                )
                timeframe_data[timeframe] = data
                logger.debug(f"{timeframe}データ取得完了: {len(data)}行")
                
            except Exception as e:
                logger.warning(f"{timeframe}データ取得エラー: {str(e)}")
                timeframe_data[timeframe] = pd.DataFrame()
        
        return timeframe_data
    
    def _get_timeframe_data(self, symbol: str, interval: str, lookback_bars: int, 
                           end_time: datetime) -> pd.DataFrame:
        """指定時間軸のデータを取得"""
        # キャッシュキーを生成
        cache_key = f"{symbol}_{interval}_{end_time.date()}"
        
        # キャッシュチェック
        if self._is_cache_valid(cache_key):
            data = self._data_cache[cache_key]
            # 指定時刻までのデータをフィルタ（タイムゾーン考慮）
            if data.index.tz is not None:
                # データにタイムゾーンがある場合、end_timeもタイムゾーン化
                if end_time.tzinfo is None:
                    import pytz
                    jst = pytz.timezone('Asia/Tokyo')
                    end_time = jst.localize(end_time)
                filtered_data = data[data.index <= end_time]
            else:
                # データにタイムゾーンがない場合、end_timeもnaive化
                if end_time.tzinfo is not None:
                    end_time = end_time.replace(tzinfo=None)
                filtered_data = data[data.index <= end_time]
            return filtered_data.tail(lookback_bars)
        
        try:
            # yfinanceでデータ取得
            ticker = yf.Ticker(symbol)
            
            # 期間を計算
            if interval in ['1m', '5m', '15m']:
                # 分足は過去数日分のみ取得可能
                period = '5d'
            elif interval == '60m':
                period = '1mo'
            elif interval == '1d':
                period = '2y'
            else:  # 1wk
                period = 'max'
            
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"データが空です: {symbol} {interval}")
                return pd.DataFrame()
            
            # キャッシュに保存
            self._data_cache[cache_key] = data
            self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
            
            # 指定時刻までのデータをフィルタして必要分を返す（タイムゾーン考慮）
            if data.index.tz is not None:
                # データにタイムゾーンがある場合、end_timeもタイムゾーン化
                if end_time.tzinfo is None:
                    import pytz
                    jst = pytz.timezone('Asia/Tokyo')
                    end_time = jst.localize(end_time)
                filtered_data = data[data.index <= end_time]
            else:
                # データにタイムゾーンがない場合、end_timeもnaive化
                if end_time.tzinfo is not None:
                    end_time = end_time.replace(tzinfo=None)
                filtered_data = data[data.index <= end_time]
            return filtered_data.tail(lookback_bars)
            
        except Exception as e:
            logger.error(f"データ取得エラー: {symbol} {interval} - {str(e)}")
            return pd.DataFrame()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """キャッシュの有効性をチェック"""
        if cache_key not in self._data_cache:
            return False
        
        expiry_time = self._cache_expiry.get(cache_key)
        if not expiry_time or datetime.now() > expiry_time:
            # 期限切れの場合はキャッシュを削除
            if cache_key in self._data_cache:
                del self._data_cache[cache_key]
            if cache_key in self._cache_expiry:
                del self._cache_expiry[cache_key]
            return False
        
        return True
    
    def _generate_current_price_data(self, symbol: str, timestamp: datetime, 
                                   timeframe_data: Dict[str, pd.DataFrame]) -> CurrentPriceData:
        """現在価格データを生成"""
        try:
            # 日足データから基本情報を取得
            daily_data = timeframe_data.get('daily', pd.DataFrame())
            minute_data = timeframe_data.get('minute_1', pd.DataFrame())
            
            if daily_data.empty:
                raise ValueError("日足データが取得できません")
            
            # 最新の価格情報
            if not minute_data.empty:
                latest_data = minute_data.iloc[-1]
                current_price = float(latest_data['Close'])
                current_volume = int(latest_data['Volume']) if not pd.isna(latest_data['Volume']) else 0
            else:
                latest_data = daily_data.iloc[-1]
                current_price = float(latest_data['Close'])
                current_volume = int(latest_data['Volume']) if not pd.isna(latest_data['Volume']) else 0
            
            # 当日データ
            today_data = daily_data.iloc[-1]
            prev_data = daily_data.iloc[-2] if len(daily_data) > 1 else today_data
            
            today_open = float(today_data['Open'])
            today_high = float(today_data['High'])
            today_low = float(today_data['Low'])
            prev_close = float(prev_data['Close'])
            
            # 価格変化
            price_change = current_price - prev_close
            price_change_percent = (price_change / prev_close) * 100 if prev_close != 0 else 0.0
            
            # 平均出来高（過去20日）
            if len(daily_data) >= 20:
                average_volume_20 = int(daily_data['Volume'].tail(20).mean())
            else:
                average_volume_20 = int(daily_data['Volume'].mean()) if not daily_data.empty else 0
            
            volume_ratio = current_volume / average_volume_20 if average_volume_20 > 0 else 1.0
            
            return CurrentPriceData(
                symbol=symbol,
                company_name=self._get_company_name(symbol),
                current_price=current_price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                timestamp=timestamp,
                today_open=today_open,
                today_high=today_high,
                today_low=today_low,
                prev_close=prev_close,
                current_volume=current_volume,
                average_volume_20=average_volume_20,
                volume_ratio=volume_ratio
            )
            
        except Exception as e:
            logger.error(f"現在価格データ生成エラー: {str(e)}")
            raise
    
    def _get_company_name(self, symbol: str) -> str:
        """銘柄名を取得"""
        # 簡単な銘柄名マップ（実際は外部データソースから取得）
        name_map = {
            '7203.T': 'トヨタ自動車',
            '6723.T': 'ルネサスエレクトロニクス',
            '9984.T': 'ソフトバンクグループ',
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation'
        }
        return name_map.get(symbol, symbol)
    
    def _calculate_all_indicators(self, timeframe_data: Dict[str, pd.DataFrame], 
                                timestamp: datetime) -> TimeframeIndicators:
        """全時間軸のテクニカル指標を計算"""
        
        # 週足指標
        weekly = self._calculate_weekly_indicators(timeframe_data.get('weekly', pd.DataFrame()))
        
        # 日足指標
        daily = self._calculate_daily_indicators(timeframe_data.get('daily', pd.DataFrame()))
        
        # 60分足指標
        hourly_60 = self._calculate_hourly_indicators(timeframe_data.get('hourly_60', pd.DataFrame()))
        
        # 15分足指標
        minute_15 = self._calculate_minute_indicators(
            timeframe_data.get('minute_15', pd.DataFrame()), 
            TIMEFRAME_CONFIG['minute_15']['ma_periods']
        )
        
        # 5分足指標
        minute_5 = self._calculate_minute_indicators(
            timeframe_data.get('minute_5', pd.DataFrame()), 
            TIMEFRAME_CONFIG['minute_5']['ma_periods']
        )
        
        # 1分足指標
        minute_1 = self._calculate_minute_indicators(
            timeframe_data.get('minute_1', pd.DataFrame()), 
            TIMEFRAME_CONFIG['minute_1']['ma_periods']
        )
        
        return TimeframeIndicators(
            weekly=weekly,
            daily=daily,
            hourly_60=hourly_60,
            minute_15=minute_15,
            minute_5=minute_5,
            minute_1=minute_1
        )
    
    def _calculate_weekly_indicators(self, data: pd.DataFrame) -> WeeklyIndicators:
        """週足指標を計算"""
        if data.empty:
            return WeeklyIndicators(
                moving_averages=MovingAverageData(),
                volume_profile=VolumeProfileData(poc=0, value_area_high=0, value_area_low=0)
            )
        
        # 移動平均
        ma_data = self.tech_indicators.calculate_moving_averages(data, [20, 50, 200])
        ma_values = self.tech_indicators.get_latest_values(ma_data)
        moving_averages = MovingAverageData(
            ma20=ma_values.get('ma20'),
            ma50=ma_values.get('ma50'),
            ma200=ma_values.get('ma200')
        )
        
        # 出来高プロファイル
        volume_profile_data = self.tech_indicators.calculate_volume_profile(data)
        volume_profile = VolumeProfileData(**volume_profile_data)
        
        return WeeklyIndicators(
            moving_averages=moving_averages,
            volume_profile=volume_profile
        )
    
    def _calculate_daily_indicators(self, data: pd.DataFrame) -> DailyIndicators:
        """日足指標を計算"""
        if data.empty:
            return DailyIndicators(
                moving_averages=MovingAverageData(),
                atr14=0,
                volume_profile=VolumeProfileData(poc=0, value_area_high=0, value_area_low=0)
            )
        
        # 移動平均
        ma_data = self.tech_indicators.calculate_moving_averages(data, [20, 50, 200])
        ma_values = self.tech_indicators.get_latest_values(ma_data)
        moving_averages = MovingAverageData(
            ma20=ma_values.get('ma20'),
            ma50=ma_values.get('ma50'),
            ma200=ma_values.get('ma200')
        )
        
        # ATR
        atr14 = self.tech_indicators.calculate_atr(data, 14)
        
        # 出来高プロファイル
        volume_profile_data = self.tech_indicators.calculate_volume_profile(data)
        volume_profile = VolumeProfileData(**volume_profile_data)
        
        return DailyIndicators(
            moving_averages=moving_averages,
            atr14=atr14 if not np.isnan(atr14) else 0,
            volume_profile=volume_profile
        )
    
    def _calculate_hourly_indicators(self, data: pd.DataFrame) -> HourlyIndicators:
        """60分足指標を計算"""
        if data.empty:
            return HourlyIndicators(
                moving_averages=MovingAverageData(),
                vwap=VWAPData(daily=0),
                bollinger_bands=BollingerBandData(upper=0, middle=0, lower=0)
            )
        
        # 移動平均
        ma_data = self.tech_indicators.calculate_moving_averages(data, [20, 50])
        ma_values = self.tech_indicators.get_latest_values(ma_data)
        moving_averages = MovingAverageData(
            ma20=ma_values.get('ma20'),
            ma50=ma_values.get('ma50')
        )
        
        # VWAP
        vwap_data = self.tech_indicators.calculate_vwap(data)
        vwap = VWAPData(
            daily=vwap_data['daily_vwap'],
            anchored=vwap_data['anchored_vwap']
        )
        
        # ボリンジャーバンド
        bb_data = self.tech_indicators.calculate_bollinger_bands(data, 20)
        bollinger_bands = BollingerBandData(**bb_data)
        
        return HourlyIndicators(
            moving_averages=moving_averages,
            vwap=vwap,
            bollinger_bands=bollinger_bands
        )
    
    def _calculate_minute_indicators(self, data: pd.DataFrame, ma_periods: list) -> MinuteIndicators:
        """分足指標を計算"""
        if data.empty:
            return MinuteIndicators(
                moving_averages=MovingAverageData(),
                vwap=VWAPData(daily=0)
            )
        
        # 移動平均
        ma_data = self.tech_indicators.calculate_moving_averages(data, ma_periods)
        ma_values = self.tech_indicators.get_latest_values(ma_data)
        
        # MovingAverageDataに期間に応じて設定
        moving_averages = MovingAverageData()
        for period in ma_periods:
            key = f'ma{period}'
            if key in ma_values:
                setattr(moving_averages, key, ma_values[key])
        
        # VWAP
        vwap_data = self.tech_indicators.calculate_vwap(data)
        vwap = VWAPData(daily=vwap_data['daily_vwap'])
        
        return MinuteIndicators(
            moving_averages=moving_averages,
            vwap=vwap
        )