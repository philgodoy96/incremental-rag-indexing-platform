from pathlib import Path
from uuid import UUID

from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionAction,
    LocalSeedDocumentIngestionService,
)
from app.application.services.markdown_chunking_service import MarkdownChunkingService
from app.application.services.source_document_discovery import (
    SourceDocumentDiscoveryResult,
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
from app.domain.documents.source_candidates import SourceDocumentCandidate
from app.domain.retrieval.entities import RetrievedChunk
from app.providers.embeddings import EmbeddingProviderResponse
from app.providers.fake_embedding_provider import FakeEmbeddingProvider


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
        self.memberships: dict[tuple[UUID, UUID], int] = {}

    def list_for_document_version(
        self,
        document_version_id: UUID,
    ) -> list[SectionVersion]:
        membership_rows = [
            (section_version_id, ordinal)
            for (
                membership_document_version_id,
                section_version_id,
            ), ordinal in self.memberships.items()
            if membership_document_version_id == document_version_id
        ]

        sections: list[SectionVersion] = []
        for section_version_id, ordinal in sorted(
            membership_rows,
            key=lambda item: item[1],
        ):
            content = self.section_versions[section_version_id]
            sections.append(
                SectionVersion(
                    id=content.id,
                    document_version_id=document_version_id,
                    stable_section_key=content.stable_section_key,
                    heading_path=content.heading_path,
                    heading_level=content.heading_level,
                    title=content.title,
                    body=content.body,
                    section_checksum=content.section_checksum,
                    ordinal=ordinal,
                    created_at=content.created_at,
                )
            )

        return sections

    def save_many(self, section_versions: list[SectionVersion]) -> None:
        for section_version in section_versions:
            self.section_versions[section_version.id] = section_version
            self.memberships[
                (section_version.document_version_id, section_version.id)
            ] = section_version.ordinal


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
    assert result.vector_entries_created == result.chunks_created
    assert result.vector_entries_updated == 0
    assert result.vector_entries_deactivated == 0
    assert result.embedding_tokens_processed == 3
    assert result.estimated_embedding_cost_usd_micros == 0
    assert result.documents[0].action == LocalSeedDocumentIngestionAction.CREATED
    assert result.documents[0].embeddings_created == 1
    assert result.documents[0].embeddings_reused == 0
    assert result.documents[0].vector_entries_created == result.documents[0].chunks_created
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
    assert second_result.vector_entries_created == 0
    assert second_result.vector_entries_updated == 0
    assert second_result.vector_entries_deactivated == 0
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
    assert second_result.vector_entries_created == 0
    assert second_result.vector_entries_updated == 0
    assert second_result.vector_entries_deactivated == 0
    assert second_result.embedding_tokens_processed == 0

    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert second_result.documents[0].embeddings_created == 0
    assert second_result.documents[0].embeddings_reused == 1
    assert second_result.documents[0].vector_entries_created == 0
    assert second_result.documents[0].vector_entries_updated == 0
    assert second_result.documents[0].vector_entries_deactivated == 0

    assert len(transaction.document_version_repository.document_versions) == 1
    assert len(transaction.section_version_repository.section_versions) == 1
    assert len(transaction.chunk_version_repository.chunk_versions) == 1
    assert len(transaction.embedding_record_repository.embedding_records) == 1
    assert len(transaction.chunk_embedding_link_repository.links) == 1
    assert len(transaction.embedding_cost_record_repository.cost_records) == 0
    assert len(transaction.vector_index_entry_repository.entries) == 1


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
    assert second_result.sections_modified == 1
    assert second_result.sections_unchanged == 0
    assert second_result.chunks_created == 1
    assert second_result.chunks_reused == 0
    assert second_result.embeddings_created == 1
    assert second_result.embeddings_reused == 0
    assert second_result.vector_entries_created == 0
    assert second_result.vector_entries_updated == 1
    assert second_result.vector_entries_deactivated == 0

    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert second_result.documents[0].version_number == 2
    assert second_result.documents[0].embeddings_created == 1
    assert second_result.documents[0].embeddings_reused == 0
    assert second_result.documents[0].vector_entries_created == 0
    assert second_result.documents[0].vector_entries_updated == 1
    assert second_result.documents[0].vector_entries_deactivated == 0

    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 2
    assert len(transaction.section_version_repository.section_versions) == 2
    assert len(transaction.chunk_version_repository.chunk_versions) == 2
    assert len(transaction.embedding_record_repository.embedding_records) == 2
    assert len(transaction.chunk_embedding_link_repository.links) == 2
    assert len(transaction.embedding_cost_record_repository.cost_records) == 2
    assert len(transaction.vector_index_entry_repository.entries) == 1


class StubDiscoveryService:
    def __init__(self, result: SourceDocumentDiscoveryResult) -> None:
        self._result = result
        self.discover_calls = 0

    def discover(self) -> SourceDocumentDiscoveryResult:
        self.discover_calls += 1
        return self._result


def test_local_seed_ingestion_service_accepts_custom_discovery_service(
    tmp_path: Path,
) -> None:
    discovery_result = SourceDocumentDiscoveryResult(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        source_path=tmp_path.as_posix(),
        documents=(
            SourceDocumentCandidate.create(
                source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
                external_id="custom.md",
                source_uri="seed_documents/custom.md",
                title="Custom Document",
                raw_content="# Custom Document\n\nBody.",
            ),
        ),
    )
    discovery_service = StubDiscoveryService(discovery_result)
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        discovery_service=discovery_service,
    )

    result = service.ingest(transaction)

    assert discovery_service.discover_calls == 1
    assert result.documents_seen == 1
    assert result.source_path == tmp_path.as_posix()
    assert result.documents[0].external_id == "custom.md"
    assert result.documents[0].action == LocalSeedDocumentIngestionAction.CREATED


