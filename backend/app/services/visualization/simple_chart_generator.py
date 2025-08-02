"""
軽量チャート生成エンジン（matplotlib + mplfinance使用）

TradingViewの代わりに、より軽量で確実なmatplotlibベースのチャート生成を提供します。
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from app.core.data_models import ChartImages, ChartImageData, TIMEFRAME_CONFIG

logger = logging.getLogger(__name__)

# 日本語フォント設定
import matplotlib.font_manager as fm

# 利用可能な日本語フォントを検索
available_fonts = [f.name for f in fm.fontManager.ttflist]
japanese_fonts = []
for font in ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meiryo', 'MS Gothic', 'Arial Unicode MS']:
    if font in available_fonts:
        japanese_fonts.append(font)

# フォールバック付きフォント設定
if japanese_fonts:
    plt.rcParams['font.sans-serif'] = japanese_fonts + ['DejaVu Sans']
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号文字化け対策

class SimpleChartGenerator:
    """軽量チャート生成クラス"""
    
    def __init__(self, output_dir: str = "charts"):
        """
        初期化
        
        Args:
            output_dir: チャート画像の出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # カラーパレット
        self.colors = {
            'ma5': '#FF9800',    # オレンジ
            'ma9': '#2196F3',    # ブルー
            'ma20': '#4CAF50',   # グリーン
            'ma50': '#FF5722',   # レッド
            'ma200': '#9C27B0',  # パープル
            'vwap': '#FF6B35',   # オレンジレッド
            'bb_upper': '#9C27B0',  # パープル
            'bb_lower': '#9C27B0',  # パープル
            'volume_up': '#26a69a',  # 緑
            'volume_down': '#ef5350'  # 赤
        }
        
        # mplfinanceスタイル
        self.mpf_style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a',
                down='#ef5350',
                edge='inherit',
                wick={'up': '#26a69a', 'down': '#ef5350'},
                volume='in'
            ),
            gridstyle='-',
            gridcolor='#f0f0f0',
            facecolor='white'
        )
    
    def _prepare_chart_data(self, data: pd.DataFrame, indicators: Dict) -> Tuple[pd.DataFrame, List]:
        """
        チャートデータとプロット設定を準備
        
        Args:
            data: OHLCV データ
            indicators: テクニカル指標データ
            
        Returns:
            (準備されたデータ, プロット設定リスト)
        """
        if data.empty:
            return data, []
        
        # データをコピーして加工
        chart_data = data.copy()
        addplots = []
        
        # 移動平均線の追加
        if 'moving_averages' in indicators:
            ma_data = indicators['moving_averages']
            for period_key, ma_series in ma_data.items():
                if isinstance(ma_series, pd.Series) and not ma_series.empty:
                    period = int(period_key.replace('ma', ''))
                    color = self.colors.get(period_key, '#666666')
                    
                    # データのインデックスを合わせる
                    aligned_ma = ma_series.reindex(chart_data.index).ffill()
                    
                    addplots.append(
                        mpf.make_addplot(
                            aligned_ma,
                            color=color,
                            width=2,
                            alpha=0.8
                        )
                    )
        
        # VWAPの追加
        if 'vwap' in indicators and 'daily' in indicators['vwap']:
            vwap_series = indicators['vwap']['daily']
            if isinstance(vwap_series, pd.Series) and not vwap_series.empty:
                aligned_vwap = vwap_series.reindex(chart_data.index).ffill()
                
                addplots.append(
                    mpf.make_addplot(
                        aligned_vwap,
                        color=self.colors['vwap'],
                        width=2,
                        linestyle='--',
                        alpha=0.8
                    )
                )
        
        # ボリンジャーバンドの追加
        if 'bollinger_bands' in indicators:
            bb = indicators['bollinger_bands']
            if 'upper' in bb and 'lower' in bb:
                upper_series = bb['upper']
                lower_series = bb['lower']
                
                if isinstance(upper_series, pd.Series) and isinstance(lower_series, pd.Series):
                    aligned_upper = upper_series.reindex(chart_data.index).ffill()
                    aligned_lower = lower_series.reindex(chart_data.index).ffill()
                    
                    addplots.extend([
                        mpf.make_addplot(
                            aligned_upper,
                            color=self.colors['bb_upper'],
                            width=1,
                            linestyle='--',
                            alpha=0.6
                        ),
                        mpf.make_addplot(
                            aligned_lower,
                            color=self.colors['bb_lower'],
                            width=1,
                            linestyle='--',
                            alpha=0.6
                        )
                    ])
        
        return chart_data, addplots
    
    def generate_chart_image(
        self,
        timeframe: str,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict,
        timestamp: datetime
    ) -> str:
        """
        単一時間軸のチャート画像を生成
        
        Args:
            timeframe: 時間軸
            symbol: 銘柄コード
            data: OHLCV データ
            indicators: テクニカル指標データ
            timestamp: 生成時刻
            
        Returns:
            生成された画像ファイルのパス
        """
        try:
            if data.empty:
                logger.warning(f"{timeframe}のデータが空です")
                return ""
            
            # チャートデータの準備
            chart_data, addplots = self._prepare_chart_data(data, indicators)
            
            # 時間軸名の取得（英語版でフォント警告回避）
            timeframe_names = {
                'weekly': 'Weekly',
                'daily': 'Daily', 
                'hourly_60': '60min',
                'minute_15': '15min',
                'minute_5': '5min',
                'minute_1': '1min'
            }
            
            # ファイル名の生成
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            image_filename = f"chart_{symbol}_{timeframe}_{timestamp_str}.png"
            image_path = self.output_dir / image_filename
            
            # チャートタイトル
            title_name = timeframe_names.get(timeframe, timeframe)
            start_time = data.index[0].strftime('%Y-%m-%d %H:%M')
            end_time = data.index[-1].strftime('%Y-%m-%d %H:%M')
            title = f"{symbol} - {title_name}\n{start_time} to {end_time}"
            
            # チャート生成
            fig, axes = mpf.plot(
                chart_data,
                type='candle',
                style=self.mpf_style,
                volume=True,
                addplot=addplots if addplots else None,
                title=title,
                figsize=(12, 8),
                tight_layout=True,
                returnfig=True,
                savefig=dict(
                    fname=str(image_path),
                    dpi=100,
                    bbox_inches='tight',
                    facecolor='white'
                )
            )
            
            # リソースを解放
            plt.close(fig)
            
            logger.info(f"チャート生成完了: {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"チャート生成エラー ({timeframe}): {e}")
            return ""
    
    def generate_all_timeframe_charts(
        self,
        symbol: str,
        timestamp: datetime,
        price_data: Dict[str, pd.DataFrame],
        indicators_data: Dict[str, Dict]
    ) -> ChartImages:
        """
        全時間軸のチャート画像を生成
        
        Args:
            symbol: 銘柄コード
            timestamp: 判断時刻
            price_data: 各時間軸の価格データ
            indicators_data: 各時間軸のテクニカル指標データ
            
        Returns:
            生成されたチャート画像の情報
        """
        chart_images = {}
        
        timeframe_mapping = {
            'weekly': 'weekly',
            'daily': 'daily',
            'hourly_60': '60min',
            'minute_15': '15min',
            'minute_5': '5min',
            'minute_1': '1min'
        }
        
        for internal_name, display_name in timeframe_mapping.items():
            if internal_name in price_data and internal_name in indicators_data:
                try:
                    print(f"📊 {display_name}チャートを生成中...")
                    
                    image_path = self.generate_chart_image(
                        timeframe=internal_name,
                        symbol=symbol,
                        data=price_data[internal_name],
                        indicators=indicators_data[internal_name],
                        timestamp=timestamp
                    )
                    
                    if image_path:
                        # 時間範囲の計算
                        data = price_data[internal_name]
                        start_time = data.index[0].strftime('%Y-%m-%d %H:%M')
                        end_time = data.index[-1].strftime('%Y-%m-%d %H:%M')
                        
                        chart_images[display_name] = {
                            'imagePath': image_path,
                            'timeRange': f"{start_time} to {end_time}",
                            'lastUpdate': timestamp
                        }
                        
                        print(f"✅ {display_name}チャート生成完了: {image_path}")
                    else:
                        print(f"❌ {display_name}チャート生成に失敗しました")
                    
                except Exception as e:
                    print(f"❌ {display_name}チャート生成エラー: {e}")
                    continue
        
        return ChartImages(**chart_images)
    
    def generate_backtest_chart(
        self,
        symbol: str,
        target_datetime: datetime,
        price_data: Dict[str, pd.DataFrame],
        indicators_data: Dict[str, Dict]
    ) -> ChartImages:
        """
        バックテスト用チャート生成（指定時刻でのスナップショット）
        
        Args:
            symbol: 銘柄コード
            target_datetime: 対象時刻
            price_data: 各時間軸の価格データ
            indicators_data: 各時間軸のテクニカル指標データ
            
        Returns:
            生成されたチャート画像の情報
        """
        print(f"🔄 バックテスト用チャート生成: {symbol} at {target_datetime}")
        
        # 指定時刻までのデータにフィルタリング
        filtered_price_data = {}
        filtered_indicators_data = {}
        
        for timeframe, data in price_data.items():
            if data.empty:
                continue
                
            # タイムゾーン考慮でフィルタリング
            if data.index.tz is not None:
                if target_datetime.tzinfo is None:
                    import pytz
                    jst = pytz.timezone('Asia/Tokyo')
                    target_datetime = jst.localize(target_datetime)
                filtered_data = data[data.index <= target_datetime]
            else:
                if target_datetime.tzinfo is not None:
                    target_datetime = target_datetime.replace(tzinfo=None)
                filtered_data = data[data.index <= target_datetime]
            
            if not filtered_data.empty:
                filtered_price_data[timeframe] = filtered_data
                
                # 指標データも同様にフィルタリング
                if timeframe in indicators_data:
                    filtered_indicators = {}
                    for indicator_name, indicator_data in indicators_data[timeframe].items():
                        if isinstance(indicator_data, dict):
                            filtered_indicator_dict = {}
                            for key, series in indicator_data.items():
                                if isinstance(series, pd.Series):
                                    filtered_series = series[series.index <= target_datetime]
                                    filtered_indicator_dict[key] = filtered_series
                                else:
                                    filtered_indicator_dict[key] = series
                            filtered_indicators[indicator_name] = filtered_indicator_dict
                        elif isinstance(indicator_data, pd.Series):
                            filtered_series = indicator_data[indicator_data.index <= target_datetime]
                            filtered_indicators[indicator_name] = filtered_series
                        else:
                            filtered_indicators[indicator_name] = indicator_data
                    
                    filtered_indicators_data[timeframe] = filtered_indicators
        
        # フィルタリングされたデータでチャート生成
        return self.generate_all_timeframe_charts(
            symbol=symbol,
            timestamp=target_datetime,
            price_data=filtered_price_data,
            indicators_data=filtered_indicators_data
        )
    
    def close(self):
        """リソースのクリーンアップ（matplotlib用）"""
        plt.close('all')


# ヘルパー関数
def create_simple_chart_generator() -> SimpleChartGenerator:
    """軽量チャート生成エンジンのファクトリー関数"""
    return SimpleChartGenerator()