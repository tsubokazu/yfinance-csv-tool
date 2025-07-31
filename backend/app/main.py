"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.config import settings

# Configure basic logging for now
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting yfinance Trading Platform API...")
    # TODO: Initialize services
    # - Setup logging
    # - Connect to databases
    # - Initialize cache
    # - Load ML models
    
    yield
    
    # Shutdown
    logger.info("Shutting down yfinance Trading Platform API...")
    # TODO: Cleanup
    # - Close database connections
    # - Clear cache
    # - Save state

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="高速トレーディング分析プラットフォーム - AI判断と効率化システム搭載",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

# Include routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to yfinance Trading Platform API",
        "documentation": "/docs",
        "health": "/health"
    }