from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

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
from app.domain.documents.repositories import (
    ChunkEmbeddingLinkRepository,
    ChunkVersionRepository,
    DocumentVersionRepository,
    EmbeddingCostRecordRepository,
    EmbeddingRecordRepository,
    IngestionRunRepository,
    SectionVersionRepository,
    SourceDocumentRepository,
    VectorIndexEntryRepository,
)
from app.infrastructure.db.mappers.document_mappers import (
    chunk_embedding_link_from_model,
    chunk_embedding_link_to_model,
    chunk_version_from_model,
    chunk_version_to_model,
    document_version_from_model,
    document_version_to_model,
    embedding_cost_record_to_model,
    embedding_record_from_model,
    embedding_record_to_model,
    ingestion_run_from_model,
    ingestion_run_to_model,
    section_version_from_model,
    section_version_to_model,
    source_document_from_model,
    source_document_to_model,
    vector_index_entry_from_model,
    vector_index_entry_to_model,
)
from app.infrastructure.db.models.document_models import (
    ChunkEmbeddingLinkModel,
    ChunkVersionModel,
    DocumentVersionModel,
    EmbeddingRecordModel,
    IngestionRunModel,
    SectionVersionModel,
    SourceDocumentModel,
    VectorIndexEntryModel,
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


class SqlAlchemyChunkVersionRepository(ChunkVersionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_section_version(
        self,
        section_version_id: UUID,
    ) -> list[ChunkVersion]:
        statement: Select[tuple[ChunkVersionModel]] = (
            select(ChunkVersionModel)
            .where(ChunkVersionModel.section_version_id == section_version_id)
            .order_by(ChunkVersionModel.chunk_index.asc())
        )

        return [
            chunk_version_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save_many(self, chunk_versions: list[ChunkVersion]) -> None:
        for chunk_version in chunk_versions:
            self._session.merge(chunk_version_to_model(chunk_version))


class SqlAlchemyEmbeddingRecordRepository(EmbeddingRecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_chunk_identity(
        self,
        *,
        chunk_version_id: UUID,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        statement: Select[tuple[EmbeddingRecordModel]] = select(
            EmbeddingRecordModel,
        ).where(
            EmbeddingRecordModel.chunk_version_id == chunk_version_id,
            EmbeddingRecordModel.provider == provider,
            EmbeddingRecordModel.model_name == model_name,
            EmbeddingRecordModel.embedding_input_hash == embedding_input_hash,
        )
        model = self._session.execute(statement).scalar_one_or_none()

        if model is None:
            return None

        return embedding_record_from_model(model)

    def get_by_embedding_identity(
        self,
        *,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        statement: Select[tuple[EmbeddingRecordModel]] = select(
            EmbeddingRecordModel,
        ).where(
            EmbeddingRecordModel.provider == provider,
            EmbeddingRecordModel.model_name == model_name,
            EmbeddingRecordModel.embedding_input_hash == embedding_input_hash,
        )
        model = self._session.execute(statement).scalar_one_or_none()

        if model is None:
            return None

        return embedding_record_from_model(model)

    def save_many(self, embedding_records: list[EmbeddingRecord]) -> None:
        for embedding_record in embedding_records:
            self._session.merge(embedding_record_to_model(embedding_record))


class SqlAlchemyChunkEmbeddingLinkRepository(ChunkEmbeddingLinkRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_chunk_version_id(
        self,
        chunk_version_id: UUID,
    ) -> ChunkEmbeddingLink | None:
        model = self._session.execute(
            select(ChunkEmbeddingLinkModel).where(
                ChunkEmbeddingLinkModel.chunk_version_id == chunk_version_id,
            )
        ).scalar_one_or_none()

        if model is None:
            return None

        return chunk_embedding_link_from_model(model)

    def save_many(self, links: list[ChunkEmbeddingLink]) -> None:
        for link in links:
            self._session.merge(chunk_embedding_link_to_model(link))


class SqlAlchemyVectorIndexEntryRepository(VectorIndexEntryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_logical_identity(
        self,
        *,
        source_document_id: UUID,
        stable_section_key: str,
        chunk_index: int,
        provider: str,
        model_name: str,
    ) -> VectorIndexEntry | None:
        statement: Select[tuple[VectorIndexEntryModel]] = select(
            VectorIndexEntryModel,
        ).where(
            VectorIndexEntryModel.source_document_id == source_document_id,
            VectorIndexEntryModel.stable_section_key == stable_section_key,
            VectorIndexEntryModel.chunk_index == chunk_index,
            VectorIndexEntryModel.provider == provider,
            VectorIndexEntryModel.model_name == model_name,
        )

        model = self._session.execute(statement).scalar_one_or_none()

        if model is None:
            return None

        return vector_index_entry_from_model(model)

    def save(self, entry: VectorIndexEntry) -> None:
        self._session.merge(vector_index_entry_to_model(entry))

    def save_many(self, entries: list[VectorIndexEntry]) -> None:
        for entry in entries:
            self.save(entry)


class SqlAlchemyEmbeddingCostRecordRepository(EmbeddingCostRecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_many(self, cost_records: list[EmbeddingCostRecord]) -> None:
        for cost_record in cost_records:
            self._session.merge(embedding_cost_record_to_model(cost_record))


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