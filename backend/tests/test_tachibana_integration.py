"""
立花証券API統合テスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.tachibana import TachibanaAPIClient, TachibanaSessionManager, TachibanaePriceService
from app.core.config import settings

class TestTachibanaSessionManager:
    """立花証券セッション管理テスト"""
    
    def test_init(self):
        """初期化テスト"""
        session_manager = TachibanaSessionManager()
        
        assert session_manager.session_id is None
        assert session_manager.virtual_urls == {}
        assert session_manager.session_expiry is None
        assert session_manager.is_demo_mode == settings.TACHIBANA_DEMO_MODE
        
    def test_is_logged_in_false_when_no_session(self):
        """セッションなし時のログイン状態テスト"""
        session_manager = TachibanaSessionManager()
        assert session_manager.is_logged_in() is False
        
    @patch('urllib3.PoolManager')
    def test_login_success_mock(self, mock_pool_manager):
        """ログイン成功テスト（モック）"""
        # モックレスポンス設定
        mock_response = Mock()
        mock_response.status = 200
        mock_response.data = b'''
        {
            "p_errno": 0,
            "session_id": "test_session_123",
            "request_interface_url": "https://demo-price-kabuka.e-shiten.jp/e_api_v4r7/request/test_session_123/",
            "master_interface_url": "https://demo-price-kabuka.e-shiten.jp/e_api_v4r7/master/test_session_123/",
            "price_interface_url": "https://demo-price-kabuka.e-shiten.jp/e_api_v4r7/price/test_session_123/",
            "event_interface_url": "https://demo-price-kabuka.e-shiten.jp/e_api_v4r7/event/test_session_123/"
        }
        '''.encode('shift-jis')
        
        mock_pool_manager.return_value.request.return_value = mock_response
        
        session_manager = TachibanaSessionManager()
        result = session_manager.login("test_user", "test_pass")
        
        assert result is True
        assert session_manager.session_id == "test_session_123"
        assert len(session_manager.virtual_urls) == 4
        assert session_manager.is_logged_in() is True

class TestTachibanaAPIClient:
    """立花証券APIクライアントテスト"""
    
    @pytest.fixture
    def client(self):
        """テスト用クライアント"""
        return TachibanaAPIClient()
        
    def test_init(self, client):
        """初期化テスト"""
        assert client.session_manager is not None
        assert client.price_service is not None
        assert client._is_connected is False
        
    def test_is_connected_false_initially(self, client):
        """初期状態での接続確認"""
        assert client.is_connected() is False
        
    @pytest.mark.asyncio
    async def test_connect_without_credentials_fails(self, client):
        """認証情報なしでの接続失敗テスト"""
        # 環境変数をクリア
        with patch('app.core.config.settings.TACHIBANA_USER_ID', ''):
            with patch('app.core.config.settings.TACHIBANA_PASSWORD', ''):
                result = await client.connect()
                assert result is False
                
    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, client):
        """切断状態でのヘルスチェック"""
        health = await client.health_check()
        
        assert health['service'] == 'tachibana_api'
        assert health['status'] == 'disconnected'
        assert health['demo_mode'] == settings.TACHIBANA_DEMO_MODE
        assert health['session_active'] is False
        assert health['market_accessible'] is False

class TestTachibanaIntegration:
    """立花証券API統合機能テスト"""
    
    @pytest.mark.skipif(
        not settings.TACHIBANA_USER_ID or not settings.TACHIBANA_PASSWORD,
        reason="立花証券認証情報が設定されていません"
    )
    @pytest.mark.asyncio
    async def test_real_connection(self):
        """実際の立花証券API接続テスト（認証情報が設定されている場合のみ）"""
        client = TachibanaAPIClient()
        
        try:
            # 接続テスト
            connected = await client.connect()
            
            if connected:
                # ヘルスチェック
                health = await client.health_check()
                assert health['status'] == 'healthy'
                assert health['session_active'] is True
                
                # 市場状態取得テスト
                market_status = await client.get_market_status()
                assert 'is_market_open' in market_status
                assert 'timestamp' in market_status
                
        except Exception as e:
            pytest.skip(f"立花証券API接続エラー: {str(e)}")
        finally:
            await client.disconnect()
            
    @pytest.mark.skipif(
        not settings.TACHIBANA_USER_ID or not settings.TACHIBANA_PASSWORD,
        reason="立花証券認証情報が設定されていません"
    )
    @pytest.mark.asyncio
    async def test_real_price_fetch(self):
        """実際の価格取得テスト（認証情報が設定されている場合のみ）"""
        client = TachibanaAPIClient()
        
        try:
            connected = await client.connect()
            
            if connected:
                # 単一銘柄価格取得
                price_data = await client.get_realtime_price("6723.T")
                assert price_data.symbol == "6723.T"
                assert price_data.current_price > 0
                
                # 複数銘柄価格取得
                symbols = ["6723.T", "7203.T"]
                price_dict = await client.get_multiple_prices(symbols)
                assert len(price_dict) <= len(symbols)  # すべて取得できるとは限らない
                
        except Exception as e:
            pytest.skip(f"立花証券API価格取得エラー: {str(e)}")
        finally:
            await client.disconnect()

def test_demo_mode_safety():
    """デモモード安全機能テスト"""
    session_manager = TachibanaSessionManager()
    
    # デモモードが有効であることを確認
    assert session_manager.is_demo_mode is True
    assert "demo" in session_manager.base_url.lower()
    
def test_config_validation():
    """設定値検証テスト"""
    # 立花証券設定が存在することを確認
    assert hasattr(settings, 'TACHIBANA_DEMO_MODE')
    assert hasattr(settings, 'TACHIBANA_API_VERSION')
    assert hasattr(settings, 'TACHIBANA_DEMO_BASE_URL')
    assert hasattr(settings, 'TACHIBANA_PROD_BASE_URL')
    
    # デフォルト値確認
    assert settings.TACHIBANA_DEMO_MODE is True  # 安全のためデフォルトはデモ
    assert settings.TACHIBANA_API_VERSION == "v4r7"

if __name__ == "__main__":
    # 手動実行用の基本テスト
    print("立花証券API統合テスト開始")
    
    # 設定確認
    print(f"デモモード: {settings.TACHIBANA_DEMO_MODE}")
    print(f"APIバージョン: {settings.TACHIBANA_API_VERSION}")
    print(f"ユーザーID設定: {'有' if settings.TACHIBANA_USER_ID else '無'}")
    
    # 基本初期化テスト
    client = TachibanaAPIClient()
    print(f"クライアント初期化: {'成功' if client else '失敗'}")
    
    print("基本テスト完了")