"""
データ構造定義モジュール
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional
import json

@dataclass
class CurrentPriceData:
    """現在価格情報"""
    symbol: str
    company_name: str
    current_price: float
    price_change: float
    price_change_percent: float
    timestamp: datetime
    
    # 当日統計
    today_open: float
    today_high: float
    today_low: float
    prev_close: float
    
    # 出来高情報
    current_volume: int
    average_volume_20: int
    volume_ratio: float

@dataclass
class MovingAverageData:
    """移動平均データ"""
    ma5: Optional[float] = None
    ma9: Optional[float] = None
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    ma200: Optional[float] = None

@dataclass
class VWAPData:
    """VWAPデータ"""
    daily: float
    anchored: Optional[float] = None

@dataclass
class BollingerBandData:
    """ボリンジャーバンドデータ"""
    upper: float
    middle: float
    lower: float

@dataclass
class VolumeProfileData:
    """出来高プロファイルデータ"""
    poc: float  # Point of Control
    value_area_high: float
    value_area_low: float

@dataclass
class WeeklyIndicators:
    """週足指標"""
    moving_averages: MovingAverageData
    volume_profile: VolumeProfileData

@dataclass
class DailyIndicators:
    """日足指標"""
    moving_averages: MovingAverageData
    atr14: float
    volume_profile: VolumeProfileData

@dataclass
class HourlyIndicators:
    """60分足指標"""
    moving_averages: MovingAverageData
    vwap: VWAPData
    bollinger_bands: BollingerBandData

@dataclass
class MinuteIndicators:
    """分足指標（15分、5分、1分共通）"""
    moving_averages: MovingAverageData
    vwap: VWAPData

@dataclass
class TimeframeIndicators:
    """全時間軸のテクニカル指標"""
    weekly: WeeklyIndicators
    daily: DailyIndicators
    hourly_60: HourlyIndicators
    minute_15: MinuteIndicators
    minute_5: MinuteIndicators
    minute_1: MinuteIndicators

@dataclass
class IndexData:
    """指数データ"""
    price: float
    change: float
    change_percent: float

@dataclass
class MarketContext:
    """市場環境データ"""
    indices: Dict[str, IndexData]
    futures: Dict[str, IndexData]
    forex: Dict[str, IndexData]
    sector: Dict[str, any]

@dataclass
class MarketStatus:
    """市場状態"""
    current_time: datetime
    session: str  # PRE_MARKET | MORNING | LUNCH_BREAK | AFTERNOON | AFTER_HOURS
    time_to_next_event: int
    next_event: str

@dataclass
class MinuteDecisionPackage:
    """毎分判断用データパッケージ"""
    timestamp: datetime
    symbol: str
    current_price: CurrentPriceData
    technical_indicators: TimeframeIndicators
    market_context: Optional[MarketContext] = None
    market_status: Optional[MarketStatus] = None
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        data_dict = self.to_dict()
        return json.dumps(data_dict, indent=indent, default=datetime_serializer, ensure_ascii=False)

# 時間軸設定
TIMEFRAME_CONFIG = {
    'weekly': {
        'interval': '1wk',
        'lookback_bars': 200,
        'ma_periods': [20, 50, 200],
        'indicators': ['ma', 'volume_profile']
    },
    'daily': {
        'interval': '1d',
        'lookback_bars': 260,
        'ma_periods': [20, 50, 200],
        'indicators': ['ma', 'atr', 'volume_profile']
    },
    'hourly_60': {
        'interval': '60m',
        'lookback_bars': 120,
        'ma_periods': [20, 50],
        'indicators': ['ma', 'vwap', 'bollinger_bands']
    },
    'minute_15': {
        'interval': '15m',
        'lookback_bars': 90,
        'ma_periods': [9, 20],
        'indicators': ['ma', 'vwap']
    },
    'minute_5': {
        'interval': '5m',
        'lookback_bars': 60,
        'ma_periods': [5, 21],  # または [8, 21]
        'indicators': ['ma', 'vwap']
    },
    'minute_1': {
        'interval': '1m',
        'lookback_bars': 45,
        'ma_periods': [5, 9],
        'indicators': ['ma', 'vwap']
    }
}