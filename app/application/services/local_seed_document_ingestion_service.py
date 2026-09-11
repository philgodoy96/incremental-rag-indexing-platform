from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from app.application.services.chunk_embedding_service import (
    ChunkEmbeddingService,
    EmbeddingGenerationSummary,
)
from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryService,
)
from app.application.services.markdown_chunking_service import MarkdownChunkingService
from app.application.services.markdown_section_extraction_service import (
    ExtractedMarkdownSection,
    MarkdownSectionExtractionService,
)
from app.application.services.section_delta_planner import (
    SectionDeltaKind,
    SectionDeltaPlanner,
)
from app.application.services.source_document_discovery import (
    SourceDocumentDiscoveryResult,
    SourceDocumentDiscoveryService,
)
from app.application.services.vector_indexing_service import (
    SectionChunks,
    VectorIndexingService,
    VectorIndexingSummary,
)
from app.application.transactions import DocumentIngestionTransaction
from app.domain.documents.entities import (
    ChunkVersion,
    DocumentVersion,
    IngestionRun,
    SectionVersion,
    SourceDocument,
)
from app.domain.documents.enums import IngestionRunStatus, SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate
from app.providers.embeddings import EmbeddingProvider
from app.providers.fake_embedding_provider import FakeEmbeddingProvider


class LocalSeedDocumentIngestionAction(StrEnum):
    CREATED = "created"
    UNCHANGED = "unchanged"
    VERSION_CREATED = "version_created"


@dataclass(frozen=True, slots=True)
class LocalSeedDocumentIngestionItem:
    external_id: str
    title: str
    action: LocalSeedDocumentIngestionAction
    source_document_id: UUID
    document_version_id: UUID | None
    version_number: int | None
    content_checksum: str
    sections_created: int
    sections_unchanged: int
    sections_modified: int
    sections_added: int
    sections_removed: int
    chunks_created: int
    chunks_reused: int
    embeddings_created: int
    embeddings_reused: int
    vector_entries_created: int
    vector_entries_updated: int
    vector_entries_deactivated: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int


@dataclass(frozen=True, slots=True)
class LocalSeedDocumentIngestionResult:
    run_id: UUID
    source_system: SourceSystem
    source_path: str
    status: IngestionRunStatus
    documents_seen: int
    documents_changed: int
    sections_created: int
    sections_unchanged: int
    sections_modified: int
    sections_added: int
    sections_removed: int
    chunks_created: int
    chunks_reused: int
    embeddings_created: int
    embeddings_reused: int
    vector_entries_created: int
    vector_entries_updated: int
    vector_entries_deactivated: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int
    documents: tuple[LocalSeedDocumentIngestionItem, ...]


@dataclass(frozen=True, slots=True)
class _SectionMaterializationResult:
    sections: list[SectionVersion]
    sections_created: int
    sections_unchanged: int
    sections_modified: int
    sections_added: int
    sections_removed: int
    chunks: list[ChunkVersion]
    chunks_created: int
    chunks_reused: int


