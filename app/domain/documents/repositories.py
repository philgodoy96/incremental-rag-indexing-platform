from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.documents.entities import (
    ChunkEmbeddingLink,
    ChunkVersion,
    DocumentVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
    IngestionRun,
    SectionVersion,
    SourceDocument,
    VectorIndexEntry,
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


class ChunkVersionRepository(ABC):
    @abstractmethod
    def list_for_section_version(
        self,
        section_version_id: UUID,
    ) -> list[ChunkVersion]:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, chunk_versions: list[ChunkVersion]) -> None:
        raise NotImplementedError


class EmbeddingRecordRepository(ABC):
    @abstractmethod
    def get_by_chunk_identity(
        self,
        *,
        chunk_version_id: UUID,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_embedding_identity(
        self,
        *,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, embedding_records: list[EmbeddingRecord]) -> None:
        raise NotImplementedError


class ChunkEmbeddingLinkRepository(ABC):
    @abstractmethod
    def get_by_chunk_version_id(
        self,
        chunk_version_id: UUID,
    ) -> ChunkEmbeddingLink | None:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, links: list[ChunkEmbeddingLink]) -> None:
        raise NotImplementedError


class VectorIndexEntryRepository(ABC):
    @abstractmethod
    def get_by_logical_identity(
        self,
        *,
        source_document_id: UUID,
        stable_section_key: str,
        chunk_index: int,
        provider: str,
        model_name: str,
    ) -> VectorIndexEntry | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, entry: VectorIndexEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, entries: list[VectorIndexEntry]) -> None:
        raise NotImplementedError


class EmbeddingCostRecordRepository(ABC):
    @abstractmethod
    def save_many(self, cost_records: list[EmbeddingCostRecord]) -> None:
        raise NotImplementedError


class IngestionRunRepository(ABC):
    @abstractmethod
    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, ingestion_run: IngestionRun) -> None:
        raise NotImplementedError