#!/usr/bin/env python3
"""
毎分判断エンジンのテストスクリプト
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json

from minute_decision_engine import MinuteDecisionEngine

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def test_decision_engine():
    """決定エンジンのテスト"""
    print("=== 毎分判断エンジン テスト ===")
    
    # エンジン初期化
    engine = MinuteDecisionEngine()
    
    # テスト対象
    symbol = "6723.T"  # ルネサス
    timestamp = datetime.now().replace(second=0, microsecond=0)
    
    print(f"銘柄: {symbol}")
    print(f"判断時刻: {timestamp}")
    print("データ生成中...")
    
    try:
        # データ生成
        package = engine.get_minute_decision_data(symbol, timestamp)
        
        print("=== 生成結果 ===")
        print(f"銘柄: {package.current_price.symbol}")
        print(f"銘柄名: {package.current_price.company_name}")
        print(f"現在価格: ¥{package.current_price.current_price:,.0f}")
        print(f"前日比: {package.current_price.price_change:+.1f} ({package.current_price.price_change_percent:+.2f}%)")
        print(f"当日範囲: ¥{package.current_price.today_low:,.0f} - ¥{package.current_price.today_high:,.0f}")
        print(f"出来高: {package.current_price.current_volume:,} (比率: {package.current_price.volume_ratio:.2f})")
        
        print("\n=== テクニカル指標 ===")
        
        # 週足
        weekly = package.technical_indicators.weekly
        print(f"週足MA: 20={weekly.moving_averages.ma20:.0f}, 50={weekly.moving_averages.ma50:.0f}, 200={weekly.moving_averages.ma200:.0f}")
        print(f"週足VP: POC={weekly.volume_profile.poc:.0f}, VA={weekly.volume_profile.value_area_low:.0f}-{weekly.volume_profile.value_area_high:.0f}")
        
        # 日足
        daily = package.technical_indicators.daily
        print(f"日足MA: 20={daily.moving_averages.ma20:.0f}, 50={daily.moving_averages.ma50:.0f}, 200={daily.moving_averages.ma200:.0f}")
        print(f"日足ATR: {daily.atr14:.1f}")
        
        # 60分足
        hourly = package.technical_indicators.hourly_60
        print(f"60分MA: 20={hourly.moving_averages.ma20:.0f}, 50={hourly.moving_averages.ma50:.0f}")
        print(f"60分VWAP: 日次={hourly.vwap.daily:.0f}, アンカー={hourly.vwap.anchored:.0f}")
        print(f"60分BB: {hourly.bollinger_bands.lower:.0f} | {hourly.bollinger_bands.middle:.0f} | {hourly.bollinger_bands.upper:.0f}")
        
        # 15分足
        minute15 = package.technical_indicators.minute_15
        print(f"15分MA: 9={minute15.moving_averages.ma9:.0f}, 20={minute15.moving_averages.ma20:.0f}")
        print(f"15分VWAP: {minute15.vwap.daily:.0f}")
        
        # 5分足
        minute5 = package.technical_indicators.minute_5
        print(f"5分MA: 5={minute5.moving_averages.ma5:.0f}, 21={minute5.moving_averages.ma21:.0f}")
        print(f"5分VWAP: {minute5.vwap.daily:.0f}")
        
        # 1分足
        minute1 = package.technical_indicators.minute_1
        print(f"1分MA: 5={minute1.moving_averages.ma5:.0f}, 9={minute1.moving_averages.ma9:.0f}")
        print(f"1分VWAP: {minute1.vwap.daily:.0f}")
        
        # JSON出力
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        json_filename = f"decision_data_{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        json_path = output_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(package.to_json())
        
        print(f"\nJSONファイル出力: {json_path}")
        print(f"ファイルサイズ: {json_path.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='毎分判断エンジンテスト')
    parser.add_argument('--symbol', '-s', type=str, default='6723.T', help='銘柄コード')
    parser.add_argument('--datetime', '-d', type=str, help='判断時刻 (YYYY-MM-DD HH:MM)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # 判断時刻の設定
    if args.datetime:
        try:
            timestamp = datetime.strptime(args.datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            print("日時形式が正しくありません。YYYY-MM-DD HH:MM形式で入力してください。")
            return
    else:
        timestamp = datetime.now().replace(second=0, microsecond=0)
    
    # エンジン初期化とテスト
    engine = MinuteDecisionEngine()
    
    print(f"=== 毎分判断エンジン テスト ===")
    print(f"銘柄: {args.symbol}")
    print(f"判断時刻: {timestamp}")
    print("データ生成中...")
    
    try:
        package = engine.get_minute_decision_data(args.symbol, timestamp)
        
        # 結果表示
        print("\n=== 基本情報 ===")
        print(f"銘柄名: {package.current_price.company_name}")
        print(f"現在価格: ¥{package.current_price.current_price:,.0f}")
        print(f"前日比: {package.current_price.price_change:+.1f} ({package.current_price.price_change_percent:+.2f}%)")
        
        # 市場環境データの表示
        if package.market_context:
            print("\n=== 市場環境 ===")
            print(f"日経225: {package.market_context.indices['nikkei225'].price:,.0f} ({package.market_context.indices['nikkei225'].change_percent:+.2f}%)")
            print(f"TOPIX: {package.market_context.indices['topix'].price:,.0f} ({package.market_context.indices['topix'].change_percent:+.2f}%)")
            print(f"USD/JPY: {package.market_context.forex['usdjpy'].price:.2f} ({package.market_context.forex['usdjpy'].change_percent:+.2f}%)")
            print(f"セクター: {package.market_context.sector['name']} ({package.market_context.sector['performance']:+.2f}%)")
        
        if package.market_status:
            print(f"\n=== 市場状態 ===")
            print(f"セッション: {package.market_status.session}")
            print(f"次のイベント: {package.market_status.next_event} (あと{package.market_status.time_to_next_event//60:.0f}分)")
            print(f"地合い: {package.market_status.market_sentiment['direction']} (強度: {package.market_status.market_sentiment['strength']:.2f})")
        
        # JSON出力
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        json_filename = f"decision_data_{args.symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        json_path = output_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(package.to_json())
        
        print(f"\nJSONファイル出力完了: {json_path}")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()