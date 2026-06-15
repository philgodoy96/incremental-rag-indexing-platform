from fastapi import FastAPI

from app.api.routes.health import router as health_router
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

    return app


app = create_app()
