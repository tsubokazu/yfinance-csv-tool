#!/usr/bin/env python3
"""
バッチ処理用判断データ生成スクリプト
複数銘柄を一括処理し、結果をまとめて出力
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv
from typing import List, Dict, Any

from minute_decision_engine import MinuteDecisionEngine

def setup_logging(log_level: str = "INFO"):
    """ログ設定"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

class BatchDecisionProcessor:
    """バッチ処理クラス"""
    
    def __init__(self):
        self.engine = MinuteDecisionEngine()
        self.logger = logging.getLogger(__name__)
    
    def load_symbols_from_file(self, filepath: str) -> List[str]:
        """
        ファイルから銘柄リストを読み込み
        
        Args:
            filepath: ファイルパス
        
        Returns:
            List[str]: 銘柄コードリスト
        """
        symbols = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    symbol = line.strip()
                    if symbol and not symbol.startswith('#'):
                        symbols.append(symbol)
            
            self.logger.info(f"銘柄リスト読み込み完了: {len(symbols)}銘柄")
            return symbols
            
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー: {filepath} - {str(e)}")
            return []
    
    def process_symbols(self, symbols: List[str], timestamp: datetime, 
                       max_workers: int = 3) -> Dict[str, Any]:
        """
        複数銘柄を処理
        
        Args:
            symbols: 銘柄コードリスト
            timestamp: 判断時刻
            max_workers: 最大並列処理数
        
        Returns:
            Dict: 処理結果サマリー
        """
        self.logger.info(f"バッチ処理開始: {len(symbols)}銘柄")
        
        # 複数銘柄の判断データを取得
        results = self.engine.get_multiple_decisions(symbols, timestamp, max_workers)
        
        # 結果をファイル保存
        saved_files = self.engine.save_multiple_results(results)
        
        # サマリー情報を生成
        summary = self._generate_summary(results, timestamp)
        
        # サマリーCSVを保存
        summary_file = self._save_summary_csv(summary, timestamp)
        
        return {
            'timestamp': timestamp,
            'total_symbols': len(symbols),
            'successful': summary['successful'],
            'failed': summary['failed'],
            'saved_files': saved_files,
            'summary_file': summary_file,
            'summary_data': summary
        }
    
    def _generate_summary(self, results: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """処理結果のサマリーを生成"""
        successful = []
        failed = []
        market_summary = {}
        
        for symbol, package in results.items():
            if package is None:
                failed.append(symbol)
                continue
            
            successful.append({
                'symbol': symbol,
                'company_name': package.current_price.company_name,
                'current_price': package.current_price.current_price,
                'price_change': package.current_price.price_change,
                'price_change_percent': package.current_price.price_change_percent,
                'volume_ratio': package.current_price.volume_ratio,
                # テクニカル指標サマリー
                'ma20_1d': package.technical_indicators.daily.moving_averages.ma20,
                'ma50_1d': package.technical_indicators.daily.moving_averages.ma50,
                'atr14': package.technical_indicators.daily.atr14,
                'vwap_60m': package.technical_indicators.hourly_60.vwap.daily,
                'bb_upper_60m': package.technical_indicators.hourly_60.bollinger_bands.upper,
                'bb_lower_60m': package.technical_indicators.hourly_60.bollinger_bands.lower,
            })
            
            # 市場環境データ（最初の銘柄から取得）
            if not market_summary and package.market_context:
                market_summary = {
                    'nikkei225': package.market_context.indices['nikkei225'].price,
                    'nikkei225_change': package.market_context.indices['nikkei225'].change_percent,
                    'topix': package.market_context.indices['topix'].price,
                    'topix_change': package.market_context.indices['topix'].change_percent,
                    'usdjpy': package.market_context.forex['usdjpy'].price,
                    'usdjpy_change': package.market_context.forex['usdjpy'].change_percent,
                    'session': package.market_status.session if package.market_status else 'UNKNOWN',
                    'sentiment': package.market_status.market_sentiment['direction'] if package.market_status else 'NEUTRAL'
                }
        
        return {
            'timestamp': timestamp.isoformat(),
            'successful': successful,
            'failed': failed,
            'success_count': len(successful),
            'failure_count': len(failed),
            'success_rate': len(successful) / (len(successful) + len(failed)) * 100 if (len(successful) + len(failed)) > 0 else 0,
            'market_summary': market_summary
        }
    
    def _save_summary_csv(self, summary: Dict[str, Any], timestamp: datetime) -> str:
        """サマリーデータをCSV形式で保存"""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            filename = f"batch_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = output_dir / filename
            
            if not summary['successful']:
                self.logger.warning("成功データがないためCSV出力をスキップ")
                return ""
            
            # CSVヘッダー
            fieldnames = [
                'symbol', 'company_name', 'current_price', 'price_change', 'price_change_percent',
                'volume_ratio', 'ma20_1d', 'ma50_1d', 'atr14', 'vwap_60m', 'bb_upper_60m', 'bb_lower_60m'
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in summary['successful']:
                    # None値を空文字に変換
                    clean_row = {k: (v if v is not None else '') for k, v in row.items()}
                    writer.writerow(clean_row)
            
            self.logger.info(f"サマリーCSV保存完了: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"サマリーCSV保存エラー: {str(e)}")
            return ""
    
    def save_batch_summary_json(self, batch_result: Dict[str, Any]) -> str:
        """バッチ処理結果をJSON形式で保存"""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = batch_result['timestamp']
            filename = f"batch_result_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = output_dir / filename
            
            # datetime型をJSON serializable に変換
            def datetime_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(batch_result, f, indent=2, default=datetime_serializer, ensure_ascii=False)
            
            self.logger.info(f"バッチ結果JSON保存完了: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"バッチ結果JSON保存エラー: {str(e)}")
            return ""

def create_sample_symbols_file():
    """サンプル銘柄ファイルを作成"""
    sample_symbols = [
        "# 日本株 - 大型株",
        "7203.T",  # トヨタ自動車
        "9984.T",  # ソフトバンクグループ
        "6758.T",  # ソニーグループ
        "7974.T",  # 任天堂
        "9434.T",  # ソフトバンク
        "",
        "# 日本株 - 中小型株・テーマ株",
        "6723.T",  # ルネサスエレクトロニクス
        "4385.T",  # メルカリ
        "3659.T",  # ネクソン
        "4689.T",  # ヤフー
        "",
        "# 米国株（参考実装）",
        "# AAPL",    # Apple
        "# MSFT",    # Microsoft
        "# GOOGL",   # Google
        "# TSLA",    # Tesla
    ]
    
    with open("sample_symbols.txt", 'w', encoding='utf-8') as f:
        for symbol in sample_symbols:
            f.write(f"{symbol}\n")
    
    print("サンプル銘柄ファイル作成完了: sample_symbols.txt")

def main():
    parser = argparse.ArgumentParser(description='バッチ処理用判断データ生成')
    parser.add_argument('--symbols-file', '-f', type=str, help='銘柄リストファイル')
    parser.add_argument('--symbols', '-s', type=str, nargs='+', help='銘柄コード直接指定')
    parser.add_argument('--datetime', '-d', type=str, help='判断時刻 (YYYY-MM-DD HH:MM)')
    parser.add_argument('--workers', '-w', type=int, default=3, help='並列処理数 (デフォルト: 3)')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='ログレベル')
    parser.add_argument('--create-sample', action='store_true', help='サンプル銘柄ファイルを作成')
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # サンプルファイル作成
    if args.create_sample:
        create_sample_symbols_file()
        return
    
    # 銘柄リスト準備
    symbols = []
    if args.symbols_file:
        processor = BatchDecisionProcessor()
        symbols = processor.load_symbols_from_file(args.symbols_file)
    elif args.symbols:
        symbols = args.symbols
    else:
        logger.error("銘柄リストファイル (--symbols-file) または銘柄コード (--symbols) を指定してください")
        return
    
    if not symbols:
        logger.error("有効な銘柄が見つかりません")
        return
    
    # 判断時刻の設定
    if args.datetime:
        try:
            timestamp = datetime.strptime(args.datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            logger.error("日時形式が正しくありません。YYYY-MM-DD HH:MM形式で入力してください。")
            return
    else:
        timestamp = datetime.now().replace(second=0, microsecond=0)
    
    # バッチ処理実行
    processor = BatchDecisionProcessor()
    
    logger.info(f"=== バッチ処理開始 ===")
    logger.info(f"対象銘柄: {len(symbols)}銘柄")
    logger.info(f"判断時刻: {timestamp}")
    logger.info(f"並列処理数: {args.workers}")
    
    try:
        batch_result = processor.process_symbols(symbols, timestamp, args.workers)
        
        # 結果サマリー表示
        print(f"\n=== バッチ処理結果 ===")
        print(f"処理銘柄数: {batch_result['total_symbols']}")
        print(f"成功: {len(batch_result['successful'])}")
        print(f"失敗: {len(batch_result['failed'])}")
        print(f"成功率: {batch_result['summary_data']['success_rate']:.1f}%")
        
        if batch_result['summary_data']['market_summary']:
            market = batch_result['summary_data']['market_summary']
            print(f"\n=== 市場環境 ===")
            print(f"日経225: {market['nikkei225']:,.0f} ({market['nikkei225_change']:+.2f}%)")
            print(f"セッション: {market['session']}")
            print(f"地合い: {market['sentiment']}")
        
        # バッチ結果JSON保存
        batch_json_file = processor.save_batch_summary_json(batch_result)
        
        print(f"\n=== 出力ファイル ===")
        print(f"個別JSONファイル: {len(batch_result['saved_files'])}個")
        print(f"サマリーCSV: {batch_result['summary_file']}")
        print(f"バッチ結果JSON: {batch_json_file}")
        
        logger.info("バッチ処理完了")
        
    except Exception as e:
        logger.error(f"バッチ処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()