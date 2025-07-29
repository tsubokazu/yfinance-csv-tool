#!/usr/bin/env python3
"""
キャッシュシステムの簡易動作確認
"""

import subprocess
import time
from pathlib import Path
import shutil

def test_cache_with_backtest():
    """実際のバックテストでキャッシュ動作を確認"""
    
    print("🧪 キャッシュシステム動作テスト")
    print("=" * 60)
    
    # キャッシュディレクトリをクリア
    cache_dir = Path("cache")
    state_dir = Path("trading_states")
    
    for dir_path in [cache_dir, state_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"🗑️  {dir_path} をクリア")
    
    # テスト1: 2分間のバックテスト
    print("\n📊 テスト1: 2分間のバックテスト（14:00-14:01）")
    print("-" * 60)
    
    start_time = time.time()
    result1 = subprocess.run([
        "python", "backtest_runner.py",
        "--symbol", "TEST_STOCK",
        "--start", "2025-07-25 14:00",
        "--end", "2025-07-25 14:01",
        "--interval", "1",
        "--no-charts",  # チャート生成は無効化してテストを高速化
        "--no-ai-decision"  # AI判断も無効化
    ], capture_output=True, text=True)
    
    elapsed1 = time.time() - start_time
    print(f"⏱️  実行時間: {elapsed1:.2f}秒")
    
    # キャッシュファイルの確認
    cache_files = list(cache_dir.glob("*.json")) if cache_dir.exists() else []
    print(f"📁 生成されたキャッシュファイル: {len(cache_files)}個")
    
    if cache_files:
        print("\n📋 キャッシュファイル内容確認:")
        for cache_file in cache_files:
            print(f"  - {cache_file.name}")
            
            # ファイルサイズ確認
            size = cache_file.stat().st_size
            print(f"    サイズ: {size} bytes")
    
    # テスト2: 連続実行でキャッシュの効果を確認
    print("\n📊 テスト2: 同じ期間を再実行（キャッシュ効果確認）")
    print("-" * 60)
    
    start_time = time.time()
    result2 = subprocess.run([
        "python", "backtest_runner.py",
        "--symbol", "TEST_STOCK",
        "--start", "2025-07-25 14:00",
        "--end", "2025-07-25 14:01",
        "--interval", "1",
        "--no-charts",
        "--no-ai-decision"
    ], capture_output=True, text=True)
    
    elapsed2 = time.time() - start_time
    print(f"⏱️  実行時間: {elapsed2:.2f}秒")
    
    # パフォーマンス比較
    if elapsed1 > 0:
        speedup = elapsed1 / elapsed2
        print(f"🚀 速度向上: {speedup:.1f}倍")
    
    # エラーチェック
    if result1.returncode != 0:
        print(f"\n❌ テスト1でエラー発生:")
        print(result1.stderr)
    
    if result2.returncode != 0:
        print(f"\n❌ テスト2でエラー発生:")
        print(result2.stderr)
    
    # クリーンアップ
    for dir_path in [cache_dir, state_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    test_cache_with_backtest()