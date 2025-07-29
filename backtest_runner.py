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
from ai_trading_decision import AITradingDecisionEngine


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
    enable_ai_decision: bool = True,
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
        enable_ai_decision: AI売買判断機能有効
        output_dir: 出力ディレクトリ
        
    Returns:
        バックテスト結果サマリー
    """
    print(f"🎯 バックテスト開始: {symbol}")
    print(f"  期間: {start_datetime} ～ {end_datetime}")
    print(f"  間隔: {interval_minutes}分")
    print(f"  チャート生成: {'有効' if enable_charts else '無効'}")
    print(f"  AI売買判断: {'有効' if enable_ai_decision else '無効'}")
    
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
    
    # AI判断エンジン初期化（有効な場合）
    ai_engine = None
    if enable_ai_decision:
        try:
            ai_engine = AITradingDecisionEngine(enable_logging=True)
            print("🤖 AI売買判断エンジン初期化完了")
        except Exception as e:
            print(f"⚠️ AI売買判断エンジン初期化失敗: {e}")
            print("   OPENAI_API_KEYが設定されているか確認してください")
            enable_ai_decision = False
    
    results = []
    failed_count = 0
    
    try:
        # 進捗バーを表示してバックテスト実行
        for timestamp in tqdm(timeline, desc="バックテスト進行中"):
            try:
                # 判断データ生成
                decision_data = engine.get_backtest_decision_data(symbol, timestamp)
                
                # AI売買判断実行（有効な場合）
                ai_decision = None
                if enable_ai_decision and ai_engine:
                    try:
                        ai_decision = ai_engine.analyze_trading_decision(decision_data)
                        print(f"🤖 AI判断: {ai_decision.get('trading_decision', 'ERROR')} (信頼度: {ai_decision.get('confidence_level', 0):.2f})")
                    except Exception as e:
                        print(f"⚠️ AI判断エラー: {e}")
                        ai_decision = {"error": str(e), "trading_decision": "ERROR"}
                
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
                    'chart_images': {},
                    
                    # AI売買判断結果（主要項目のみCSVに含める）
                    'ai_trading_decision': ai_decision.get('trading_decision', 'HOLD') if ai_decision else 'HOLD',
                    'ai_confidence': ai_decision.get('confidence_level', 0.0) if ai_decision else 0.0,
                    'ai_strategy': ai_decision.get('strategy_used', 'なし') if ai_decision else 'なし',
                    'ai_reasoning': '; '.join(ai_decision.get('reasoning', [])) if ai_decision and ai_decision.get('reasoning') else 'データ不足',
                    'ai_risk_factors': '; '.join(ai_decision.get('risk_factors', [])) if ai_decision and ai_decision.get('risk_factors') else 'データ不足',
                    
                    # 将来エントリー条件
                    'ai_buy_conditions': '; '.join(ai_decision.get('future_entry_conditions', {}).get('buy_conditions', [])) if ai_decision and ai_decision.get('future_entry_conditions') else 'なし',
                    'ai_sell_conditions': '; '.join(ai_decision.get('future_entry_conditions', {}).get('sell_conditions', [])) if ai_decision and ai_decision.get('future_entry_conditions') else 'なし',
                    'ai_next_review': ai_decision.get('future_entry_conditions', {}).get('next_review_trigger', 'なし') if ai_decision and ai_decision.get('future_entry_conditions') else 'なし',
                    'ai_market_phase': ai_decision.get('market_outlook', {}).get('market_phase', 'なし') if ai_decision and ai_decision.get('market_outlook') else 'なし',
                    'ai_recommended_strategy': ai_decision.get('market_outlook', {}).get('recommended_strategy', 'なし') if ai_decision and ai_decision.get('market_outlook') else 'なし',
                    'ai_full_data': ai_decision  # 完全なデータはJSONサマリーに保存
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
    
    # 結果を保存（セッション統一形式）
    session_id = f"{symbol}_{start_datetime.strftime('%Y%m%d_%H%M')}-{end_datetime.strftime('%H%M')}"
    
    # サマリーJSON（シリアライゼーション対応）
    summary_file = output_path / f"{session_id}_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    # CSV形式のサマリー（見やすく整理）
    if results:
        df = pd.DataFrame(results)
        
        # CSV列の順序を整理
        csv_columns = [
            'timestamp', 'symbol', 'current_price', 'price_change_percent', 'volume_ratio',
            'ai_trading_decision', 'ai_confidence', 'ai_strategy',
            'ai_reasoning', 'ai_risk_factors',
            'ai_buy_conditions', 'ai_sell_conditions', 'ai_next_review',
            'ai_market_phase', 'ai_recommended_strategy',
            'ma20_daily', 'ma50_daily', 'atr14_daily', 'vwap_60m'
        ]
        
        # 存在する列のみを選択
        available_columns = [col for col in csv_columns if col in df.columns]
        df_ordered = df[available_columns]
        
        csv_file = output_path / f"{session_id}_data.csv"
        df_ordered.to_csv(csv_file, index=False, encoding='utf-8')
        
        # AI判断サマリーレポートも作成
        ai_summary_file = output_path / f"{session_id}_ai_report.txt"
        _create_ai_summary_report(df, ai_summary_file, symbol, start_datetime, end_datetime)
        
        print(f"\n📊 バックテスト完了!")
        print(f"  成功: {len(results)}/{len(timeline)}件 ({summary['success_rate']:.1f}%)")
        print(f"  失敗: {failed_count}件")
        print(f"\n💾 出力ファイル:")
        print(f"  📋 データCSV: {csv_file}")
        print(f"  📄 詳細JSON: {summary_file}")
        print(f"  📝 AIレポート: {ai_summary_file}")
        
        # 価格統計
        prices = [r['current_price'] for r in results]
        print(f"\n📈 価格統計:")
        print(f"  最高値: ¥{max(prices):,.0f}")
        print(f"  最安値: ¥{min(prices):,.0f}")
        print(f"  平均値: ¥{sum(prices)/len(prices):,.0f}")
    
    return summary


def _create_ai_summary_report(df: pd.DataFrame, output_file: Path, symbol: str, start_datetime: datetime, end_datetime: datetime):
    """AI判断サマリーレポートを作成"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🤖 AI トレーディング判断サマリーレポート\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"📊 基本情報\n")
        f.write(f"  銘柄: {symbol}\n")
        f.write(f"  期間: {start_datetime} ～ {end_datetime}\n")
        f.write(f"  判断回数: {len(df)}回\n\n")
        
        # AI判断統計
        if 'ai_trading_decision' in df.columns:
            decisions = df['ai_trading_decision'].value_counts()
            f.write(f"🎯 AI判断統計\n")
            for decision, count in decisions.items():
                percentage = count / len(df) * 100
                f.write(f"  {decision}: {count}回 ({percentage:.1f}%)\n")
            f.write("\n")
            
            # 平均信頼度
            if 'ai_confidence' in df.columns:
                avg_confidence = df['ai_confidence'].mean()
                f.write(f"📈 平均信頼度: {avg_confidence:.2f}\n\n")
            
            # 戦略使用統計
            if 'ai_strategy' in df.columns:
                strategies = df['ai_strategy'].value_counts()
                f.write(f"🎛️ 使用戦略統計\n")
                for strategy, count in strategies.items():
                    percentage = count / len(df) * 100
                    f.write(f"  {strategy}: {count}回 ({percentage:.1f}%)\n")
                f.write("\n")
        
        # 価格統計
        if 'current_price' in df.columns:
            prices = df['current_price']
            f.write(f"💰 価格統計\n")
            f.write(f"  最高値: ¥{prices.max():,.0f}\n")
            f.write(f"  最安値: ¥{prices.min():,.0f}\n")
            f.write(f"  平均値: ¥{prices.mean():,.0f}\n")
            f.write(f"  変動率: {((prices.max() - prices.min()) / prices.mean() * 100):.2f}%\n\n")
        
        # 主要な判断理由トップ5
        if 'ai_reasoning' in df.columns:
            all_reasons = []
            for reasons_str in df['ai_reasoning'].dropna():
                if reasons_str not in ['なし', 'データ不足', '']:
                    reasons = reasons_str.split('; ')
                    all_reasons.extend(reasons)
            
            if all_reasons:
                from collections import Counter
                top_reasons = Counter(all_reasons).most_common(5)
                f.write(f"🔍 主要な判断理由 TOP5\n")
                for i, (reason, count) in enumerate(top_reasons, 1):
                    f.write(f"  {i}. {reason} ({count}回)\n")
                f.write("\n")
        
        # 主要なリスク要因トップ5
        if 'ai_risk_factors' in df.columns:
            all_risks = []
            for risks_str in df['ai_risk_factors'].dropna():
                if risks_str not in ['なし', 'データ不足', '']:
                    risks = risks_str.split('; ')
                    all_risks.extend(risks)
            
            if all_risks:
                from collections import Counter
                top_risks = Counter(all_risks).most_common(5)
                f.write(f"⚠️ 主要なリスク要因 TOP5\n")
                for i, (risk, count) in enumerate(top_risks, 1):
                    f.write(f"  {i}. {risk} ({count}回)\n")
                f.write("\n")
        
        # 時系列の判断変化
        if 'ai_trading_decision' in df.columns and len(df) > 1:
            f.write(f"📅 時系列判断変化\n")
            prev_decision = None
            changes = 0
            for _, row in df.iterrows():
                current_decision = row['ai_trading_decision']
                timestamp = row['timestamp']
                confidence = row.get('ai_confidence', 0)
                
                if prev_decision and prev_decision != current_decision:
                    f.write(f"  {timestamp}: {prev_decision} → {current_decision} (信頼度: {confidence:.2f})\n")
                    changes += 1
                prev_decision = current_decision
            
            f.write(f"\n  判断変更回数: {changes}回\n")
        
        # 将来エントリー条件サマリー（最新データのみ）
        if len(df) > 0:
            latest_row = df.iloc[-1]
            f.write(f"\n🎯 最新の将来エントリー条件\n")
            f.write(f"  時刻: {latest_row['timestamp']}\n")
            f.write(f"  市場フェーズ: {latest_row.get('ai_market_phase', 'なし')}\n")
            f.write(f"  推奨戦略: {latest_row.get('ai_recommended_strategy', 'なし')}\n")
            
            buy_conditions = latest_row.get('ai_buy_conditions', 'なし')
            if buy_conditions and buy_conditions != 'なし':
                f.write(f"\n  📈 今後のBUY条件:\n")
                for condition in buy_conditions.split('; '):
                    if condition.strip():
                        f.write(f"    - {condition.strip()}\n")
            
            sell_conditions = latest_row.get('ai_sell_conditions', 'なし')
            if sell_conditions and sell_conditions != 'なし':
                f.write(f"\n  📉 今後のSELL条件:\n")
                for condition in sell_conditions.split('; '):
                    if condition.strip():
                        f.write(f"    - {condition.strip()}\n")
            
            next_review = latest_row.get('ai_next_review', 'なし')
            if next_review and next_review != 'なし':
                f.write(f"\n  ⏰ 次回見直しタイミング: {next_review}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📝 このレポートは自動生成されました\n")
        f.write("=" * 80 + "\n")


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
    parser.add_argument('--no-ai-decision', action='store_true',
                       help='AI売買判断を無効化')
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
        enable_ai_decision=not args.no_ai_decision,
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