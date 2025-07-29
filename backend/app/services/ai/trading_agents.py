#!/usr/bin/env python3
"""
LangGraphトレーディングエージェント定義

3つの専門エージェントを定義:
1. チャート分析エージェント (chart_analyst_agent)
2. テクニカル指標分析エージェント (technical_analyst_agent)  
3. 売買判断エージェント (trading_decision_agent)
"""

import os
import logging
from typing import Dict, Any, List, Literal
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from app.services.ai.trading_tools import (
    analyze_chart_image,
    extract_technical_patterns,
    analyze_technical_indicators,
    calculate_signals,
    make_trading_decision,
    calculate_position_size
)

logger = logging.getLogger(__name__)

# OpenAI APIキーの設定と確認
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key or openai_api_key.startswith("your-"):
    logger.warning("OPENAI_API_KEY not properly configured")

# OpenAI GPT-4 LLMモデルの初期化
llm = ChatOpenAI(
    api_key=openai_api_key,
    model="gpt-4o",
    temperature=0.1,  # 一貫性のある分析のため低温度設定
    max_tokens=4000
)


def create_chart_analyst_agent():
    """
    チャート分析専門エージェントを作成
    
    チャート画像を分析し、テクニカルパターンを特定する専門家
    """
    chart_analyst_tools = [
        analyze_chart_image,
        extract_technical_patterns
    ]
    
    chart_analyst_prompt = """
あなたは株式チャート分析の専門家です。

## 役割
- チャート画像を詳細に分析し、テクニカルパターンを特定
- 複数時間軸のチャートから統合的な分析を実施
- サポート・レジスタンスライン、トレンドラインを識別
- 出来高パターンと価格動向の関係を分析

## 分析方針
1. **パターン認識**: 三角持合い、ダブルトップ/ボトム、ヘッドアンドショルダー等
2. **トレンド分析**: 長期・中期・短期トレンドの方向性と強度
3. **重要レベル**: サポート・レジスタンスの信頼性と有効性
4. **出来高確認**: 価格動向を裏付ける出来高の動き
5. **ブレイクアウト**: パターンブレイクアウトの可能性と方向性

## 出力要件
- 客観的で具体的な分析結果を提供
- 各パターンの信頼度を0-1で評価
- 複数時間軸の整合性を確認
- 明確な根拠とともに判断を説明

## 重要な注意点
- チャート画像の詳細を正確に読み取る
- 主観的な判断より客観的なパターンを重視
- 不確実な要素は明確に「不明」として記録
- 次のテクニカル分析エージェントに有用な情報を提供

分析完了後は「technical_analyst」に結果を渡してください。
"""
    
    return create_react_agent(
        llm,
        tools=chart_analyst_tools,
        prompt=chart_analyst_prompt,
        name="chart_analyst"
    )


def create_technical_analyst_agent():
    """
    テクニカル指標分析専門エージェントを作成
    
    テクニカル指標データを分析し、売買シグナルを生成する専門家
    """
    technical_analyst_tools = [
        analyze_technical_indicators,
        calculate_signals
    ]
    
    technical_analyst_prompt = """
あなたはテクニカル指標分析の専門家です。

## 役割
- 各種テクニカル指標を詳細に分析
- 複数時間軸での指標の整合性を確認
- 明確な売買シグナルを生成
- リスク・リワード比率を評価

## 分析対象指標
1. **移動平均線**: ゴールデンクロス/デッドクロス、MA配列
2. **VWAP**: 価格とVWAPの関係、VWAP傾き
3. **ボリンジャーバンド**: バンド内位置、スクイーズ/エクスパンション
4. **ATR**: ボラティリティ水準と変化
5. **出来高プロファイル**: POC、Value Area、出来高分布

## 分析プロセス
1. **各時間軸分析**: 週足→日足→時間足→分足の順序で分析
2. **整合性確認**: 複数時間軸でのシグナル一致度確認
3. **強度評価**: シグナルの強さを定量的に評価
4. **タイミング判定**: エントリー/エグジットの最適タイミング
5. **リスク評価**: 現在の市場環境でのリスク水準

## 出力要件
- 各指標の現在値と過去比較
- 明確な売買シグナル（BUY/SELL/NEUTRAL）
- シグナル強度の定量評価（0-1）
- エントリー条件の具体的説明
- 想定されるリスクレベル

## 重要な注意点
- データの正確性を最優先
- 複数指標の総合的判断を重視
- 相反するシグナルは慎重に評価
- 市場環境に応じたシグナル調整

分析完了後は「trading_decision」エージェントに結果を渡してください。
"""
    
    return create_react_agent(
        llm,
        tools=technical_analyst_tools,
        prompt=technical_analyst_prompt,
        name="technical_analyst"
    )


