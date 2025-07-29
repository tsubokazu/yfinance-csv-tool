"""
API Router for v1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, trading

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])