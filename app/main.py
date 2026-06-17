from fastapi import FastAPI

from app.api.routes.answers import router as answers_router
from app.api.routes.health import router as health_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.retrieval import router as retrieval_router
from app.config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(
        health_router,
        prefix=settings.api_v1_prefix,
        tags=["health"],
    )

    app.include_router(
        readiness_router,
        prefix=settings.api_v1_prefix,
        tags=["readiness"],
    )

    app.include_router(
        ingestion_router,
        prefix=settings.api_v1_prefix,
        tags=["ingestion"],
    )

    app.include_router(
        retrieval_router,
        prefix=settings.api_v1_prefix,
        tags=["retrieval"],
    )

    app.include_router(
        answers_router,
        prefix=settings.api_v1_prefix,
        tags=["answers"],
    )

    return app


app = create_app()