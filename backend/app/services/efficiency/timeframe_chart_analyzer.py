#!/usr/bin/env python3
"""
時間足別チャート分析専門エージェント

各時間足に特化した分析内容を効率的に実行する
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..ai.ai_provider_factory import get_ai_provider
from ..ai.langchain_adapter import create_langchain_llm
from langchain_core.messages import HumanMessage
import os

logger = logging.getLogger(__name__)

class TimeframeChartAnalyzer:
    """
    時間足別チャート分析エンジン
    
    各時間足に特化した分析項目を実行し、効率的な分析結果を生成する
    """
    
    def __init__(self):
        # マルチAI対応プロバイダー設定
        try:
            ai_provider = get_ai_provider()
            self.llm = create_langchain_llm(ai_provider)
            logger.info(f"TimeframeChartAnalyzer: {ai_provider.provider_name} - {ai_provider.model} で初期化")
        except Exception as e:
            logger.error(f"TimeframeChartAnalyzer AI初期化エラー: {e}")
            raise RuntimeError(f"AI初期化失敗: {e}")
        
        # 時間足別分析テンプレート
        self.analysis_templates = {
            'weekly': self._get_weekly_analysis_prompt(),
            'daily': self._get_daily_analysis_prompt(),
            'hourly_60': self._get_hourly_analysis_prompt(),
            'minute_15': self._get_15min_analysis_prompt(),
            'minute_5': self._get_5min_analysis_prompt(),
            'minute_1': self._get_1min_analysis_prompt()
        }
    
    def analyze_timeframe(self, timeframe: str, chart_image_path: str, 
                         technical_indicators: Dict[str, Any], 
                         market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        指定時間足のチャート分析を実行
        
        Args:
            timeframe: 時間足名
            chart_image_path: チャート画像パス
            technical_indicators: テクニカル指標データ
            market_context: 市場環境データ
            
        Returns:
            時間足別分析結果
        """
        try:
            # 時間足別分析プロンプト取得
            analysis_prompt = self.analysis_templates.get(timeframe)
            if not analysis_prompt:
                raise ValueError(f"未対応の時間足: {timeframe}")
            
            # プロンプト構築
            full_prompt = self._build_analysis_prompt(
                timeframe, analysis_prompt, technical_indicators, market_context
            )
            
            # AI分析実行
            response = self.llm.invoke([HumanMessage(content=full_prompt)])
            
            # 結果解析
            analysis_result = self._parse_analysis_result(response.content, timeframe)
            
            logger.info(f"✅ {timeframe} チャート分析完了")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ {timeframe} チャート分析エラー: {e}")
            return self._create_error_result(timeframe, str(e))
    
    def _build_analysis_prompt(self, timeframe: str, analysis_prompt: str, 
                              technical_indicators: Dict[str, Any], 
                              market_context: Dict[str, Any]) -> str:
        """分析プロンプトを構築"""
        
        # テクニカル指標の要約
        tech_summary = self._summarize_technical_indicators(technical_indicators, timeframe)
        
        # 市場環境の要約
        market_summary = self._summarize_market_context(market_context)
        
        full_prompt = f"""
{analysis_prompt}

## テクニカル指標データ
{tech_summary}

## 市場環境
{market_summary}

## 分析要求
上記データに基づいて、{timeframe}に特化した分析を実行してください。
JSON形式で結果を返してください。
"""
        
        return full_prompt
    
    def _summarize_technical_indicators(self, indicators: Dict[str, Any], timeframe: str) -> str:
        """テクニカル指標を要約"""
        if not indicators:
            return "テクニカル指標データなし"
        
        summary_lines = []
        
        # 移動平均線
        if 'moving_averages' in indicators:
            ma_data = indicators['moving_averages']
            summary_lines.append(f"移動平均: {ma_data}")
        
        # VWAP
        if 'vwap' in indicators:
            vwap_data = indicators['vwap']
            summary_lines.append(f"VWAP: {vwap_data}")
        
        # ボリンジャーバンド
        if 'bollinger_bands' in indicators:
            bb_data = indicators['bollinger_bands']
            summary_lines.append(f"ボリンジャーバンド: {bb_data}")
        
        # ATR
        if 'atr14' in indicators:
            summary_lines.append(f"ATR(14): {indicators['atr14']}")
        
        return "\\n".join(summary_lines) if summary_lines else "主要指標データなし"
    
    def _summarize_market_context(self, market_context: Dict[str, Any]) -> str:
        """市場環境を要約"""
        if not market_context:
            return "市場環境データなし"
        
        summary_lines = []
        
        # 価格変動
        if 'price_change_percent' in market_context:
            change = market_context['price_change_percent']
            summary_lines.append(f"価格変動: {change:+.2f}%")
        
        # 出来高比率
        if 'volume_ratio' in market_context:
            vol_ratio = market_context['volume_ratio']
            summary_lines.append(f"出来高比率: {vol_ratio:.2f}")
        
        return "\\n".join(summary_lines) if summary_lines else "市場データなし"
    
    def _parse_analysis_result(self, response_content: str, timeframe: str) -> Dict[str, Any]:
        """AI分析結果を解析"""
        try:
            import json
            
            # JSON部分を抽出
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                result = json.loads(json_str)
                
                # メタデータ追加
                result['timeframe'] = timeframe
                result['analysis_timestamp'] = datetime.now().isoformat()
                result['ai_confidence'] = result.get('confidence_score', 0.5)
                
                return result
            else:
                # JSON形式でない場合のフォールバック
                return {
                    'timeframe': timeframe,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'summary': response_content[:500],  # 先頭500文字
                    'ai_confidence': 0.3,
                    'parsing_error': True
                }
                
        except Exception as e:
            logger.warning(f"分析結果解析エラー: {e}")
            return self._create_error_result(timeframe, f"結果解析エラー: {e}")
    
    def _create_error_result(self, timeframe: str, error_message: str) -> Dict[str, Any]:
        """エラー結果を作成"""
        return {
            'timeframe': timeframe,
            'analysis_timestamp': datetime.now().isoformat(),
            'error': error_message,
            'ai_confidence': 0.0,
            'status': 'failed'
        }
    
    # ========== 時間足別分析プロンプト定義 ==========
    
    def _get_weekly_analysis_prompt(self) -> str:
        """週足分析プロンプト"""
        return """
# 週足チャート分析エージェント

あなたは週足チャート分析の専門家です。長期的な投資判断に必要な分析を行ってください。

## 分析フォーカス項目
1. **長期トレンド方向**: 月足、年足レベルでのトレンド判定
2. **主要サポート・レジスタンス**: 長期間有効な重要価格帯
3. **投資家心理**: 大口投資家の動向、機関投資家のポジション推測
4. **週次モメンタム**: 長期的な勢い、転換点の兆候
5. **長期移動平均**: 200日線、52週線との位置関係

## 出力形式 (JSON)
{
  "long_term_trend": "上昇/下降/横ばい",
  "trend_strength": 0.0-1.0,
  "major_resistance": [価格レベル配列],
  "major_support": [価格レベル配列],
  "investor_sentiment": "強気/弱気/中立",
  "momentum_direction": "加速/減速/安定",
  "key_price_levels": [重要価格配列],
  "next_week_outlook": "来週の見通し",
  "confidence_score": 0.0-1.0
}
"""
    
    def _get_daily_analysis_prompt(self) -> str:
        """日足分析プロンプト"""
        return """
# 日足チャート分析エージェント

あなたは日足チャート分析の専門家です。中期的なトレード判断に必要な分析を行ってください。

## 分析フォーカス項目
1. **中期トレンド**: 2週間〜3ヶ月のトレンド状況
2. **日次移動平均**: 20日、50日、200日線の位置関係
3. **ボリューム分析**: 出来高とプライスアクションの関係
4. **日次パターン**: ヘッドアンドショルダー、フラッグ等
5. **ギャップ分析**: 窓開け、窓埋めの状況

## 出力形式 (JSON)
{
  "medium_term_trend": "上昇/下降/横ばい",
  "ma_alignment": "ゴールデンクロス/デッドクロス/混在",
  "volume_confirmation": true/false,
  "chart_pattern": "パターン名",
  "gap_status": "ギャップ状況",
  "daily_support": 価格,
  "daily_resistance": 価格,
  "swing_outlook": "数日〜数週間の見通し",
  "confidence_score": 0.0-1.0
}
"""
    
    def _get_hourly_analysis_prompt(self) -> str:
        """60分足分析プロンプト"""
        return """
# 60分足チャート分析エージェント

あなたは60分足チャート分析の専門家です。デイトレード判断に必要な分析を行ってください。

## 分析フォーカス項目
1. **短期トレンド**: 数時間〜数日のトレンド
2. **VWAP位置**: 日次VWAPとの位置関係
3. **時間足モメンタム**: RSI、MACD等の短期指標
4. **日中サポレジ**: 当日の重要価格帯
5. **ボリュームプロファイル**: 時間帯別出来高分析

## 出力形式 (JSON)
{
  "short_term_trend": "上昇/下降/横ばい",
  "vwap_position": "上位/下位/近辺",
  "momentum_indicators": {"rsi": 値, "macd": "状況"},
  "intraday_support": 価格,
  "intraday_resistance": 価格,
  "volume_profile": "厚い価格帯",
  "session_outlook": "セッション内見通し",
  "confidence_score": 0.0-1.0
}
"""
    
    def _get_15min_analysis_prompt(self) -> str:
        """15分足分析プロンプト"""
        return """
# 15分足チャート分析エージェント

あなたは15分足チャート分析の専門家です。エントリータイミング判断に必要な分析を行ってください。

## 分析フォーカス項目
1. **エントリータイミング**: 最適な参入タイミング
2. **短期サポレジ**: 15分足レベルの重要価格
3. **ブレイクアウト確認**: トレンド転換、継続の兆候
4. **マイクロトレンド変化**: 細かいトレンド変化の検知

## 出力形式 (JSON)
{
  "entry_signal": "BUY/SELL/WAIT",
  "signal_strength": 0.0-1.0,
  "micro_support": 価格,
  "micro_resistance": 価格,
  "breakout_potential": "高/中/低",
  "trend_change_signal": true/false,
  "entry_timing": "即座/待機/見送り",
  "confidence_score": 0.0-1.0
}
"""
    
    def _get_5min_analysis_prompt(self) -> str:
        """5分足分析プロンプト"""
        return """
# 5分足チャート分析エージェント

あなたは5分足チャート分析の専門家です。直近の値動き分析を行ってください。

## 分析フォーカス項目
1. **直近プライスアクション**: 最新の値動きパターン
2. **ブレイクアウト検証**: 上位足シグナルの確認
3. **クイックリバーサル**: 短期的な反転シグナル
4. **スキャルピング機会**: 短期売買チャンス

## 出力形式 (JSON)
{
  "immediate_action": "BUY/SELL/HOLD",
  "price_momentum": "加速/減速/安定",
  "breakout_validation": true/false,
  "reversal_signal": true/false,
  "scalping_opportunity": "有/無",
  "quick_support": 価格,
  "quick_resistance": 価格,
  "confidence_score": 0.0-1.0
}
"""
    
    def _get_1min_analysis_prompt(self) -> str:
        """1分足分析プロンプト"""
        return """
# 1分足チャート分析エージェント

あなたは1分足チャート分析の専門家です。実行判断に必要な分析を行ってください。

## 分析フォーカス項目
1. **エグゼキューション判断**: 即座の売買実行可否
2. **ティック分析**: 最小値動き単位での分析
3. **即時マーケット反応**: リアルタイム市場反応
4. **オーダーフロー**: 注文の流れ推測

## 出力形式 (JSON)
{
  "execution_signal": "EXECUTE_BUY/EXECUTE_SELL/WAIT",
  "tick_direction": "上昇/下降/横ばい",
  "market_response": "強い/普通/弱い",
  "order_flow": "買い優勢/売り優勢/均衡",
  "immediate_risk": "高/中/低",
  "execution_timing": "今すぐ/数分後/見送り",
  "confidence_score": 0.0-1.0
}
"""