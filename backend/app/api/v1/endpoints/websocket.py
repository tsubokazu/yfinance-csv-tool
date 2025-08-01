"""
WebSocketライブ配信エンドポイント
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.websockets import WebSocketState

from app.services.data_source_router import DataSourceRouter, DataSource
from app.core.auth import get_current_user_from_token

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        # 接続管理
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}
        self.symbol_subscribers: Dict[str, Set[WebSocket]] = {}
        
        # データソースルーター
        self.data_router = DataSourceRouter()
        self.router_initialized = False
        
        # ライブ配信状態
        self.is_streaming = False
        self.streaming_symbols: Set[str] = set()
        
    async def initialize(self):
        """接続マネージャー初期化"""
        if not self.router_initialized:
            await self.data_router.initialize()
            self.router_initialized = True
            logger.info("WebSocket接続マネージャー初期化完了")
            
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> bool:
        """
        WebSocket接続を受け入れ
        
        Args:
            websocket: WebSocket接続
            user_id: ユーザーID（認証済みの場合）
            
        Returns:
            bool: 接続成功時True
        """
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            if user_id:
                self.user_connections[user_id] = websocket
                
            logger.info(f"WebSocket接続確立: {websocket.client.host} (User: {user_id})")
            
            # 接続確認メッセージ送信
            await websocket.send_json({
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "authenticated": user_id is not None,
                "user_id": user_id,
                "available_streams": ["price", "ai_decision", "market_status"]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket接続エラー: {str(e)}")
            return False
            
    async def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """
        WebSocket接続を切断
        
        Args:
            websocket: WebSocket接続
            user_id: ユーザーID
        """
        try:
            # 接続リストから削除
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
            if user_id and user_id in self.user_connections:
                del self.user_connections[user_id]
                
            # シンボル購読から削除
            for symbol, subscribers in self.symbol_subscribers.items():
                if websocket in subscribers:
                    subscribers.remove(websocket)
                    
            logger.info(f"WebSocket切断完了: {websocket.client.host} (User: {user_id})")
            
        except Exception as e:
            logger.error(f"WebSocket切断エラー: {str(e)}")
            
    async def subscribe_symbol(self, websocket: WebSocket, symbol: str):
        """
        銘柄購読開始
        
        Args:
            websocket: WebSocket接続
            symbol: 銘柄コード
        """
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
            
        self.symbol_subscribers[symbol].add(websocket)
        self.streaming_symbols.add(symbol)
        
        logger.info(f"銘柄購読開始: {symbol} (購読者: {len(self.symbol_subscribers[symbol])})")
        
        # 購読確認メッセージ
        await websocket.send_json({
            "type": "subscription_confirmed",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
        # ライブストリーミング開始
        if not self.is_streaming:
            asyncio.create_task(self.start_price_streaming())
            
    async def unsubscribe_symbol(self, websocket: WebSocket, symbol: str):
        """
        銘柄購読停止
        
        Args:
            websocket: WebSocket接続
            symbol: 銘柄コード
        """
        if symbol in self.symbol_subscribers and websocket in self.symbol_subscribers[symbol]:
            self.symbol_subscribers[symbol].remove(websocket)
            
            # 購読者がいなくなった場合
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]
                self.streaming_symbols.discard(symbol)
                
        logger.info(f"銘柄購読停止: {symbol}")
        
        await websocket.send_json({
            "type": "unsubscription_confirmed", 
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
    async def broadcast_to_symbol(self, symbol: str, data: Dict[str, Any]):
        """
        銘柄購読者への一斉配信
        
        Args:
            symbol: 銘柄コード
            data: 配信データ
        """
        if symbol not in self.symbol_subscribers:
            return
            
        disconnected_connections = []
        
        for websocket in self.symbol_subscribers[symbol].copy():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(data)
                else:
                    disconnected_connections.append(websocket)
            except Exception as e:
                logger.warning(f"配信エラー: {str(e)}")
                disconnected_connections.append(websocket)
                
        # 切断された接続を削除
        for websocket in disconnected_connections:
            self.symbol_subscribers[symbol].discard(websocket)
            
    async def broadcast_to_all(self, data: Dict[str, Any]):
        """
        全接続への一斉配信
        
        Args:
            data: 配信データ
        """
        disconnected_connections = []
        
        for websocket in self.active_connections.copy():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(data)
                else:
                    disconnected_connections.append(websocket)
            except Exception as e:
                logger.warning(f"一斉配信エラー: {str(e)}")
                disconnected_connections.append(websocket)
                
        # 切断された接続を削除
        for websocket in disconnected_connections:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
    async def start_price_streaming(self):
        """価格ライブストリーミング開始"""
        if self.is_streaming:
            return
            
        self.is_streaming = True
        logger.info("価格ライブストリーミング開始")
        
        try:
            while self.streaming_symbols and self.active_connections:
                # 各シンボルの価格を取得して配信
                for symbol in self.streaming_symbols.copy():
                    try:
                        # データソースルーターで価格取得
                        price_data = await self.data_router.get_current_price(symbol, DataSource.AUTO)
                        
                        # WebSocket配信
                        stream_data = {
                            "type": "price_update",
                            "symbol": symbol,
                            "timestamp": datetime.now().isoformat(),
                            "current_price": price_data.current_price,
                            "price_change": price_data.price_change,
                            "price_change_percent": price_data.price_change_percent,
                            "volume": price_data.volume,
                            "source": "live_stream"
                        }
                        
                        await self.broadcast_to_symbol(symbol, stream_data)
                        
                    except Exception as e:
                        logger.warning(f"価格ストリーミングエラー [{symbol}]: {str(e)}")
                        # エラーメッセージを送信
                        error_data = {
                            "type": "price_update_error",
                            "symbol": symbol,
                            "timestamp": datetime.now().isoformat(),
                            "error": str(e),
                            "source": "live_stream"
                        }
                        await self.broadcast_to_symbol(symbol, error_data)
                        # エラーが続く場合は少し間隔を空ける
                        continue
                        
                # 配信間隔（調整可能）
                await asyncio.sleep(2.0)  # 2秒間隔
                
        except Exception as e:
            logger.error(f"ライブストリーミングエラー: {str(e)}")
        finally:
            self.is_streaming = False
            logger.info("価格ライブストリーミング停止")
            
    async def get_status(self) -> Dict[str, Any]:
        """接続マネージャー状態取得"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(self.active_connections),
            "authenticated_users": len(self.user_connections),
            "streaming_symbols": list(self.streaming_symbols),
            "is_streaming": self.is_streaming,
            "data_router_status": await self.data_router.get_data_source_status()
        }

