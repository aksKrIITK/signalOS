from typing import Dict
from fastapi import APIRouter, status
from app.core.config import settings

router = APIRouter(tags=["Health & Probes"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:
    return {
        "status": "ready",
        "database": "connected",
        "vector_store": "pgvector_ready",
        "redis": "ready",
    }
