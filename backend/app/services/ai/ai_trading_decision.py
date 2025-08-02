#!/usr/bin/env python3
"""
AI トレーディング判断システム

LangGraphを使用したマルチエージェントワークフローで
チャート分析・テクニカル分析・売買判断を順次実行します。

使用方法:
1. MinuteDecisionPackageデータを入力
2. チャート分析 → テクニカル分析 → 売買判断の順で実行
3. 最終的な売買判断結果を取得
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState

from app.core.data_models import MinuteDecisionPackage, ChartImages
from app.services.ai.trading_agents import (
    chart_analyst_node,
    technical_analyst_node, 
    trading_decision_node
)
from app.services.efficiency.trading_continuity_engine import TradingContinuityEngine

logger = logging.getLogger(__name__)


class TradingDecisionState(MessagesState):
    """
    トレーディング判断ワークフローの状態管理
    
    LangGraphワークフロー内で共有される状態データ
    """
    # 入力データ
    symbol: str
    timestamp: str
    current_price: float
    chart_images: Dict[str, str]
    technical_indicators: Dict[str, Any]
    market_context: Dict[str, Any]
    
    # 中間結果
    chart_analysis_result: Optional[Dict[str, Any]] = None
    technical_analysis_result: Optional[Dict[str, Any]] = None
    
    # 最終結果
    final_decision: Optional[Dict[str, Any]] = None


class AITradingDecisionEngine:
    """
    AIトレーディング判断エンジン
    
    LangGraphワークフローを管理し、
    バックテストデータから売買判断を生成します。
    """
    
    def __init__(self, enable_logging: bool = True, ai_provider: str = None, ai_model: str = None):
        """
        初期化
        
        Args:
            enable_logging: ログ出力を有効にするか
            ai_provider: 使用するAIプロバイダー ("openai" または "gemini")
            ai_model: 使用するAIモデル名
        """
        self.enable_logging = enable_logging
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self._setup_logging()
        self._workflow = self._build_workflow()
        self.continuity_engine = TradingContinuityEngine()
        
        provider_info = f" (Provider: {ai_provider}, Model: {ai_model})" if ai_provider else ""
        logger.info(f"🤖 AIトレーディング判断エンジン初期化完了{provider_info}")
    
    def _setup_logging(self):
        """ログ設定"""
        if self.enable_logging:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # LangGraphとエージェント用のログ設定
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(log_dir / 'ai_trading_decision.log')
                ]
            )
    
    def _build_workflow(self) -> StateGraph:
        """
        LangGraphワークフローを構築
        
        Returns:
            コンパイル済みワークフロー
        """
        # 動的エージェント作成用のカスタムノード関数を作成
        from .trading_agents import (
            create_chart_analyst_agent,
            create_technical_analyst_agent, 
            create_trading_decision_agent
        )
        
        def dynamic_chart_analyst_node(state):
            """AIプロバイダー対応チャート分析ノード"""
            # ワークフロー実行時にプロバイダー情報を取得
            ai_provider = getattr(self, 'ai_provider', None)
            ai_model = getattr(self, 'ai_model', None)
            
            # 動的にエージェントを作成
            dynamic_agent = create_chart_analyst_agent(ai_provider, ai_model)
            
            # 既存のノード処理をコピー
            from .trading_agents import chart_analyst_node
            import types
            
            # グローバルエージェントを一時的に置換
            original_agent = None
            try:
                import app.services.ai.trading_agents as agents_module
                original_agent = agents_module.chart_analyst_agent
                agents_module.chart_analyst_agent = dynamic_agent
                
                return chart_analyst_node(state)
            finally:
                if original_agent:
                    agents_module.chart_analyst_agent = original_agent
        
        def dynamic_technical_analyst_node(state):
            """AIプロバイダー対応テクニカル分析ノード"""
            ai_provider = getattr(self, 'ai_provider', None)
            ai_model = getattr(self, 'ai_model', None)
            
            dynamic_agent = create_technical_analyst_agent(ai_provider, ai_model)
            
            from .trading_agents import technical_analyst_node
            original_agent = None
            try:
                import app.services.ai.trading_agents as agents_module
                original_agent = agents_module.technical_analyst_agent
                agents_module.technical_analyst_agent = dynamic_agent
                
                return technical_analyst_node(state)
            finally:
                if original_agent:
                    agents_module.technical_analyst_agent = original_agent
        
        def dynamic_trading_decision_node(state):
            """AIプロバイダー対応売買判断ノード"""
            ai_provider = getattr(self, 'ai_provider', None)
            ai_model = getattr(self, 'ai_model', None)
            
            dynamic_agent = create_trading_decision_agent(ai_provider, ai_model)
            
            from .trading_agents import trading_decision_node
            original_agent = None
            try:
                import app.services.ai.trading_agents as agents_module
                original_agent = agents_module.trading_decision_agent
                agents_module.trading_decision_agent = dynamic_agent
                
                return trading_decision_node(state)
            finally:
                if original_agent:
                    agents_module.trading_decision_agent = original_agent
        
        # ワークフローグラフの定義
        workflow = StateGraph(TradingDecisionState)
        
        # 動的ノードの追加
        workflow.add_node("chart_analyst", dynamic_chart_analyst_node)
        workflow.add_node("technical_analyst", dynamic_technical_analyst_node)
        workflow.add_node("trading_decision", dynamic_trading_decision_node)
        
        # エッジの定義 (実行フロー)
        workflow.add_edge(START, "chart_analyst")
        # chart_analyst_node 内で technical_analyst への遷移を制御
        # technical_analyst_node 内で trading_decision への遷移を制御
        # trading_decision_node 内で END への遷移を制御
        workflow.add_edge("trading_decision", END)
        
        # ワークフローのコンパイル
        compiled_workflow = workflow.compile()
        
        provider_info = f" (Provider: {self.ai_provider}, Model: {self.ai_model})" if self.ai_provider else ""
        logger.info(f"📊 LangGraphワークフロー構築完了{provider_info}")
        return compiled_workflow
    
    def analyze_trading_decision(
        self, 
        decision_package: MinuteDecisionPackage,
        force_full_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        トレーディング判断分析を実行
        
        Args:
            decision_package: バックテストデータパッケージ
            
        Returns:
            AI売買判断結果
        """
        try:
            symbol = decision_package.symbol
            current_time = decision_package.timestamp
            
            logger.info(f"🎯 AI売買判断開始: {symbol} @ {current_time}")
            
            # 効率化分析プランを取得（バックテスト時はキャッシュ無効化）
            if force_full_analysis:
                # バックテスト時はキャッシュを無効化して全時間軸を強制更新
                logger.info("🚫 バックテスト時キャッシュクリア: 全時間軸を強制分析")
                analysis_plan = {
                    "analysis_type": "forced_full_analysis",
                    "timeframes_to_update": ["weekly", "daily", "hourly_60", "minute_15", "minute_5", "minute_1"],
                    "trading_state": None
                }
            else:
                analysis_plan = self.continuity_engine.get_incremental_analysis_plan(symbol, current_time)
            
            logger.info(f"📋 分析プラン: {analysis_plan['analysis_type']} (更新対象: {len(analysis_plan['timeframes_to_update'])}時間軸)")
            
            # 継続性分析を実行（バックテスト時は強制フル分析）
            if force_full_analysis:
                # バックテスト時は継続性判断を無効化し、常にフル分析を実行
                continuity_result = {"requires_full_analysis": True, "trigger_reason": "backtest_forced"}
            else:
                continuity_result = self.continuity_engine.execute_incremental_analysis(
                    analysis_plan,
                    decision_package.current_price.current_price,
                    self._prepare_market_context(decision_package)
                )
            
            # フル分析が不要な場合は継続結果を返す（バックテスト時は強制実行）
            if not continuity_result.get("requires_full_analysis", False) and not force_full_analysis:
                logger.info("♻️ 継続判断を採用、フル分析をスキップ")
                
                final_decision = continuity_result.get("decision_continuation", {})
                # 基本情報を追加
                final_decision.update({
                    "timestamp": current_time.isoformat(),
                    "symbol": symbol,
                    "current_price": decision_package.current_price.current_price,
                    "analysis_efficiency": "continuity_based",
                    "ai_engine_version": "1.1.0_optimized",
                    "processing_time": datetime.now().isoformat(),
                    "workflow_status": "efficiency_optimized"
                })
                
                # 将来エントリー条件を維持
                if "future_entry_conditions" not in final_decision:
                    trading_state = analysis_plan.get("trading_state")
                    if trading_state:
                        final_decision["future_entry_conditions"] = trading_state.active_conditions
                
                return final_decision
            
            # フル分析が必要な場合は従来のワークフローを実行
            if force_full_analysis:
                logger.info("🔍 バックテスト強制分析モード: フル分析を実行")
            else:
                logger.info("🔍 フル分析を実行...")
            
            # 入力データの準備（バックテスト時はキャッシュ無効化）
            initial_state = self._prepare_initial_state(decision_package, disable_cache=force_full_analysis)
            
            # ワークフロー実行
            result = self._workflow.invoke(initial_state)
            
            # 結果の処理
            final_decision = self._process_workflow_result(result)
            
            # チャート分析が完了した時間軸をキャッシュに記録
            if result.get("chart_analysis_result"):
                # 分析が完了した時間軸をキャッシュに保存
                for timeframe in analysis_plan.get("timeframes_to_update", []):
                    # 分析完了フラグとして簡易的なデータを保存
                    analysis_summary = {
                        "analyzed": True,
                        "timestamp": current_time.isoformat(),
                        "price_at_analysis": decision_package.current_price.current_price
                    }
                    self.continuity_engine.chart_cache.update_analysis(
                        symbol, timeframe, analysis_summary, current_time
                    )
                logger.info(f"✅ {len(analysis_plan.get('timeframes_to_update', []))}時間軸の分析完了をキャッシュに記録")
            
            # 将来エントリー条件とマーケット分析を追加
            self._add_future_analysis(final_decision, initial_state)
            
            # 効率化情報を追加
            final_decision["analysis_efficiency"] = "full_analysis"
            final_decision["trigger_reason"] = continuity_result.get("trigger_reason", "scheduled_review")
            
            # トレーディング状態を更新
            self.continuity_engine.update_trading_state(symbol, final_decision, current_time)
            
            logger.info(f"✅ AI売買判断完了: {final_decision.get('trading_decision', 'ERROR')}")
            return final_decision
            
        except Exception as e:
            logger.error(f"❌ AI売買判断エラー: {e}")
            return self._create_error_response(str(e), decision_package)
    
    def _prepare_initial_state(self, decision_package: MinuteDecisionPackage, disable_cache: bool = False) -> Dict[str, Any]:
        """
        ワークフロー初期状態を準備
        
        Args:
            decision_package: 判断データパッケージ
            
        Returns:
            初期状態データ
        """
        # チャート画像パスの抽出
        chart_images = {}
        if decision_package.chart_images:
            chart_images = self._extract_chart_image_paths(decision_package.chart_images)
        
        # テクニカル指標データの変換
        technical_indicators = {}
        if decision_package.technical_indicators:
            technical_indicators = self._convert_technical_indicators(
                decision_package.technical_indicators
            )
        
        # 市場環境データの準備
        market_context = self._prepare_market_context(decision_package)
        
        initial_state = {
            "messages": [
                HumanMessage(content=f"銘柄 {decision_package.symbol} の売買判断分析を開始します")
            ],
            "symbol": decision_package.symbol,
            "timestamp": decision_package.timestamp.isoformat(),
            "current_price": decision_package.current_price.current_price,
            "chart_images": chart_images,
            "technical_indicators": technical_indicators,
            "market_context": market_context
        }
        
        logger.debug(f"初期状態準備完了: {len(chart_images)}枚のチャート, {len(technical_indicators)}時間軸")
        return initial_state
    
    def _extract_chart_image_paths(self, chart_images: ChartImages) -> Dict[str, str]:
        """
        チャート画像オブジェクトからパス情報を抽出
        
        Args:
            chart_images: チャート画像オブジェクト
            
        Returns:
            時間軸別画像パス辞書
        """
        image_paths = {}
        
        # 各時間軸のチャート画像パス取得
        timeframes = ['weekly', 'daily', 'hourly_60', 'minute_15', 'minute_5', 'minute_1']
        
        for timeframe in timeframes:
            chart_data = getattr(chart_images, timeframe, None)
            if chart_data and hasattr(chart_data, 'imagePath'):
                image_path = Path(chart_data.imagePath)
                if image_path.exists():
                    image_paths[timeframe] = str(image_path)
                else:
                    logger.warning(f"チャート画像が存在しません: {timeframe} - {image_path}")
        
        return image_paths
    
    def _convert_technical_indicators(self, technical_indicators) -> Dict[str, Any]:
        """
        テクニカル指標オブジェクトを辞書形式に変換
        
        Args:
            technical_indicators: テクニカル指標オブジェクト
            
        Returns:
            時間軸別テクニカル指標辞書
        """
        indicators_dict = {}
        
        # 各時間軸のテクニカル指標を辞書に変換
        timeframes = ['weekly', 'daily', 'hourly_60', 'minute_15', 'minute_5', 'minute_1']
        
        for timeframe in timeframes:
            timeframe_data = getattr(technical_indicators, timeframe, None)
            if timeframe_data:
                indicators_dict[timeframe] = self._timeframe_indicators_to_dict(timeframe_data)
        
        return indicators_dict
    
    def _timeframe_indicators_to_dict(self, timeframe_data) -> Dict[str, Any]:
        """
        単一時間軸のテクニカル指標を辞書に変換
        
        Args:
            timeframe_data: 時間軸別テクニカル指標データ
            
        Returns:
            指標辞書
        """
        indicators = {}
        
        # 移動平均線
        if hasattr(timeframe_data, 'moving_averages'):
            ma_data = timeframe_data.moving_averages
            indicators['moving_averages'] = {
                attr: getattr(ma_data, attr) 
                for attr in dir(ma_data) 
                if not attr.startswith('_') and getattr(ma_data, attr) is not None
            }
        
        # VWAP
        if hasattr(timeframe_data, 'vwap'):
            vwap_data = timeframe_data.vwap
            indicators['vwap'] = {
                attr: getattr(vwap_data, attr)
                for attr in dir(vwap_data)
                if not attr.startswith('_') and getattr(vwap_data, attr) is not None
            }
        
        # ボリンジャーバンド
        if hasattr(timeframe_data, 'bollinger_bands'):
            bb_data = timeframe_data.bollinger_bands
            indicators['bollinger_bands'] = {
                attr: getattr(bb_data, attr)
                for attr in dir(bb_data)
                if not attr.startswith('_') and getattr(bb_data, attr) is not None
            }
        
        # ATR
        if hasattr(timeframe_data, 'atr14'):
            indicators['atr14'] = timeframe_data.atr14
        
        # 出来高プロファイル
        if hasattr(timeframe_data, 'volume_profile'):
            vp_data = timeframe_data.volume_profile
            indicators['volume_profile'] = {
                attr: getattr(vp_data, attr)
                for attr in dir(vp_data)
                if not attr.startswith('_') and getattr(vp_data, attr) is not None
            }
        
        return indicators
    
    def _prepare_market_context(self, decision_package: MinuteDecisionPackage) -> Dict[str, Any]:
        """
        市場環境データを準備
        
        Args:
            decision_package: 判断データパッケージ
            
        Returns:
            市場環境辞書
        """
        market_context = {
            "price_change_percent": decision_package.current_price.price_change_percent,
            "volume_ratio": decision_package.current_price.volume_ratio,
            "timestamp": decision_package.timestamp.isoformat(),
            "symbol": decision_package.symbol
        }
        
        # 追加の市場データがあれば追加
        if hasattr(decision_package, 'market_context') and decision_package.market_context:
            market_context.update(decision_package.market_context.__dict__)
        
        return market_context
    
    def _add_future_analysis(self, final_decision: Dict[str, Any], initial_state: Dict[str, Any]) -> None:
        """
        将来エントリー条件とマーケット分析を追加
        
        Args:
            final_decision: AI判断結果
            initial_state: ワークフロー初期状態
        """
        try:
            from app.services.ai.trading_tools import _generate_future_entry_conditions, _analyze_market_outlook
            
            # 必要なデータの取得
            technical_analysis = initial_state.get("technical_indicators", {})
            market_context = initial_state.get("market_context", {})
            current_price = initial_state.get("current_price", 0)
            current_decision = final_decision.get("trading_decision", "HOLD")
            
            # 将来エントリー条件の生成
            future_conditions = _generate_future_entry_conditions(
                technical_analysis, current_price, current_decision
            )
            final_decision["future_entry_conditions"] = future_conditions
            
            # マーケット見通し分析
            market_outlook = _analyze_market_outlook(
                technical_analysis, market_context, current_decision
            )
            final_decision["market_outlook"] = market_outlook
            
            logger.info(f"✅ 将来エントリー条件とマーケット分析を追加完了")
            
        except Exception as e:
            logger.warning(f"将来分析の追加に失敗: {e}")
            # デフォルト値を設定
            final_decision["future_entry_conditions"] = {
                "buy_conditions": ["データ不足のため分析不可"],
                "sell_conditions": ["データ不足のため分析不可"],
                "watch_levels": {},
                "timeframe_focus": [],
                "next_review_trigger": "次回市場オープン時"
            }
            final_decision["market_outlook"] = {
                "market_phase": "分析不可",
                "trend_strength": "不明",
                "recommended_strategy": "様子見",
                "patience_level": "高",
                "action_urgency": "低",
                "monitoring_frequency": "日足で十分"
            }
    
    def _process_workflow_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        ワークフロー実行結果を処理
        
        Args:
            result: ワークフロー実行結果
            
        Returns:
            処理済み売買判断結果
        """
        final_decision = result.get("final_decision", {})
        
        if not final_decision or "error" in final_decision:
            error_msg = final_decision.get("error", "不明なエラー")
            logger.error(f"ワークフロー実行エラー: {error_msg}")
            return self._create_error_response(error_msg)
        
        # 追加のメタデータを付与
        final_decision["ai_engine_version"] = "1.0.0"
        final_decision["processing_time"] = datetime.now().isoformat()
        final_decision["workflow_status"] = "completed"
        
        # メッセージログの要約
        messages = result.get("messages", [])
        final_decision["agent_messages"] = [
            {
                "agent": getattr(msg, 'name', 'unknown'),
                "timestamp": datetime.now().isoformat(),
                "content_preview": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            }
            for msg in messages[-6:]  # 最新6メッセージを保持
        ]
        
        return final_decision
    
    def _create_error_response(
        self, 
        error_message: str, 
        decision_package: Optional[MinuteDecisionPackage] = None
    ) -> Dict[str, Any]:
        """
        エラーレスポンスを作成
        
        Args:
            error_message: エラーメッセージ
            decision_package: 元のデータパッケージ（オプション）
            
        Returns:
            エラーレスポンス
        """
        error_response = {
            "timestamp": datetime.now().isoformat(),
            "trading_decision": "ERROR",
            "confidence_level": 0.0,
            "error": error_message,
            "workflow_status": "failed",
            "ai_engine_version": "1.0.0"
        }
        
        if decision_package:
            error_response.update({
                "symbol": decision_package.symbol,
                "original_timestamp": decision_package.timestamp.isoformat(),
                "current_price": decision_package.current_price.current_price
            })
        
        return error_response
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        ワークフロー情報を取得
        
        Returns:
            ワークフロー情報
        """
        return {
            "engine_version": "1.0.0",
            "workflow_type": "multi_agent_trading_decision",
            "agents": [
                "chart_analyst", 
                "technical_analyst", 
                "trading_decision"
            ],
            "execution_order": [
                "START → chart_analyst",
                "chart_analyst → technical_analyst", 
                "technical_analyst → trading_decision",
                "trading_decision → END"
            ],
            "required_inputs": [
                "symbol", "timestamp", "current_price",
                "chart_images", "technical_indicators"
            ],
            "output_format": "trading_decision_json"
        }


# 使用例とテスト用関数

def test_ai_trading_decision():
    """
    AIトレーディング判断システムのテスト
    """
    print("🧪 AIトレーディング判断システムテスト開始")
    
    # エンジン初期化
    engine = AITradingDecisionEngine(enable_logging=True)
    
    # ワークフロー情報表示
    workflow_info = engine.get_workflow_info()
    print(f"📊 ワークフロー情報: {workflow_info}")
    
    print("✅ AIトレーディング判断システムテスト完了")


if __name__ == "__main__":
    # 環境変数チェック
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is required")
        print("💡 Set your OpenAI API key: export OPENAI_API_KEY='your-api-key'")
        exit(1)
    
    # テスト実行
    test_ai_trading_decision()