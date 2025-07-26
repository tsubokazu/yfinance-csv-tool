"""
TradingView Lightweight Charts を使用したチャート画像生成エンジン

このモジュールは、TradingView Lightweight Charts ライブラリを使用して
6つの時間軸のチャート画像を生成します。
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from jinja2 import Template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from data_models import ChartImages, MinuteDecisionPackage, TimeframeIndicators, TIMEFRAME_CONFIG


class ChartImageGenerator:
    """TradingView Lightweight Charts を使用したチャート画像生成クラス"""
    
    def __init__(self, output_dir: str = "charts"):
        """
        初期化
        
        Args:
            output_dir: チャート画像の出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # テンプレートディレクトリ作成
        self.template_dir = Path("templates")
        self.template_dir.mkdir(exist_ok=True)
        
        # WebDriverの設定
        self.driver = None
        self._setup_webdriver()
        
        # HTMLテンプレートの作成
        self._create_chart_template()
    
    def _setup_webdriver(self):
        """Seleniumドライバーのセットアップ"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # ヘッドレスモード
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1200,800")
            chrome_options.add_argument("--disable-gpu")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            print(f"WebDriver設定エラー: {e}")
            self.driver = None
    
    def _create_chart_template(self):
        """HTMLチャートテンプレートの作成"""
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #ffffff;
        }
        .chart-container {
            width: 1000px;
            height: 600px;
            margin: 0 auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #ffffff;
        }
        .chart-title {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .chart-info {
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="chart-title">{{ symbol }} - {{ timeframe_name }}</div>
    <div class="chart-info">{{ time_range }}</div>
    <div id="chart" class="chart-container"></div>
    
    <script>
        const chart = LightweightCharts.createChart(document.getElementById('chart'), {
            width: 1000,
            height: 600,
            layout: {
                backgroundColor: '#ffffff',
                textColor: '#333',
            },
            grid: {
                vertLines: {
                    color: '#f0f0f0',
                },
                horzLines: {
                    color: '#f0f0f0',
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#cccccc',
            },
            timeScale: {
                borderColor: '#cccccc',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // ローソク足データの追加
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        const candleData = {{ candle_data|safe }};
        candlestickSeries.setData(candleData);

        // 出来高データの追加
        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
        
        const volumeData = {{ volume_data|safe }};
        volumeSeries.setData(volumeData);

        // 移動平均線の追加
        {% for ma_period, ma_data in moving_averages.items() %}
        const ma{{ ma_period }}Series = chart.addLineSeries({
            color: '{{ ma_colors[ma_period] }}',
            lineWidth: 2,
            title: 'MA{{ ma_period }}',
        });
        ma{{ ma_period }}Series.setData({{ ma_data|safe }});
        {% endfor %}

        // VWAP（該当時間軸のみ）
        {% if vwap_data %}
        const vwapSeries = chart.addLineSeries({
            color: '#FF6B35',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: 'VWAP',
        });
        vwapSeries.setData({{ vwap_data|safe }});
        {% endif %}

        // ボリンジャーバンド（60分足のみ）
        {% if bollinger_bands %}
        const bbUpperSeries = chart.addLineSeries({
            color: '#9C27B0',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: 'BB Upper',
        });
        bbUpperSeries.setData({{ bollinger_bands.upper|safe }});
        
        const bbLowerSeries = chart.addLineSeries({
            color: '#9C27B0',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: 'BB Lower',
        });
        bbLowerSeries.setData({{ bollinger_bands.lower|safe }});
        {% endif %}

        // チャートのフィット
        chart.timeScale().fitContent();
        
        // レンダリング完了のマーク
        window.chartReady = true;
    </script>
</body>
</html>
        """
        
        template_path = self.template_dir / "chart_template.html"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _prepare_chart_data(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """チャートデータの準備"""
        # ローソク足データの変換
        candle_data = []
        volume_data = []
        
        for idx, row in data.iterrows():
            timestamp = int(idx.timestamp())
            
            candle_data.append({
                'time': timestamp,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            })
            
            volume_data.append({
                'time': timestamp,
                'value': float(row['Volume']),
                'color': '#26a69a' if row['Close'] >= row['Open'] else '#ef5350'
            })
        
        # 移動平均線データの準備
        moving_averages = {}
        ma_colors = {
            5: '#FF9800',    # オレンジ
            9: '#2196F3',    # ブルー
            20: '#4CAF50',   # グリーン
            50: '#FF5722',   # レッド
            200: '#9C27B0'   # パープル
        }
        
        if 'moving_averages' in indicators:
            for period, values in indicators['moving_averages'].items():
                ma_period = int(period.replace('ma', ''))
                ma_data = []
                
                for idx, value in values.items():
                    if pd.notna(value):
                        ma_data.append({
                            'time': int(idx.timestamp()),
                            'value': float(value)
                        })
                
                moving_averages[ma_period] = ma_data
        
        # VWAPデータの準備
        vwap_data = None
        if 'vwap' in indicators and 'daily' in indicators['vwap']:
            vwap_data = []
            for idx, value in indicators['vwap']['daily'].items():
                if pd.notna(value):
                    vwap_data.append({
                        'time': int(idx.timestamp()),
                        'value': float(value)
                    })
        
        # ボリンジャーバンドデータの準備
        bollinger_bands = None
        if 'bollinger_bands' in indicators:
            bb = indicators['bollinger_bands']
            if 'upper' in bb and 'lower' in bb:
                bb_upper = []
                bb_lower = []
                
                for idx, value in bb['upper'].items():
                    if pd.notna(value):
                        bb_upper.append({
                            'time': int(idx.timestamp()),
                            'value': float(value)
                        })
                
                for idx, value in bb['lower'].items():
                    if pd.notna(value):
                        bb_lower.append({
                            'time': int(idx.timestamp()),
                            'value': float(value)
                        })
                
                bollinger_bands = {
                    'upper': bb_upper,
                    'lower': bb_lower
                }
        
        return {
            'candle_data': candle_data,
            'volume_data': volume_data,
            'moving_averages': moving_averages,
            'ma_colors': ma_colors,
            'vwap_data': vwap_data,
            'bollinger_bands': bollinger_bands
        }
    
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
            timeframe: 時間軸 (weekly, daily, hourly_60, etc.)
            symbol: 銘柄コード
            data: OHLCV データ
            indicators: テクニカル指標データ
            timestamp: 生成時刻
            
        Returns:
            生成された画像ファイルのパス
        """
        if self.driver is None:
            raise RuntimeError("WebDriverが初期化されていません")
        
        # チャートデータの準備
        chart_data = self._prepare_chart_data(data, indicators)
        
        # 時間軸名の取得
        timeframe_names = {
            'weekly': '週足',
            'daily': '日足', 
            'hourly_60': '60分足',
            'minute_15': '15分足',
            'minute_5': '5分足',
            'minute_1': '1分足'
        }
        
        # 時間範囲の計算
        start_time = data.index[0].strftime('%Y-%m-%d %H:%M')
        end_time = data.index[-1].strftime('%Y-%m-%d %H:%M')
        time_range = f"{start_time} to {end_time}"
        
        # テンプレートの読み込みと描画
        template_path = self.template_dir / "chart_template.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        html_content = template.render(
            symbol=symbol,
            timeframe_name=timeframe_names.get(timeframe, timeframe),
            time_range=time_range,
            **chart_data
        )
        
        # 一時HTMLファイルの作成
        temp_html_path = self.output_dir / f"temp_chart_{timeframe}.html"
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # ブラウザでHTMLを開く
        file_url = f"file://{temp_html_path.absolute()}"
        self.driver.get(file_url)
        
        # チャートの描画完了を待機
        for _ in range(30):  # 最大30秒待機
            try:
                if self.driver.execute_script("return window.chartReady === true"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            print(f"警告: {timeframe} チャートの描画タイムアウト")
        
        # 追加の描画完了待機
        time.sleep(2)
        
        # スクリーンショットの撮影
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        image_filename = f"chart_{symbol}_{timeframe}_{timestamp_str}.png"
        image_path = self.output_dir / image_filename
        
        self.driver.save_screenshot(str(image_path))
        
        # 一時ファイルの削除
        temp_html_path.unlink()
        
        return str(image_path)
    
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
                    
                except Exception as e:
                    print(f"❌ {display_name}チャート生成エラー: {e}")
                    continue
        
        return ChartImages(**chart_images)
    
    def close(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()
            self.driver = None


# ヘルパー関数
def create_chart_generator() -> ChartImageGenerator:
    """チャート生成エンジンのファクトリー関数"""
    return ChartImageGenerator()