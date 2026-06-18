from uuid import UUID, uuid4

from app.application.services.vector_indexing_service import (
    SectionChunks,
    VectorIndexingService,
)
from app.domain.documents.entities import (
    ChunkEmbeddingLink,
    ChunkVersion,
    DocumentVersion,
    EmbeddingRecord,
    SectionVersion,
    SourceDocument,
    VectorIndexEntry,
)
from app.domain.documents.enums import SourceSystem
from app.domain.documents.repositories import (
    ChunkEmbeddingLinkRepository,
    EmbeddingRecordRepository,
    VectorIndexEntryRepository,
)
from app.domain.retrieval.entities import RetrievedChunk


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

    def list_current_chunk_version_ids_by_stable_section_keys(
        self,
        *,
        stable_section_keys: tuple[str, ...],
        source_system: SourceSystem,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> dict[str, tuple[UUID, ...]]:
        return {
            stable_section_key: tuple(
                chunk_version_id
                for _chunk_index, chunk_version_id in sorted(
                    (
                        (entry.chunk_index, entry.chunk_version_id)
                        for entry in self.entries.values()
                        if entry.is_active
                        and entry.stable_section_key == stable_section_key
                        and (provider is None or entry.provider == provider)
                        and (model_name is None or entry.model_name == model_name)
                    ),
                    key=lambda item: item[0],
                )
            )
            for stable_section_key in stable_section_keys
        }

    def search_active_by_vector(
        self,
        *,
        query_vector: tuple[float, ...],
        provider: str,
        model_name: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        candidates = [
            entry
            for entry in self.entries.values()
            if (
                entry.is_active
                and entry.provider == provider
                and entry.model_name == model_name
                and entry.dimensions == len(query_vector)
            )
        ]

        def calculate_distance(entry: VectorIndexEntry) -> float:
            return float(
                sum(
                    (left - right) ** 2
                    for left, right in zip(entry.embedding_vector, query_vector, strict=True)
                )
                ** 0.5
            )

        return [
            RetrievedChunk(
                vector_index_entry_id=entry.id,
                source_document_id=entry.source_document_id,
                document_version_id=entry.document_version_id,
                section_version_id=entry.section_version_id,
                chunk_version_id=entry.chunk_version_id,
                embedding_record_id=entry.embedding_record_id,
                stable_section_key=entry.stable_section_key,
                chunk_index=entry.chunk_index,
                provider=entry.provider,
                model_name=entry.model_name,
                content=entry.content,
                heading_context=entry.heading_context,
                distance=calculate_distance(entry),
            )
            for entry in sorted(candidates, key=calculate_distance)[:top_k]
        ]

    def save(self, entry: VectorIndexEntry) -> None:
        self.entries[entry.id] = entry

    def save_many(self, entries: list[VectorIndexEntry]) -> None:
        for entry in entries:
            self.save(entry)


class InMemoryVectorIndexTransaction:
    def __init__(self) -> None:
        self.embedding_records = InMemoryEmbeddingRecordRepository()
        self.chunk_embedding_links = InMemoryChunkEmbeddingLinkRepository()
        self.vector_index_entries = InMemoryVectorIndexEntryRepository()
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1


def make_source_document() -> SourceDocument:
    return SourceDocument.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="project-atlas-status.md",
        source_uri="seed_documents/project-atlas-status.md",
        title="Project Atlas Status",
    )


def make_document_version(source_document_id: UUID) -> DocumentVersion:
    return DocumentVersion(
        id=uuid4(),
        source_document_id=source_document_id,
        version_number=1,
        content_checksum="content-checksum",
        metadata_checksum="metadata-checksum",
        raw_content="# Project Atlas Status",
        created_by_run_id=uuid4(),
    )


def make_section(document_version_id: UUID) -> SectionVersion:
    return SectionVersion(
        id=uuid4(),
        document_version_id=document_version_id,
        stable_section_key="project-atlas-status/summary",
        heading_path=("Project Atlas Status", "Summary"),
        heading_level=2,
        title="Summary",
        body="Status: On Track",
        section_checksum="section-checksum",
        ordinal=0,
    )


def make_chunk(section_version_id: UUID) -> ChunkVersion:
    return ChunkVersion(
        id=uuid4(),
        section_version_id=section_version_id,
        chunk_index=0,
        content="Status: On Track",
        heading_context=("Project Atlas Status", "Summary"),
        chunk_hash="chunk-hash",
        embedding_input_hash="embedding-input-hash",
        token_estimate=3,
    )


def make_embedding_record(chunk: ChunkVersion) -> EmbeddingRecord:
    return EmbeddingRecord(
        id=uuid4(),
        chunk_version_id=chunk.id,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash=chunk.embedding_input_hash,
        embedding_vector=(0.1, 0.2, 0.3),
        dimensions=3,
        input_token_estimate=chunk.token_estimate,
    )


def test_vector_indexing_service_creates_current_projection_entry() -> None:
    source_document = make_source_document()
    document_version = make_document_version(source_document.id)
    section = make_section(document_version.id)
    chunk = make_chunk(section.id)
    embedding_record = make_embedding_record(chunk)

    transaction = InMemoryVectorIndexTransaction()
    transaction.embedding_records.embedding_records[embedding_record.id] = (
        embedding_record
    )
    transaction.chunk_embedding_links.links[uuid4()] = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=chunk.id,
        embedding_record_id=embedding_record.id,
    )

    summary = VectorIndexingService().ensure_current_index_for_document(
        source_document=source_document,
        document_version=document_version,
        section_chunks=[SectionChunks(section=section, chunks=[chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert summary.vector_entries_created == 1
    assert summary.vector_entries_updated == 0
    assert summary.vector_entries_deactivated == 0
    assert len(transaction.vector_index_entries.entries) == 1
    assert transaction.flush_count == 1


def test_vector_indexing_service_updates_existing_logical_entry() -> None:
    source_document = make_source_document()
    first_document_version = make_document_version(source_document.id)
    first_section = make_section(first_document_version.id)
    first_chunk = make_chunk(first_section.id)
    first_embedding_record = make_embedding_record(first_chunk)

    transaction = InMemoryVectorIndexTransaction()
    transaction.embedding_records.embedding_records[first_embedding_record.id] = (
        first_embedding_record
    )
    transaction.chunk_embedding_links.links[uuid4()] = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=first_chunk.id,
        embedding_record_id=first_embedding_record.id,
    )

    service = VectorIndexingService()
    service.ensure_current_index_for_document(
        source_document=source_document,
        document_version=first_document_version,
        section_chunks=[SectionChunks(section=first_section, chunks=[first_chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    second_document_version = DocumentVersion(
        id=uuid4(),
        source_document_id=source_document.id,
        version_number=2,
        content_checksum="new-content-checksum",
        metadata_checksum="metadata-checksum",
        raw_content="# Project Atlas Status",
        created_by_run_id=uuid4(),
    )
    second_section = make_section(second_document_version.id)
    second_chunk = make_chunk(second_section.id)
    second_embedding_record = EmbeddingRecord(
        id=uuid4(),
        chunk_version_id=second_chunk.id,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="new-embedding-input-hash",
        embedding_vector=(0.4, 0.5, 0.6),
        dimensions=3,
        input_token_estimate=3,
    )
    transaction.embedding_records.embedding_records[second_embedding_record.id] = (
        second_embedding_record
    )
    transaction.chunk_embedding_links.links[uuid4()] = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=second_chunk.id,
        embedding_record_id=second_embedding_record.id,
    )

    summary = service.ensure_current_index_for_document(
        source_document=source_document,
        document_version=second_document_version,
        section_chunks=[SectionChunks(section=second_section, chunks=[second_chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    entries = list(transaction.vector_index_entries.entries.values())

    assert summary.vector_entries_created == 0
    assert summary.vector_entries_updated == 1
    assert summary.vector_entries_deactivated == 0
    assert len(entries) == 1
    assert entries[0].document_version_id == second_document_version.id
    assert entries[0].chunk_version_id == second_chunk.id
    assert entries[0].embedding_input_hash == "new-embedding-input-hash"
    assert entries[0].embedding_vector == (0.4, 0.5, 0.6)


def test_vector_indexing_service_deactivates_stale_entries() -> None:
    source_document = make_source_document()
    document_version = make_document_version(source_document.id)
    section = make_section(document_version.id)
    chunk = make_chunk(section.id)
    embedding_record = make_embedding_record(chunk)

    stale_entry = VectorIndexEntry(
        id=uuid4(),
        source_document_id=source_document.id,
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/old-section",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="old-hash",
        content="Old content",
        heading_context=("Project Atlas Status", "Old Section"),
        embedding_vector=(0.9, 0.8, 0.7),
        dimensions=3,
    )

    transaction = InMemoryVectorIndexTransaction()
    transaction.vector_index_entries.save(stale_entry)
    transaction.embedding_records.embedding_records[embedding_record.id] = (
        embedding_record
    )
    transaction.chunk_embedding_links.links[uuid4()] = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=chunk.id,
        embedding_record_id=embedding_record.id,
    )

    summary = VectorIndexingService().ensure_current_index_for_document(
        source_document=source_document,
        document_version=document_version,
        section_chunks=[SectionChunks(section=section, chunks=[chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    active_entries = [
        entry
        for entry in transaction.vector_index_entries.entries.values()
        if entry.is_active
    ]

    assert summary.vector_entries_created == 1
    assert summary.vector_entries_updated == 0
    assert summary.vector_entries_deactivated == 1
    assert len(active_entries) == 1
    assert stale_entry.is_active is False

def test_vector_indexing_service_is_idempotent_when_projection_is_current() -> None:
    source_document = make_source_document()
    document_version = make_document_version(source_document.id)
    section = make_section(document_version.id)
    chunk = make_chunk(section.id)
    embedding_record = make_embedding_record(chunk)

    transaction = InMemoryVectorIndexTransaction()
    transaction.embedding_records.embedding_records[embedding_record.id] = (
        embedding_record
    )
    transaction.chunk_embedding_links.links[uuid4()] = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=chunk.id,
        embedding_record_id=embedding_record.id,
    )

    service = VectorIndexingService()

    first_summary = service.ensure_current_index_for_document(
        source_document=source_document,
        document_version=document_version,
        section_chunks=[SectionChunks(section=section, chunks=[chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    second_summary = service.ensure_current_index_for_document(
        source_document=source_document,
        document_version=document_version,
        section_chunks=[SectionChunks(section=section, chunks=[chunk])],
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert first_summary.vector_entries_created == 1
    assert first_summary.vector_entries_updated == 0
    assert first_summary.vector_entries_deactivated == 0

    assert second_summary.vector_entries_created == 0
    assert second_summary.vector_entries_updated == 0
    assert second_summary.vector_entries_deactivated == 0

    assert len(transaction.vector_index_entries.entries) == 1


def test_in_memory_vector_index_repository_searches_active_entries_by_distance() -> None:
    repository = InMemoryVectorIndexEntryRepository()

    closer_entry = VectorIndexEntry(
        id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="hash-1",
        content="Project Atlas is at risk",
        heading_context=("Project Atlas Status", "Summary"),
        embedding_vector=(0.1, 0.1, 0.1),
        dimensions=3,
    )
    farther_entry = VectorIndexEntry(
        id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="billing-system/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="hash-2",
        content="Billing supports invoices",
        heading_context=("Billing System", "Summary"),
        embedding_vector=(0.9, 0.9, 0.9),
        dimensions=3,
    )

    repository.save(closer_entry)
    repository.save(farther_entry)

    results = repository.search_active_by_vector(
        query_vector=(0.0, 0.0, 0.0),
        provider="fake",
        model_name="fake-embedding-v1",
        top_k=2,
    )

    assert [result.vector_index_entry_id for result in results] == [
        closer_entry.id,
        farther_entry.id,
    ]
    assert results[0].distance < results[1].distance