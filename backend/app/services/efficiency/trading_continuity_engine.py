#!/usr/bin/env python3
"""
トレーディング判断継続性エンジン

前回の分析結果と将来エントリー条件を活用して、効率的な判断システムを構築する
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from app.services.efficiency.chart_analysis_cache import ChartAnalysisCache
from app.services.efficiency.timeframe_chart_analyzer import TimeframeChartAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class TradingState:
    """トレーディング状態管理"""
    symbol: str
    last_decision: str  # BUY, SELL, HOLD
    last_decision_time: datetime
    confidence_level: float
    active_conditions: Dict[str, Any]  # 将来エントリー条件
    monitoring_frequency: str  # 監視頻度
    next_review_time: datetime
    decision_rationale: List[str]  # 判断根拠
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'last_decision': self.last_decision,
            'last_decision_time': self.last_decision_time.isoformat(),
            'confidence_level': self.confidence_level,
            'active_conditions': self.active_conditions,
            'monitoring_frequency': self.monitoring_frequency,
            'next_review_time': self.next_review_time.isoformat(),
            'decision_rationale': self.decision_rationale
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingState':
        return cls(
            symbol=data['symbol'],
            last_decision=data['last_decision'],
            last_decision_time=datetime.fromisoformat(data['last_decision_time']),
            confidence_level=data['confidence_level'],
            active_conditions=data['active_conditions'],
            monitoring_frequency=data['monitoring_frequency'],
            next_review_time=datetime.fromisoformat(data['next_review_time']),
            decision_rationale=data['decision_rationale']
        )


class TradingContinuityEngine:
    """
    トレーディング判断継続性エンジン
    
    前回の判断結果と将来条件を活用して、効率的な継続判断を行う
    """
    
    def __init__(self, state_dir: str = "trading_states"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.chart_cache = ChartAnalysisCache()
        self.timeframe_analyzer = TimeframeChartAnalyzer()
    
    def get_state_file_path(self, symbol: str) -> Path:
        """銘柄別状態ファイルパス"""
        return self.state_dir / f"{symbol}_trading_state.json"
    
    def load_trading_state(self, symbol: str) -> Optional[TradingState]:
        """トレーディング状態を読み込み"""
        state_file = self.get_state_file_path(symbol)
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TradingState.from_dict(data)
        except Exception as e:
            logger.warning(f"状態読み込み失敗: {e}")
            return None
    
    def save_trading_state(self, trading_state: TradingState) -> None:
        """トレーディング状態を保存"""
        state_file = self.get_state_file_path(trading_state.symbol)
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(trading_state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"状態保存失敗: {e}")
    
    def should_perform_full_analysis(self, symbol: str, current_time: datetime) -> bool:
        """フル分析が必要かどうかを判定"""
        trading_state = self.load_trading_state(symbol)
        
        if trading_state is None:
            logger.info("📋 初回分析のため、フル分析を実行")
            return True
        
        # 次回レビュー時刻をチェック
        if current_time >= trading_state.next_review_time:
            logger.info(f"⏰ レビュー時刻到達のため、フル分析を実行 ({trading_state.next_review_time})")
            return True
        
        # 条件チェックが必要かどうか
        if self._should_check_entry_conditions(trading_state, current_time):
            logger.info("🎯 エントリー条件チェックのため、分析を実行")
            return True
        
        logger.info(f"♻️ 前回の判断を継続 (次回レビュー: {trading_state.next_review_time})")
        return False
    
    def _should_check_entry_conditions(self, trading_state: TradingState, current_time: datetime) -> bool:
        """エントリー条件チェックが必要かどうか"""
        if trading_state.last_decision != "HOLD":
            return False  # HOLDでない場合は条件チェック不要
        
        # 高頻度監視が設定されている場合
        if trading_state.monitoring_frequency in ["5-15分足で継続監視", "15分足", "5分足"]:
            # 最後の判断から15分以上経過している場合
            if current_time - trading_state.last_decision_time > timedelta(minutes=15):
                return True
        
        return False
    
    def get_incremental_analysis_plan(self, symbol: str, current_time: datetime) -> Dict[str, Any]:
        """
        増分分析プランを作成
        
        Returns:
            {
                "analysis_type": "full" | "incremental" | "condition_check",
                "timeframes_to_update": [更新が必要な時間足],
                "cached_analysis": {既存の分析結果},
                "trading_state": TradingState,
                "focus_areas": [重点分析項目]
            }
        """
        trading_state = self.load_trading_state(symbol)
        
        # チャート分析キャッシュの状態確認
        cached_analysis, timeframes_to_update = self.chart_cache.get_timeframes_to_update(symbol, current_time)
        
        if trading_state is None:
            # 初回分析
            return {
                "analysis_type": "full",
                "timeframes_to_update": list(self.chart_cache.timeframe_config.keys()),
                "cached_analysis": {},
                "trading_state": None,
                "focus_areas": ["complete_market_analysis"]
            }
        
        elif len(timeframes_to_update) > 3:
            # 多くの時間足で更新が必要な場合はフル分析
            return {
                "analysis_type": "full",
                "timeframes_to_update": timeframes_to_update,
                "cached_analysis": cached_analysis,
                "trading_state": trading_state,
                "focus_areas": ["trend_change_detection", "new_signal_identification"]
            }
        
        elif len(timeframes_to_update) > 0:
            # 部分的な更新が必要
            return {
                "analysis_type": "incremental",
                "timeframes_to_update": timeframes_to_update,
                "cached_analysis": cached_analysis,
                "trading_state": trading_state,
                "focus_areas": self._get_incremental_focus_areas(timeframes_to_update, trading_state)
            }
        
        else:
            # エントリー条件チェックのみ
            return {
                "analysis_type": "condition_check",
                "timeframes_to_update": [],
                "cached_analysis": cached_analysis,
                "trading_state": trading_state,
                "focus_areas": ["entry_condition_validation"]
            }
    
    def _get_incremental_focus_areas(self, timeframes_to_update: List[str], trading_state: TradingState) -> List[str]:
        """増分分析の重点項目を決定"""
        focus_areas = []
        
        # 更新される時間足に基づいて重点項目を設定
        if "weekly" in timeframes_to_update:
            focus_areas.append("long_term_trend_shift")
        if "daily" in timeframes_to_update:
            focus_areas.append("medium_term_signal_update")
        if any(tf in timeframes_to_update for tf in ["hourly_60", "minute_15"]):
            focus_areas.append("short_term_timing_refinement")
        if any(tf in timeframes_to_update for tf in ["minute_5", "minute_1"]):
            focus_areas.append("execution_timing_adjustment")
        
        # 前回の判断に基づく重点項目
        if trading_state.last_decision == "HOLD":
            focus_areas.append("breakout_signal_detection")
        else:
            focus_areas.append("position_management_update")
        
        return focus_areas
    
    def execute_incremental_analysis(self, analysis_plan: Dict[str, Any], 
                                   current_price: float, 
                                   market_context: Dict[str, Any]) -> Dict[str, Any]:
        """増分分析を実行"""
        analysis_type = analysis_plan["analysis_type"]
        timeframes_to_update = analysis_plan["timeframes_to_update"]
        cached_analysis = analysis_plan["cached_analysis"]
        trading_state = analysis_plan["trading_state"]
        
        if analysis_type == "condition_check":
            return self._execute_condition_check(trading_state, current_price, market_context)
        
        elif analysis_type == "incremental":
            return self._execute_incremental_update(
                timeframes_to_update, cached_analysis, trading_state, current_price, market_context
            )
        
        else:  # full analysis
            return self._execute_full_analysis(
                timeframes_to_update, trading_state, current_price, market_context
            )
    
    def _execute_condition_check(self, trading_state: TradingState, 
                                current_price: float, 
                                market_context: Dict[str, Any]) -> Dict[str, Any]:
        """エントリー条件チェックのみを実行"""
        logger.info("🎯 エントリー条件チェック実行中...")
        
        conditions = trading_state.active_conditions
        buy_conditions = conditions.get("buy_conditions", [])
        sell_conditions = conditions.get("sell_conditions", [])
        
        # 簡易的な条件チェック
        decision_changes = []
        
        # 価格ベースの条件チェック例
        for condition in buy_conditions:
            if "上抜け" in condition and self._check_breakout_condition(condition, current_price):
                decision_changes.append(f"BUY条件達成: {condition}")
        
        for condition in sell_conditions:
            if "下抜け" in condition and self._check_breakdown_condition(condition, current_price):
                decision_changes.append(f"SELL条件達成: {condition}")
        
        if decision_changes:
            # 条件達成時はフル分析に切り替え
            logger.info(f"🚨 エントリー条件達成を検知: {decision_changes}")
            return {
                "requires_full_analysis": True,
                "trigger_reason": "entry_condition_met",
                "detected_changes": decision_changes
            }
        else:
            # 条件未達成、前回判断を継続
            logger.info("✅ エントリー条件未達成、前回判断を継続")
            return {
                "requires_full_analysis": False,
                "decision_continuation": {
                    "trading_decision": trading_state.last_decision,
                    "confidence_level": trading_state.confidence_level,
                    "reasoning": ["前回分析結果を継続", "エントリー条件未達成"],
                    "future_entry_conditions": trading_state.active_conditions
                }
            }
    
    def _check_breakout_condition(self, condition: str, current_price: float) -> bool:
        """ブレイクアウト条件チェック（簡易版）"""
        # 実際の実装では、条件文字列を解析して価格レベルを抽出
        # ここでは簡易的な実装
        return False  # 実装時に詳細化
    
    def _check_breakdown_condition(self, condition: str, current_price: float) -> bool:
        """ブレイクダウン条件チェック（簡易版）"""
        # 実際の実装では、条件文字列を解析して価格レベルを抽出
        return False  # 実装時に詳細化
    
    def _execute_incremental_update(self, timeframes_to_update: List[str], 
                                   cached_analysis: Dict[str, Any], 
                                   trading_state: TradingState,
                                   current_price: float, 
                                   market_context: Dict[str, Any]) -> Dict[str, Any]:
        """増分更新分析を実行"""
        logger.info(f"📊 増分分析実行中... (更新対象: {timeframes_to_update})")
        
        # 必要な時間足のみ更新
        updated_analysis = cached_analysis.copy()
        
        for timeframe in timeframes_to_update:
            # 時間足別分析を実行（実際のチャート画像は省略し、テクニカル指標のみ使用）
            analysis_result = self._analyze_timeframe_from_indicators(
                timeframe, market_context
            )
            updated_analysis[timeframe] = analysis_result
            
            # キャッシュに保存
            self.chart_cache.update_analysis(
                trading_state.symbol, timeframe, analysis_result, datetime.now()
            )
        
        # 部分的な判断更新
        partial_decision = self._make_partial_decision(
            updated_analysis, trading_state, current_price, market_context
        )
        
        return {
            "requires_full_analysis": False,
            "partial_update": partial_decision,
            "updated_timeframes": timeframes_to_update
        }
    
    def _execute_full_analysis(self, timeframes_to_update: List[str], 
                              trading_state: Optional[TradingState],
                              current_price: float, 
                              market_context: Dict[str, Any]) -> Dict[str, Any]:
        """フル分析を実行"""
        logger.info("🔍 フル分析実行中...")
        
        return {
            "requires_full_analysis": True,
            "analysis_type": "complete",
            "context": {
                "previous_state": trading_state.to_dict() if trading_state else None,
                "updated_timeframes": timeframes_to_update
            }
        }
    
    def _analyze_timeframe_from_indicators(self, timeframe: str, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """テクニカル指標のみから時間足分析を実行"""
        # チャート画像なしでの簡易分析
        # 実際の実装では、テクニカル指標データを基に分析を行う
        return {
            "timeframe": timeframe,
            "analysis_method": "indicators_only",
            "timestamp": datetime.now().isoformat(),
            "summary": f"{timeframe} indicators-based analysis",
            "confidence_score": 0.6
        }
    
    def _make_partial_decision(self, analysis: Dict[str, Any], 
                              trading_state: TradingState,
                              current_price: float, 
                              market_context: Dict[str, Any]) -> Dict[str, Any]:
        """部分的な判断を実行"""
        # 前回の判断を基準に、更新された分析結果を考慮して調整
        adjusted_confidence = trading_state.confidence_level
        
        # 新しい分析結果に基づく信頼度調整
        for timeframe, tf_analysis in analysis.items():
            tf_confidence = tf_analysis.get("confidence_score", 0.5)
            # 重み付き平均で信頼度を調整
            adjusted_confidence = (adjusted_confidence * 0.7) + (tf_confidence * 0.3)
        
        return {
            "trading_decision": trading_state.last_decision,
            "confidence_level": adjusted_confidence,
            "reasoning": [
                "前回分析結果を基準に部分更新",
                f"信頼度調整: {trading_state.confidence_level:.2f} → {adjusted_confidence:.2f}"
            ],
            "analysis_efficiency": "partial_update"
        }
    
    def update_trading_state(self, symbol: str, decision_result: Dict[str, Any], current_time: datetime) -> None:
        """トレーディング状態を更新"""
        # 次回レビュー時刻を計算
        monitoring_freq = decision_result.get("market_outlook", {}).get("monitoring_frequency", "日足で十分")
        next_review = self._calculate_next_review_time(monitoring_freq, current_time)
        
        trading_state = TradingState(
            symbol=symbol,
            last_decision=decision_result.get("trading_decision", "HOLD"),
            last_decision_time=current_time,
            confidence_level=decision_result.get("confidence_level", 0.5),
            active_conditions=decision_result.get("future_entry_conditions", {}),
            monitoring_frequency=monitoring_freq,
            next_review_time=next_review,
            decision_rationale=decision_result.get("reasoning", [])
        )
        
        self.save_trading_state(trading_state)
        logger.info(f"💾 トレーディング状態更新完了 (次回レビュー: {next_review})")
    
    def _calculate_next_review_time(self, monitoring_frequency: str, current_time: datetime) -> datetime:
        """次回レビュー時刻を計算"""
        if "5-15分足" in monitoring_frequency:
            return current_time + timedelta(minutes=15)
        elif "60分足" in monitoring_frequency:
            return current_time + timedelta(hours=1)
        elif "日足" in monitoring_frequency:
            return current_time + timedelta(days=1)
        else:
            return current_time + timedelta(hours=4)  # デフォルト4時間後