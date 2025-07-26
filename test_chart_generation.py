#!/usr/bin/env python3
"""
チャート生成機能のテストスクリプト

TradingView Lightweight Charts を使用したチャート画像生成をテストします。
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
            logging.FileHandler('logs/chart_test.log')
        ]
    )


def test_chart_generation(symbol: str, timestamp: datetime):
    """
    チャート生成のテスト
    
    Args:
        symbol: 銘柄コード
        timestamp: 判断時刻
    """
    print(f"🔄 チャート生成テスト開始: {symbol} at {timestamp}")
    
    # チャート生成エンジンを有効にしてMinuteDecisionEngineを初期化
    engine = MinuteDecisionEngine(enable_chart_generation=True)
    
    try:
        # 判断データ生成（チャート含む）
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
            charts = decision_data.chart_images
            
            for timeframe in ['weekly', 'daily', 'hourly_60', 'minute_15', 'minute_5', 'minute_1']:
                chart_data = getattr(charts, timeframe, None)
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
        output_file = output_dir / f"chart_test_{symbol}_{timestamp_str}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(decision_data.to_json())
        
        print(f"\n💾 結果を保存しました: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
        
    finally:
        # リソースのクリーンアップ
        engine.close()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='チャート生成機能のテスト')
    parser.add_argument('--symbol', '-s', default='6723.T', 
                       help='銘柄コード (デフォルト: 6723.T)')
    parser.add_argument('--datetime', '-d', 
                       help='判断日時 (YYYY-MM-DD HH:MM形式、省略時は現在時刻)')
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
    
    print("🚀 TradingView チャート生成テスト")
    print("=" * 50)
    print(f"銘柄: {args.symbol}")
    print(f"日時: {timestamp}")
    print("=" * 50)
    
    # 必要なライブラリがインストールされているかチェック
    try:
        import selenium
        import jinja2
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ 必要なライブラリがインストールされています")
    except ImportError as e:
        print(f"❌ 必要なライブラリがインストールされていません: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install selenium webdriver-manager jinja2")
        return
    
    # チャート生成テスト実行
    success = test_chart_generation(args.symbol, timestamp)
    
    if success:
        print("\n✅ チャート生成テストが正常に完了しました")
        print("\n📁 生成されたファイル:")
        print("  - output/chart_test_*.json: 判断データ")
        print("  - charts/chart_*.png: チャート画像")
    else:
        print("\n❌ チャート生成テストに失敗しました")
        print("ログファイル logs/chart_test.log を確認してください")


if __name__ == "__main__":
    main()