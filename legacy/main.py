#!/usr/bin/env python3
"""
yfinance CSV出力ツール
銘柄指定で各時間足のCSVファイルを出力する
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd
from typing import Optional, List

class YFinanceCSVTool:
    def __init__(self):
        self.intervals = {
            '1m': '1分足',
            '5m': '5分足',
            '15m': '15分足',
            '60m': '60分足',
            '1d': '日足',
            '1wk': '週足'
        }
        self.setup_logging()
        self.setup_directories()
    
    def setup_logging(self):
        """ログ設定"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"yfinance_tool_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_directories(self):
        """必要なディレクトリを作成"""
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
    
    def get_stock_data(self, symbol: str, interval: str, period: Optional[str] = None, 
                      start: Optional[str] = None, end: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        株価データを取得
        
        Args:
            symbol: 銘柄コード
            interval: 時間足
            period: 期間（例: '1mo', '3mo', '1y'）
            start: 開始日（YYYY-MM-DD）
            end: 終了日（YYYY-MM-DD）
        
        Returns:
            pandas.DataFrame: 株価データ
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if start and end:
                data = ticker.history(start=start, end=end, interval=interval)
            elif period:
                data = ticker.history(period=period, interval=interval)
            else:
                # デフォルトは1ヶ月
                data = ticker.history(period='1mo', interval=interval)
            
            if data.empty:
                self.logger.warning(f"データが取得できませんでした: {symbol} ({self.intervals[interval]})")
                return None
            
            self.logger.info(f"データ取得成功: {symbol} ({self.intervals[interval]}) - {len(data)}行")
            return data
            
        except Exception as e:
            self.logger.error(f"データ取得エラー: {symbol} ({self.intervals[interval]}) - {str(e)}")
            return None
    
    def save_to_csv(self, data: pd.DataFrame, symbol: str, interval: str, 
                   start: Optional[str] = None, end: Optional[str] = None) -> str:
        """
        CSVファイルに保存
        
        Args:
            data: 株価データ
            symbol: 銘柄コード
            interval: 時間足
            start: 開始日
            end: 終了日
        
        Returns:
            str: 保存されたファイルパス
        """
        # ファイル名を生成
        if start and end:
            filename = f"{symbol}_{interval}_{start}_{end}.csv"
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            filename = f"{symbol}_{interval}_{start_date}_{end_date}.csv"
        
        filepath = Path("data") / filename
        
        try:
            # インデックス（日時）を含めてCSV保存
            data.to_csv(filepath, encoding='utf-8')
            self.logger.info(f"CSV保存完了: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {filepath} - {str(e)}")
            raise
    
    def process_symbol(self, symbol: str, intervals: List[str], 
                      period: Optional[str] = None, 
                      start: Optional[str] = None, end: Optional[str] = None):
        """
        指定された銘柄の全時間足データを処理
        
        Args:
            symbol: 銘柄コード
            intervals: 時間足リスト
            period: 期間
            start: 開始日
            end: 終了日
        """
        self.logger.info(f"処理開始: {symbol}")
        
        for interval in intervals:
            if interval not in self.intervals:
                self.logger.warning(f"未対応の時間足: {interval}")
                continue
            
            self.logger.info(f"取得中: {symbol} - {self.intervals[interval]}")
            
            data = self.get_stock_data(symbol, interval, period, start, end)
            if data is not None:
                self.save_to_csv(data, symbol, interval, start, end)
        
        self.logger.info(f"処理完了: {symbol}")
    
    def interactive_mode(self):
        """対話式モード"""
        print("=== yfinance CSV出力ツール ===")
        
        # 銘柄入力
        symbol = input("銘柄コードを入力してください (例: AAPL, 7203.T): ").strip().upper()
        if not symbol:
            print("銘柄コードが入力されていません。")
            return
        
        # 時間足選択
        print("\n利用可能な時間足:")
        for key, value in self.intervals.items():
            print(f"  {key}: {value}")
        
        print("時間足を選択してください（カンマ区切りで複数選択可能、Enterで全選択）:")
        interval_input = input().strip()
        
        if not interval_input:
            selected_intervals = list(self.intervals.keys())
        else:
            selected_intervals = [i.strip() for i in interval_input.split(',')]
        
        # 期間選択
        print("\n期間選択:")
        print("1. 期間指定 (例: 1mo, 3mo, 1y)")
        print("2. 日付範囲指定 (開始日-終了日)")
        choice = input("選択してください (1 or 2, デフォルト: 1): ").strip()
        
        period = start = end = None
        
        if choice == '2':
            start = input("開始日を入力してください (YYYY-MM-DD): ").strip()
            end = input("終了日を入力してください (YYYY-MM-DD): ").strip()
            if not start or not end:
                print("日付が正しく入力されていません。デフォルト期間(1mo)を使用します。")
                period = '1mo'
        else:
            period = input("期間を入力してください (デフォルト: 1mo): ").strip() or '1mo'
        
        # 処理実行
        self.process_symbol(symbol, selected_intervals, period, start, end)
        print(f"\nCSVファイルは data/ ディレクトリに保存されました。")

def main():
    parser = argparse.ArgumentParser(description='yfinance CSV出力ツール')
    parser.add_argument('--symbol', '-s', type=str, help='銘柄コード (例: AAPL, 7203.T)')
    parser.add_argument('--intervals', '-i', type=str, nargs='+', 
                       choices=['1m', '5m', '15m', '60m', '1d', '1wk'],
                       help='時間足 (複数選択可能)')
    parser.add_argument('--period', '-p', type=str, help='期間 (例: 1mo, 3mo, 1y)')
    parser.add_argument('--start', type=str, help='開始日 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='終了日 (YYYY-MM-DD)')
    parser.add_argument('--interactive', action='store_true', help='対話式モード')
    
    args = parser.parse_args()
    
    tool = YFinanceCSVTool()
    
    if args.interactive or not args.symbol:
        tool.interactive_mode()
    else:
        intervals = args.intervals or ['1m', '5m', '15m', '60m', '1d', '1wk']
        tool.process_symbol(args.symbol, intervals, args.period, args.start, args.end)

if __name__ == "__main__":
    main()