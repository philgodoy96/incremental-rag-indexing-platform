from pathlib import Path
from uuid import UUID

from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionAction,
    LocalSeedDocumentIngestionService,
)
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


class InMemorySourceDocumentRepository(SourceDocumentRepository):
    def __init__(self) -> None:
        self.documents: dict[UUID, SourceDocument] = {}

    def get_by_id(self, document_id: UUID) -> SourceDocument | None:
        return self.documents.get(document_id)

    def get_by_external_id(
        self,
        *,
        source_system: SourceSystem,
        external_id: str,
    ) -> SourceDocument | None:
        for document in self.documents.values():
            if (
                document.source_system == source_system
                and document.external_id == external_id
            ):
                return document

        return None

    def save(self, document: SourceDocument) -> None:
        self.documents[document.id] = document


class InMemoryDocumentVersionRepository(DocumentVersionRepository):
    def __init__(self) -> None:
        self.document_versions: dict[UUID, DocumentVersion] = {}

    def get_by_id(self, document_version_id: UUID) -> DocumentVersion | None:
        return self.document_versions.get(document_version_id)

    def get_latest_for_source_document(
        self,
        source_document_id: UUID,
    ) -> DocumentVersion | None:
        versions = [
            version
            for version in self.document_versions.values()
            if version.source_document_id == source_document_id
        ]

        if not versions:
            return None

        return max(versions, key=lambda version: version.version_number)

    def save(self, document_version: DocumentVersion) -> None:
        self.document_versions[document_version.id] = document_version


class InMemorySectionVersionRepository(SectionVersionRepository):
    def __init__(self) -> None:
        self.section_versions: dict[UUID, SectionVersion] = {}

    def list_for_document_version(
        self,
        document_version_id: UUID,
    ) -> list[SectionVersion]:
        return sorted(
            [
                section
                for section in self.section_versions.values()
                if section.document_version_id == document_version_id
            ],
            key=lambda section: section.ordinal,
        )

    def save_many(self, section_versions: list[SectionVersion]) -> None:
        for section_version in section_versions:
            self.section_versions[section_version.id] = section_version


class InMemoryChunkVersionRepository(ChunkVersionRepository):
    def __init__(self) -> None:
        self.chunk_versions: dict[UUID, ChunkVersion] = {}

    def list_for_section_version(
        self,
        section_version_id: UUID,
    ) -> list[ChunkVersion]:
        return sorted(
            [
                chunk
                for chunk in self.chunk_versions.values()
                if chunk.section_version_id == section_version_id
            ],
            key=lambda chunk: chunk.chunk_index,
        )

    def save_many(self, chunk_versions: list[ChunkVersion]) -> None:
        for chunk_version in chunk_versions:
            self.chunk_versions[chunk_version.id] = chunk_version


