from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    timestamp_utc: datetime


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return basic application health.

    This endpoint intentionally does not check database readiness yet.
    A database readiness check will be added when persistence is introduced.
    """

    settings = get_settings()

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_environment,
        timestamp_utc=datetime.now(UTC),
    )
