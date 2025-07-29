# yfinance Trading Platform - リファクタリング実装計画

## 🎯 プロジェクト概要

yfinanceベースのトレーディングデータツールを、FastAPI + Supabaseを使用したエンタープライズグレードのWeb APIプラットフォームにリファクタリングします。

## 📋 実装フェーズ

### Phase 1: ディレクトリ構造のリファクタリング（Day 1）

#### 1.1 新ディレクトリ構造の作成
```
yfinance-csv-tool/
├── backend/                      # バックエンドAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI エントリーポイント
│   │   ├── core/                # コア機能
│   │   ├── api/                 # APIエンドポイント
│   │   ├── models/              # Pydanticモデル
│   │   ├── services/            # ビジネスロジック
│   │   └── db/                  # データベース関連
│   ├── tests/
│   └── requirements.txt
├── scripts/                      # ユーティリティスクリプト
├── data/                        # 生成データ
├── docs/                        # ドキュメント
└── legacy/                      # 旧コード（一時保管）
```

#### 1.2 ファイル移動計画
- **core/**: config.py, data_models.py, technical_indicators.py
- **services/**: minute_decision_engine.py, market_data_engine.py, batch_decision_engine.py
- **services/ai/**: ai_trading_decision.py, trading_agents.py, trading_tools.py
- **services/efficiency/**: chart_analysis_cache.py, timeframe_chart_analyzer.py, trading_continuity_engine.py
- **services/visualization/**: chart_generator.py, simple_chart_generator.py
- **runners/**: main.py, backtest_runner.py

### Phase 2: FastAPI基本構成（Day 2-3）

#### 2.1 基本セットアップ
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title="yfinance Trading Platform API",
    version="1.0.0",
    description="高速トレーディング分析プラットフォーム"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター
app.include_router(api_router, prefix="/api/v1")
```

#### 2.2 環境設定
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 基本設定
    PROJECT_NAME: str = "yfinance Trading Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # セキュリティ
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Phase 3: Supabase統合（Day 4-5）

#### 3.1 認証システム
```python
# backend/app/core/auth.py
from supabase import create_client, Client
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_supabase_client() -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )

async def get_current_user(
    credentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    # トークン検証ロジック
    pass
```

#### 3.2 データベーススキーマ
```sql
-- Supabaseマイグレーション
CREATE TABLE profiles (
    id UUID REFERENCES auth.users PRIMARY KEY,
    plan TEXT DEFAULT 'free',
    api_calls_remaining INT DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE trading_decisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    symbol TEXT NOT NULL,
    decision TEXT NOT NULL,
    confidence FLOAT,
    strategy_used TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE trading_decisions ENABLE ROW LEVEL SECURITY;
```

### Phase 4: API エンドポイント実装（Day 6-8）

#### 4.1 トレーディングAPI
```python
# backend/app/api/v1/endpoints/trading.py
from fastapi import APIRouter, Depends
from app.models.trading import TradingDecisionRequest, TradingDecisionResponse
from app.services.trading_service import TradingService

router = APIRouter()

@router.post("/decision", response_model=TradingDecisionResponse)
async def get_trading_decision(
    request: TradingDecisionRequest,
    current_user = Depends(get_current_user),
    trading_service: TradingService = Depends()
):
    return await trading_service.get_decision(request, current_user)

@router.get("/symbols/{symbol}/realtime")
async def get_realtime_data(
    symbol: str,
    current_user = Depends(get_current_user)
):
    # リアルタイムデータ取得
    pass
```

#### 4.2 バックテストAPI
```python
# backend/app/api/v1/endpoints/backtest.py
@router.post("/backtest/run")
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    # 非同期バックテスト実行
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        backtest_service.run_async,
        task_id,
        request,
        current_user.id
    )
    return {"task_id": task_id, "status": "started"}
```

### Phase 5: エラーハンドリング・ログ実装（Day 9）

#### 5.1 構造化ログ
```python
# backend/app/core/logging.py
from loguru import logger

def setup_logging():
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        serialize=True,
        level="INFO"
    )
```

#### 5.2 エラーハンドリング
```python
# backend/app/core/exceptions.py
class TradingError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
```

### Phase 6: キャッシュ・パフォーマンス最適化（Day 10-11）

#### 6.1 Redis統合
```python
# backend/app/core/cache.py
import redis.asyncio as redis
from app.core.config import settings

class CacheManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    async def get_or_set(self, key: str, func, ttl: int = 300):
        # キャッシュロジック
        pass
```

### Phase 7: テスト・デプロイ準備（Day 12-14）

#### 7.1 テスト実装
```python
# backend/tests/test_trading_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_trading_decision():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/trading/decision", json={
            "symbol": "AAPL",
            "timestamp": "2025-01-29T10:00:00"
        })
        assert response.status_code == 200
```

#### 7.2 Docker設定
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 マイルストーン

| フェーズ | 期間 | 成果物 |
|---------|------|--------|
| Phase 1 | Day 1 | 新ディレクトリ構造 |
| Phase 2 | Day 2-3 | FastAPI基本構成 |
| Phase 3 | Day 4-5 | Supabase認証 |
| Phase 4 | Day 6-8 | APIエンドポイント |
| Phase 5 | Day 9 | エラー処理・ログ |
| Phase 6 | Day 10-11 | キャッシュ最適化 |
| Phase 7 | Day 12-14 | テスト・デプロイ |

## 🚀 次のステップ

1. **環境準備**
   - Supabaseプロジェクト作成
   - Redis環境構築
   - 開発環境セットアップ

2. **段階的移行**
   - 既存機能を保持しながら新構造へ移行
   - テストカバレッジの確保
   - パフォーマンス計測

3. **本番準備**
   - CI/CDパイプライン構築
   - モニタリング設定
   - ドキュメント整備

## 📝 注意事項

- **後方互換性**: 既存のCLIツールは維持
- **データ移行**: 既存のキャッシュデータは保持
- **段階的リリース**: 機能ごとに段階的にリリース
- **ロールバック**: 各フェーズでロールバック可能な設計

## 🔧 必要なツール・サービス

- Python 3.11+
- FastAPI
- Supabase (Auth, Database, Storage)
- Redis
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Sentry (エラー監視)
- Prometheus + Grafana (メトリクス)

---

**開始日**: 2025年1月29日  
**目標完了日**: 2025年2月12日（2週間）  
**ステータス**: 準備完了