# グローバル接続マネージャーインスタンス
connection_manager = ConnectionManager()

@router.websocket("/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    ライブデータ配信WebSocketエンドポイント（認証不要）
    """
    await connection_manager.initialize()
    
    if not await connection_manager.connect(websocket):
        return
        
    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe":
                symbol = data.get("symbol")
                if symbol:
                    await connection_manager.subscribe_symbol(websocket, symbol)
                    
            elif message_type == "unsubscribe":
                symbol = data.get("symbol")
                if symbol:
                    await connection_manager.unsubscribe_symbol(websocket, symbol)
                    
            elif message_type == "status":
                status = await connection_manager.get_status()
                await websocket.send_json({
                    "type": "status_response",
                    "data": status
                })
                
            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocketエラー: {str(e)}")
        await connection_manager.disconnect(websocket)

@router.websocket("/live/authenticated")
async def websocket_authenticated_endpoint(websocket: WebSocket):
    """
    認証済みライブデータ配信WebSocketエンドポイント
    """
    await connection_manager.initialize()
    
    # クエリパラメータからトークンを取得
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Token required")
            return
            
        user = await get_current_user_from_token(token)
        user_id = user.get("id")
    except Exception as e:
        logger.error(f"WebSocket認証エラー: {str(e)}")
        await websocket.close(code=4001, reason="Authentication failed")
        return
        
    if not await connection_manager.connect(websocket, user_id):
        return
        
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe":
                symbol = data.get("symbol")
                if symbol:
                    await connection_manager.subscribe_symbol(websocket, symbol)
                    
            elif message_type == "ai_decision_request":
                # AI判断リクエスト（認証済みユーザーのみ）
                symbol = data.get("symbol")
                if symbol:
                    try:
                        # AI判断実行とリアルタイム配信
                        decision_data = await connection_manager.data_router.get_trading_data(
                            symbol, 
                            datetime.now(),
                            DataSource.AUTO
                        )
                        
                        # AI判断結果をリアルタイム配信
                        ai_response = {
                            "type": "ai_decision_result",
                            "symbol": symbol,
                            "timestamp": datetime.now().isoformat(),
                            "decision_data": decision_data.__dict__,
                            "premium_feature": True,
                            "user_id": user_id
                        }
                        
                        await websocket.send_json(ai_response)
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "ai_decision_error",
                            "symbol": symbol,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                        
            elif message_type == "unsubscribe":
                symbol = data.get("symbol")
                if symbol:
                    await connection_manager.unsubscribe_symbol(websocket, symbol)
                    
            elif message_type == "status":
                status = await connection_manager.get_status()
                await websocket.send_json({
                    "type": "status_response",
                    "data": status
                })
                
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"認証WebSocketエラー: {str(e)}")
        await connection_manager.disconnect(websocket, user_id)

@router.get("/websocket/status")
async def get_websocket_status() -> Dict[str, Any]:
    """
    WebSocket状態確認エンドポイント
    """
    try:
        await connection_manager.initialize()
        return await connection_manager.get_status()
    except Exception as e:
        logger.error(f"WebSocket状態取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WebSocket status check failed: {str(e)}"
        )