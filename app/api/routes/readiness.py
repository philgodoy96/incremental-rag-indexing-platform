from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.application.services.database_readiness_service import (
    DatabaseReadinessError,
    DatabaseReadinessService,
)
from app.infrastructure.db.session import SessionLocal


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    database: Literal["ok"]
    pgvector_extension: Literal["ok"]
    timestamp_utc: datetime


router = APIRouter()


def get_database_readiness_service() -> DatabaseReadinessService:
    return DatabaseReadinessService(session_factory=SessionLocal)


@router.get("/readiness", response_model=ReadinessResponse)
def readiness_check(
    service: Annotated[
        DatabaseReadinessService,
        Depends(get_database_readiness_service),
    ],
) -> ReadinessResponse:
    """Return application readiness.

    Unlike the health endpoint, this endpoint checks database dependencies.
    """

    try:
        result = service.check()
    except DatabaseReadinessError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": str(exc),
            },
        ) from exc

    return ReadinessResponse(
        status="ready",
        database=result.database_status,
        pgvector_extension=result.pgvector_status,
        timestamp_utc=datetime.now(UTC),
    )