MULTI_SECTION_DOCUMENT = """# Handbook

## Summary

Status is stable.

## Risks

No open risks.

## Next Steps

Continue monitoring.
"""


class SpyChunkingService(MarkdownChunkingService):
    def __init__(self) -> None:
        super().__init__()
        self.section_ids: list[UUID] = []

    def create_chunk_versions(self, *, section_version: SectionVersion) -> list[ChunkVersion]:
        self.section_ids.append(section_version.id)
        return super().create_chunk_versions(section_version=section_version)


class CountingEmbeddingProvider:
    provider = "fake"
    model_name = "fake-embedding-v1"
    dimensions = 8

    def __init__(self) -> None:
        self._inner = FakeEmbeddingProvider()
        self.embed_calls = 0

    def embed(self, text: str) -> EmbeddingProviderResponse:
        self.embed_calls += 1
        return self._inner.embed(text)


def test_unchanged_document_skips_version_and_embedding_work(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    embedding_provider = CountingEmbeddingProvider()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
        embedding_provider=embedding_provider,
    )

    first = service.ingest(transaction)
    first_chunker_calls = len(chunker.section_ids)
    first_embed_calls = embedding_provider.embed_calls

    second = service.ingest(transaction)

    assert first.documents[0].action == LocalSeedDocumentIngestionAction.CREATED
    assert second.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert len(transaction.document_version_repository.document_versions) == 1
    assert len(chunker.section_ids) == first_chunker_calls
    assert embedding_provider.embed_calls == first_embed_calls
    assert second.sections_created == 0
    assert second.chunks_created == 0
    assert second.embeddings_created == 0


def test_one_modified_section_skips_chunker_for_unchanged_sections(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    embedding_provider = CountingEmbeddingProvider()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
        embedding_provider=embedding_provider,
    )

    first = service.ingest(transaction)
    first_version_id = next(
        iter(transaction.document_version_repository.document_versions)
    )
    first_sections = transaction.section_version_repository.list_for_document_version(
        first_version_id,
    )
    first_section_ids = {section.stable_section_key: section.id for section in first_sections}
    first_chunker_calls = len(chunker.section_ids)
    first_embed_calls = embedding_provider.embed_calls

    document_path.write_text(
        """# Handbook

## Summary

Status is stable.

## Risks

Risk level increased.

## Next Steps

Continue monitoring.
""",
        encoding="utf-8",
    )

    second = service.ingest(transaction)
    second_version = max(
        transaction.document_version_repository.document_versions.values(),
        key=lambda version: version.version_number,
    )
    second_sections = transaction.section_version_repository.list_for_document_version(
        second_version.id,
    )
    second_by_key = {section.stable_section_key: section for section in second_sections}

    assert second.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert second.sections_unchanged == 2
    assert second.sections_modified == 1
    assert second.sections_added == 0
    assert second.sections_removed == 0
    assert second.sections_created == 1
    assert second.chunks_reused == 2
    assert second.chunks_created == 1
    assert len(chunker.section_ids) == first_chunker_calls + 1
    assert embedding_provider.embed_calls == first_embed_calls + 1

    assert second_by_key["handbook/summary"].id == first_section_ids["handbook/summary"]
    assert second_by_key["handbook/next-steps"].id == first_section_ids["handbook/next-steps"]
    assert second_by_key["handbook/risks"].id != first_section_ids["handbook/risks"]

    historical = transaction.section_version_repository.list_for_document_version(
        first_version_id,
    )
    assert {section.id for section in historical} == set(first_section_ids.values())
    assert first.documents_changed == 1


