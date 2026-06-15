from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DatabaseReadinessResult:
    database_status: Literal["ok"]
    pgvector_status: Literal["ok"]


class DatabaseReadinessError(RuntimeError):
    """Raised when the database is not ready for application use."""


class DatabaseReadinessService:
    """Checks whether database dependencies are ready."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def check(self) -> DatabaseReadinessResult:
        try:
            with self._session_factory() as session:
                database_result = session.execute(text("SELECT 1")).scalar_one()

                if database_result != 1:
                    raise DatabaseReadinessError(
                        "database readiness query returned an unexpected result"
                    )

                pgvector_available = bool(
                    session.execute(
                        text(
                            """
                            SELECT EXISTS (
                                SELECT 1
                                FROM pg_extension
                                WHERE extname = 'vector'
                            )
                            """
                        )
                    ).scalar_one()
                )

                if not pgvector_available:
                    raise DatabaseReadinessError("pgvector extension is not installed")

                return DatabaseReadinessResult(
                    database_status="ok",
                    pgvector_status="ok",
                )

        except DatabaseReadinessError:
            raise
        except Exception as exc:
            raise DatabaseReadinessError("database readiness check failed") from exc