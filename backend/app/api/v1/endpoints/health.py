"""
Health check endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, status
from datetime import datetime

from app.core.config import settings

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Detailed readiness check
    """
    checks = {
        "service": True,
        "config": bool(settings.SECRET_KEY),
        "environment": settings.ENVIRONMENT,
    }
    
    all_ready = all(v for v in checks.values() if isinstance(v, bool))
    
    return {
        "status": "ready" if all_ready else "not ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }