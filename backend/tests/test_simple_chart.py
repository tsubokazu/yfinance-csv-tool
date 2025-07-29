#!/usr/bin/env python3
"""
軽量チャート生成機能のテストスクリプト

matplotlib + mplfinance を使用した高速・確実なチャート生成をテストします。
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from app.services.minute_decision_engine import MinuteDecisionEngine
from app.services.visualization.simple_chart_generator import SimpleChartGenerator


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/simple_chart_test.log')
        ]
    )


def test_simple_chart_generation(symbol: str, timestamp: datetime, enable_backtest: bool = False):
    """
    軽量チャート生成のテスト
    
    Args:
        symbol: 銘柄コード
        timestamp: 判断時刻
        enable_backtest: バックテストモード（指定時刻でのスナップショット）
    """
    print(f"🔄 軽量チャート生成テスト開始: {symbol} at {timestamp}")
    
    # データエンジンを初期化（チャート生成は無効）
    engine = MinuteDecisionEngine(enable_chart_generation=False)
    chart_generator = SimpleChartGenerator()
    
    try:
        # 基本的な判断データ生成（チャートなし）
        print("📊 データ収集中...")
        decision_data = engine.get_minute_decision_data(symbol, timestamp)
        
        # 価格データとテクニカル指標データを取得
        timeframe_data = engine._get_all_timeframe_data(symbol, timestamp)
        indicators_data = engine._prepare_indicators_for_chart(timeframe_data, decision_data.technical_indicators)
        
        print(f"✅ データ収集完了")
        print(f"  銘柄: {decision_data.symbol}")
        print(f"  時刻: {decision_data.timestamp}")
        print(f"  現在価格: ¥{decision_data.current_price.current_price:,.0f}")
        print(f"  変化率: {decision_data.current_price.price_change_percent:.2f}%")
        
        # チャート生成
        if enable_backtest:
            print(f"\n🎯 バックテスト用チャート生成中（{timestamp}時点）...")
            chart_images = chart_generator.generate_backtest_chart(
                symbol=symbol,
                target_datetime=timestamp,
                price_data=timeframe_data,
                indicators_data=indicators_data
            )
        else:
            print(f"\n📊 通常チャート生成中...")
            chart_images = chart_generator.generate_all_timeframe_charts(
                symbol=symbol,
                timestamp=timestamp,
                price_data=timeframe_data,
                indicators_data=indicators_data
            )
        
        # チャート画像の情報表示
        if chart_images:
            print(f"\n🖼️  生成されたチャート画像:")
            
            for timeframe in ['weekly', 'daily', '60min', '15min', '5min', '1min']:
                chart_data = getattr(chart_images, timeframe.replace('min', '_min').replace('60_min', 'hourly_60'), None)
                if chart_data:
                    print(f"  {timeframe}: {chart_data.imagePath}")
                    print(f"    時間範囲: {chart_data.timeRange}")
                else:
                    print(f"  {timeframe}: 生成されませんでした")
        else:
            print("❌ チャート画像は生成されませんでした")
        
        # JSONファイルとして保存
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        mode_suffix = "_backtest" if enable_backtest else "_normal"
        output_file = output_dir / f"simple_chart_test_{symbol}_{timestamp_str}{mode_suffix}.json"
        
        # チャート情報を判断データに追加
        decision_data.chart_images = chart_images
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(decision_data.to_json())
        
        print(f"\n💾 結果を保存しました: {output_file}")
        
        # 生成された画像ファイルのサイズ確認
        print(f"\n📁 生成されたファイル:")
        chart_dir = Path("charts")
        if chart_dir.exists():
            for chart_file in chart_dir.glob(f"chart_{symbol}_*_{timestamp_str}.png"):
                file_size = chart_file.stat().st_size / 1024  # KB
                print(f"  {chart_file.name} ({file_size:.1f}KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # リソースのクリーンアップ
        chart_generator.close()
        engine.close()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='軽量チャート生成機能のテスト')
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
    print("🚀 軽量チャート生成テスト")
    print("=" * 50)
    print(f"銘柄: {args.symbol}")
    print(f"日時: {timestamp}")
    print(f"モード: {mode_text}")
    print("=" * 50)
    
    # チャート生成テスト実行
    success = test_simple_chart_generation(args.symbol, timestamp, args.backtest)
    
    if success:
        print("\n✅ 軽量チャート生成テストが正常に完了しました")
        print("\n📁 生成されたファイル:")
        print("  - output/simple_chart_test_*.json: 判断データ")
        print("  - charts/chart_*.png: チャート画像")
        print("\n💡 バックテストモードを試すには --backtest オプションを追加してください")
    else:
        print("\n❌ チャート生成テストに失敗しました")
        print("ログファイル logs/simple_chart_test.log を確認してください")


if __name__ == "__main__":
    main()