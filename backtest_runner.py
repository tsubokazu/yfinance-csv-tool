#!/usr/bin/env python3
"""
包括的バックテスト実行スクリプト

指定した期間・銘柄・間隔でバックテストを実行し、
AI判断用のデータ（チャート画像付き）を時系列で生成します。
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import json
import pandas as pd
from tqdm import tqdm

from minute_decision_engine import MinuteDecisionEngine


def setup_logging(log_level: str = "INFO"):
    """ログ設定"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'backtest.log')
        ]
    )


def generate_backtest_timeline(
    start_datetime: datetime,
    end_datetime: datetime,
    interval_minutes: int,
    market_hours_only: bool = True
) -> List[datetime]:
    """
    バックテスト用の時刻リストを生成
    
    Args:
        start_datetime: 開始日時
        end_datetime: 終了日時
        interval_minutes: 間隔（分）
        market_hours_only: 取引時間のみ（9:00-15:00）
        
    Returns:
        時刻リスト
    """
    timeline = []
    current_time = start_datetime
    
    while current_time <= end_datetime:
        # 市場時間チェック
        if market_hours_only:
            hour = current_time.hour
            minute = current_time.minute
            
            # 平日の9:00-15:00のみ
            if (current_time.weekday() < 5 and  # 平日
                ((hour == 9 and minute >= 0) or  # 9:00以降
                 (10 <= hour <= 14) or           # 10:00-14:59
                 (hour == 15 and minute == 0))):  # 15:00まで
                timeline.append(current_time)
        else:
            timeline.append(current_time)
            
        current_time += timedelta(minutes=interval_minutes)
    
    return timeline


