"""
Trading related endpoints
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import pandas as pd

from app.services.minute_decision_engine import MinuteDecisionEngine
from app.services.data_source_router import DataSourceRouter, DataSource
from app.core.auth import get_current_user, get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# データソースルーターのインスタンス
data_router = DataSourceRouter()
# 従来のトレーディングエンジン（後方互換性）
trading_engine = MinuteDecisionEngine(enable_chart_generation=True)

class TradingDecisionRequest(BaseModel):
    """
    Request model for trading decision
    """
    symbol: str
    timestamp: datetime
    use_cache: bool = True

class TradingDecisionResponse(BaseModel):
    """
    Response model for trading decision
    """
    symbol: str
    timestamp: datetime
    current_price: float
    price_change: float
    price_change_percent: float
    volume: int
    market_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    user_authenticated: bool = False

@router.post("/decision", response_model=TradingDecisionResponse)
async def get_trading_decision(
    request: TradingDecisionRequest,
    http_request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> TradingDecisionResponse:
    """
    Get comprehensive trading data for a symbol at specific timestamp
    
    Integrates with MinuteDecisionEngine to provide real-time market data,
    technical indicators, and market context.
    """
    try:
        logger.info(f"トレーディングデータ取得開始: {request.symbol} @ {request.timestamp}")
        
        # MinuteDecisionEngineでデータ取得
        result = trading_engine.get_minute_decision_data(request.symbol, request.timestamp)
        
        # 市場データの整理
        market_data = {
            "indices": {k: {"price": v.price, "change": v.change, "change_percent": v.change_percent} 
                        for k, v in result.market_context.indices.items()},
            "forex": {k: {"price": v.price, "change": v.change, "change_percent": v.change_percent} 
                     for k, v in result.market_context.forex.items()}
        }
        
        # テクニカル指標の整理
        technical_data = {}
        if result.technical_indicators.daily:
            technical_data["daily"] = {
                "ma20": result.technical_indicators.daily.moving_averages.ma20,
                "ma50": result.technical_indicators.daily.moving_averages.ma50,
                "atr14": result.technical_indicators.daily.atr14
            }
        if result.technical_indicators.hourly_60:
            technical_data["hourly_60"] = {
                "vwap": result.technical_indicators.hourly_60.vwap.daily
            }
        
        return TradingDecisionResponse(
            symbol=result.symbol,
            timestamp=result.timestamp,
            current_price=result.current_price.current_price,
            price_change=result.current_price.price_change,
            price_change_percent=result.current_price.price_change_percent,
            volume=result.current_price.current_volume,
            market_data=market_data,
            technical_indicators=technical_data,
            user_authenticated=current_user is not None
        )
        
    except Exception as e:
        logger.error(f"トレーディングデータ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trading data retrieval failed: {str(e)}"
        )

@router.get("/symbols/{symbol}")
async def get_symbol_info(
    symbol: str,
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Get basic information about a trading symbol
    """
    try:
        # 現在時刻でのデータ取得
        current_time = datetime.now()
        result = trading_engine.get_minute_decision_data(symbol, current_time)
        
        return {
            "symbol": result.symbol,
            "name": result.current_price.company_name,
            "market": "JP" if symbol.endswith(".T") else "US",
            "current_price": result.current_price.current_price,
            "price_change": result.current_price.price_change,
            "price_change_percent": result.current_price.price_change_percent,
            "volume": result.current_price.current_volume,
            "status": "active",
            "timestamp": result.timestamp,
            "user_authenticated": current_user is not None
        }
        
    except Exception as e:
        logger.error(f"シンボル情報取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol information not found: {symbol}"
        )

