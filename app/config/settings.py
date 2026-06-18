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
    llm_provider: str = Field(default="fake")
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-5.4-mini")
    openai_timeout_seconds: float = Field(default=30.0)
    openai_max_output_tokens: int = Field(default=800)
    openai_input_price_per_1m_tokens_usd: str = Field(default="0.75")
    openai_output_price_per_1m_tokens_usd: str = Field(default="4.50")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()