def run_backtest(
    symbol: str,
    start_datetime: datetime,
    end_datetime: datetime,
    interval_minutes: int = 1,
    market_hours_only: bool = True,
    enable_charts: bool = True,
    output_dir: str = "backtest_results"
) -> Dict:
    """
    バックテスト実行
    
    Args:
        symbol: 銘柄コード
        start_datetime: 開始日時
        end_datetime: 終了日時
        interval_minutes: 判断間隔（分）
        market_hours_only: 取引時間のみ
        enable_charts: チャート生成有効
        output_dir: 出力ディレクトリ
        
    Returns:
        バックテスト結果サマリー
    """
    print(f"🎯 バックテスト開始: {symbol}")
    print(f"  期間: {start_datetime} ～ {end_datetime}")
    print(f"  間隔: {interval_minutes}分")
    print(f"  チャート生成: {'有効' if enable_charts else '無効'}")
    
    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 時刻リスト生成
    timeline = generate_backtest_timeline(
        start_datetime, end_datetime, interval_minutes, market_hours_only
    )
    
    print(f"  生成データポイント数: {len(timeline)}件")
    
    if len(timeline) == 0:
        print("❌ 有効な時刻がありません")
        return {}
    
    # エンジン初期化
    engine = MinuteDecisionEngine(enable_chart_generation=enable_charts)
    
    results = []
    failed_count = 0
    
    try:
        # 進捗バーを表示してバックテスト実行
        for timestamp in tqdm(timeline, desc="バックテスト進行中"):
            try:
                # 判断データ生成
                decision_data = engine.get_backtest_decision_data(symbol, timestamp)
                
                # 結果を記録
                result = {
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol,
                    'current_price': decision_data.current_price.current_price,
                    'price_change_percent': decision_data.current_price.price_change_percent,
                    'volume_ratio': decision_data.current_price.volume_ratio,
                    
                    # テクニカル指標（主要なもの）
                    'ma20_daily': decision_data.technical_indicators.daily.moving_averages.ma20,
                    'ma50_daily': decision_data.technical_indicators.daily.moving_averages.ma50,
                    'atr14_daily': decision_data.technical_indicators.daily.atr14,
                    'vwap_60m': decision_data.technical_indicators.hourly_60.vwap.daily,
                    
                    # チャート画像パス
                    'chart_images': {}
                }
                
                # チャート画像情報を追加
                if decision_data.chart_images:
                    for timeframe in ['weekly', 'daily', 'hourly_60', 'minute_15', 'minute_5', 'minute_1']:
                        chart_data = getattr(decision_data.chart_images, timeframe, None)
                        if chart_data:
                            result['chart_images'][timeframe] = chart_data.imagePath
                
                results.append(result)
                
                # 個別の詳細データも保存（JSON）
                if len(results) % 10 == 0:  # 10件ごとに詳細データ保存
                    detail_file = output_path / f"detail_{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                    with open(detail_file, 'w', encoding='utf-8') as f:
                        f.write(decision_data.to_json())
                
            except Exception as e:
                logging.error(f"バックテストエラー ({timestamp}): {e}")
                failed_count += 1
                continue
    
    finally:
        engine.close()
    
    # 結果サマリー作成
    summary = {
        'symbol': symbol,
        'start_datetime': start_datetime.isoformat(),
        'end_datetime': end_datetime.isoformat(),
        'interval_minutes': interval_minutes,
        'total_datapoints': len(timeline),
        'successful_datapoints': len(results),
        'failed_datapoints': failed_count,
        'success_rate': len(results) / len(timeline) * 100 if timeline else 0,
        'results': results
    }
    
    # 結果を保存
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # サマリーJSON
    summary_file = output_path / f"backtest_summary_{symbol}_{timestamp_str}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # CSV形式のサマリー
    if results:
        df = pd.DataFrame(results)
        csv_file = output_path / f"backtest_data_{symbol}_{timestamp_str}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"\n📊 バックテスト完了!")
        print(f"  成功: {len(results)}/{len(timeline)}件 ({summary['success_rate']:.1f}%)")
        print(f"  失敗: {failed_count}件")
        print(f"\n💾 出力ファイル:")
        print(f"  サマリー: {summary_file}")
        print(f"  CSVデータ: {csv_file}")
        
        # 価格統計
        prices = [r['current_price'] for r in results]
        print(f"\n📈 価格統計:")
        print(f"  最高値: ¥{max(prices):,.0f}")
        print(f"  最安値: ¥{min(prices):,.0f}")
        print(f"  平均値: ¥{sum(prices)/len(prices):,.0f}")
    
    return summary


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='包括的バックテスト実行')
    parser.add_argument('--symbol', '-s', required=True,
                       help='銘柄コード (例: 7203.T)')
    parser.add_argument('--start', '-st', required=True,
                       help='開始日時 (YYYY-MM-DD HH:MM)')
    parser.add_argument('--end', '-ed', required=True,
                       help='終了日時 (YYYY-MM-DD HH:MM)')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='判断間隔（分、デフォルト: 5分）')
    parser.add_argument('--all-hours', action='store_true',
                       help='24時間（市場時間外も含む）')
    parser.add_argument('--no-charts', action='store_true',
                       help='チャート生成を無効化')
    parser.add_argument('--output', '-o', default='backtest_results',
                       help='出力ディレクトリ')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細ログ')
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # 日時パース
    try:
        start_datetime = datetime.strptime(args.start, '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(args.end, '%Y-%m-%d %H:%M')
    except ValueError:
        print("❌ 日時の形式が正しくありません。YYYY-MM-DD HH:MM形式で指定してください。")
        return
    
    if start_datetime >= end_datetime:
        print("❌ 開始日時は終了日時より前である必要があります。")
        return
    
    print("🚀 バックテスト実行")
    print("=" * 60)
    
    # バックテスト実行
    summary = run_backtest(
        symbol=args.symbol,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        interval_minutes=args.interval,
        market_hours_only=not args.all_hours,
        enable_charts=not args.no_charts,
        output_dir=args.output
    )
    
    if summary:
        print("\n✅ バックテストが正常に完了しました")
        print(f"\n🎯 次のステップ:")
        print(f"  1. 生成されたデータを確認: {args.output}/")
        print(f"  2. AI判断システムに判断データを送信")
        print(f"  3. 取引シミュレーション実行")
    else:
        print("\n❌ バックテストに失敗しました")


if __name__ == "__main__":
    main()