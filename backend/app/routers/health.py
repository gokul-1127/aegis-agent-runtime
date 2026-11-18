"""Health check router."""
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return basic application health information."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }