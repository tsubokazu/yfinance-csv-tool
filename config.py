"""
設定ファイル
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ToolConfig:
    """ツール設定"""
    
    # サポートする時間足
    SUPPORTED_INTERVALS: Dict[str, str] = None
    
    # デフォルト期間
    DEFAULT_PERIOD: str = "1mo"
    
    # デフォルト時間足
    DEFAULT_INTERVALS: List[str] = None
    
    # CSVファイル保存先
    DATA_DIR: str = "data"
    
    # ログファイル保存先
    LOG_DIR: str = "logs"
    
    def __post_init__(self):
        if self.SUPPORTED_INTERVALS is None:
            self.SUPPORTED_INTERVALS = {
                '1m': '1分足',
                '5m': '5分足',
                '15m': '15分足',
                '60m': '60分足',
                '1d': '日足',
                '1wk': '週足'
            }
        
        if self.DEFAULT_INTERVALS is None:
            self.DEFAULT_INTERVALS = ['1m', '5m', '15m', '60m', '1d', '1wk']

# グローバル設定インスタンス
config = ToolConfig()