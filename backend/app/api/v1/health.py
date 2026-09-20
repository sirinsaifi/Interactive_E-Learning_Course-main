"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.config import settings
from app.schemas.common import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Service health")
def health(db: Session = Depends(db_session)) -> HealthResponse:
    db_ok = HealthService(db).check_database()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database="ok" if db_ok else "down",
    )


@router.get("/live", summary="Liveness probe")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe")
def readiness(db: Session = Depends(db_session)) -> dict[str, str]:
    ok = HealthService(db).check_database()
    return {"status": "ready" if ok else "not_ready"}