def create_trading_decision_agent():
    """
    売買判断専門エージェントを作成
    
    チャート分析とテクニカル分析結果を統合し、最終的な売買判断を行う専門家
    """
    trading_decision_tools = [
        make_trading_decision,
        calculate_position_size
    ]
    
    trading_decision_prompt = """
あなたは総合的な売買判断を行うトレーディング専門家です。

## 役割
- チャート分析とテクニカル分析結果を統合
- 最終的な売買判断（BUY/SELL/HOLD）を決定
- リスク管理方針を策定
- ポジションサイズを計算

## 判断プロセス
1. **情報統合**: チャート分析とテクニカル分析の整合性確認
2. **優先順位**: 長期→短期の順でトレンド方向を確認
3. **エントリー条件**: 複数条件が揃った場合のみエントリー推奨
4. **リスク管理**: ストップロスとテイクプロフィットの設定
5. **ポジション管理**: 信頼度に応じたポジションサイズ決定

## 判断基準
### BUY条件
- チャート: 上昇トレンド/上向きブレイクアウト
- テクニカル: 複数指標で買いシグナル
- 確証: 出来高裏付け、複数時間軸一致

### SELL条件  
- チャート: 下降トレンド/下向きブレイクアウト
- テクニカル: 複数指標で売りシグナル
- 確証: 出来高裏付け、複数時間軸一致

### HOLD条件
- シグナル不一致、不十分な根拠
- 高ボラティリティ時の様子見
- 重要レベル接近時の慎重判断

## リスク管理原則
1. **損失限定**: 口座資金の1-2%を上限
2. **利益確保**: 段階的利確を推奨
3. **ポジション制限**: 信頼度に応じたサイズ調整
4. **市場環境**: ボラティリティ考慮した調整

## 出力要件
- 明確な売買判断と根拠
- 具体的なエントリー/エグジット価格
- 詳細なリスク管理計画
- 判断に至った論理的根拠
- 想定されるリスク要因

## 重要な注意点
- 確証のない判断は避ける
- リスク管理を最優先
- 市場環境の変化に対応
- 一貫した判断基準を維持

これが最終判断となります。慎重かつ論理的に分析してください。
"""
    
    return create_react_agent(
        llm,
        tools=trading_decision_tools,
        prompt=trading_decision_prompt,
        name="trading_decision"
    )


# エージェント初期化
chart_analyst_agent = create_chart_analyst_agent()
technical_analyst_agent = create_technical_analyst_agent()
trading_decision_agent = create_trading_decision_agent()


# ノード関数定義（LangGraphワークフロー用）

def chart_analyst_node(state: Dict[str, Any]) -> Command[Literal["technical_analyst"]]:
    """
    チャート分析ノード
    
    チャート画像を分析し、結果をテクニカル分析エージェントに渡す
    """
    try:
        logger.info("🔍 チャート分析開始")
        
        # チャート画像データの取得
        chart_images = state.get("chart_images", {})
        current_price = state.get("current_price", 0.0)
        timestamp = state.get("timestamp", datetime.now().isoformat())
        
        if not chart_images:
            logger.warning("チャート画像データが見つかりません")
            error_result = {
                "error": "チャート画像データが提供されていません",
                "timestamp": timestamp
            }
            return Command(
                update={
                    "chart_analysis_result": error_result,
                    "messages": state.get("messages", []) + [
                        AIMessage(content="チャート画像が見つからないため分析をスキップします", name="chart_analyst")
                    ]
                },
                goto="technical_analyst"
            )
        
        # チャート分析実行
        input_data = {
            "messages": state.get("messages", []) + [
                HumanMessage(content=f"""
チャート画像分析を実行してください。

## 分析対象
現在価格: ¥{current_price:,.0f}
分析時刻: {timestamp}

## チャート画像
{_format_chart_images_for_analysis(chart_images)}

各時間軸のチャート画像を分析し、テクニカルパターンを特定してください。
""")
            ]
        }
        
        result = chart_analyst_agent.invoke(input_data)
        
        # 分析結果の構造化
        chart_analysis_result = {
            "timestamp": timestamp,
            "current_price": current_price,
            "analyzed_timeframes": list(chart_images.keys()),
            "analysis_summary": result["messages"][-1].content,
            "patterns_identified": True,  # 実際の分析結果から判定
            "confidence_score": 0.7  # LLMレスポンスから抽出すべき
        }
        
        logger.info(f"✅ チャート分析完了: {len(chart_images)}時間軸")
        
        return Command(
            update={
                "chart_analysis_result": chart_analysis_result,
                "messages": state.get("messages", []) + [
                    AIMessage(content=result["messages"][-1].content, name="chart_analyst")
                ]
            },
            goto="technical_analyst"
        )
        
    except Exception as e:
        logger.error(f"❌ チャート分析エラー: {e}")
        error_result = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return Command(
            update={
                "chart_analysis_result": error_result,
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"チャート分析でエラーが発生しました: {e}", name="chart_analyst")
                ]
            },
            goto="technical_analyst"
        )


