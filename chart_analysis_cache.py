#!/usr/bin/env python3
"""
時間足別チャート分析キャッシュシステム

各時間足の更新頻度に基づいて、チャート分析結果を効率的にキャッシュ・管理する
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TimeframeAnalysis:
    """時間足別分析結果"""
    timeframe: str
    last_updated: datetime
    analysis_result: Dict[str, Any]
    next_update_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timeframe': self.timeframe,
            'last_updated': self.last_updated.isoformat(),
            'analysis_result': self.analysis_result,
            'next_update_time': self.next_update_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeframeAnalysis':
        """辞書から復元"""
        return cls(
            timeframe=data['timeframe'],
            last_updated=datetime.fromisoformat(data['last_updated']),
            analysis_result=data['analysis_result'],
            next_update_time=datetime.fromisoformat(data['next_update_time'])
        )


class ChartAnalysisCache:
    """
    時間足別チャート分析キャッシュマネージャー
    
    各時間足の更新頻度に基づいて、効率的にチャート分析結果をキャッシュする
    """
    
    def __init__(self, cache_dir: str = "chart_analysis_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 時間足別設定
        self.timeframe_config = {
            'weekly': {
                'update_interval_minutes': 7 * 24 * 60,  # 1週間
                'update_trigger': 'monday_open',  # 月曜日の市場オープン時
                'analysis_focus': [
                    'long_term_trend_direction',
                    'major_support_resistance',
                    'investor_sentiment',
                    'weekly_momentum',
                    'long_term_moving_averages'
                ]
            },
            'daily': {
                'update_interval_minutes': 24 * 60,  # 1日
                'update_trigger': 'market_open',  # 市場オープン時
                'analysis_focus': [
                    'medium_term_trend',
                    'daily_moving_averages',
                    'volume_analysis',
                    'daily_patterns',
                    'gap_analysis'
                ]
            },
            'hourly_60': {
                'update_interval_minutes': 60,  # 1時間
                'update_trigger': 'hourly',
                'analysis_focus': [
                    'short_term_trend',
                    'vwap_position',
                    'hourly_momentum',
                    'intraday_support_resistance',
                    'volume_profile'
                ]
            },
            'minute_15': {
                'update_interval_minutes': 15,
                'update_trigger': 'quarter_hourly',
                'analysis_focus': [
                    'entry_timing_signals',
                    'short_term_support_resistance',
                    'breakout_confirmation',
                    'micro_trend_changes'
                ]
            },
            'minute_5': {
                'update_interval_minutes': 5,
                'update_trigger': 'five_minute',
                'analysis_focus': [
                    'immediate_price_action',
                    'breakout_validation',
                    'quick_reversal_signals',
                    'scalping_opportunities'
                ]
            },
            'minute_1': {
                'update_interval_minutes': 1,
                'update_trigger': 'every_minute',
                'analysis_focus': [
                    'execution_timing',
                    'tick_analysis',
                    'immediate_market_response',
                    'order_flow_signals'
                ]
            }
        }
    
    def get_cache_file_path(self, symbol: str) -> Path:
        """シンボル別キャッシュファイルパス"""
        return self.cache_dir / f"{symbol}_chart_analysis.json"
    
    def load_cache(self, symbol: str) -> Dict[str, TimeframeAnalysis]:
        """キャッシュファイルを読み込み"""
        cache_file = self.get_cache_file_path(symbol)
        
        if not cache_file.exists():
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cache = {}
            for timeframe, analysis_data in data.items():
                cache[timeframe] = TimeframeAnalysis.from_dict(analysis_data)
            
            return cache
            
        except Exception as e:
            logger.warning(f"キャッシュ読み込み失敗: {e}")
            return {}
    
    def save_cache(self, symbol: str, cache: Dict[str, TimeframeAnalysis]) -> None:
        """キャッシュファイルに保存"""
        cache_file = self.get_cache_file_path(symbol)
        
        try:
            data = {}
            for timeframe, analysis in cache.items():
                data[timeframe] = analysis.to_dict()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"キャッシュ保存失敗: {e}")
    
    def calculate_next_update_time(self, timeframe: str, current_time: datetime) -> datetime:
        """次回更新時刻を計算"""
        config = self.timeframe_config[timeframe]
        interval_minutes = config['update_interval_minutes']
        
        if timeframe == 'weekly':
            # 月曜日の市場オープン（9:00）を計算
            days_until_monday = (7 - current_time.weekday()) % 7
            if days_until_monday == 0 and current_time.hour < 9:
                # 今日が月曜日で9時前の場合は今日の9時
                next_update = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # 次の月曜日の9時
                next_update = current_time + timedelta(days=days_until_monday)
                next_update = next_update.replace(hour=9, minute=0, second=0, microsecond=0)
        
        elif timeframe == 'daily':
            # 翌日の市場オープン（9:00）
            if current_time.hour < 9:
                # 今日の9時前の場合は今日の9時
                next_update = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # 翌日の9時
                next_update = current_time + timedelta(days=1)
                next_update = next_update.replace(hour=9, minute=0, second=0, microsecond=0)
        
        else:
            # 分足の場合は次の境界時刻を直接計算
            if timeframe == 'hourly_60':
                # 次の時間の境界（00分）
                next_hour = current_time.hour + 1
                if next_hour >= 24:
                    next_update = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    next_update = current_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
                    
            elif timeframe == 'minute_15':
                # 次の15分境界（0, 15, 30, 45分）
                current_minute = current_time.minute
                next_15_minute = ((current_minute // 15) + 1) * 15
                
                if next_15_minute >= 60:
                    next_hour = current_time.hour + 1
                    if next_hour >= 24:
                        next_update = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        next_update = current_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
                else:
                    next_update = current_time.replace(minute=next_15_minute, second=0, microsecond=0)
                    
            elif timeframe == 'minute_5':
                # 次の5分境界（0, 5, 10, 15, 20...分）
                current_minute = current_time.minute
                next_5_minute = ((current_minute // 5) + 1) * 5
                
                if next_5_minute >= 60:
                    next_hour = current_time.hour + 1
                    if next_hour >= 24:
                        next_update = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        next_update = current_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
                else:
                    next_update = current_time.replace(minute=next_5_minute, second=0, microsecond=0)
                    
            elif timeframe == 'minute_1':
                # 次の1分境界
                next_minute = current_time.minute + 1
                if next_minute >= 60:
                    next_hour = current_time.hour + 1
                    if next_hour >= 24:
                        next_update = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        next_update = current_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
                else:
                    next_update = current_time.replace(minute=next_minute, second=0, microsecond=0)
        
        return next_update
    
    def needs_update(self, timeframe: str, current_time: datetime, cached_analysis: Optional[TimeframeAnalysis]) -> bool:
        """更新が必要かどうかを判定"""
        if cached_analysis is None:
            return True
        
        # 次回更新時刻を過ぎているかチェック
        return current_time >= cached_analysis.next_update_time
    
    def get_timeframes_to_update(self, symbol: str, current_time: datetime) -> Tuple[Dict[str, TimeframeAnalysis], list]:
        """
        更新が必要な時間足と既存のキャッシュを取得
        
        Returns:
            Tuple[cached_analysis, timeframes_to_update]
        """
        cached_analysis = self.load_cache(symbol)
        timeframes_to_update = []
        
        for timeframe in self.timeframe_config.keys():
            cached = cached_analysis.get(timeframe)
            
            if self.needs_update(timeframe, current_time, cached):
                timeframes_to_update.append(timeframe)
                logger.info(f"📈 {timeframe} チャート分析の更新が必要")
            else:
                logger.info(f"♻️ {timeframe} チャート分析をキャッシュから使用 (次回更新: {cached.next_update_time})")
        
        return cached_analysis, timeframes_to_update
    
    def update_analysis(self, symbol: str, timeframe: str, analysis_result: Dict[str, Any], current_time: datetime) -> None:
        """分析結果をキャッシュに更新"""
        cached_analysis = self.load_cache(symbol)
        
        next_update_time = self.calculate_next_update_time(timeframe, current_time)
        
        cached_analysis[timeframe] = TimeframeAnalysis(
            timeframe=timeframe,
            last_updated=current_time,
            analysis_result=analysis_result,
            next_update_time=next_update_time
        )
        
        self.save_cache(symbol, cached_analysis)
        logger.info(f"✅ {timeframe} チャート分析結果をキャッシュに保存 (次回更新: {next_update_time})")
    
    def get_analysis_focus(self, timeframe: str) -> list:
        """時間足別の分析フォーカス項目を取得"""
        return self.timeframe_config[timeframe]['analysis_focus']
    
    def get_all_cached_analysis(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """全時間足の分析結果を統合して取得"""
        cached_analysis = self.load_cache(symbol)
        
        result = {}
        for timeframe, analysis in cached_analysis.items():
            result[timeframe] = analysis.analysis_result
        
        return result
    
    def clear_cache(self, symbol: str) -> None:
        """指定銘柄のキャッシュをクリア"""
        cache_file = self.get_cache_file_path(symbol)
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"🗑️ {symbol} のチャート分析キャッシュをクリア")
    
    def get_cache_status(self, symbol: str, current_time: datetime) -> Dict[str, Dict[str, Any]]:
        """キャッシュの状態を取得"""
        cached_analysis = self.load_cache(symbol)
        
        status = {}
        for timeframe in self.timeframe_config.keys():
            cached = cached_analysis.get(timeframe)
            
            if cached:
                needs_update = self.needs_update(timeframe, current_time, cached)
                time_until_update = cached.next_update_time - current_time
                
                status[timeframe] = {
                    'has_cache': True,
                    'last_updated': cached.last_updated.isoformat(),
                    'next_update': cached.next_update_time.isoformat(),
                    'needs_update': needs_update,
                    'time_until_update_minutes': time_until_update.total_seconds() / 60,
                    'analysis_items': len(cached.analysis_result)
                }
            else:
                status[timeframe] = {
                    'has_cache': False,
                    'needs_update': True
                }
        
        return status