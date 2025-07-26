"""
テクニカル指標計算モジュール
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """テクニカル指標計算クラス"""
    
    def __init__(self):
        pass
    
    def calculate_moving_averages(self, data: pd.DataFrame, periods: list) -> Dict[str, pd.Series]:
        """
        移動平均線を計算
        
        Args:
            data: OHLCV DataFrame
            periods: 計算期間のリスト [5, 9, 20, 50, 200]
        
        Returns:
            Dict[str, pd.Series]: MA辞書 {'ma5': Series, 'ma9': Series, ...}
        """
        result = {}
        
        for period in periods:
            if len(data) >= period:
                result[f'ma{period}'] = data['Close'].rolling(window=period).mean()
            else:
                logger.warning(f"データ不足でMA{period}を計算できません: データ数={len(data)}")
                result[f'ma{period}'] = pd.Series(index=data.index, dtype=float)
        
        return result
    
    def calculate_vwap(self, data: pd.DataFrame, anchor_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        VWAP(Volume Weighted Average Price)を計算
        
        Args:
            data: OHLCV DataFrame
            anchor_time: アンカー時刻（指定時点からのVWAP）
        
        Returns:
            Dict[str, float]: {'daily_vwap': float, 'anchored_vwap': float}
        """
        if data.empty:
            return {'daily_vwap': np.nan, 'anchored_vwap': np.nan}
        
        # 日次VWAP（当日分のみ）
        daily_vwap = self._calculate_daily_vwap(data)
        
        # アンカーVWAP
        anchored_vwap = daily_vwap  # デフォルトは日次と同じ
        if anchor_time:
            anchored_vwap = self._calculate_anchored_vwap(data, anchor_time)
        
        return {
            'daily_vwap': daily_vwap,
            'anchored_vwap': anchored_vwap
        }
    
    def _calculate_daily_vwap(self, data: pd.DataFrame) -> float:
        """日次VWAPを計算"""
        try:
            # 典型価格 = (High + Low + Close) / 3
            typical_price = (data['High'] + data['Low'] + data['Close']) / 3
            
            # VWAP = Σ(典型価格 × 出来高) / Σ出来高
            vwap = (typical_price * data['Volume']).sum() / data['Volume'].sum()
            
            return float(vwap) if not np.isnan(vwap) else 0.0
        except Exception as e:
            logger.error(f"日次VWAP計算エラー: {e}")
            return 0.0
    
    def _calculate_anchored_vwap(self, data: pd.DataFrame, anchor_time: datetime) -> float:
        """アンカーVWAPを計算"""
        try:
            # アンカー時刻以降のデータを抽出
            anchor_data = data[data.index >= anchor_time]
            if anchor_data.empty:
                return self._calculate_daily_vwap(data)
            
            return self._calculate_daily_vwap(anchor_data)
        except Exception as e:
            logger.error(f"アンカーVWAP計算エラー: {e}")
            return self._calculate_daily_vwap(data)
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """
        ボリンジャーバンドを計算
        
        Args:
            data: OHLCV DataFrame
            period: SMA期間（デフォルト20）
            std_dev: 標準偏差倍数（デフォルト2.0）
        
        Returns:
            Dict[str, float]: {'upper': float, 'middle': float, 'lower': float}
        """
        if len(data) < period:
            return {'upper': np.nan, 'middle': np.nan, 'lower': np.nan}
        
        try:
            # 中心線（SMA）
            middle = data['Close'].rolling(window=period).mean().iloc[-1]
            
            # 標準偏差
            std = data['Close'].rolling(window=period).std().iloc[-1]
            
            # 上下バンド
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            
            return {
                'upper': float(upper) if not np.isnan(upper) else 0.0,
                'middle': float(middle) if not np.isnan(middle) else 0.0,
                'lower': float(lower) if not np.isnan(lower) else 0.0
            }
        except Exception as e:
            logger.error(f"ボリンジャーバンド計算エラー: {e}")
            return {'upper': np.nan, 'middle': np.nan, 'lower': np.nan}
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """
        ATR(Average True Range)を計算
        
        Args:
            data: OHLCV DataFrame
            period: 計算期間（デフォルト14）
        
        Returns:
            float: ATR値
        """
        if len(data) < period + 1:
            return np.nan
        
        try:
            # 真の値幅を計算
            high_low = data['High'] - data['Low']
            high_close_prev = abs(data['High'] - data['Close'].shift(1))
            low_close_prev = abs(data['Low'] - data['Close'].shift(1))
            
            true_range = pd.DataFrame({
                'hl': high_low,
                'hc': high_close_prev,
                'lc': low_close_prev
            }).max(axis=1)
            
            # ATRを計算（真の値幅の移動平均）
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return float(atr) if not np.isnan(atr) else 0.0
        except Exception as e:
            logger.error(f"ATR計算エラー: {e}")
            return np.nan
    
    def calculate_volume_profile(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        出来高プロファイルを計算
        
        Args:
            data: OHLCV DataFrame
        
        Returns:
            Dict[str, float]: {'poc': float, 'value_area_high': float, 'value_area_low': float}
        """
        if data.empty:
            return {'poc': np.nan, 'value_area_high': np.nan, 'value_area_low': np.nan}
        
        try:
            # 価格レンジを50区間に分割
            price_min = data['Low'].min()
            price_max = data['High'].max()
            price_bins = np.linspace(price_min, price_max, 51)
            
            # 各価格帯の出来高を集計
            volume_at_price = {}
            
            for i in range(len(data)):
                row = data.iloc[i]
                # 各ローソク足の価格範囲内で出来高を分散
                price_range = np.linspace(row['Low'], row['High'], 10)
                volume_per_price = row['Volume'] / len(price_range)
                
                for price in price_range:
                    # 価格を区間に割り当て
                    bin_idx = np.digitize(price, price_bins) - 1
                    bin_idx = max(0, min(bin_idx, len(price_bins) - 2))
                    
                    bin_key = (price_bins[bin_idx] + price_bins[bin_idx + 1]) / 2
                    volume_at_price[bin_key] = volume_at_price.get(bin_key, 0) + volume_per_price
            
            if not volume_at_price:
                return {'poc': np.nan, 'value_area_high': np.nan, 'value_area_low': np.nan}
            
            # POC（最大出来高価格）
            poc = max(volume_at_price.items(), key=lambda x: x[1])[0]
            
            # Value Area（出来高の68%を含む価格範囲）
            total_volume = sum(volume_at_price.values())
            target_volume = total_volume * 0.68
            
            # POC周辺から拡張
            sorted_prices = sorted(volume_at_price.keys())
            poc_idx = sorted_prices.index(min(sorted_prices, key=lambda x: abs(x - poc)))
            
            accumulated_volume = volume_at_price[poc]
            va_low_idx = va_high_idx = poc_idx
            
            while accumulated_volume < target_volume and (va_low_idx > 0 or va_high_idx < len(sorted_prices) - 1):
                # 上下のうち出来高の多い方を選択
                low_volume = volume_at_price.get(sorted_prices[va_low_idx - 1], 0) if va_low_idx > 0 else 0
                high_volume = volume_at_price.get(sorted_prices[va_high_idx + 1], 0) if va_high_idx < len(sorted_prices) - 1 else 0
                
                if low_volume >= high_volume and va_low_idx > 0:
                    va_low_idx -= 1
                    accumulated_volume += low_volume
                elif va_high_idx < len(sorted_prices) - 1:
                    va_high_idx += 1
                    accumulated_volume += high_volume
                else:
                    break
            
            value_area_low = sorted_prices[va_low_idx]
            value_area_high = sorted_prices[va_high_idx]
            
            return {
                'poc': float(poc),
                'value_area_high': float(value_area_high),
                'value_area_low': float(value_area_low)
            }
            
        except Exception as e:
            logger.error(f"出来高プロファイル計算エラー: {e}")
            return {'poc': np.nan, 'value_area_high': np.nan, 'value_area_low': np.nan}
    
    def get_latest_values(self, ma_dict: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        移動平均の最新値を取得
        
        Args:
            ma_dict: calculate_moving_averagesの戻り値
        
        Returns:
            Dict[str, float]: 最新値辞書
        """
        result = {}
        for key, series in ma_dict.items():
            if not series.empty and not pd.isna(series.iloc[-1]):
                result[key] = float(series.iloc[-1])
            else:
                result[key] = np.nan
        
        return result