def technical_analyst_node(state: Dict[str, Any]) -> Command[Literal["trading_decision"]]:
    """
    テクニカル分析ノード
    
    テクニカル指標を分析し、結果を売買判断エージェントに渡す
    """
    try:
        logger.info("📊 テクニカル分析開始")
        
        # 必要なデータの取得
        technical_indicators = state.get("technical_indicators", {})
        current_price = state.get("current_price", 0.0)
        chart_analysis_result = state.get("chart_analysis_result", {})
        timestamp = state.get("timestamp", datetime.now().isoformat())
        
        if not technical_indicators:
            logger.warning("テクニカル指標データが見つかりません")
            error_result = {
                "error": "テクニカル指標データが提供されていません",
                "timestamp": timestamp
            }
            return Command(
                update={
                    "technical_analysis_result": error_result,
                    "messages": state.get("messages", []) + [
                        AIMessage(content="テクニカル指標データが見つからないため分析をスキップします", name="technical_analyst")
                    ]
                },
                goto="trading_decision"
            )
        
        # テクニカル分析実行
        input_data = {
            "messages": state.get("messages", []) + [
                HumanMessage(content=f"""
テクニカル指標分析を実行してください。

## 市場データ
現在価格: ¥{current_price:,.0f}
分析時刻: {timestamp}

## チャート分析結果
{_format_chart_analysis_summary(chart_analysis_result)}

## テクニカル指標データ
{_format_technical_indicators_for_analysis(technical_indicators)}

全時間軸のテクニカル指標を分析し、売買シグナルを生成してください。
""")
            ]
        }
        
        result = technical_analyst_agent.invoke(input_data)
        
        # 分析結果の構造化
        technical_analysis_result = {
            "timestamp": timestamp,
            "current_price": current_price,
            "analyzed_timeframes": list(technical_indicators.keys()),
            "overall_signal": "neutral",  # LLMレスポンスから抽出すべき
            "signal_strength": 0.6,       # LLMレスポンスから抽出すべき
            "analysis_summary": result["messages"][-1].content,
            "key_indicators": _extract_key_indicators(technical_indicators)
        }
        
        logger.info("✅ テクニカル分析完了")
        
        return Command(
            update={
                "technical_analysis_result": technical_analysis_result,
                "messages": state.get("messages", []) + [
                    AIMessage(content=result["messages"][-1].content, name="technical_analyst")
                ]
            },
            goto="trading_decision"
        )
        
    except Exception as e:
        logger.error(f"❌ テクニカル分析エラー: {e}")
        error_result = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return Command(
            update={
                "technical_analysis_result": error_result,
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"テクニカル分析でエラーが発生しました: {e}", name="technical_analyst")
                ]
            },
            goto="trading_decision"
        )


