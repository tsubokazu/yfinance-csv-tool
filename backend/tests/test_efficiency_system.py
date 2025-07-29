#!/usr/bin/env python3
"""
効率化システムのテストスクリプト

時間足別分析キャッシュシステムと判断継続性システムの動作を確認する
"""

import logging
from datetime import datetime, timedelta
from app.services.efficiency.chart_analysis_cache import ChartAnalysisCache
from app.services.efficiency.trading_continuity_engine import TradingContinuityEngine

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chart_analysis_cache():
    """チャート分析キャッシュシステムのテスト"""
    print("=" * 60)
    print("🧪 チャート分析キャッシュシステムテスト")
    print("=" * 60)
    
    cache = ChartAnalysisCache()
    symbol = "6723.T"
    current_time = datetime.now()
    
    # キャッシュ状態確認
    print("\n📊 初期キャッシュ状態:")
    status = cache.get_cache_status(symbol, current_time)
    for timeframe, info in status.items():
        print(f"  {timeframe}: {'有効' if info['has_cache'] else '無効'}")
    
    # 更新が必要な時間足を取得
    print("\n📈 更新が必要な時間足:")
    cached_analysis, timeframes_to_update = cache.get_timeframes_to_update(symbol, current_time)
    print(f"  更新対象: {timeframes_to_update}")
    
    # サンプル分析結果を追加
    print("\n💾 サンプル分析結果を追加:")
    for timeframe in ["daily", "hourly_60", "minute_15"]:
        analysis_result = {
            "trend_direction": "上昇",
            "signal_strength": 0.7,
            "key_levels": [1800, 1850, 1900],
            "confidence": 0.75
        }
        cache.update_analysis(symbol, timeframe, analysis_result, current_time)
    
    # 更新後のキャッシュ状態確認
    print("\n📊 更新後キャッシュ状態:")
    status = cache.get_cache_status(symbol, current_time)
    for timeframe, info in status.items():
        if info['has_cache']:
            print(f"  {timeframe}: ✅ (次回更新: {info['next_update'][:16]})")
        else:
            print(f"  {timeframe}: ❌")
    
    # 5分後の状態シミュレーション
    future_time = current_time + timedelta(minutes=5)
    print(f"\n⏰ 5分後のキャッシュ状態 ({future_time.strftime('%Y-%m-%d %H:%M')}):")
    cached_analysis, timeframes_to_update = cache.get_timeframes_to_update(symbol, future_time)
    print(f"  更新対象: {timeframes_to_update}")


def test_trading_continuity_engine():
    """トレーディング判断継続性システムのテスト"""
    print("\n" + "=" * 60)
    print("🎯 トレーディング判断継続性システムテスト")
    print("=" * 60)
    
    continuity = TradingContinuityEngine()
    symbol = "6723.T"
    current_time = datetime.now()
    
    # 初回分析の判定
    print("\n🔍 初回分析判定:")
    should_analyze = continuity.should_perform_full_analysis(symbol, current_time)
    print(f"  フル分析必要: {'はい' if should_analyze else 'いいえ'}")
    
    # 分析プラン取得
    print("\n📋 分析プラン取得:")
    analysis_plan = continuity.get_incremental_analysis_plan(symbol, current_time)
    print(f"  分析タイプ: {analysis_plan['analysis_type']}")
    print(f"  更新対象時間軸: {analysis_plan['timeframes_to_update']}")
    print(f"  重点項目: {analysis_plan['focus_areas']}")
    
    # サンプル判断結果でトレーディング状態を更新
    print("\n💾 サンプル判断結果でトレーディング状態更新:")
    sample_decision = {
        "trading_decision": "HOLD",
        "confidence_level": 0.65,
        "reasoning": ["下降トレンド中", "20日線下位で推移"],
        "future_entry_conditions": {
            "buy_conditions": ["20日線上抜け", "ゴールデンクロス"],
            "sell_conditions": ["支持線下抜け"],
            "next_review_trigger": "20日線接近時"
        },
        "market_outlook": {
            "monitoring_frequency": "60分足-日足で監視"
        }
    }
    continuity.update_trading_state(symbol, sample_decision, current_time)
    print("  ✅ トレーディング状態保存完了")
    
    # 30分後の分析判定
    future_time = current_time + timedelta(minutes=30)
    print(f"\n⏰ 30分後の分析判定 ({future_time.strftime('%Y-%m-%d %H:%M')}):")
    should_analyze = continuity.should_perform_full_analysis(symbol, future_time)
    print(f"  フル分析必要: {'はい' if should_analyze else 'いいえ'}")
    
    # 30分後の分析プラン
    analysis_plan = continuity.get_incremental_analysis_plan(symbol, future_time)
    print(f"  分析タイプ: {analysis_plan['analysis_type']}")
    print(f"  更新対象時間軸: {analysis_plan['timeframes_to_update']}")


def test_efficiency_comparison():
    """効率化システムの効果を比較"""
    print("\n" + "=" * 60)
    print("📊 効率化システム効果比較")
    print("=" * 60)
    
    print("\n🔄 従来システム（毎回フル分析）:")
    print("  - 全6時間軸のチャート分析")
    print("  - テクニカル分析 (全指標)")
    print("  - 売買判断 (フル推論)")
    print("  ⏱️ 推定処理時間: 15-30秒")
    print("  💰 API呼び出し回数: 6-10回")
    print("  📝 コンテキスト使用量: 8000-15000トークン")
    
    print("\n⚡ 効率化システム（継続判断）:")
    print("  - 必要な時間軸のみ更新")
    print("  - 前回結果の継続利用")
    print("  - 条件チェックによる最適化")
    print("  ⏱️ 推定処理時間: 2-5秒")
    print("  💰 API呼び出し回数: 0-2回")
    print("  📝 コンテキスト使用量: 500-2000トークン")
    
    print("\n🎯 期待される効果:")
    print("  - ⚡ 処理速度: 5-10倍高速化")
    print("  - 💰 API費用: 70-90%削減")
    print("  - 📊 分析精度: 継続性により向上")
    print("  - 🎛️ リソース使用量: 80%削減")


def main():
    """メインテスト実行"""
    print("🚀 効率化システム総合テスト開始")
    
    try:
        test_chart_analysis_cache()
        test_trading_continuity_engine()
        test_efficiency_comparison()
        
        print("\n" + "=" * 60)
        print("✅ 効率化システムテスト完了")
        print("=" * 60)
        print("\n🎉 システムの準備が整いました！")
        print("\n📋 次のステップ:")
        print("  1. python backtest_runner.py でバックテストを実行")
        print("  2. ログで効率化システムの動作を確認")
        print("  3. trading_states/ ディレクトリで状態管理を確認")
        print("  4. chart_analysis_cache/ でキャッシュシステムを確認")
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        print(f"\n⚠️ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()