class InMemoryEmbeddingRecordRepository(EmbeddingRecordRepository):
    def __init__(self) -> None:
        self.embedding_records: dict[UUID, EmbeddingRecord] = {}
    
    def get_by_id(self, embedding_record_id: UUID) -> EmbeddingRecord | None:
        return self.embedding_records.get(embedding_record_id)

    def get_by_chunk_identity(
        self,
        *,
        chunk_version_id: UUID,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        for record in self.embedding_records.values():
            if (
                record.chunk_version_id == chunk_version_id
                and record.provider == provider
                and record.model_name == model_name
                and record.embedding_input_hash == embedding_input_hash
            ):
                return record

        return None
    
    def get_by_embedding_identity(
        self,
        *,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        for record in self.embedding_records.values():
            if (
                record.provider == provider
                and record.model_name == model_name
                and record.embedding_input_hash == embedding_input_hash
            ):
                return record

        return None

    def save_many(self, embedding_records: list[EmbeddingRecord]) -> None:
        for embedding_record in embedding_records:
            self.embedding_records[embedding_record.id] = embedding_record


class InMemoryChunkEmbeddingLinkRepository(ChunkEmbeddingLinkRepository):
    def __init__(self) -> None:
        self.links: dict[UUID, ChunkEmbeddingLink] = {}

    def get_by_chunk_version_id(
        self,
        chunk_version_id: UUID,
    ) -> ChunkEmbeddingLink | None:
        for link in self.links.values():
            if link.chunk_version_id == chunk_version_id:
                return link

        return None

    def save_many(self, links: list[ChunkEmbeddingLink]) -> None:
        for link in links:
            self.links[link.id] = link

class InMemoryEmbeddingCostRecordRepository(EmbeddingCostRecordRepository):
    def __init__(self) -> None:
        self.cost_records: dict[UUID, EmbeddingCostRecord] = {}

    def save_many(self, cost_records: list[EmbeddingCostRecord]) -> None:
        for cost_record in cost_records:
            self.cost_records[cost_record.id] = cost_record


class InMemoryIngestionRunRepository(IngestionRunRepository):
    def __init__(self) -> None:
        self.ingestion_runs: dict[UUID, IngestionRun] = {}

    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        return self.ingestion_runs.get(ingestion_run_id)

    def save(self, ingestion_run: IngestionRun) -> None:
        self.ingestion_runs[ingestion_run.id] = ingestion_run


class InMemoryVectorIndexEntryRepository(VectorIndexEntryRepository):
    def __init__(self) -> None:
        self.entries: dict[UUID, VectorIndexEntry] = {}

    def get_by_logical_identity(
        self,
        *,
        source_document_id: UUID,
        stable_section_key: str,
        chunk_index: int,
        provider: str,
        model_name: str,
    ) -> VectorIndexEntry | None:
        for entry in self.entries.values():
            if (
                entry.source_document_id == source_document_id
                and entry.stable_section_key == stable_section_key
                and entry.chunk_index == chunk_index
                and entry.provider == provider
                and entry.model_name == model_name
            ):
                return entry

        return None

    def list_active_for_source_document(
        self,
        source_document_id: UUID,
    ) -> list[VectorIndexEntry]:
        return [
            entry
            for entry in self.entries.values()
            if entry.source_document_id == source_document_id and entry.is_active
        ]

    def save(self, entry: VectorIndexEntry) -> None:
        self.entries[entry.id] = entry

    def save_many(self, entries: list[VectorIndexEntry]) -> None:
        for entry in entries:
            self.save(entry)


class InMemoryDocumentIngestionTransaction:
    def __init__(self) -> None:
        self.source_document_repository = InMemorySourceDocumentRepository()
        self.document_version_repository = InMemoryDocumentVersionRepository()
        self.section_version_repository = InMemorySectionVersionRepository()
        self.chunk_version_repository = InMemoryChunkVersionRepository()
        self.embedding_record_repository = InMemoryEmbeddingRecordRepository()
        self.chunk_embedding_link_repository = InMemoryChunkEmbeddingLinkRepository()
        self.embedding_cost_record_repository = InMemoryEmbeddingCostRecordRepository()
        self.ingestion_run_repository = InMemoryIngestionRunRepository()
        self.vector_index_entry_repository = InMemoryVectorIndexEntryRepository()

        self.source_documents: SourceDocumentRepository = self.source_document_repository
        self.document_versions: DocumentVersionRepository = self.document_version_repository
        self.section_versions: SectionVersionRepository = self.section_version_repository
        self.chunk_versions: ChunkVersionRepository = self.chunk_version_repository
        self.embedding_records: EmbeddingRecordRepository = (
            self.embedding_record_repository
        )
        self.chunk_embedding_links: ChunkEmbeddingLinkRepository = (
            self.chunk_embedding_link_repository
        )
        self.embedding_cost_records: EmbeddingCostRecordRepository = (
            self.embedding_cost_record_repository
        )
        self.ingestion_runs: IngestionRunRepository = self.ingestion_run_repository
        self.vector_index_entries: VectorIndexEntryRepository = (
            self.vector_index_entry_repository
        )

        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_local_seed_ingestion_creates_document_version_sections_chunks_and_embeddings(
    tmp_path: Path,
) -> None:
    (tmp_path / "project-atlas-status.md").write_text(
        "# Project Atlas Status\n\n## Summary\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    result = service.ingest(transaction)

    assert result.documents_seen == 1
    assert result.documents_changed == 1
    assert result.sections_created == 1
    assert result.chunks_created == 1
    assert result.embeddings_created == 1
    assert result.embeddings_reused == 0
    assert result.embedding_tokens_processed == 3
    assert result.estimated_embedding_cost_usd_micros == 0
    assert result.documents[0].action == LocalSeedDocumentIngestionAction.CREATED
    assert result.documents[0].embeddings_created == 1
    assert result.documents[0].embeddings_reused == 0
    assert result.documents[0].embedding_tokens_processed == 3
    assert result.documents[0].estimated_embedding_cost_usd_micros == 0
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 1
    assert len(transaction.section_version_repository.section_versions) == 1
    assert len(transaction.chunk_version_repository.chunk_versions) == 1
    assert len(transaction.embedding_record_repository.embedding_records) == 1
    assert len(transaction.chunk_embedding_link_repository.links) == 1
    assert len(transaction.embedding_cost_record_repository.cost_records) == 1
    assert transaction.commit_count == 1
    assert transaction.rollback_count == 0


def test_local_seed_ingestion_is_idempotent_for_unchanged_documents(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "project-atlas-status.md"
    document_path.write_text(
        "# Project Atlas Status\n\n## Summary\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)
    second_result = service.ingest(transaction)

    assert second_result.documents_seen == 1
    assert second_result.documents_changed == 0
    assert second_result.sections_created == 0
    assert second_result.chunks_created == 0
    assert second_result.embeddings_created == 0
    assert second_result.embeddings_reused == 0
    assert second_result.embedding_tokens_processed == 0
    assert second_result.estimated_embedding_cost_usd_micros == 0
    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 1
    assert len(transaction.section_version_repository.section_versions) == 1
    assert len(transaction.chunk_version_repository.chunk_versions) == 1
    assert len(transaction.chunk_embedding_link_repository.links) == 1
    assert len(transaction.embedding_record_repository.embedding_records) == 1
    assert len(transaction.embedding_cost_record_repository.cost_records) == 1


def test_local_seed_ingestion_backfills_embeddings_for_existing_chunks(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "project-atlas-status.md"
    document_path.write_text(
        "# Project Atlas Status\n\n## Summary\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)
    transaction.chunk_embedding_link_repository.links.clear()
    transaction.embedding_cost_record_repository.cost_records.clear()

    second_result = service.ingest(transaction)

    assert second_result.documents_changed == 0
    assert second_result.sections_created == 0
    assert second_result.chunks_created == 0
    assert second_result.embeddings_created == 0
    assert second_result.embeddings_reused == 1
    assert second_result.embedding_tokens_processed == 0
    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert second_result.documents[0].embeddings_created == 0
    assert second_result.documents[0].embeddings_reused == 1
    assert len(transaction.document_version_repository.document_versions) == 1
    assert len(transaction.section_version_repository.section_versions) == 1
    assert len(transaction.chunk_version_repository.chunk_versions) == 1
    assert len(transaction.embedding_record_repository.embedding_records) == 1
    assert len(transaction.chunk_embedding_link_repository.links) == 1
    assert len(transaction.embedding_cost_record_repository.cost_records) == 0


def test_ingestion_creates_new_version_artifacts_when_content_changes(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "project-atlas-status.md"
    document_path.write_text(
        "# Project Atlas Status\n\n## Summary\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)

    document_path.write_text(
        "# Project Atlas Status\n\n## Summary\n\nStatus: At Risk\n",
        encoding="utf-8",
    )

    second_result = service.ingest(transaction)

    assert second_result.documents_seen == 1
    assert second_result.documents_changed == 1
    assert second_result.sections_created == 1
    assert second_result.chunks_created == 1
    assert second_result.embeddings_created == 1
    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert second_result.documents[0].version_number == 2
    assert second_result.documents[0].embeddings_created == 1
    assert second_result.documents[0].embeddings_reused == 0
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 2
    assert len(transaction.section_version_repository.section_versions) == 2
    assert len(transaction.chunk_version_repository.chunk_versions) == 2
    assert len(transaction.embedding_record_repository.embedding_records) == 2
    assert len(transaction.embedding_cost_record_repository.cost_records) == 2