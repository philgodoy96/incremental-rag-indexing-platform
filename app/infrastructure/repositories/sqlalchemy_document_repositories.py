from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.domain.documents.entities import (
    DocumentVersion,
    IngestionRun,
    SectionVersion,
    SourceDocument,
)
from app.domain.documents.enums import SourceSystem
from app.domain.documents.repositories import (
    DocumentVersionRepository,
    IngestionRunRepository,
    SectionVersionRepository,
    SourceDocumentRepository,
)
from app.infrastructure.db.mappers.document_mappers import (
    document_version_from_model,
    document_version_to_model,
    ingestion_run_from_model,
    ingestion_run_to_model,
    section_version_from_model,
    section_version_to_model,
    source_document_from_model,
    source_document_to_model,
)
from app.infrastructure.db.models.document_models import (
    DocumentVersionModel,
    IngestionRunModel,
    SectionVersionModel,
    SourceDocumentModel,
)


class SqlAlchemySourceDocumentRepository(SourceDocumentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, document_id: UUID) -> SourceDocument | None:
        model = self._session.get(SourceDocumentModel, document_id)

        if model is None:
            return None

        return source_document_from_model(model)

    def get_by_external_id(
        self,
        *,
        source_system: SourceSystem,
        external_id: str,
    ) -> SourceDocument | None:
        statement: Select[tuple[SourceDocumentModel]] = select(SourceDocumentModel).where(
            SourceDocumentModel.source_system == source_system.value,
            SourceDocumentModel.external_id == external_id,
        )
        model = self._session.execute(statement).scalar_one_or_none()

        if model is None:
            return None

        return source_document_from_model(model)

    def save(self, document: SourceDocument) -> None:
        self._session.merge(source_document_to_model(document))


class SqlAlchemyDocumentVersionRepository(DocumentVersionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, document_version_id: UUID) -> DocumentVersion | None:
        model = self._session.get(DocumentVersionModel, document_version_id)

        if model is None:
            return None

        return document_version_from_model(model)

    def get_latest_for_source_document(
        self,
        source_document_id: UUID,
    ) -> DocumentVersion | None:
        statement: Select[tuple[DocumentVersionModel]] = (
            select(DocumentVersionModel)
            .where(DocumentVersionModel.source_document_id == source_document_id)
            .order_by(DocumentVersionModel.version_number.desc())
            .limit(1)
        )
        model = self._session.execute(statement).scalar_one_or_none()

        if model is None:
            return None

        return document_version_from_model(model)

    def save(self, document_version: DocumentVersion) -> None:
        self._session.merge(document_version_to_model(document_version))


class SqlAlchemySectionVersionRepository(SectionVersionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_document_version(
        self,
        document_version_id: UUID,
    ) -> list[SectionVersion]:
        statement: Select[tuple[SectionVersionModel]] = (
            select(SectionVersionModel)
            .where(SectionVersionModel.document_version_id == document_version_id)
            .order_by(SectionVersionModel.ordinal.asc())
        )

        return [
            section_version_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save_many(self, section_versions: list[SectionVersion]) -> None:
        for section_version in section_versions:
            self._session.merge(section_version_to_model(section_version))


class SqlAlchemyIngestionRunRepository(IngestionRunRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        model = self._session.get(IngestionRunModel, ingestion_run_id)

        if model is None:
            return None

        return ingestion_run_from_model(model)

    def save(self, ingestion_run: IngestionRun) -> None:
        self._session.merge(ingestion_run_to_model(ingestion_run))