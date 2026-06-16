from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryService,
)
from app.application.services.markdown_section_extraction_service import (
    MarkdownSectionExtractionService,
)
from app.application.transactions import DocumentIngestionTransaction
from app.domain.documents.entities import DocumentVersion, IngestionRun, SourceDocument
from app.domain.documents.enums import IngestionRunStatus, SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate


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


@dataclass(frozen=True, slots=True)
class LocalSeedDocumentIngestionResult:
    run_id: UUID
    source_system: SourceSystem
    source_path: str
    status: IngestionRunStatus
    documents_seen: int
    documents_changed: int
    sections_created: int
    documents: tuple[LocalSeedDocumentIngestionItem, ...]


class LocalSeedDocumentIngestionService:
    """Persists local seed Markdown documents as versioned source documents."""

    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path
        self._section_extraction_service = MarkdownSectionExtractionService()

    def ingest(
        self,
        transaction: DocumentIngestionTransaction,
    ) -> LocalSeedDocumentIngestionResult:
        run = IngestionRun.start(source_system=SourceSystem.LOCAL_SEED_DOCUMENTS)
        transaction.ingestion_runs.save(run)
        transaction.flush()

        try:
            discovery_result = LocalSeedDocumentDiscoveryService(
                source_path=self._source_path,
            ).discover()

            documents_changed = 0
            sections_created = 0
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
                ingested_documents.append(item)

            run.mark_completed(
                documents_seen=discovery_result.document_count,
                documents_changed=documents_changed,
                sections_created=sections_created,
            )
            transaction.ingestion_runs.save(run)
            transaction.commit()

            return LocalSeedDocumentIngestionResult(
                run_id=run.id,
                source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
                source_path=discovery_result.source_path,
                status=run.status,
                documents_seen=run.documents_seen,
                documents_changed=run.documents_changed,
                sections_created=run.sections_created,
                documents=tuple(ingested_documents),
            )

        except Exception:
            transaction.rollback()
            raise

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

            created_section_count = self._ensure_sections_for_document_version(
                document_version=document_version,
                title=candidate.title,
                transaction=transaction,
            )

            source_document.mark_current_version(document_version.id)
            transaction.source_documents.save(source_document)

            return LocalSeedDocumentIngestionItem(
                external_id=candidate.external_id,
                title=candidate.title,
                action=LocalSeedDocumentIngestionAction.CREATED,
                source_document_id=source_document.id,
                document_version_id=document_version.id,
                version_number=document_version.version_number,
                content_checksum=candidate.content_checksum,
                sections_created=created_section_count,
            )

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
            created_section_count = self._ensure_sections_for_document_version(
                document_version=latest_version,
                title=candidate.title,
                transaction=transaction,
            )

            return LocalSeedDocumentIngestionItem(
                external_id=candidate.external_id,
                title=candidate.title,
                action=LocalSeedDocumentIngestionAction.UNCHANGED,
                source_document_id=existing_document.id,
                document_version_id=latest_version.id,
                version_number=latest_version.version_number,
                content_checksum=candidate.content_checksum,
                sections_created=created_section_count,
            )

        next_version_number = (
            1 if latest_version is None else latest_version.version_number + 1
        )

        document_version = self._create_document_version(
            candidate=candidate,
            source_document_id=existing_document.id,
            version_number=next_version_number,
            run_id=run_id,
        )
        transaction.document_versions.save(document_version)
        transaction.flush()

        created_section_count = self._ensure_sections_for_document_version(
            document_version=document_version,
            title=candidate.title,
            transaction=transaction,
        )

        existing_document.mark_current_version(document_version.id)
        transaction.source_documents.save(existing_document)

        return LocalSeedDocumentIngestionItem(
            external_id=candidate.external_id,
            title=candidate.title,
            action=LocalSeedDocumentIngestionAction.VERSION_CREATED,
            source_document_id=existing_document.id,
            document_version_id=document_version.id,
            version_number=document_version.version_number,
            content_checksum=candidate.content_checksum,
            sections_created=created_section_count,
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

    def _ensure_sections_for_document_version(
        self,
        *,
        document_version: DocumentVersion,
        title: str,
        transaction: DocumentIngestionTransaction,
    ) -> int:
        existing_sections = transaction.section_versions.list_for_document_version(
            document_version.id,
        )

        if existing_sections:
            return 0

        section_versions = self._section_extraction_service.create_section_versions(
            document_version_id=document_version.id,
            content=document_version.raw_content,
            fallback_title=title,
        )

        transaction.section_versions.save_many(section_versions)
        transaction.flush()

        return len(section_versions)