def trading_decision_node(state: Dict[str, Any]) -> Command[Literal["__end__"]]:
    """
    売買判断ノード
    
    最終的な売買判断を行い、ワークフローを終了
    """
    try:
        logger.info("⚖️ 売買判断開始")
        
        # 必要なデータの取得
        chart_analysis_result = state.get("chart_analysis_result", {})
        technical_analysis_result = state.get("technical_analysis_result", {})
        current_price = state.get("current_price", 0.0)
        market_context = state.get("market_context", {})
        timestamp = state.get("timestamp", datetime.now().isoformat())
        
        # 売買判断実行
        input_data = {
            "messages": state.get("messages", []) + [
                HumanMessage(content=f"""
最終的な売買判断を行ってください。

## 市場データ
現在価格: ¥{current_price:,.0f}
判断時刻: {timestamp}

## チャート分析結果
{_format_analysis_summary(chart_analysis_result)}

## テクニカル分析結果
{_format_analysis_summary(technical_analysis_result)}

## 市場環境
{_format_market_context(market_context)}

すべての分析結果を統合し、最終的な売買判断を行ってください。
リスク管理も含めた具体的な推奨事項を提示してください。
""")
            ]
        }
        
        result = trading_decision_agent.invoke(input_data)
        
        # 最終判断結果の構造化
        final_decision = {
            "timestamp": timestamp,
            "symbol": state.get("symbol", "unknown"),
            "current_price": current_price,
            
            # 判断結果
            "trading_decision": "HOLD",  # LLMレスポンスから抽出すべき
            "confidence_level": 0.5,     # LLMレスポンスから抽出すべき
            
            # 価格レベル
            "entry_price": current_price,
            "stop_loss": None,           # LLMレスポンスから抽出すべき
            "take_profit": [],           # LLMレスポンスから抽出すべき
            
            # リスク管理
            "position_size_percent": 0.0, # LLMレスポンスから抽出すべき
            "max_risk_percent": 2.0,
            
            # 分析サマリー
            "reasoning": [],             # LLMレスポンスから抽出すべき
            "risk_factors": [],          # LLMレスポンスから抽出すべき
            "decision_summary": result["messages"][-1].content,
            
            # 元データ参照
            "chart_analysis": chart_analysis_result,
            "technical_analysis": technical_analysis_result,
            "market_context": market_context
        }
        
        logger.info(f"✅ 売買判断完了: {final_decision['trading_decision']}")
        
        return Command(
            update={
                "final_decision": final_decision,
                "messages": state.get("messages", []) + [
                    AIMessage(content=result["messages"][-1].content, name="trading_decision")
                ]
            },
            goto="__end__"
        )
        
    except Exception as e:
        logger.error(f"❌ 売買判断エラー: {e}")
        error_decision = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "trading_decision": "ERROR",
            "confidence_level": 0.0
        }
        return Command(
            update={
                "final_decision": error_decision,
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"売買判断でエラーが発生しました: {e}", name="trading_decision")
                ]
            },
            goto="__end__"
        )


# ヘルパー関数

def _format_chart_images_for_analysis(chart_images: Dict[str, str]) -> str:
    """チャート画像情報を分析用にフォーマット"""
    formatted = []
    for timeframe, image_path in chart_images.items():
        formatted.append(f"- {timeframe}: {image_path}")
    return "\n".join(formatted)


def _format_technical_indicators_for_analysis(technical_indicators: Dict) -> str:
    """テクニカル指標データを分析用にフォーマット"""
    formatted = []
    for timeframe, indicators in technical_indicators.items():
        formatted.append(f"\n### {timeframe.upper()}")
        if isinstance(indicators, dict):
            for indicator, value in indicators.items():
                formatted.append(f"- {indicator}: {value}")
    return "\n".join(formatted)


def _format_chart_analysis_summary(chart_analysis: Dict) -> str:
    """チャート分析結果をサマリー形式でフォーマット"""
    if "error" in chart_analysis:
        return f"エラー: {chart_analysis['error']}"
    
    summary = chart_analysis.get("analysis_summary", "分析結果なし")
    confidence = chart_analysis.get("confidence_score", 0.0)
    return f"信頼度: {confidence:.2f}\n{summary}"


def _format_analysis_summary(analysis_result: Dict) -> str:
    """分析結果をサマリー形式でフォーマット"""
    if "error" in analysis_result:
        return f"エラー: {analysis_result['error']}"
    
    summary = analysis_result.get("analysis_summary", "分析結果なし")
    return summary


def _format_market_context(market_context: Dict) -> str:
    """市場環境データをフォーマット"""
    if not market_context:
        return "市場環境データなし"
    
    formatted = []
    for key, value in market_context.items():
        formatted.append(f"- {key}: {value}")
    return "\n".join(formatted)


def _extract_key_indicators(technical_indicators: Dict) -> Dict:
    """主要テクニカル指標を抽出"""
    key_indicators = {}
    
    for timeframe, indicators in technical_indicators.items():
        if isinstance(indicators, dict):
            # 移動平均線
            if "moving_averages" in indicators:
                key_indicators[f"{timeframe}_ma"] = indicators["moving_averages"]
            
            # VWAP
            if "vwap" in indicators:
                key_indicators[f"{timeframe}_vwap"] = indicators["vwap"]
            
            # ATR
            if "atr14" in indicators:
                key_indicators[f"{timeframe}_atr"] = indicators["atr14"]
    
    return key_indicators