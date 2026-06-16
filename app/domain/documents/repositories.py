from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.documents.entities import (
    DocumentVersion,
    IngestionRun,
    SectionVersion,
    SourceDocument,
)
from app.domain.documents.enums import SourceSystem


class SourceDocumentRepository(ABC):
    @abstractmethod
    def get_by_id(self, document_id: UUID) -> SourceDocument | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_external_id(
        self,
        *,
        source_system: SourceSystem,
        external_id: str,
    ) -> SourceDocument | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, document: SourceDocument) -> None:
        raise NotImplementedError


class DocumentVersionRepository(ABC):
    @abstractmethod
    def get_by_id(self, document_version_id: UUID) -> DocumentVersion | None:
        raise NotImplementedError

    @abstractmethod
    def get_latest_for_source_document(
        self,
        source_document_id: UUID,
    ) -> DocumentVersion | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, document_version: DocumentVersion) -> None:
        raise NotImplementedError


class SectionVersionRepository(ABC):
    @abstractmethod
    def list_for_document_version(
        self,
        document_version_id: UUID,
    ) -> list[SectionVersion]:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, section_versions: list[SectionVersion]) -> None:
        raise NotImplementedError


class IngestionRunRepository(ABC):
    @abstractmethod
    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, ingestion_run: IngestionRun) -> None:
        raise NotImplementedError