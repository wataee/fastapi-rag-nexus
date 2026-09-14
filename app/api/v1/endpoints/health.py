from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/live", summary="Liveness probe")
async def liveness():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}


@router.get("/ready", summary="Readiness probe")
async def readiness():
    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "database": f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
        "cache": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    }
