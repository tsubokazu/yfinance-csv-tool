#!/usr/bin/env python3
"""
統合チャート生成機能のテストスクリプト

MinuteDecisionEngineに統合されたチャート生成機能をテストします。
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from minute_decision_engine import MinuteDecisionEngine


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/integrated_chart_test.log')
        ]
    )


def test_integrated_chart_generation(symbol: str, timestamp: datetime, backtest_mode: bool = False):
    """
    統合チャート生成のテスト
    
    Args:
        symbol: 銘柄コード
        timestamp: 判断時刻
        backtest_mode: バックテストモード
    """
    mode_text = "バックテスト" if backtest_mode else "通常"
    print(f"🔄 統合チャート生成テスト開始: {symbol} at {timestamp} ({mode_text}モード)")
    
    # チャート生成を有効にしてエンジンを初期化
    engine = MinuteDecisionEngine(
        enable_chart_generation=True,
        use_simple_charts=True  # 軽量チャート使用
    )
    
    try:
        # 判断データ生成
        if backtest_mode:
            decision_data = engine.get_backtest_decision_data(symbol, timestamp)
        else:
            decision_data = engine.get_minute_decision_data(symbol, timestamp)
        
        # 結果の表示
        print(f"\n📊 判断データ生成完了:")
        print(f"  銘柄: {decision_data.symbol}")
        print(f"  時刻: {decision_data.timestamp}")
        print(f"  現在価格: ¥{decision_data.current_price.current_price:,.0f}")
        print(f"  変化率: {decision_data.current_price.price_change_percent:.2f}%")
        
        # チャート画像の情報表示
        if decision_data.chart_images:
            print(f"\n🖼️  生成されたチャート画像:")
            
            for timeframe in ['weekly', 'daily', 'hourly_60', 'minute_15', 'minute_5', 'minute_1']:
                chart_data = getattr(decision_data.chart_images, timeframe, None)
                if chart_data:
                    file_name = Path(chart_data.imagePath).name
                    print(f"  {timeframe}: {file_name}")
                    print(f"    時間範囲: {chart_data.timeRange}")
                else:
                    print(f"  {timeframe}: 生成されませんでした")
        else:
            print("❌ チャート画像は生成されませんでした")
        
        # テクニカル指標の要約表示
        print(f"\n📈 テクニカル指標要約:")
        ti = decision_data.technical_indicators
        print(f"  日足MA20: ¥{ti.daily.moving_averages.ma20:,.0f}" if ti.daily.moving_averages.ma20 else "  日足MA20: N/A")
        print(f"  日足ATR14: {ti.daily.atr14:.1f}" if ti.daily.atr14 else "  日足ATR14: N/A")
        print(f"  60分VWAP: ¥{ti.hourly_60.vwap.daily:,.0f}" if ti.hourly_60.vwap.daily else "  60分VWAP: N/A")
        
        # JSONファイルとして保存
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        mode_suffix = "_backtest" if backtest_mode else "_integrated"
        output_file = output_dir / f"integrated_test_{symbol}_{timestamp_str}{mode_suffix}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(decision_data.to_json())
        
        print(f"\n💾 結果を保存しました: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # リソースのクリーンアップ
        engine.close()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='統合チャート生成機能のテスト')
    parser.add_argument('--symbol', '-s', default='6723.T', 
                       help='銘柄コード (デフォルト: 6723.T)')
    parser.add_argument('--datetime', '-d', 
                       help='判断日時 (YYYY-MM-DD HH:MM形式、省略時は現在時刻)')
    parser.add_argument('--backtest', '-b', action='store_true',
                       help='バックテストモード（指定時刻でのスナップショット）')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細ログを表示')
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)
    
    # 日時の処理
    if args.datetime:
        try:
            timestamp = datetime.strptime(args.datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            print("❌ 日時の形式が正しくありません。YYYY-MM-DD HH:MM形式で指定してください。")
            return
    else:
        timestamp = datetime.now()
    
    mode_text = "バックテスト" if args.backtest else "通常"
    print("🚀 統合チャート生成テスト")
    print("=" * 50)
    print(f"銘柄: {args.symbol}")
    print(f"日時: {timestamp}")
    print(f"モード: {mode_text}")
    print("=" * 50)
    
    # 統合チャート生成テスト実行
    success = test_integrated_chart_generation(args.symbol, timestamp, args.backtest)
    
    if success:
        print("\n✅ 統合チャート生成テストが正常に完了しました")
        print("\n📁 生成されたファイル:")
        print("  - output/integrated_test_*.json: 判断データ")
        print("  - charts/chart_*.png: チャート画像")
        print("\n🎯 使用方法:")
        print("  通常モード: python test_integrated_charts.py --symbol 7203.T")
        print("  バックテスト: python test_integrated_charts.py --symbol 7203.T --datetime '2025-07-25 10:30' --backtest")
    else:
        print("\n❌ 統合チャート生成テストに失敗しました")
        print("ログファイル logs/integrated_chart_test.log を確認してください")


if __name__ == "__main__":
    main()