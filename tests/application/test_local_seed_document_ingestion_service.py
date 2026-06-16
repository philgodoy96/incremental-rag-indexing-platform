from pathlib import Path
from uuid import UUID

from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionAction,
    LocalSeedDocumentIngestionService,
)
from app.domain.documents.entities import DocumentVersion, IngestionRun, SourceDocument
from app.domain.documents.enums import SourceSystem
from app.domain.documents.repositories import (
    DocumentVersionRepository,
    IngestionRunRepository,
    SourceDocumentRepository,
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


class InMemoryIngestionRunRepository(IngestionRunRepository):
    def __init__(self) -> None:
        self.ingestion_runs: dict[UUID, IngestionRun] = {}

    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        return self.ingestion_runs.get(ingestion_run_id)

    def save(self, ingestion_run: IngestionRun) -> None:
        self.ingestion_runs[ingestion_run.id] = ingestion_run


class InMemoryDocumentIngestionTransaction:
    def __init__(self) -> None:
        self.source_document_repository = InMemorySourceDocumentRepository()
        self.document_version_repository = InMemoryDocumentVersionRepository()
        self.ingestion_run_repository = InMemoryIngestionRunRepository()

        self.source_documents: SourceDocumentRepository = self.source_document_repository
        self.document_versions: DocumentVersionRepository = self.document_version_repository
        self.ingestion_runs: IngestionRunRepository = self.ingestion_run_repository

        self.commit_count = 0
        self.rollback_count = 0

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_local_seed_ingestion_creates_document_and_initial_version(
    tmp_path: Path,
) -> None:
    (tmp_path / "project-atlas-status.md").write_text(
        "# Project Atlas Status\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    result = service.ingest(transaction)

    assert result.documents_seen == 1
    assert result.documents_changed == 1
    assert result.documents[0].action == LocalSeedDocumentIngestionAction.CREATED
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 1
    assert transaction.commit_count == 1
    assert transaction.rollback_count == 0


def test_local_seed_ingestion_is_idempotent_for_unchanged_documents(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "project-atlas-status.md"
    document_path.write_text(
        "# Project Atlas Status\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)
    second_result = service.ingest(transaction)

    assert second_result.documents_seen == 1
    assert second_result.documents_changed == 0
    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.UNCHANGED
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 1


def test_local_seed_ingestion_creates_new_version_when_content_changes(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "project-atlas-status.md"
    document_path.write_text(
        "# Project Atlas Status\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    transaction = InMemoryDocumentIngestionTransaction()
    service = LocalSeedDocumentIngestionService(source_path=tmp_path)

    service.ingest(transaction)

    document_path.write_text(
        "# Project Atlas Status\n\nStatus: At Risk\n",
        encoding="utf-8",
    )

    second_result = service.ingest(transaction)

    assert second_result.documents_seen == 1
    assert second_result.documents_changed == 1
    assert second_result.documents[0].action == LocalSeedDocumentIngestionAction.VERSION_CREATED
    assert second_result.documents[0].version_number == 2
    assert len(transaction.source_document_repository.documents) == 1
    assert len(transaction.document_version_repository.document_versions) == 2