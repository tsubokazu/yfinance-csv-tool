#!/usr/bin/env python3
"""
トレーディングエージェント用ツール定義

各専門エージェントが使用するツール群を定義します。
- チャート分析ツール
- テクニカル指標分析ツール  
- 売買判断ツール
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import base64

from langchain_core.tools import tool
from app.core.data_models import MinuteDecisionPackage, CurrentPriceData, TimeframeIndicators

logger = logging.getLogger(__name__)


@tool
def analyze_chart_image(chart_image_path: str, timeframe: str) -> Dict[str, Any]:
    """
    チャート画像を分析してパターンとトレンドを特定
    
    Args:
        chart_image_path: チャート画像のファイルパス
        timeframe: 時間軸 (weekly, daily, hourly_60, minute_15, minute_5, minute_1)
        
    Returns:
        チャート分析結果
    """
    try:
        image_path = Path(chart_image_path)
        
        if not image_path.exists():
            return {
                "error": f"チャート画像が見つかりません: {chart_image_path}",
                "timeframe": timeframe,
                "patterns": [],
                "trend_direction": "unknown",
                "confidence_score": 0.0
            }
        
        # チャート画像の存在確認とメタデータ取得
        image_size = image_path.stat().st_size
        
        # 実際の画像分析はLLMに委ねるため、ここではメタデータのみ返す
        # LangGraphのエージェント内でClaude Visionが画像を直接分析
        
        analysis_result = {
            "timeframe": timeframe,
            "image_path": str(image_path),
            "image_size_bytes": image_size,
            "analysis_timestamp": datetime.now().isoformat(),
            
            # 基本的な分析フレームワーク（LLMが埋める）
            "chart_patterns": [],
            "support_levels": [],
            "resistance_levels": [],
            "trend_direction": "unknown",  # bullish/bearish/sideways
            "volume_pattern": "unknown",   # increasing/decreasing/stable
            "confidence_score": 0.0,
            
            # 時間軸別の重点分析項目
            "analysis_focus": _get_analysis_focus_for_timeframe(timeframe)
        }
        
        logger.info(f"チャート画像分析準備完了: {timeframe} - {image_path}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"チャート画像分析エラー: {e}")
        return {
            "error": str(e),
            "timeframe": timeframe,
            "patterns": [],
            "trend_direction": "unknown",
            "confidence_score": 0.0
        }


@tool
def extract_technical_patterns(chart_analyses: List[Dict]) -> Dict[str, Any]:
    """
    複数時間軸のチャート分析結果からテクニカルパターンを抽出
    
    Args:
        chart_analyses: 各時間軸のチャート分析結果リスト
        
    Returns:
        統合されたテクニカルパターン分析
    """
    try:
        pattern_summary = {
            "multi_timeframe_alignment": False,
            "dominant_pattern": None,
            "pattern_strength": 0.0,
            "breakout_signals": [],
            "confluence_zones": [],
            "timeframe_analysis": {}
        }
        
        valid_analyses = [a for a in chart_analyses if "error" not in a]
        
        if not valid_analyses:
            pattern_summary["error"] = "有効なチャート分析結果がありません"
            return pattern_summary
        
        # 各時間軸の分析結果を整理
        for analysis in valid_analyses:
            timeframe = analysis.get("timeframe", "unknown")
            pattern_summary["timeframe_analysis"][timeframe] = {
                "patterns": analysis.get("chart_patterns", []),
                "trend": analysis.get("trend_direction", "unknown"),
                "confidence": analysis.get("confidence_score", 0.0)
            }
        
        # 複数時間軸の整合性チェック
        trend_directions = [a.get("trend_direction") for a in valid_analyses]
        bullish_count = trend_directions.count("bullish")
        bearish_count = trend_directions.count("bearish")
        
        if bullish_count >= len(valid_analyses) * 0.7:
            pattern_summary["multi_timeframe_alignment"] = True
            pattern_summary["dominant_pattern"] = "bullish_alignment"
            pattern_summary["pattern_strength"] = bullish_count / len(valid_analyses)
        elif bearish_count >= len(valid_analyses) * 0.7:
            pattern_summary["multi_timeframe_alignment"] = True
            pattern_summary["dominant_pattern"] = "bearish_alignment"
            pattern_summary["pattern_strength"] = bearish_count / len(valid_analyses)
        
        logger.info(f"テクニカルパターン抽出完了: {len(valid_analyses)}時間軸分析")
        return pattern_summary
        
    except Exception as e:
        logger.error(f"テクニカルパターン抽出エラー: {e}")
        return {"error": str(e)}


@tool
def analyze_technical_indicators(indicators: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    テクニカル指標データを分析してシグナルを生成
    
    Args:
        indicators: 全時間軸のテクニカル指標データ
        current_price: 現在価格
        
    Returns:
        テクニカル指標分析結果
    """
    try:
        analysis_result = {
            "ma_signals": {},
            "vwap_signals": {},
            "bollinger_signals": {},
            "volume_signals": {},
            "atr_signals": {},
            "overall_signal": "neutral",
            "signal_strength": 0.0,
            "key_levels": {},
            "timeframe_signals": {}
        }
        
        signal_scores = []
        
        # 各時間軸のテクニカル指標を分析
        for timeframe, indicator_data in indicators.items():
            if not isinstance(indicator_data, dict):
                continue
                
            timeframe_signal = _analyze_timeframe_indicators(
                indicator_data, current_price, timeframe
            )
            analysis_result["timeframe_signals"][timeframe] = timeframe_signal
            
            if timeframe_signal.get("signal_score") is not None:
                signal_scores.append(timeframe_signal["signal_score"])
        
        # 全体シグナルの統合
        if signal_scores:
            avg_score = sum(signal_scores) / len(signal_scores)
            analysis_result["signal_strength"] = abs(avg_score)
            
            if avg_score > 0.3:
                analysis_result["overall_signal"] = "buy"
            elif avg_score < -0.3:
                analysis_result["overall_signal"] = "sell"
            else:
                analysis_result["overall_signal"] = "neutral"
        
        # 移動平均線分析
        analysis_result["ma_signals"] = _analyze_moving_averages(indicators, current_price)
        
        # VWAP分析
        analysis_result["vwap_signals"] = _analyze_vwap(indicators, current_price)
        
        # ボリンジャーバンド分析
        analysis_result["bollinger_signals"] = _analyze_bollinger_bands(indicators, current_price)
        
        logger.info(f"テクニカル指標分析完了: {len(signal_scores)}時間軸")
        return analysis_result
        
    except Exception as e:
        logger.error(f"テクニカル指標分析エラー: {e}")
        return {"error": str(e)}


