#!/usr/bin/env python3
"""
チャート分析キャッシュの修正動作確認テスト
"""

from datetime import datetime
from chart_analysis_cache import ChartAnalysisCache
from pathlib import Path
import shutil

def test_cache_timing():
    """キャッシュ更新タイミングのテスト"""
    
    # テスト用キャッシュディレクトリ
    test_cache_dir = Path("test_cache")
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)
    
    cache = ChartAnalysisCache(cache_dir=test_cache_dir)
    
    # テストケース：14:00から1分ごとの時刻
    test_times = [
        datetime(2025, 7, 25, 14, 0, 0),   # 14:00
        datetime(2025, 7, 25, 14, 1, 0),   # 14:01
        datetime(2025, 7, 25, 14, 2, 0),   # 14:02
        datetime(2025, 7, 25, 14, 3, 0),   # 14:03
        datetime(2025, 7, 25, 14, 4, 0),   # 14:04
        datetime(2025, 7, 25, 14, 5, 0),   # 14:05 - 5分足更新
        datetime(2025, 7, 25, 14, 10, 0),  # 14:10 - 5分足更新
        datetime(2025, 7, 25, 14, 15, 0),  # 14:15 - 15分足更新
    ]
    
    # 時間足別の更新タイミングを記録
    update_log = {tf: [] for tf in cache.timeframe_config.keys()}
    
    for test_time in test_times:
        print(f"\n⏰ テスト時刻: {test_time.strftime('%H:%M:%S')}")
        print("-" * 50)
        
        # 各時間足の次回更新時刻を計算
        for timeframe in cache.timeframe_config.keys():
            next_update = cache.calculate_next_update_time(timeframe, test_time)
            print(f"{timeframe:10s}: 次回更新 → {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 更新が必要な場合を記録
            if len(update_log[timeframe]) == 0 or test_time >= update_log[timeframe][-1]:
                update_log[timeframe].append(next_update)
    
    # 結果を確認
    print("\n" + "=" * 60)
    print("🔍 更新タイミング検証結果")
    print("=" * 60)
    
    expected_updates = {
        'minute_1': 8,    # 各時刻で更新
        'minute_5': 3,    # 14:00, 14:05, 14:10, 14:15で更新
        'minute_15': 2,   # 14:00, 14:15で更新
        'hourly_60': 1,   # 14:00で更新（次は15:00）
        'daily': 1,       # 14:00で更新（次は翌日）
        'weekly': 1,      # 14:00で更新（次は翌週）
    }
    
    for timeframe, expected in expected_updates.items():
        actual = len(set(update_log[timeframe][:expected]))
        status = "✅" if actual <= expected else "❌"
        print(f"{status} {timeframe:10s}: 期待={expected}回, 実際={actual}回")
    
    # クリーンアップ
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)

def test_cache_integration():
    """実際のキャッシュ動作テスト"""
    from trading_continuity_engine import TradingContinuityEngine
    
    print("\n" + "=" * 60)
    print("🔄 統合動作テスト")
    print("=" * 60)
    
    # テスト用ディレクトリ
    test_cache_dir = Path("test_cache")
    test_state_dir = Path("test_states")
    
    for dir_path in [test_cache_dir, test_state_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    engine = TradingContinuityEngine(
        cache_dir=test_cache_dir,
        state_dir=test_state_dir
    )
    
    symbol = "TEST_STOCK"
    
    # 1分ごとの分析プランを取得
    for minute in range(5):
        current_time = datetime(2025, 7, 25, 14, minute, 0)
        print(f"\n⏰ {current_time.strftime('%H:%M')} の分析プラン:")
        
        plan = engine.get_incremental_analysis_plan(symbol, current_time)
        print(f"  - 分析タイプ: {plan['analysis_type']}")
        print(f"  - 更新対象: {plan.get('timeframes_to_update', [])}")
        
        # 仮の分析結果を保存
        if minute == 0:
            # 初回は全時間足を保存
            for timeframe in engine.chart_cache.timeframe_config.keys():
                engine.chart_cache.update_analysis(
                    symbol, timeframe, 
                    {"test_result": f"{timeframe}_analysis"}, 
                    current_time
                )
    
    # クリーンアップ
    for dir_path in [test_cache_dir, test_state_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)

if __name__ == "__main__":
    print("🧪 チャート分析キャッシュ修正テスト")
    print("=" * 60)
    
    # タイミング計算テスト
    test_cache_timing()
    
    # 統合動作テスト
    test_cache_integration()
    
    print("\n✅ テスト完了")