class LocalSeedDocumentIngestionService:
    """Persists local seed Markdown documents as versioned source documents."""

    def __init__(
        self,
        source_path: Path,
        *,
        discovery_service: SourceDocumentDiscoveryService | None = None,
        chunking_service: MarkdownChunkingService | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._source_path = source_path
        self._discovery_service = discovery_service
        self._section_extraction_service = MarkdownSectionExtractionService()
        self._section_delta_planner = SectionDeltaPlanner()
        self._chunking_service = chunking_service or MarkdownChunkingService()
        self._embedding_service = ChunkEmbeddingService(
            provider=embedding_provider or FakeEmbeddingProvider(),
        )
        self._vector_indexing_service = VectorIndexingService()

    def ingest(
        self,
        transaction: DocumentIngestionTransaction,
    ) -> LocalSeedDocumentIngestionResult:
        discovery_result = self._discover_documents()

        run = IngestionRun.start(source_system=discovery_result.source_system)
        transaction.ingestion_runs.save(run)
        transaction.flush()

        try:
            documents_seen = len(discovery_result.documents)

            documents_changed = 0
            sections_created = 0
            sections_unchanged = 0
            sections_modified = 0
            sections_added = 0
            sections_removed = 0
            chunks_created = 0
            chunks_reused = 0
            embeddings_created = 0
            embeddings_reused = 0
            vector_entries_created = 0
            vector_entries_updated = 0
            vector_entries_deactivated = 0
            embedding_tokens_processed = 0
            estimated_embedding_cost_usd_micros = 0
            ingested_documents: list[LocalSeedDocumentIngestionItem] = []

            for candidate in discovery_result.documents:
                item = self._ingest_candidate(
                    candidate=candidate,
                    run_id=run.id,
                    transaction=transaction,
                )

                if item.action in {
                    LocalSeedDocumentIngestionAction.CREATED,
                    LocalSeedDocumentIngestionAction.VERSION_CREATED,
                }:
                    documents_changed += 1

                sections_created += item.sections_created
                sections_unchanged += item.sections_unchanged
                sections_modified += item.sections_modified
                sections_added += item.sections_added
                sections_removed += item.sections_removed
                chunks_created += item.chunks_created
                chunks_reused += item.chunks_reused
                embeddings_created += item.embeddings_created
                embeddings_reused += item.embeddings_reused
                vector_entries_created += item.vector_entries_created
                vector_entries_updated += item.vector_entries_updated
                vector_entries_deactivated += item.vector_entries_deactivated
                embedding_tokens_processed += item.embedding_tokens_processed
                estimated_embedding_cost_usd_micros += (
                    item.estimated_embedding_cost_usd_micros
                )

                ingested_documents.append(item)

            run.mark_completed(
                documents_seen=documents_seen,
                documents_changed=documents_changed,
                sections_created=sections_created,
                chunks_created=chunks_created,
                embeddings_created=embeddings_created,
                embeddings_reused=embeddings_reused,
                vector_entries_created=vector_entries_created,
                vector_entries_updated=vector_entries_updated,
                vector_entries_deactivated=vector_entries_deactivated,
                embedding_tokens_processed=embedding_tokens_processed,
                estimated_embedding_cost_usd_micros=estimated_embedding_cost_usd_micros,
            )
            transaction.ingestion_runs.save(run)
            transaction.commit()

            return LocalSeedDocumentIngestionResult(
                run_id=run.id,
                source_system=run.source_system,
                source_path=discovery_result.source_path,
                status=run.status,
                documents_seen=documents_seen,
                documents_changed=documents_changed,
                sections_created=sections_created,
                sections_unchanged=sections_unchanged,
                sections_modified=sections_modified,
                sections_added=sections_added,
                sections_removed=sections_removed,
                chunks_created=chunks_created,
                chunks_reused=chunks_reused,
                embeddings_created=embeddings_created,
                embeddings_reused=embeddings_reused,
                vector_entries_created=vector_entries_created,
                vector_entries_updated=vector_entries_updated,
                vector_entries_deactivated=vector_entries_deactivated,
                embedding_tokens_processed=embedding_tokens_processed,
                estimated_embedding_cost_usd_micros=estimated_embedding_cost_usd_micros,
                documents=tuple(ingested_documents),
            )

        except Exception:
            transaction.rollback()
            raise

    def _discover_documents(self) -> SourceDocumentDiscoveryResult:
        if self._discovery_service is not None:
            return self._discovery_service.discover()

        return LocalSeedDocumentDiscoveryService(
            source_path=self._source_path,
        ).discover()

    def _ingest_candidate(
        self,
        *,
        candidate: SourceDocumentCandidate,
        run_id: UUID,
        transaction: DocumentIngestionTransaction,
    ) -> LocalSeedDocumentIngestionItem:
        existing_document = transaction.source_documents.get_by_external_id(
            source_system=candidate.source_system,
            external_id=candidate.external_id,
        )

        if existing_document is None:
            return self._ingest_new_document(
                candidate=candidate,
                run_id=run_id,
                transaction=transaction,
            )

        return self._ingest_existing_document(
            candidate=candidate,
            existing_document=existing_document,
            run_id=run_id,
            transaction=transaction,
        )

    def _ingest_new_document(
        self,
        *,
        candidate: SourceDocumentCandidate,
        run_id: UUID,
        transaction: DocumentIngestionTransaction,
    ) -> LocalSeedDocumentIngestionItem:
        source_document = SourceDocument.create(
            source_system=candidate.source_system,
            external_id=candidate.external_id,
            source_uri=candidate.source_uri,
            title=candidate.title,
        )
        transaction.source_documents.save(source_document)
        transaction.flush()

        document_version = self._create_document_version(
            candidate=candidate,
            source_document_id=source_document.id,
            version_number=1,
            run_id=run_id,
        )
        transaction.document_versions.save(document_version)
        transaction.flush()

        materialization = self._materialize_sections_for_new_document_version(
            document_version=document_version,
            title=candidate.title,
            previous_sections=[],
            transaction=transaction,
        )
        embedding_summary = self._embedding_service.ensure_embeddings_for_chunks(
            chunks=materialization.chunks,
            ingestion_run_id=run_id,
            transaction=transaction,
        )

        vector_summary = self._vector_indexing_service.ensure_current_index_for_document(
            source_document=source_document,
            document_version=document_version,
            section_chunks=self._build_section_chunks(
                sections=materialization.sections,
                chunks=materialization.chunks,
            ),
            transaction=transaction,
        )

        source_document.mark_current_version(document_version.id)
        transaction.source_documents.save(source_document)

        return self._build_ingestion_item(
            candidate=candidate,
            action=LocalSeedDocumentIngestionAction.CREATED,
            source_document_id=source_document.id,
            document_version=document_version,
            materialization=materialization,
            embedding_summary=embedding_summary,
            vector_summary=vector_summary,
        )

    def _ingest_existing_document(
        self,
        *,
        candidate: SourceDocumentCandidate,
        existing_document: SourceDocument,
        run_id: UUID,
        transaction: DocumentIngestionTransaction,
    ) -> LocalSeedDocumentIngestionItem:
        latest_version = transaction.document_versions.get_latest_for_source_document(
            existing_document.id,
        )

        if (
            existing_document.source_uri != candidate.source_uri
            or existing_document.title != candidate.title
        ):
            existing_document.refresh_metadata(
                source_uri=candidate.source_uri,
                title=candidate.title,
            )
            transaction.source_documents.save(existing_document)

        if (
            latest_version is not None
            and latest_version.content_checksum == candidate.content_checksum
        ):
            materialization = self._ensure_existing_document_version_materialized(
                document_version=latest_version,
                title=candidate.title,
                transaction=transaction,
            )
            embedding_summary = self._embedding_service.ensure_embeddings_for_chunks(
                chunks=materialization.chunks,
                ingestion_run_id=run_id,
                transaction=transaction,
            )

            vector_summary = self._vector_indexing_service.ensure_current_index_for_document(
                source_document=existing_document,
                document_version=latest_version,
                section_chunks=self._build_section_chunks(
                    sections=materialization.sections,
                    chunks=materialization.chunks,
                ),
                transaction=transaction,
            )

            return self._build_ingestion_item(
                candidate=candidate,
                action=LocalSeedDocumentIngestionAction.UNCHANGED,
                source_document_id=existing_document.id,
                document_version=latest_version,
                materialization=materialization,
                embedding_summary=embedding_summary,
                vector_summary=vector_summary,
            )

        next_version_number = (
            1 if latest_version is None else latest_version.version_number + 1
        )
        previous_sections: list[SectionVersion] = []
        if latest_version is not None:
            previous_sections = transaction.section_versions.list_for_document_version(
                latest_version.id,
            )

        document_version = self._create_document_version(
            candidate=candidate,
            source_document_id=existing_document.id,
            version_number=next_version_number,
            run_id=run_id,
        )
        transaction.document_versions.save(document_version)
        transaction.flush()

        materialization = self._materialize_sections_for_new_document_version(
            document_version=document_version,
            title=candidate.title,
            previous_sections=previous_sections,
            transaction=transaction,
        )
        embedding_summary = self._embedding_service.ensure_embeddings_for_chunks(
            chunks=materialization.chunks,
            ingestion_run_id=run_id,
            transaction=transaction,
        )

        vector_summary = self._vector_indexing_service.ensure_current_index_for_document(
            source_document=existing_document,
            document_version=document_version,
            section_chunks=self._build_section_chunks(
                sections=materialization.sections,
                chunks=materialization.chunks,
            ),
            transaction=transaction,
        )

        existing_document.mark_current_version(document_version.id)
        transaction.source_documents.save(existing_document)

        return self._build_ingestion_item(
            candidate=candidate,
            action=LocalSeedDocumentIngestionAction.VERSION_CREATED,
            source_document_id=existing_document.id,
            document_version=document_version,
            materialization=materialization,
            embedding_summary=embedding_summary,
            vector_summary=vector_summary,
        )

    def _create_document_version(
        self,
        *,
        candidate: SourceDocumentCandidate,
        source_document_id: UUID,
        version_number: int,
        run_id: UUID,
    ) -> DocumentVersion:
        return DocumentVersion(
            id=uuid4(),
            source_document_id=source_document_id,
            version_number=version_number,
            content_checksum=candidate.content_checksum,
            metadata_checksum=candidate.metadata_checksum,
            raw_content=candidate.raw_content,
            created_by_run_id=run_id,
        )

    def _ensure_existing_document_version_materialized(
        self,
        *,
        document_version: DocumentVersion,
        title: str,
        transaction: DocumentIngestionTransaction,
    ) -> _SectionMaterializationResult:
        existing_sections = transaction.section_versions.list_for_document_version(
            document_version.id,
        )

        if existing_sections:
            chunks, chunks_created = self._ensure_chunks_for_sections(
                sections=existing_sections,
                transaction=transaction,
            )
            return _SectionMaterializationResult(
                sections=existing_sections,
                sections_created=0,
                sections_unchanged=0,
                sections_modified=0,
                sections_added=0,
                sections_removed=0,
                chunks=chunks,
                chunks_created=chunks_created,
                chunks_reused=len(chunks) - chunks_created,
            )

        return self._materialize_sections_for_new_document_version(
            document_version=document_version,
            title=title,
            previous_sections=[],
            transaction=transaction,
        )

    def _materialize_sections_for_new_document_version(
        self,
        *,
        document_version: DocumentVersion,
        title: str,
        previous_sections: list[SectionVersion],
        transaction: DocumentIngestionTransaction,
    ) -> _SectionMaterializationResult:
        existing_sections = transaction.section_versions.list_for_document_version(
            document_version.id,
        )
        if existing_sections:
            chunks, chunks_created = self._ensure_chunks_for_sections(
                sections=existing_sections,
                transaction=transaction,
            )
            return _SectionMaterializationResult(
                sections=existing_sections,
                sections_created=0,
                sections_unchanged=0,
                sections_modified=0,
                sections_added=0,
                sections_removed=0,
                chunks=chunks,
                chunks_created=chunks_created,
                chunks_reused=len(chunks) - chunks_created,
            )

        incoming_sections = self._section_extraction_service.extract(
            content=document_version.raw_content,
            fallback_title=title,
        )
        plan = self._section_delta_planner.plan(
            previous_sections=previous_sections,
            incoming_sections=incoming_sections,
        )

        snapshot_sections: list[SectionVersion] = []
        sections_created = 0
        sections_to_persist: list[SectionVersion] = []
        sections_requiring_chunking: list[SectionVersion] = []

        for incoming in incoming_sections:
            entry = next(
                item
                for item in plan.entries
                if item.incoming is not None
                and item.incoming.stable_section_key == incoming.stable_section_key
            )

            if entry.kind == SectionDeltaKind.UNCHANGED:
                assert entry.previous is not None
                section = SectionVersion(
                    id=entry.previous.id,
                    document_version_id=document_version.id,
                    stable_section_key=entry.previous.stable_section_key,
                    heading_path=entry.previous.heading_path,
                    heading_level=entry.previous.heading_level,
                    title=entry.previous.title,
                    body=entry.previous.body,
                    section_checksum=entry.previous.section_checksum,
                    ordinal=incoming.ordinal,
                    created_at=entry.previous.created_at,
                )
                sections_to_persist.append(section)
                snapshot_sections.append(section)
                continue

            section = self._create_section_version_from_extracted(
                document_version_id=document_version.id,
                extracted=incoming,
            )
            sections_to_persist.append(section)
            snapshot_sections.append(section)
            sections_requiring_chunking.append(section)
            sections_created += 1

        if sections_to_persist:
            transaction.section_versions.save_many(sections_to_persist)
            transaction.flush()

        all_chunks: list[ChunkVersion] = []
        chunks_created = 0
        chunks_reused = 0
        chunking_section_ids = {section.id for section in sections_requiring_chunking}

        for section in snapshot_sections:
            if section.id in chunking_section_ids:
                chunk_versions = self._chunking_service.create_chunk_versions(
                    section_version=section,
                )
                transaction.chunk_versions.save_many(chunk_versions)
                all_chunks.extend(chunk_versions)
                chunks_created += len(chunk_versions)
                continue

            existing_chunks = transaction.chunk_versions.list_for_section_version(
                section.id,
            )
            all_chunks.extend(existing_chunks)
            chunks_reused += len(existing_chunks)

        if chunks_created > 0:
            transaction.flush()

        return _SectionMaterializationResult(
            sections=snapshot_sections,
            sections_created=sections_created,
            sections_unchanged=len(plan.unchanged),
            sections_modified=len(plan.modified),
            sections_added=len(plan.added),
            sections_removed=len(plan.removed),
            chunks=all_chunks,
            chunks_created=chunks_created,
            chunks_reused=chunks_reused,
        )

    def _create_section_version_from_extracted(
        self,
        *,
        document_version_id: UUID,
        extracted: ExtractedMarkdownSection,
    ) -> SectionVersion:
        return SectionVersion(
            id=uuid4(),
            document_version_id=document_version_id,
            stable_section_key=extracted.stable_section_key,
            heading_path=extracted.heading_path,
            heading_level=extracted.heading_level,
            title=extracted.title,
            body=extracted.body,
            section_checksum=extracted.section_checksum,
            ordinal=extracted.ordinal,
        )

    def _ensure_chunks_for_sections(
        self,
        *,
        sections: list[SectionVersion],
        transaction: DocumentIngestionTransaction,
    ) -> tuple[list[ChunkVersion], int]:
        all_chunks: list[ChunkVersion] = []
        chunks_created = 0

        for section in sections:
            existing_chunks = transaction.chunk_versions.list_for_section_version(
                section.id,
            )

            if existing_chunks:
                all_chunks.extend(existing_chunks)
                continue

            chunk_versions = self._chunking_service.create_chunk_versions(
                section_version=section,
            )
            transaction.chunk_versions.save_many(chunk_versions)
            all_chunks.extend(chunk_versions)
            chunks_created += len(chunk_versions)

        if chunks_created > 0:
            transaction.flush()

        return all_chunks, chunks_created

    def _build_ingestion_item(
        self,
        *,
        candidate: SourceDocumentCandidate,
        action: LocalSeedDocumentIngestionAction,
        source_document_id: UUID,
        document_version: DocumentVersion,
        materialization: _SectionMaterializationResult,
        embedding_summary: EmbeddingGenerationSummary,
        vector_summary: VectorIndexingSummary,
    ) -> LocalSeedDocumentIngestionItem:
        return LocalSeedDocumentIngestionItem(
            external_id=candidate.external_id,
            title=candidate.title,
            action=action,
            source_document_id=source_document_id,
            document_version_id=document_version.id,
            version_number=document_version.version_number,
            content_checksum=candidate.content_checksum,
            sections_created=materialization.sections_created,
            sections_unchanged=materialization.sections_unchanged,
            sections_modified=materialization.sections_modified,
            sections_added=materialization.sections_added,
            sections_removed=materialization.sections_removed,
            chunks_created=materialization.chunks_created,
            chunks_reused=materialization.chunks_reused,
            embeddings_created=embedding_summary.embeddings_created,
            embeddings_reused=embedding_summary.embeddings_reused,
            vector_entries_created=vector_summary.vector_entries_created,
            vector_entries_updated=vector_summary.vector_entries_updated,
            vector_entries_deactivated=vector_summary.vector_entries_deactivated,
            embedding_tokens_processed=embedding_summary.embedding_tokens_processed,
            estimated_embedding_cost_usd_micros=(
                embedding_summary.estimated_embedding_cost_usd_micros
            ),
        )

    def _build_section_chunks(
        self,
        *,
        sections: list[SectionVersion],
        chunks: list[ChunkVersion],
    ) -> list[SectionChunks]:
        chunks_by_section_id: dict[UUID, list[ChunkVersion]] = {}

        for chunk in chunks:
            chunks_by_section_id.setdefault(chunk.section_version_id, []).append(chunk)

        return [
            SectionChunks(
                section=section,
                chunks=sorted(
                    chunks_by_section_id.get(section.id, []),
                    key=lambda chunk: chunk.chunk_index,
                ),
            )
            for section in sorted(sections, key=lambda section: section.ordinal)
        ]
