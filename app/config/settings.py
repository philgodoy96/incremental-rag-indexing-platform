from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Incremental RAG Indexing Platform")
    app_environment: str = Field(default="local")
    log_level: str = Field(default="INFO")
    api_v1_prefix: str = Field(default="/api/v1")
    database_url: str = Field(
        default="postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_indexing"
    )
    seed_documents_path: str = Field(default="seed_documents")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()