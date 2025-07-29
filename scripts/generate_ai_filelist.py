#!/usr/bin/env python3
"""
AI(LLMエージェント)用ファイル一覧生成スクリプト

バックテスト結果から、AIに渡すべきファイル一覧を生成します。
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def find_latest_backtest(result_dir: str = "backtest_results") -> Dict:
    """
    最新のバックテスト結果を検索
    
    Args:
        result_dir: バックテスト結果ディレクトリ
        
    Returns:
        最新のバックテスト結果辞書
    """
    result_path = Path(result_dir)
    if not result_path.exists():
        raise FileNotFoundError(f"バックテスト結果ディレクトリが見つかりません: {result_dir}")
    
    # サマリーファイルを検索
    summary_files = list(result_path.glob("backtest_summary_*.json"))
    if not summary_files:
        raise FileNotFoundError("バックテスト結果が見つかりません")
    
    # 最新のファイルを取得（ファイル名のタイムスタンプでソート）
    latest_file = max(summary_files, key=lambda f: f.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_ai_filelist(backtest_result: Dict, output_file: str = "ai_filelist.json") -> Dict:
    """
    AI用ファイル一覧を生成
    
    Args:
        backtest_result: バックテスト結果
        output_file: 出力ファイル名
        
    Returns:
        AI用ファイル一覧辞書
    """
    symbol = backtest_result['symbol']
    start_time = backtest_result['start_datetime']
    end_time = backtest_result['end_datetime']
    
    ai_filelist = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "symbol": symbol,
            "backtest_period": f"{start_time} to {end_time}",
            "total_datapoints": backtest_result['total_datapoints'],
            "successful_datapoints": backtest_result['successful_datapoints'],
            "success_rate": backtest_result['success_rate']
        },
        "data_files": {
            "summary_json": None,
            "csv_data": None,
            "detail_files": []
        },
        "chart_images": {},
        "trading_decisions": []
    }
    
    # データファイルのパス設定
    timestamp_str = datetime.fromisoformat(start_time).strftime('%Y%m%d_%H%M%S')
    ai_filelist["data_files"]["summary_json"] = f"backtest_results/backtest_summary_{symbol}_{timestamp_str}.json"
    ai_filelist["data_files"]["csv_data"] = f"backtest_results/backtest_data_{symbol}_{timestamp_str}.csv"
    
    # 詳細ファイルの検索
    detail_pattern = f"backtest_results/detail_{symbol}_*.json"
    detail_files = list(Path(".").glob(detail_pattern.replace("backtest_results/", "backtest_results/")))
    ai_filelist["data_files"]["detail_files"] = [str(f) for f in detail_files]
    
    # 各時刻のチャート画像と判断データを整理
    for i, result in enumerate(backtest_result['results']):
        timestamp = result['timestamp']
        decision_data = {
            "timestamp": timestamp,
            "datapoint_index": i + 1,
            "price_data": {
                "current_price": result['current_price'],
                "price_change_percent": result['price_change_percent'],
                "volume_ratio": result['volume_ratio']
            },
            "technical_indicators": {
                "ma20_daily": result['ma20_daily'],
                "ma50_daily": result['ma50_daily'],
                "atr14_daily": result['atr14_daily'],
                "vwap_60m": result['vwap_60m']
            },
            "chart_images": result.get('chart_images', {}),
            "ai_decision": None,  # AIの判断結果を記録する場所
            "trading_action": None  # 実際の取引アクションを記録する場所
        }
        
        ai_filelist["trading_decisions"].append(decision_data)
        
        # チャート画像の存在確認
        for timeframe, image_path in result.get('chart_images', {}).items():
            if Path(image_path).exists():
                if timeframe not in ai_filelist["chart_images"]:
                    ai_filelist["chart_images"][timeframe] = []
                ai_filelist["chart_images"][timeframe].append({
                    "timestamp": timestamp,
                    "path": image_path,
                    "exists": True
                })
    
    # ファイル一覧を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ai_filelist, f, indent=2, ensure_ascii=False)
    
    return ai_filelist


def print_file_summary(ai_filelist: Dict):
    """AI用ファイル一覧のサマリーを表示"""
    metadata = ai_filelist["metadata"]
    
    print("🤖 AI(LLMエージェント)用ファイル一覧")
    print("=" * 60)
    print(f"銘柄: {metadata['symbol']}")
    print(f"期間: {metadata['backtest_period']}")
    print(f"データポイント数: {metadata['successful_datapoints']}/{metadata['total_datapoints']} ({metadata['success_rate']:.1f}%)")
    print(f"生成日時: {metadata['generated_at']}")
    
    print(f"\n📊 データファイル:")
    print(f"  サマリー: {ai_filelist['data_files']['summary_json']}")
    print(f"  CSVデータ: {ai_filelist['data_files']['csv_data']}")
    print(f"  詳細ファイル: {len(ai_filelist['data_files']['detail_files'])}件")
    
    print(f"\n🖼️  チャート画像:")
    for timeframe, images in ai_filelist["chart_images"].items():
        print(f"  {timeframe}: {len(images)}枚")
    
    total_images = sum(len(images) for images in ai_filelist["chart_images"].values())
    print(f"  合計: {total_images}枚")
    
    print(f"\n🎯 判断データポイント:")
    for i, decision in enumerate(ai_filelist["trading_decisions"][:3]):  # 最初の3件のみ表示
        print(f"  {i+1}. {decision['timestamp']} - ¥{decision['price_data']['current_price']:,.0f} ({decision['price_data']['price_change_percent']:+.2f}%)")
    
    if len(ai_filelist["trading_decisions"]) > 3:
        print(f"  ... 他{len(ai_filelist['trading_decisions']) - 3}件")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='AI用ファイル一覧生成')
    parser.add_argument('--result-dir', '-r', default='backtest_results',
                       help='バックテスト結果ディレクトリ')
    parser.add_argument('--output', '-o', default='ai_filelist.json',
                       help='出力ファイル名')
    parser.add_argument('--latest-only', action='store_true',
                       help='最新のバックテスト結果のみ使用')
    
    args = parser.parse_args()
    
    try:
        print("🔍 バックテスト結果を検索中...")
        
        if args.latest_only:
            # 最新のバックテスト結果のみ
            backtest_result = find_latest_backtest(args.result_dir)
            print(f"✅ 最新のバックテスト結果を発見: {backtest_result['symbol']}")
        else:
            # 指定されたバックテスト結果（今回は最新を使用）
            backtest_result = find_latest_backtest(args.result_dir)
            print(f"✅ バックテスト結果を読み込み: {backtest_result['symbol']}")
        
        print("📝 AI用ファイル一覧を生成中...")
        ai_filelist = generate_ai_filelist(backtest_result, args.output)
        
        print(f"💾 ファイル一覧を保存: {args.output}")
        print_file_summary(ai_filelist)
        
        print(f"\n🚀 次のステップ:")
        print(f"  1. {args.output} をAIシステムに読み込ませる")
        print(f"  2. 各時刻のチャート画像をAIに分析させる")
        print(f"  3. 判断結果を ai_decision フィールドに記録する")
        print(f"  4. 取引シミュレーションを実行する")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())