def test_added_section_reuses_unchanged_sections(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
    )

    service.ingest(transaction)
    first_chunker_calls = len(chunker.section_ids)

    document_path.write_text(
        MULTI_SECTION_DOCUMENT + "\n## Appendix\n\nExtra notes.\n",
        encoding="utf-8",
    )
    second = service.ingest(transaction)

    assert second.sections_unchanged == 3
    assert second.sections_added == 1
    assert second.sections_modified == 0
    assert second.sections_removed == 0
    assert second.sections_created == 1
    assert second.chunks_reused == 3
    assert second.chunks_created == 1
    assert len(chunker.section_ids) == first_chunker_calls + 1


def test_removed_section_stays_historical_and_leaves_current_projection(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
    )

    service.ingest(transaction)
    first_version = next(
        iter(transaction.document_version_repository.document_versions.values())
    )
    first_chunker_calls = len(chunker.section_ids)

    document_path.write_text(
        """# Handbook

## Summary

Status is stable.

## Next Steps

Continue monitoring.
""",
        encoding="utf-8",
    )
    second = service.ingest(transaction)
    second_version = max(
        transaction.document_version_repository.document_versions.values(),
        key=lambda version: version.version_number,
    )

    historical_keys = {
        section.stable_section_key
        for section in transaction.section_version_repository.list_for_document_version(
            first_version.id,
        )
    }
    current_keys = {
        section.stable_section_key
        for section in transaction.section_version_repository.list_for_document_version(
            second_version.id,
        )
    }
    active_keys = {
        entry.stable_section_key
        for entry in transaction.vector_index_entry_repository.list_active_for_source_document(
            next(iter(transaction.source_document_repository.documents.values())).id,
        )
    }

    assert "handbook/risks" in historical_keys
    assert "handbook/risks" not in current_keys
    assert "handbook/risks" not in active_keys
    assert second.sections_removed == 1
    assert second.sections_unchanged == 2
    assert second.sections_created == 0
    assert second.chunks_reused == 2
    assert second.chunks_created == 0
    assert second.vector_entries_deactivated == 1
    assert len(chunker.section_ids) == first_chunker_calls