@router.post("/ai-decision")
async def get_ai_trading_decision(
    request: TradingDecisionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get AI-powered trading decision (Premium feature - requires authentication)
    """
    try:
        logger.info(f"AI判断要求開始: {request.symbol} @ {request.timestamp} (User: {current_user['email']})")
        
        # MinuteDecisionEngineでデータ取得
        decision_package = trading_engine.get_minute_decision_data(request.symbol, request.timestamp)
        
        # AI判断システムを使用して分析実行
        try:
            from app.services.ai.ai_trading_decision import AITradingDecisionEngine
            ai_engine = AITradingDecisionEngine()
            ai_result = ai_engine.analyze_trading_decision(decision_package)
            
            return {
                "symbol": request.symbol,
                "timestamp": request.timestamp,
                "ai_decision": ai_result.get("final_decision", "HOLD"),
                "confidence": ai_result.get("confidence_level", 0.5),
                "reasoning": ai_result.get("reasoning", []),
                "risk_factors": ai_result.get("risk_factors", []),
                "strategy_used": ai_result.get("strategy_used", "cautious_hold"),
                "market_outlook": ai_result.get("market_outlook", {}),
                "future_entry_conditions": ai_result.get("future_entry_conditions", {}),
                "analysis_efficiency": ai_result.get("analysis_efficiency", "full_analysis"),
                "processing_time": ai_result.get("processing_time", ""),
                "premium_feature": True,
                "user_id": current_user["id"]
            }
            
        except ImportError as e:
            logger.warning(f"AI判断システムが利用できません: {e}")
            return {
                "symbol": request.symbol,
                "timestamp": request.timestamp,
                "ai_decision": "HOLD",
                "confidence": 0.5,
                "reasoning": ["AI判断システムが一時的に利用できません"],
                "premium_feature": True,
                "user_id": current_user["id"],
                "message": "AI判断システム初期化中（OpenAI APIキー確認が必要）"
            }
        
    except Exception as e:
        logger.error(f"AI判断エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI trading decision failed: {str(e)}"
        )

@router.get("/user/portfolio")
async def get_user_portfolio(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's trading portfolio (Premium feature - requires authentication)
    """
    try:
        # TODO: ユーザーポートフォリオ実装
        return {
            "user_id": current_user["id"],
            "portfolio": {
                "positions": [],
                "total_value": 0.0,
                "daily_pnl": 0.0,
                "total_pnl": 0.0
            },
            "premium_feature": True,
            "message": "ポートフォリオ機能は今後実装予定"
        }
        
    except Exception as e:
        logger.error(f"ポートフォリオ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio retrieval failed: {str(e)}"
        )

class BacktestRequest(BaseModel):
    """
    Request model for backtest execution
    """
    symbol: str
    start_time: datetime
    end_time: datetime
    interval_minutes: int = 5
    max_decisions: int = 20

@router.post("/ai-backtest")
async def run_ai_backtest(
    request: BacktestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run AI-powered backtest over specified time period (Premium feature - requires authentication)
    """
    try:
        logger.info(f"AI バックテスト開始: {request.symbol} {request.start_time} - {request.end_time} (User: {current_user['email']})")
        
        # AI判断エンジンの初期化
        from app.services.ai.ai_trading_decision import AITradingDecisionEngine
        ai_engine = AITradingDecisionEngine()
        
        # 指定期間内の取引時間のみでタイムラインを生成
        timeline = []
        current_date = request.start_time.date()
        end_date = request.end_time.date()
        
        while current_date <= end_date:
            # 平日のみ処理
            if current_date.weekday() < 5:  # 0=月曜日, 6=日曜日
                # その日の9:00から15:00まで、指定間隔で時刻を生成
                market_start = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=0))
                market_end = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=0))
                
                # 指定された期間内の場合のみ追加
                if market_start.date() == request.start_time.date():
                    # 開始日の場合、開始時刻を考慮
                    if request.start_time.time() > market_start.time():
                        if request.start_time.time() <= market_end.time():
                            market_start = request.start_time.replace(second=0, microsecond=0)
                        else:
                            # 開始時刻が15:00を超えている場合はスキップ
                            current_date += timedelta(days=1)
                            continue
                
                if market_end.date() == request.end_time.date():
                    # 終了日の場合、終了時刻を考慮
                    if request.end_time.time() < market_start.time():
                        # 終了時刻が9:00より前の場合はスキップ
                        current_date += timedelta(days=1)
                        continue
                    elif request.end_time.time() < market_end.time():
                        market_end = request.end_time.replace(second=0, microsecond=0)
                
                # 市場時間内で指定間隔ごとにタイムスタンプを生成
                current_time = market_start
                while current_time <= market_end:
                    timeline.append(current_time)
                    current_time += timedelta(minutes=request.interval_minutes)
            
            current_date += timedelta(days=1)
        
        # タイムラインを最大判断回数で制限
        if len(timeline) > request.max_decisions:
            timeline = timeline[:request.max_decisions]
        
        logger.info(f"生成されたタイムライン: {len(timeline)}件 (最初: {timeline[0] if timeline else 'なし'}, 最後: {timeline[-1] if timeline else 'なし'})")
        
        # 時系列でのAI判断実行
        decisions = []
        
        for i, timestamp in enumerate(timeline):
            try:
                # データ取得とAI判断（バックテスト時は強制詳細分析）
                decision_package = trading_engine.get_minute_decision_data(request.symbol, timestamp)
                ai_result = ai_engine.analyze_trading_decision(decision_package, force_full_analysis=True)
                
                # 結果を記録（バックテスト用詳細情報付き）
                decisions.append({
                    "timestamp": timestamp.isoformat(),
                    "price": decision_package.current_price.current_price,
                    "ai_decision": ai_result.get("final_decision", ai_result.get("trading_decision", "HOLD")),
                    "confidence": ai_result.get("confidence_level", ai_result.get("confidence", 0.5)),
                    "reasoning": ai_result.get("reasoning", ai_result.get("reasons", ["分析結果なし"]))[:3],  # 詳細理由3つまで
                    "analysis_efficiency": ai_result.get("analysis_efficiency", "forced_full_analysis"),
                    "strategy_used": ai_result.get("strategy_used", "unknown"), 
                    "risk_factors": ai_result.get("risk_factors", [])[:2],  # リスク要因2つまで
                    "market_outlook": ai_result.get("market_outlook", {}),
                    "trigger_reason": ai_result.get("trigger_reason", "backtest_forced")
                })
                
                # プログレス情報
                if (i + 1) % 5 == 0:
                    logger.info(f"バックテスト進捗: {i + 1}/{len(timeline)}")
                
            except Exception as e:
                logger.warning(f"時刻 {timestamp} でのAI判断失敗: {e}")
                continue
        
        # 統計情報の計算
        buy_count = sum(1 for d in decisions if d["ai_decision"] == "BUY")
        sell_count = sum(1 for d in decisions if d["ai_decision"] == "SELL")
        hold_count = sum(1 for d in decisions if d["ai_decision"] == "HOLD")
        avg_confidence = sum(d["confidence"] for d in decisions) / len(decisions) if decisions else 0
        
        return {
            "symbol": request.symbol,
            "backtest_period": {
                "start": request.start_time.isoformat(),
                "end": request.end_time.isoformat(),
                "interval_minutes": request.interval_minutes
            },
            "statistics": {
                "total_decisions": len(decisions),
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "hold_signals": hold_count,
                "average_confidence": round(avg_confidence, 3)
            },
            "decisions": decisions,
            "premium_feature": True,
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"AIバックテストエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI backtest failed: {str(e)}"
        )

# === データソースルーター統合エンドポイント ===

@router.get("/data-sources/status")
async def get_data_sources_status(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    データソース状態確認
    """
    try:
        status_info = await data_router.get_data_source_status()
        status_info["user_authenticated"] = current_user is not None
        return status_info
        
    except Exception as e:
        logger.error(f"データソース状態取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data source status check failed: {str(e)}"
        )

@router.post("/realtime/price")
async def get_realtime_price(
    request: TradingDecisionRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    リアルタイム価格取得（データソース自動選択）
    """
    try:
        # データソース自動選択で価格取得
        price_data = await data_router.get_current_price(request.symbol, DataSource.AUTO)
        
        return {
            "symbol": request.symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": price_data.current_price,
            "price_change": price_data.price_change,
            "price_change_percent": price_data.price_change_percent,
            "volume": price_data.volume,
            "source": "auto_selected",
            "user_authenticated": current_user is not None
        }
        
    except Exception as e:
        logger.error(f"リアルタイム価格取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Realtime price retrieval failed: {str(e)}"
        )

@router.post("/hybrid/decision")
async def get_hybrid_trading_decision(
    request: TradingDecisionRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    ハイブリッドトレーディングデータ取得
    （立花証券リアルタイム価格 + yfinance分析データ）
    """
    try:
        logger.info(f"ハイブリッドデータ要求: {request.symbol} @ {request.timestamp}")
        
        # データソースルーターでハイブリッドデータ取得
        decision_package = await data_router.get_trading_data(
            request.symbol, 
            request.timestamp,
            DataSource.AUTO
        )
        
        return {
            "symbol": decision_package.symbol,
            "timestamp": decision_package.timestamp.isoformat(),
            "current_price": decision_package.current_price.current_price,
            "price_change": decision_package.current_price.price_change,
            "price_change_percent": decision_package.current_price.price_change_percent,
            "volume": decision_package.current_price.volume,
            "market_data": {
                "indices": decision_package.market_context.indices if decision_package.market_context else {},
                "forex": decision_package.market_context.forex_rates if decision_package.market_context else {}
            },
            "technical_indicators": {
                timeframe: getattr(decision_package.technical_indicators, timeframe, {})
                for timeframe in ["daily", "hourly_60", "minute_15", "minute_5", "minute_1"]
            },
            "data_source": "hybrid",
            "user_authenticated": current_user is not None
        }
        
    except Exception as e:
        logger.error(f"ハイブリッドデータ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid trading data retrieval failed: {str(e)}"
        )

class HistoricalDataRequest(BaseModel):
    """
    Request model for historical price data
    """
    symbol: str
    period: str = "1mo"  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: str = "1d"  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

@router.post("/historical")
async def get_historical_data(
    request: HistoricalDataRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Get historical price data for charts
    """
    try:
        import yfinance as yf
        logger.info(f"履歴データ取得: {request.symbol} period={request.period} interval={request.interval}")
        
        # yfinanceでデータ取得
        ticker = yf.Ticker(request.symbol)
        hist = ticker.history(period=request.period, interval=request.interval)
        
        if hist.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for {request.symbol}"
            )
        
        # チャート用データに変換
        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "timestamp": index.isoformat(),
                "date": index.strftime("%Y-%m-%d"),
                "time": index.strftime("%H:%M"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
            })
        
        return {
            "symbol": request.symbol,
            "period": request.period,
            "interval": request.interval,
            "data_points": len(chart_data),
            "chart_data": chart_data,
            "user_authenticated": current_user is not None
        }
        
    except Exception as e:
        logger.error(f"履歴データ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical data retrieval failed: {str(e)}"
        )