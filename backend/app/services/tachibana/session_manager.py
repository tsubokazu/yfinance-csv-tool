"""
立花証券APIセッション管理
"""

import urllib3
import urllib.parse
import json
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class TachibanaSessionManager:
    """立花証券APIセッション管理クラス"""
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.virtual_urls: Dict[str, str] = {}
        self.session_expiry: Optional[datetime] = None
        self.http = urllib3.PoolManager()
        
        # 安全機能: デモモードを強制
        self.is_demo_mode = settings.TACHIBANA_DEMO_MODE
        self.base_url = (
            settings.TACHIBANA_DEMO_BASE_URL 
            if self.is_demo_mode 
            else settings.TACHIBANA_PROD_BASE_URL
        )
        
        logger.info(f"立花証券API初期化: {'デモモード' if self.is_demo_mode else '本番モード'}")
        
    def login(self, user_id: str, password: str) -> bool:
        """
        立花証券APIにログイン
        
        Args:
            user_id: ユーザーID
            password: パスワード
            
        Returns:
            bool: ログイン成功時True
            
        Raises:
            Exception: ログイン失敗時
        """
        try:
            # 安全チェック
            if not self.is_demo_mode:
                logger.warning("⚠️ 本番モードでのログイン試行")
                
            # ログインパラメータ準備（立花証券API公式仕様に従った形式）
            from datetime import datetime
            login_params = {
                "sCLMID": "CLMAuthLoginRequest",
                "sUserId": user_id,
                "sPassword": password,
                "p_no": "1",
                "p_sd_date": datetime.now().strftime("%Y%m%d%H%M%S"),
                "sJsonOfmt": "4"
            }
            
            # JSON文字列に変換してURLエンコード
            json_str = json.dumps(login_params, ensure_ascii=False)
            encoded_json = urllib.parse.quote(json_str, safe='')
            
            # URL構築（JSON-in-GET方式）
            login_url = f"{self.base_url}?{encoded_json}"
            
            # リクエスト実行
            logger.info(f"立花証券APIログイン試行: {login_url}")
            logger.info(f"ログインパラメータ: userid={user_id}")
            
            response = self.http.request(
                'GET',
                login_url,
                headers={
                    'User-Agent': 'yfinance-trading-platform/1.0'
                }
            )
            
            # レスポンス処理
            logger.info(f"レスポンスステータス: {response.status}")
            logger.info(f"レスポンスデータ: {response.data}")
            
            if response.status == 200:
                try:
                    response_text = response.data.decode('shift-jis')
                    logger.info(f"デコード済みレスポンス: {response_text}")
                    response_data = json.loads(response_text)
                except UnicodeDecodeError:
                    # UTF-8でも試行
                    response_text = response.data.decode('utf-8')
                    logger.info(f"UTF-8デコード済みレスポンス: {response_text}")
                    response_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析エラー: {e}")
                    logger.error(f"レスポンス内容: {response.data}")
                    raise Exception(f"API応答の解析に失敗: {e}")
                
                # エラーチェック（立花証券API仕様）
                if 'p_errno' in response_data and int(response_data['p_errno']) != 0:
                    error_msg = response_data.get('p_err', '不明なエラー')
                    logger.error(f"立花証券APIログインエラー: {error_msg}")
                    raise Exception(f"ログインエラー: {error_msg}")
                
                # セッション情報保存（立花証券API仕様のレスポンス形式）
                self.session_id = response_data.get('sSKey')  # セッションキー
                self.virtual_urls = {
                    'request': response_data.get('sUrlRequest'),   # REQUEST I/F URL
                    'master': response_data.get('sUrlMaster'),     # MASTER I/F URL
                    'price': response_data.get('sUrlPrice'),       # PRICE I/F URL
                    'event': response_data.get('sUrlEvent'),       # EVENT I/F URL
                    'event_ws': response_data.get('sUrlEventWS')   # EVENT I/F WebSocket URL
                }
                
                # セッション有効期限設定
                self.session_expiry = datetime.now() + timedelta(
                    seconds=settings.TACHIBANA_SESSION_TIMEOUT
                )
                
                logger.info(f"立花証券APIログイン成功: セッションID={self.session_id}")
                logger.info(f"仮想URL取得完了: {list(self.virtual_urls.keys())}")
                
                return True
            else:
                logger.error(f"立花証券APIログイン失敗: HTTP {response.status}")
                raise Exception(f"HTTPエラー: {response.status}")
                
        except Exception as e:
            logger.error(f"立花証券APIログインエラー: {str(e)}")
            raise
            
    def logout(self) -> bool:
        """
        立花証券APIからログアウト
        
        Returns:
            bool: ログアウト成功時True
        """
        try:
            if not self.is_logged_in():
                logger.warning("ログインしていないためログアウトをスキップ")
                return True
                
            # ログアウトパラメータ（立花証券API仕様）
            from datetime import datetime
            logout_params = {
                "sCLMID": "CLMAuthLogoutRequest", 
                "sSKey": self.session_id,
                "p_no": "1",
                "p_sd_date": datetime.now().strftime("%Y%m%d%H%M%S"),
                "sJsonOfmt": "4"
            }
            
            # JSON文字列に変換してURLエンコード
            json_str = json.dumps(logout_params, ensure_ascii=False)
            encoded_json = urllib.parse.quote(json_str, safe='')
            
            # ログアウトURL構築
            logout_url = f"{self.base_url}?{encoded_json}"
            
            response = self.http.request(
                'GET',
                logout_url,
                headers={
                    'User-Agent': 'yfinance-trading-platform/1.0'
                }
            )
            
            # セッション情報クリア
            self.session_id = None
            self.virtual_urls = {}
            self.session_expiry = None
            
            logger.info("立花証券APIログアウト完了")
            return True
            
        except Exception as e:
            logger.error(f"立花証券APIログアウトエラー: {str(e)}")
            return False
            
    def is_logged_in(self) -> bool:
        """
        ログイン状態確認
        
        Returns:
            bool: ログイン済みかつセッション有効時True
        """
        if not self.session_id or not self.session_expiry:
            return False
            
        # セッション有効期限チェック
        if datetime.now() > self.session_expiry:
            logger.warning("立花証券APIセッション期限切れ")
            self.session_id = None
            self.virtual_urls = {}
            self.session_expiry = None
            return False
            
        return True
        
    def get_interface_url(self, interface_type: str) -> str:
        """
        指定インターフェースの仮想URL取得
        
        Args:
            interface_type: 'request', 'master', 'price', 'event'
            
        Returns:
            str: 仮想URL
            
        Raises:
            Exception: ログインしていない、または無効なインターフェース
        """
        if not self.is_logged_in():
            raise Exception("立花証券APIにログインしていません")
            
        if interface_type not in self.virtual_urls:
            raise Exception(f"無効なインターフェース: {interface_type}")
            
        return self.virtual_urls[interface_type]
        
    def make_request(self, interface_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        立花証券APIリクエスト実行
        
        Args:
            interface_type: インターフェース種別
            params: リクエストパラメータ
            
        Returns:
            Dict[str, Any]: APIレスポンス
            
        Raises:
            Exception: APIエラー
        """
        try:
            if not self.is_logged_in():
                raise Exception("立花証券APIにログインしていません")
                
            # URL取得
            url = self.get_interface_url(interface_type)
            
            # JSONエンコード
            json_str = json.dumps(params, ensure_ascii=False)
            encoded_json = json_str.encode('shift-jis')
            
            # リクエスト実行
            response = self.http.request(
                'GET',
                url,
                body=encoded_json,
                headers={
                    'Content-Type': 'application/json; charset=Shift-JIS'
                }
            )
            
            # レスポンス処理
            if response.status == 200:
                response_data = json.loads(response.data.decode('shift-jis'))
                
                # エラーチェック
                if 'p_errno' in response_data and response_data['p_errno'] != 0:
                    error_msg = response_data.get('p_err', '不明なエラー')
                    logger.error(f"立花証券APIエラー: {error_msg}")
                    raise Exception(f"APIエラー: {error_msg}")
                    
                return response_data
            else:
                raise Exception(f"HTTPエラー: {response.status}")
                
        except Exception as e:
            logger.error(f"立花証券APIリクエストエラー: {str(e)}")
            raise
            
    def __enter__(self):
        """コンテキストマネージャー開始"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.logout()