def test_modified_section_reuses_embedding_when_chunk_content_matches_history(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(
        """# Handbook

## Summary

Alpha body.

## Risks

Beta body.
""",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    embedding_provider = CountingEmbeddingProvider()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        embedding_provider=embedding_provider,
    )

    service.ingest(transaction)
    first_embed_calls = embedding_provider.embed_calls

    document_path.write_text(
        """# Handbook

## Summary

Gamma body.

## Risks

Beta body.
""",
        encoding="utf-8",
    )
    service.ingest(transaction)
    mid_embed_calls = embedding_provider.embed_calls
    assert mid_embed_calls == first_embed_calls + 1

    document_path.write_text(
        """# Handbook

## Summary

Alpha body.

## Risks

Beta body.
""",
        encoding="utf-8",
    )
    third = service.ingest(transaction)

    assert third.sections_modified == 1
    assert third.sections_unchanged == 1
    assert third.embeddings_created == 0
    assert third.embeddings_reused == 1
    assert embedding_provider.embed_calls == mid_embed_calls


def test_section_reorder_without_content_change_reuses_artifacts(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(
        """# Handbook

## Summary

Status is stable.

## Risks

No open risks.
""",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
    )

    service.ingest(transaction)
    first_version = next(
        iter(transaction.document_version_repository.document_versions.values())
    )
    first_sections = {
        section.stable_section_key: section
        for section in transaction.section_version_repository.list_for_document_version(
            first_version.id,
        )
    }
    first_chunker_calls = len(chunker.section_ids)

    document_path.write_text(
        """# Handbook

## Risks

No open risks.

## Summary

Status is stable.
""",
        encoding="utf-8",
    )
    second = service.ingest(transaction)
    second_version = max(
        transaction.document_version_repository.document_versions.values(),
        key=lambda version: version.version_number,
    )
    second_sections = transaction.section_version_repository.list_for_document_version(
        second_version.id,
    )

    assert second.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert second.sections_unchanged == 2
    assert second.sections_modified == 0
    assert second.sections_created == 0
    assert second.chunks_reused == 2
    assert second.chunks_created == 0
    assert len(chunker.section_ids) == first_chunker_calls
    assert [section.stable_section_key for section in second_sections] == [
        "handbook/risks",
        "handbook/summary",
    ]
    assert second_sections[0].id == first_sections["handbook/risks"].id
    assert second_sections[1].id == first_sections["handbook/summary"].id


def test_mixed_delta_builds_complete_new_snapshot(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(
        """# Handbook

## Summary

Status is stable.

## Risks

No open risks.

## Next Steps

Continue monitoring.
""",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    chunker = SpyChunkingService()
    service = LocalSeedDocumentIngestionService(
        source_path=tmp_path,
        chunking_service=chunker,
    )

    service.ingest(transaction)
    first_chunker_calls = len(chunker.section_ids)

    document_path.write_text(
        """# Handbook

## Summary

Status is stable.

## Risks

Risk level increased.

## Appendix

Extra notes.
""",
        encoding="utf-8",
    )
    second = service.ingest(transaction)
    second_version = max(
        transaction.document_version_repository.document_versions.values(),
        key=lambda version: version.version_number,
    )
    current_keys = [
        section.stable_section_key
        for section in transaction.section_version_repository.list_for_document_version(
            second_version.id,
        )
    ]

    assert second.sections_unchanged == 1
    assert second.sections_modified == 1
    assert second.sections_added == 1
    assert second.sections_removed == 1
    assert second.sections_created == 2
    assert second.chunks_reused == 1
    assert second.chunks_created == 2
    assert len(chunker.section_ids) == first_chunker_calls + 2
    assert current_keys == [
        "handbook/summary",
        "handbook/risks",
        "handbook/appendix",
    ]


def test_retry_of_changed_document_does_not_duplicate_snapshot_membership(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)

    document_path.write_text(
        MULTI_SECTION_DOCUMENT.replace("No open risks.", "Risk level increased."),
        encoding="utf-8",
    )
    second = service.ingest(transaction)
    membership_count_after_change = len(
        transaction.section_version_repository.memberships,
    )
    section_count_after_change = len(
        transaction.section_version_repository.section_versions,
    )

    # Re-ingest identical changed content: document checksum matches latest version.
    third = service.ingest(transaction)

    assert second.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert third.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert len(transaction.document_version_repository.document_versions) == 2
    assert (
        len(transaction.section_version_repository.memberships)
        == membership_count_after_change
    )
    assert (
        len(transaction.section_version_repository.section_versions)
        == section_count_after_change
    )


def test_vector_projection_includes_reused_unchanged_content(tmp_path: Path) -> None:
    document_path = tmp_path / "handbook.md"
    document_path.write_text(MULTI_SECTION_DOCUMENT, encoding="utf-8")
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)
    source_document = next(iter(transaction.source_document_repository.documents.values()))
    first_active = {
        entry.stable_section_key: entry.section_version_id
        for entry in transaction.vector_index_entry_repository.list_active_for_source_document(
            source_document.id,
        )
    }

    document_path.write_text(
        MULTI_SECTION_DOCUMENT.replace("No open risks.", "Risk level increased."),
        encoding="utf-8",
    )
    service.ingest(transaction)

    second_active = {
        entry.stable_section_key: entry
        for entry in transaction.vector_index_entry_repository.list_active_for_source_document(
            source_document.id,
        )
    }

    assert set(second_active) == set(first_active)
    assert (
        second_active["handbook/summary"].section_version_id
        == first_active["handbook/summary"]
    )
    assert (
        second_active["handbook/next-steps"].section_version_id
        == first_active["handbook/next-steps"]
    )
    assert (
        second_active["handbook/risks"].section_version_id
        != first_active["handbook/risks"]
    )
    assert all(entry.is_active for entry in second_active.values())
