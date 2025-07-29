"""
Trading related endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
import logging

from app.services.minute_decision_engine import MinuteDecisionEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# トレーディングエンジンのインスタンス
trading_engine = MinuteDecisionEngine()

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

@router.post("/decision", response_model=TradingDecisionResponse)
async def get_trading_decision(request: TradingDecisionRequest) -> TradingDecisionResponse:
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
            technical_indicators=technical_data
        )
        
    except Exception as e:
        logger.error(f"トレーディングデータ取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trading data retrieval failed: {str(e)}"
        )

@router.get("/symbols/{symbol}")
async def get_symbol_info(symbol: str) -> Dict[str, Any]:
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
            "timestamp": result.timestamp
        }
        
    except Exception as e:
        logger.error(f"シンボル情報取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol information not found: {symbol}"
        )