@tool
def calculate_signals(technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    テクニカル分析結果からトレーディングシグナルを計算
    
    Args:
        technical_analysis: テクニカル指標分析結果
        
    Returns:
        計算されたシグナル
    """
    try:
        signals = {
            "entry_signals": [],
            "exit_signals": [],
            "stop_loss_levels": [],
            "take_profit_levels": [],
            "signal_quality": "low",
            "timeframe_consensus": False
        }
        
        overall_signal = technical_analysis.get("overall_signal", "neutral")
        signal_strength = technical_analysis.get("signal_strength", 0.0)
        
        # エントリーシグナル生成
        if overall_signal == "buy" and signal_strength > 0.5:
            signals["entry_signals"].append({
                "type": "buy",
                "strength": signal_strength,
                "reasons": _extract_buy_reasons(technical_analysis)
            })
        elif overall_signal == "sell" and signal_strength > 0.5:
            signals["entry_signals"].append({
                "type": "sell", 
                "strength": signal_strength,
                "reasons": _extract_sell_reasons(technical_analysis)
            })
        
        # シグナル品質評価
        if signal_strength > 0.7:
            signals["signal_quality"] = "high"
        elif signal_strength > 0.4:
            signals["signal_quality"] = "medium"
        else:
            signals["signal_quality"] = "low"
        
        # 時間軸コンセンサス確認
        timeframe_signals = technical_analysis.get("timeframe_signals", {})
        if len(timeframe_signals) >= 3:
            consensus_signals = [
                sig.get("signal", "neutral") 
                for sig in timeframe_signals.values()
                if sig.get("signal") == overall_signal
            ]
            signals["timeframe_consensus"] = len(consensus_signals) >= len(timeframe_signals) * 0.6
        
        logger.info(f"シグナル計算完了: {overall_signal} ({signal_strength:.2f})")
        return signals
        
    except Exception as e:
        logger.error(f"シグナル計算エラー: {e}")
        return {"error": str(e)}


@tool
def make_trading_decision(
    chart_analysis: Dict[str, Any], 
    technical_analysis: Dict[str, Any], 
    current_price: float,
    market_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    最終的な売買判断を行う
    
    Args:
        chart_analysis: チャート分析結果
        technical_analysis: テクニカル分析結果
        current_price: 現在価格
        market_context: 市場環境データ
        
    Returns:
        売買判断結果
    """
    try:
        decision = {
            "trading_decision": "HOLD",
            "confidence_level": 0.0,
            "entry_price": current_price,
            "stop_loss": None,
            "take_profit": [],
            "position_size_percent": 0.0,
            "reasoning": [],
            "risk_factors": [],
            "decision_timestamp": datetime.now().isoformat()
        }
        
        # チャート分析の信頼度
        chart_confidence = chart_analysis.get("confidence_score", 0.0)
        chart_signal = chart_analysis.get("trend_direction", "unknown")
        
        # テクニカル分析の信頼度
        tech_confidence = technical_analysis.get("signal_strength", 0.0)
        tech_signal = technical_analysis.get("overall_signal", "neutral")
        
        # 明確なトレーディング戦略による判断
        decision_result = _make_strategic_decision(
            chart_signal, chart_confidence,
            tech_signal, tech_confidence,
            technical_analysis, current_price
        )
        
        decision["trading_decision"] = decision_result["action"]
        decision["confidence_level"] = decision_result["confidence"]
        decision["strategy_used"] = decision_result["strategy"]
        
        # リスク管理の設定
        if decision["trading_decision"] in ["BUY", "SELL"]:
            decision["stop_loss"], decision["take_profit"] = _calculate_risk_levels(
                current_price, decision["trading_decision"], technical_analysis
            )
            decision["position_size_percent"] = _calculate_position_size(
                decision["confidence_level"]
            )
        
        # 判断理由の生成
        decision["reasoning"] = _generate_reasoning(
            chart_analysis, technical_analysis, decision["trading_decision"]
        )
        
        # リスク要因の特定
        decision["risk_factors"] = _identify_risk_factors(
            chart_analysis, technical_analysis, market_context
        )
        
        # 将来エントリー条件の生成
        decision["future_entry_conditions"] = _generate_future_entry_conditions(
            technical_analysis, current_price, decision["trading_decision"]
        )
        
        # 市場状況判定と推奨アクション
        decision["market_outlook"] = _analyze_market_outlook(
            technical_analysis, market_context, decision["trading_decision"]
        )
        
        logger.info(f"売買判断完了: {decision['trading_decision']} (信頼度: {decision['confidence_level']:.2f})")
        return decision
        
    except Exception as e:
        logger.error(f"売買判断エラー: {e}")
        return {"error": str(e)}


@tool
def calculate_position_size(confidence_level: float, account_risk_percent: float = 2.0) -> Dict[str, Any]:
    """
    ポジションサイズを計算
    
    Args:
        confidence_level: 判断への信頼度 (0-1)
        account_risk_percent: 口座リスク率 (デフォルト2%)
        
    Returns:
        ポジションサイズ計算結果
    """
    try:
        base_position_size = account_risk_percent
        
        # 信頼度に基づくポジションサイズ調整
        if confidence_level > 0.8:
            position_multiplier = 1.5
        elif confidence_level > 0.6:
            position_multiplier = 1.0
        elif confidence_level > 0.4:
            position_multiplier = 0.5
        else:
            position_multiplier = 0.2
        
        final_position_size = base_position_size * position_multiplier
        
        # 最大5%に制限
        final_position_size = min(final_position_size, 5.0)
        
        return {
            "position_size_percent": final_position_size,
            "base_risk_percent": base_position_size,
            "confidence_multiplier": position_multiplier,
            "max_risk_limit": 5.0
        }
        
    except Exception as e:
        logger.error(f"ポジションサイズ計算エラー: {e}")
        return {"error": str(e)}


# ヘルパー関数

def _calculate_next_review_timing(
    technical_analysis: Dict, current_price: float, current_decision: str
) -> str:
    """
    市場状況に応じた次回見直しタイミングを動的に計算
    """
    key_indicators = technical_analysis.get("key_indicators", {})
    review_triggers = []
    
    # ボラティリティベースの判定
    if "daily_atr" in key_indicators:
        atr = key_indicators["daily_atr"]
        if atr > 0:
            price_move_threshold = (atr / current_price) * 100
            if price_move_threshold > 3:
                # 高ボラティリティ時は短い間隔
                review_triggers.append("15分足更新時")
            elif price_move_threshold > 1.5:
                # 中程度のボラティリティ
                review_triggers.append("60分足更新時")
            else:
                # 低ボラティリティ
                review_triggers.append("日足更新時")
    
    # 価格位置による判定
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        ma50 = daily_ma.get("ma50", 0)
        
        if ma20 > 0:
            distance_to_ma20 = abs(current_price - ma20) / ma20 * 100
            if distance_to_ma20 < 1:
                # 移動平均線に近い場合は頻繁にチェック
                review_triggers.append(f"20日線（¥{ma20:,.0f}）タッチ時")
            elif distance_to_ma20 < 3:
                review_triggers.append(f"20日線接近時（現在±{distance_to_ma20:.1f}%）")
    
    # VWAP位置による判定
    if "hourly_60_vwap" in key_indicators:
        vwap_data = key_indicators["hourly_60_vwap"]
        vwap_price = vwap_data.get("daily", 0)
        
        if vwap_price > 0:
            vwap_distance = abs(current_price - vwap_price) / vwap_price * 100
            if vwap_distance < 0.5:
                review_triggers.append("5分足更新時（VWAP付近）")
    
    # 現在の判断による調整
    if current_decision == "HOLD":
        # HOLD時は重要な時間軸を重視
        if not review_triggers:
            review_triggers.append("60分足更新時")
        review_triggers.append("価格が2%以上変動時")
    
    # 最も重要なトリガーを選択
    if review_triggers:
        return " または ".join(review_triggers[:2])  # 最大2つまで
    else:
        return "60分足更新時（次の時間の00分）または価格が2%以上変動時"


def _get_analysis_focus_for_timeframe(timeframe: str) -> List[str]:
    """時間軸別の分析重点項目を取得"""
    focus_map = {
        "weekly": ["長期トレンド", "主要サポレジ", "大局的パターン"],
        "daily": ["中期トレンド", "移動平均線", "出来高分析"],
        "hourly_60": ["短期トレンド", "VWAP", "ボリンジャーバンド"],
        "minute_15": ["エントリータイミング", "短期パターン", "出来高確認"],
        "minute_5": ["精密エントリー", "直近動向", "ノイズ除去"],
        "minute_1": ["瞬間的動き", "約定タイミング", "スプレッド確認"]
    }
    return focus_map.get(timeframe, ["一般的なテクニカル分析"])


def _analyze_timeframe_indicators(indicator_data: Dict, current_price: float, timeframe: str) -> Dict:
    """時間軸別テクニカル指標分析"""
    result = {
        "timeframe": timeframe,
        "signal": "neutral",
        "signal_score": 0.0,
        "key_observations": []
    }
    
    score = 0.0
    observations = []
    
    # 移動平均線分析
    if "moving_averages" in indicator_data:
        ma_data = indicator_data["moving_averages"]
        ma_score = _calculate_ma_score(ma_data, current_price)
        score += ma_score
        if ma_score > 0:
            observations.append(f"移動平均線: 上昇傾向 ({ma_score:.2f})")
        elif ma_score < 0:
            observations.append(f"移動平均線: 下降傾向 ({ma_score:.2f})")
    
    # VWAP分析
    if "vwap" in indicator_data:
        vwap_data = indicator_data["vwap"]
        if "daily" in vwap_data:
            vwap_price = vwap_data["daily"]
            if current_price > vwap_price:
                score += 0.2
                observations.append("VWAP上抜け")
            else:
                score -= 0.2
                observations.append("VWAP下抜け")
    
    result["signal_score"] = score
    result["key_observations"] = observations
    
    if score > 0.2:
        result["signal"] = "buy"
    elif score < -0.2:
        result["signal"] = "sell"
    
    return result


def _calculate_ma_score(ma_data: Dict, current_price: float) -> float:
    """移動平均線スコア計算"""
    score = 0.0
    
    # 短期・中期・長期MAの順序確認
    ma_values = []
    for key, value in ma_data.items():
        if key.startswith("ma") and isinstance(value, (int, float)):
            period = int(key[2:])  # ma20 -> 20
            ma_values.append((period, value))
    
    ma_values.sort()  # 期間順にソート
    
    # 現在価格とMAの関係
    above_ma_count = sum(1 for _, ma_value in ma_values if current_price > ma_value)
    total_ma = len(ma_values)
    
    if total_ma > 0:
        score = (above_ma_count / total_ma - 0.5) * 2  # -1 to 1 の範囲
    
    return score


def _analyze_moving_averages(indicators: Dict, current_price: float) -> Dict:
    """移動平均線総合分析"""
    ma_signals = {
        "trend_direction": "neutral",
        "golden_cross": False,
        "death_cross": False,
        "ma_alignment": "mixed"
    }
    
    # 各時間軸のMA分析を統合
    # 実装は時間軸データの詳細に依存
    
    return ma_signals


def _analyze_vwap(indicators: Dict, current_price: float) -> Dict:
    """VWAP分析"""
    vwap_signals = {
        "price_vs_vwap": "neutral",
        "vwap_trend": "neutral",
        "strength": 0.0
    }
    
    return vwap_signals


def _analyze_bollinger_bands(indicators: Dict, current_price: float) -> Dict:
    """ボリンジャーバンド分析"""
    bb_signals = {
        "band_position": "middle",
        "squeeze_status": "normal",
        "breakout_potential": "low"
    }
    
    return bb_signals


def _extract_buy_reasons(technical_analysis: Dict) -> List[str]:
    """買いシグナルの理由抽出"""
    reasons = []
    
    if technical_analysis.get("ma_signals", {}).get("golden_cross"):
        reasons.append("ゴールデンクロス発生")
    
    if technical_analysis.get("vwap_signals", {}).get("price_vs_vwap") == "above":
        reasons.append("VWAP上抜け")
    
    return reasons


def _extract_sell_reasons(technical_analysis: Dict) -> List[str]:
    """売りシグナルの理由抽出"""
    reasons = []
    
    if technical_analysis.get("ma_signals", {}).get("death_cross"):
        reasons.append("デッドクロス発生")
    
    if technical_analysis.get("vwap_signals", {}).get("price_vs_vwap") == "below":
        reasons.append("VWAP下抜け")
    
    return reasons


def _calculate_risk_levels(current_price: float, decision: str, technical_analysis: Dict) -> Tuple[Optional[float], List[float]]:
    """ストップロスとテイクプロフィットレベル計算"""
    stop_loss = None
    take_profit = []
    
    # ATRベースのリスク計算（簡易版）
    atr_value = 20.0  # デフォルト値、実際のATRから取得すべき
    
    if decision == "BUY":
        stop_loss = current_price - (atr_value * 1.5)
        take_profit = [
            current_price + (atr_value * 2.0),
            current_price + (atr_value * 3.0)
        ]
    elif decision == "SELL":
        stop_loss = current_price + (atr_value * 1.5)
        take_profit = [
            current_price - (atr_value * 2.0),
            current_price - (atr_value * 3.0)
        ]
    
    return stop_loss, take_profit


def _calculate_position_size(confidence_level: float) -> float:
    """信頼度ベースのポジションサイズ計算"""
    base_size = 2.0  # ベース2%
    
    if confidence_level > 0.8:
        return min(base_size * 1.5, 5.0)
    elif confidence_level > 0.6:
        return base_size
    elif confidence_level > 0.4:
        return base_size * 0.5
    else:
        return base_size * 0.2


def _generate_reasoning(chart_analysis: Dict, technical_analysis: Dict, decision: str) -> List[str]:
    """判断理由生成"""
    reasoning = []
    
    # チャート分析からの理由
    chart_patterns = chart_analysis.get("chart_patterns", [])
    if chart_patterns:
        reasoning.append(f"📈 チャートパターン: {', '.join(chart_patterns)}")
    
    # テクニカル分析からの理由
    overall_signal = technical_analysis.get("overall_signal", "neutral")
    signal_strength = technical_analysis.get("signal_strength", 0.0)
    
    if overall_signal != "neutral":
        reasoning.append(f"📊 テクニカル指標: {overall_signal}シグナル (強度: {signal_strength:.2f})")
    
    # 具体的な指標分析
    key_indicators = technical_analysis.get("key_indicators", {})
    if key_indicators:
        # 移動平均線分析
        if "daily_ma" in key_indicators:
            daily_ma = key_indicators["daily_ma"]
            if "ma20" in daily_ma and "ma50" in daily_ma:
                ma20 = daily_ma["ma20"]
                ma50 = daily_ma["ma50"]
                current_price = technical_analysis.get("current_price", 0)
                
                if current_price > ma20 > ma50:
                    reasoning.append("🟢 価格が20日線・50日線を上抜け（上昇トレンド）")
                elif current_price < ma20 < ma50:
                    reasoning.append("🔴 価格が20日線・50日線を下抜け（下降トレンド）")
                elif ma20 > ma50:
                    reasoning.append("🟡 20日線が50日線上位（中期上昇基調）")
                else:
                    reasoning.append("🟡 20日線が50日線下位（中期下降基調）")
        
        # VWAP分析
        vwap_signals = _analyze_vwap_position(key_indicators, technical_analysis.get("current_price", 0))
        if vwap_signals:
            reasoning.extend(vwap_signals)
    
    # 判断固有の理由
    if decision == "BUY":
        buy_reasons = _extract_buy_reasons(technical_analysis)
        reasoning.extend([f"🚀 {reason}" for reason in buy_reasons])
    elif decision == "SELL":
        sell_reasons = _extract_sell_reasons(technical_analysis)
        reasoning.extend([f"📉 {reason}" for reason in sell_reasons])
    elif decision == "HOLD":
        hold_reasons = _extract_hold_reasons(technical_analysis, chart_analysis)
        reasoning.extend([f"⏸️ {reason}" for reason in hold_reasons])
    
    return reasoning if reasoning else ["❓ 明確な判断根拠が不足しています"]


def _analyze_vwap_position(key_indicators: Dict, current_price: float) -> List[str]:
    """VWAP分析"""
    vwap_signals = []
    
    # 日足VWAP
    if "daily_vwap" in key_indicators:
        daily_vwap = key_indicators["daily_vwap"].get("daily", 0)
        if daily_vwap > 0:
            if current_price > daily_vwap * 1.01:
                vwap_signals.append("💹 価格がVWAP大幅上抜け（買い圧力強い）")
            elif current_price > daily_vwap:
                vwap_signals.append("📈 価格がVWAP上位（買い優勢）")
            elif current_price < daily_vwap * 0.99:
                vwap_signals.append("📉 価格がVWAP大幅下抜け（売り圧力強い）")
            else:
                vwap_signals.append("⚖️ 価格がVWAP付近（均衡状態）")
    
    return vwap_signals


def _extract_hold_reasons(technical_analysis: Dict, chart_analysis: Dict) -> List[str]:
    """HOLD判断の理由抽出"""
    hold_reasons = []
    
    # シグナル強度不足
    signal_strength = technical_analysis.get("signal_strength", 0.0)
    if signal_strength < 0.6:
        hold_reasons.append(f"シグナル強度不足（{signal_strength:.2f} < 0.6）")
    
    # データ不足
    if "error" in chart_analysis:
        hold_reasons.append("チャート分析データが不足")
    
    if technical_analysis.get("overall_signal") == "neutral":
        hold_reasons.append("テクニカル指標が中立状態")
    
    # 複数時間軸の不一致
    timeframe_signals = technical_analysis.get("timeframe_signals", {})
    if len(timeframe_signals) > 2:
        signals = [sig.get("signal", "neutral") for sig in timeframe_signals.values()]
        buy_count = signals.count("buy")
        sell_count = signals.count("sell")
        total = len(signals)
        
        if buy_count < total * 0.6 and sell_count < total * 0.6:
            hold_reasons.append("複数時間軸でシグナル不一致")
    
    return hold_reasons


def _identify_risk_factors(chart_analysis: Dict, technical_analysis: Dict, market_context: Dict) -> List[str]:
    """リスク要因特定"""
    risks = []
    
    # ボラティリティリスク
    signal_strength = technical_analysis.get("signal_strength", 0.0)
    if signal_strength < 0.5:
        risks.append("⚠️ シグナル強度が低く、判断の確実性に欠ける")
    
    # 市場環境リスク
    volume_ratio = market_context.get("volume_ratio", 1.0)
    if volume_ratio < 0.5:
        risks.append("⚠️ 出来高が平均の50%未満で流動性リスクあり")
    elif volume_ratio > 3.0:
        risks.append("⚠️ 出来高が平均の3倍超で過熱感あり")
    
    # 価格変動リスク
    price_change = market_context.get("price_change_percent", 0.0)
    if abs(price_change) > 5.0:
        risks.append(f"⚠️ 既に大幅な価格変動が発生済み（{price_change:+.1f}%）")
    
    # 市場全体の状況
    if "indices" in market_context:
        indices = market_context["indices"]
        if "nikkei225" in indices:
            nikkei_change = indices["nikkei225"].change_percent
            if nikkei_change < -2.0:
                risks.append("⚠️ 日経平均が大幅下落中（市場環境悪化）")
            elif nikkei_change > 2.0:
                risks.append("⚠️ 日経平均が大幅上昇中（過熱感に注意）")
    
    return risks if risks else ["✅ 特筆すべきリスク要因なし"]


def _make_strategic_decision(
    chart_signal: str, chart_confidence: float,
    tech_signal: str, tech_confidence: float,
    technical_analysis: Dict, current_price: float
) -> Dict[str, Any]:
    """
    明確なトレーディング戦略による判断
    
    戦略優先順位:
    1. 強いコンフルエンス（複数指標一致）
    2. トレンドフォロー戦略
    3. 平均回帰戦略
    4. 慎重HOLD戦略
    """
    
    # 1. 強いコンフルエンス戦略（最優先）
    if chart_confidence > 0.7 and tech_confidence > 0.7:
        if chart_signal == "bullish" and tech_signal == "buy":
            return {
                "action": "BUY",
                "confidence": min(chart_confidence, tech_confidence),
                "strategy": "強いコンフルエンス買い戦略（チャート・テクニカル両方強気）"
            }
        elif chart_signal == "bearish" and tech_signal == "sell":
            return {
                "action": "SELL", 
                "confidence": min(chart_confidence, tech_confidence),
                "strategy": "強いコンフルエンス売り戦略（チャート・テクニカル両方弱気）"
            }
    
    # 2. トレンドフォロー戦略
    key_indicators = technical_analysis.get("key_indicators", {})
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        ma50 = daily_ma.get("ma50", 0)
        
        # 強い上昇トレンド
        if current_price > ma20 > ma50 and tech_signal == "buy":
            trend_strength = (current_price - ma50) / ma50 * 100
            if trend_strength > 3.0:  # 50日線から3%以上上
                return {
                    "action": "BUY",
                    "confidence": 0.75,
                    "strategy": f"トレンドフォロー買い戦略（50日線+{trend_strength:.1f}%上位）"
                }
        
        # 強い下降トレンド
        elif current_price < ma20 < ma50 and tech_signal == "sell":
            trend_strength = (ma50 - current_price) / ma50 * 100
            if trend_strength > 3.0:  # 50日線から3%以上下
                return {
                    "action": "SELL",
                    "confidence": 0.75,
                    "strategy": f"トレンドフォロー売り戦略（50日線-{trend_strength:.1f}%下位）"
                }
    
    # 3. 平均回帰戦略（VWAP乖離）
    if "hourly_60_vwap" in key_indicators:
        vwap_data = key_indicators["hourly_60_vwap"]
        vwap_price = vwap_data.get("daily", 0)
        
        if vwap_price > 0:
            vwap_deviation = (current_price - vwap_price) / vwap_price * 100
            
            # VWAP大幅下乖離からの買い
            if vwap_deviation < -2.0 and tech_confidence > 0.4:
                return {
                    "action": "BUY",
                    "confidence": 0.65,
                    "strategy": f"平均回帰買い戦略（VWAP{vwap_deviation:.1f}%下乖離）"
                }
            
            # VWAP大幅上乖離からの売り
            elif vwap_deviation > 2.0 and tech_confidence > 0.4:
                return {
                    "action": "SELL",
                    "confidence": 0.65,
                    "strategy": f"平均回帰売り戦略（VWAP+{vwap_deviation:.1f}%上乖離）"
                }
    
    # 4. 慎重HOLD戦略（デフォルト）
    hold_reason = "データ不足または明確なシグナルなし"
    
    if chart_confidence < 0.5 and tech_confidence < 0.5:
        hold_reason = "チャート・テクニカル両方の信頼度不足"
    elif chart_signal == "bullish" and tech_signal == "sell":
        hold_reason = "チャートと指標が相反（判断保留）"
    elif chart_signal == "bearish" and tech_signal == "buy":
        hold_reason = "チャートと指標が相反（判断保留）"
    elif tech_signal == "neutral":
        hold_reason = "テクニカル指標が中立状態"
    
    return {
        "action": "HOLD",
        "confidence": max(chart_confidence, tech_confidence) * 0.5,  # HOLD時は信頼度を半減
        "strategy": f"慎重HOLD戦略（{hold_reason}）"
    }


def _generate_future_entry_conditions(
    technical_analysis: Dict, current_price: float, current_decision: str
) -> Dict[str, Any]:
    """
    将来のエントリー条件を生成
    
    現在の市場状況から、どうなったらBUY/SELLするかを明示
    """
    conditions = {
        "buy_conditions": [],
        "sell_conditions": [],
        "watch_levels": {},
        "timeframe_focus": [],
        "next_review_trigger": ""
    }
    
    # より動的な見直しタイミングを最初に計算
    conditions["next_review_trigger"] = _calculate_next_review_timing(
        technical_analysis, current_price, current_decision
    )
    
    key_indicators = technical_analysis.get("key_indicators", {})
    
    # 主要価格レベルの特定
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        ma50 = daily_ma.get("ma50", 0)
        ma200 = daily_ma.get("ma200", 0)
        
        conditions["watch_levels"]["ma20_daily"] = ma20
        conditions["watch_levels"]["ma50_daily"] = ma50
        if ma200 > 0:
            conditions["watch_levels"]["ma200_daily"] = ma200
    
    # VWAP レベル
    if "hourly_60_vwap" in key_indicators:
        vwap_data = key_indicators["hourly_60_vwap"]
        vwap_price = vwap_data.get("daily", 0)
        if vwap_price > 0:
            conditions["watch_levels"]["vwap_daily"] = vwap_price
    
    # 現在の判断に応じた将来条件
    if current_decision == "HOLD":
        conditions.update(_generate_hold_to_action_conditions(key_indicators, current_price))
    elif current_decision == "BUY":
        conditions.update(_generate_buy_enhancement_conditions(key_indicators, current_price))
    elif current_decision == "SELL":
        conditions.update(_generate_sell_enhancement_conditions(key_indicators, current_price))
    
    return conditions


def _generate_hold_to_action_conditions(key_indicators: Dict, current_price: float) -> Dict:
    """HOLD状態からのエントリー条件生成"""
    buy_conditions = []
    sell_conditions = []
    timeframe_focus = []
    next_review = ""
    
    # 移動平均線ベースの条件
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        ma50 = daily_ma.get("ma50", 0)
        
        if ma20 > 0 and ma50 > 0:
            # 現在位置の分析
            price_vs_ma20 = (current_price - ma20) / ma20 * 100
            price_vs_ma50 = (current_price - ma50) / ma50 * 100
            
            if current_price < ma20 < ma50:
                # 下降トレンド中
                buy_conditions.extend([
                    f"📈 20日線（¥{ma20:,.0f}）を上抜けて定着",
                    f"🚀 20日線と50日線のゴールデンクロス発生",
                    f"📊 出来高を伴った上昇ブレイクアウト"
                ])
                next_review = f"60分足更新時または20日線（¥{ma20:,.0f}）接近時"
                timeframe_focus = ["日足", "60分足"]
                
            elif current_price > ma20 > ma50:
                # 上昇基調だが勢い不足
                buy_conditions.extend([
                    f"💪 50日線（¥{ma50:,.0f}）+3%以上での推移",
                    f"📈 20日線と50日線の乖離拡大（現在{abs(ma20-ma50)/ma50*100:.1f}%）",
                    f"🎯 VWAP上位での安定した価格推移"
                ])
                sell_conditions.extend([
                    f"📉 20日線（¥{ma20:,.0f}）を下抜け",
                    f"⚠️ 出来高減少を伴う上値重さ"
                ])
                next_review = "60分足更新時または20日線付近接近時"
                timeframe_focus = ["日足", "60分足", "15分足"]
                
            else:
                # レンジ相場
                range_high = max(ma20, ma50) * 1.02
                range_low = min(ma20, ma50) * 0.98
                buy_conditions.extend([
                    f"🔥 レンジ上限（¥{range_high:,.0f}）のブレイクアウト",
                    f"📊 移動平均線の収束解消（方向性明確化）"
                ])
                sell_conditions.extend([
                    f"📉 レンジ下限（¥{range_low:,.0f}）の下抜け"
                ])
                next_review = f"60分足更新時またはレンジ境界（¥{range_low:,.0f}-{range_high:,.0f}）接近時"
                timeframe_focus = ["日足", "60分足"]
    
    # VWAP条件
    if "hourly_60_vwap" in key_indicators:
        vwap_data = key_indicators["hourly_60_vwap"]
        vwap_price = vwap_data.get("daily", 0)
        
        if vwap_price > 0:
            vwap_deviation = (current_price - vwap_price) / vwap_price * 100
            
            if abs(vwap_deviation) < 1.0:
                # VWAP付近
                buy_conditions.append(f"💹 VWAP（¥{vwap_price:,.0f}）+1.5%以上での継続推移")
                sell_conditions.append(f"📉 VWAP（¥{vwap_price:,.0f}）-1.5%以下での継続推移")
    
    # 条件が少ない場合のデフォルト
    if not buy_conditions:
        buy_conditions.append("📊 明確な上昇トレンドの確立を待つ")
    if not sell_conditions:
        sell_conditions.append("📉 明確な下降トレンドの確立を待つ")
    if not next_review:
        # より短期的な見直しタイミングをデフォルトに設定
        next_review = "60分足更新時（次の時間の00分）または価格が2%以上変動時"
    
    return {
        "buy_conditions": buy_conditions,
        "sell_conditions": sell_conditions,
        "timeframe_focus": timeframe_focus,
        "next_review_trigger": next_review
    }


def _generate_buy_enhancement_conditions(key_indicators: Dict, current_price: float) -> Dict:
    """BUY判断時の追加エントリー・利確条件"""
    buy_conditions = []
    sell_conditions = []
    
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        ma50 = daily_ma.get("ma50", 0)
        
        if ma20 > 0:
            # 追加買い条件
            buy_conditions.extend([
                f"🚀 一時的押し目での20日線（¥{ma20:,.0f}）タッチ後の反発",
                f"📈 上昇の勢い継続（新高値更新）"
            ])
            
            # 利確・撤退条件
            sell_conditions.extend([
                f"📉 20日線（¥{ma20:,.0f}）明確な下抜け",
                f"⚠️ 出来高減少を伴う上値重さの継続"
            ])
    
    return {
        "buy_conditions": buy_conditions,
        "sell_conditions": sell_conditions,
        "timeframe_focus": ["15分足", "5分足"],
        "next_review_trigger": "ポジション保有中は継続監視"
    }


def _generate_sell_enhancement_conditions(key_indicators: Dict, current_price: float) -> Dict:
    """SELL判断時の追加エントリー・利確条件"""
    buy_conditions = []
    sell_conditions = []
    
    if "daily_ma" in key_indicators:
        daily_ma = key_indicators["daily_ma"]
        ma20 = daily_ma.get("ma20", 0)
        
        if ma20 > 0:
            # 撤退・買い転換条件
            buy_conditions.extend([
                f"🔄 20日線（¥{ma20:,.0f}）明確な上抜けと定着",
                f"📊 出来高を伴った反転上昇"
            ])
            
            # 追加売り条件
            sell_conditions.extend([
                f"📉 一時的戻りでの20日線（¥{ma20:,.0f}）タッチ後の下落再開",
                f"💥 下落の加速（新安値更新）"
            ])
    
    return {
        "buy_conditions": buy_conditions,
        "sell_conditions": sell_conditions,
        "timeframe_focus": ["15分足", "5分足"],
        "next_review_trigger": "ポジション保有中は継続監視"
    }


def _analyze_market_outlook(
    technical_analysis: Dict, market_context: Dict, current_decision: str
) -> Dict[str, Any]:
    """
    市場状況判定と推奨アクション
    """
    outlook = {
        "market_phase": "",
        "trend_strength": "",
        "recommended_strategy": "",
        "patience_level": "",
        "action_urgency": "",
        "monitoring_frequency": ""
    }
    
    # 市場フェーズの判定
    signal_strength = technical_analysis.get("signal_strength", 0.0)
    
    if signal_strength > 0.7:
        outlook["market_phase"] = "🎯 明確なトレンド相場"
        outlook["trend_strength"] = "強い"
        outlook["recommended_strategy"] = "トレンドフォロー戦略"
        outlook["action_urgency"] = "高"
        outlook["monitoring_frequency"] = "5-15分足で継続監視"
    elif signal_strength > 0.4:
        outlook["market_phase"] = "📊 方向性模索相場"
        outlook["trend_strength"] = "中程度"
        outlook["recommended_strategy"] = "様子見または小ポジション"
        outlook["action_urgency"] = "中"
        outlook["monitoring_frequency"] = "60分足-日足で監視"
    else:
        outlook["market_phase"] = "😴 膠着・レンジ相場"
        outlook["trend_strength"] = "弱い"
        outlook["recommended_strategy"] = "積極的な待機戦略"
        outlook["action_urgency"] = "低"
        outlook["monitoring_frequency"] = "日足で十分"
    
    # 忍耐レベルの設定
    if current_decision == "HOLD":
        if signal_strength < 0.3:
            outlook["patience_level"] = "🧘‍♂️ 長期忍耐推奨（数日-数週間）"
        elif signal_strength < 0.6:
            outlook["patience_level"] = "⏳ 中期待機推奨（数時間-数日）"
        else:
            outlook["patience_level"] = "⚡ 短期注視推奨（数分-数時間）"
    else:
        outlook["patience_level"] = "📈 ポジション管理モード"
    
    # 市場環境による調整
    if "indices" in market_context:
        indices = market_context["indices"]
        if "nikkei225" in indices:
            nikkei_change = indices["nikkei225"].change_percent
            if abs(nikkei_change) > 2.0:
                outlook["market_phase"] += f" (日経: {nikkei_change:+.1f}%の影響)"
                outlook["recommended_strategy"] += " + 市場全体動向考慮"
    
    return outlook