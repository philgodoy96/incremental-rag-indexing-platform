from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.services.demo_dataset_discovery_service import DemoDatasetDiscoveryService
from app.application.services.demo_dataset_loader import DemoDatasetLoader
from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionAction,
    LocalSeedDocumentIngestionResult,
    LocalSeedDocumentIngestionService,
)
from app.application.services.source_document_discovery import SourceDocumentDiscoveryResult
from app.domain.documents.enums import SourceSystem

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "demo" / "documents" / "manifest.json"


@dataclass(frozen=True, slots=True)
class SeedDemoDatasetOptions:
    manifest_path: Path
    dry_run: bool


def parse_args(argv: list[str] | None = None) -> SeedDemoDatasetOptions:
    parser = argparse.ArgumentParser(
        description="Index the deterministic demo dataset via the ingestion pipeline.",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to demo dataset manifest JSON (default: demo/documents/manifest.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover documents and print a summary without writing to the database.",
    )

    args = parser.parse_args(argv)

    return SeedDemoDatasetOptions(
        manifest_path=args.manifest_path.resolve(),
        dry_run=args.dry_run,
    )


def build_discovery_service(manifest_path: Path) -> DemoDatasetDiscoveryService:
    return DemoDatasetDiscoveryService(
        repo_root=REPO_ROOT,
        manifest_path=manifest_path,
    )


def build_ingestion_service(
    discovery_service: DemoDatasetDiscoveryService,
    manifest_path: Path,
) -> LocalSeedDocumentIngestionService:
    return LocalSeedDocumentIngestionService(
        source_path=manifest_path,
        discovery_service=discovery_service,
    )


def count_active_vector_index_entries_for_source_system(
    session: Session,
    source_system: SourceSystem,
) -> int:
    from app.infrastructure.db.models.document_models import (
        SourceDocumentModel,
        VectorIndexEntryModel,
    )

    statement = (
        select(func.count())
        .select_from(VectorIndexEntryModel)
        .join(
            SourceDocumentModel,
            VectorIndexEntryModel.source_document_id == SourceDocumentModel.id,
        )
        .where(
            SourceDocumentModel.source_system == source_system.value,
            VectorIndexEntryModel.is_active.is_(True),
        )
    )

    return session.execute(statement).scalar_one()


def count_document_versions_for_source_system(
    session: Session,
    source_system: SourceSystem,
) -> int:
    from app.infrastructure.db.models.document_models import (
        DocumentVersionModel,
        SourceDocumentModel,
    )

    statement = (
        select(func.count())
        .select_from(DocumentVersionModel)
        .join(
            SourceDocumentModel,
            DocumentVersionModel.source_document_id == SourceDocumentModel.id,
        )
        .where(SourceDocumentModel.source_system == source_system.value)
    )

    return session.execute(statement).scalar_one()


def _action_counts(
    result: LocalSeedDocumentIngestionResult,
) -> tuple[int, int, int]:
    created = 0
    updated = 0
    skipped = 0

    for document in result.documents:
        if document.action == LocalSeedDocumentIngestionAction.CREATED:
            created += 1
        elif document.action == LocalSeedDocumentIngestionAction.VERSION_CREATED:
            updated += 1
        elif document.action == LocalSeedDocumentIngestionAction.UNCHANGED:
            skipped += 1

    return created, updated, skipped


def _collect_warnings(
    *,
    result: LocalSeedDocumentIngestionResult,
    vector_index_entry_count: int,
) -> list[str]:
    warnings: list[str] = []

    if vector_index_entry_count == 0:
        warnings.append(
            "No active vector index entries found for demo_documents after ingestion. "
            "Verify the database is reachable and migrations are applied.",
        )

    if result.documents_seen > 0 and all(
        document.action == LocalSeedDocumentIngestionAction.UNCHANGED
        for document in result.documents
    ):
        warnings.append(
            "All documents were unchanged (checksum match). "
            "Reruns are idempotent for unchanged demo content.",
        )

    return warnings


def print_dry_run_summary(
    *,
    dataset_name: str,
    dataset_version: str,
    discovery_result: SourceDocumentDiscoveryResult,
) -> None:
    print(f"Dataset: {dataset_name}")
    print(f"Version: {dataset_version}")
    print(f"Manifest: {discovery_result.source_path}")
    print(f"Discovered documents: {discovery_result.document_count}")
    print()
    print("Dry run only; no database writes were performed.")
    print("Embedding provider: fake (fake-embedding-v1) via LocalSeedDocumentIngestionService.")
    print()
    print("Documents:")

    for document in discovery_result.documents:
        print(f"- {document.title} ({document.external_id})")


def print_ingestion_summary(
    *,
    dataset_name: str,
    dataset_version: str,
    discovery_result: SourceDocumentDiscoveryResult,
    result: LocalSeedDocumentIngestionResult,
    document_version_count: int,
    vector_index_entry_count: int,
    warnings: list[str],
) -> None:
    created, updated, skipped = _action_counts(result)

    print(f"Dataset: {dataset_name}")
    print(f"Version: {dataset_version}")
    print(f"Manifest: {discovery_result.source_path}")
    print(f"Ingestion run: {result.run_id}")
    print(f"Status: {result.status.value}")
    print()
    print(f"Discovered documents: {discovery_result.document_count}")
    print(f"Documents created: {created}")
    print(f"Documents updated (new version): {updated}")
    print(f"Documents skipped (unchanged): {skipped}")
    print()
    print(f"Sections created (this run): {result.sections_created}")
    print(f"Chunks created (this run): {result.chunks_created}")
    print(
        "Embeddings (this run): "
        f"{result.embeddings_created} created, {result.embeddings_reused} reused",
    )
    print(
        "Vector index entries (this run): "
        f"{result.vector_entries_created} created, "
        f"{result.vector_entries_updated} updated, "
        f"{result.vector_entries_deactivated} deactivated",
    )
    print()
    print(f"Document versions (demo_documents total): {document_version_count}")
    print(f"Active vector index entries (demo_documents total): {vector_index_entry_count}")
    print()
    print("Embedding provider: fake (fake-embedding-v1) via LocalSeedDocumentIngestionService.")

    if warnings:
        print()
        print("Warnings:")

        for warning in warnings:
            print(f"- {warning}")


def run(options: SeedDemoDatasetOptions) -> int:
    try:
        dataset = DemoDatasetLoader(
            repo_root=REPO_ROOT,
            manifest_path=options.manifest_path,
        ).load()
        discovery_service = build_discovery_service(options.manifest_path)
        discovery_result = discovery_service.discover()

        if options.dry_run:
            print_dry_run_summary(
                dataset_name=dataset.name,
                dataset_version=dataset.version,
                discovery_result=discovery_result,
            )
            return 0

        ingestion_service = build_ingestion_service(
            discovery_service,
            options.manifest_path,
        )

        from app.infrastructure.db.session import SessionLocal
        from app.infrastructure.transactions import SqlAlchemyDocumentIngestionTransaction

        with SessionLocal() as session:
            transaction = SqlAlchemyDocumentIngestionTransaction(session=session)
            result = ingestion_service.ingest(transaction)

            document_version_count = count_document_versions_for_source_system(
                session,
                SourceSystem.DEMO_DOCUMENTS,
            )
            vector_index_entry_count = count_active_vector_index_entries_for_source_system(
                session,
                SourceSystem.DEMO_DOCUMENTS,
            )

        warnings = _collect_warnings(
            result=result,
            vector_index_entry_count=vector_index_entry_count,
        )

        print_ingestion_summary(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            discovery_result=discovery_result,
            result=result,
            document_version_count=document_version_count,
            vector_index_entry_count=vector_index_entry_count,
            warnings=warnings,
        )

        return 0

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def main() -> None:
    sys.exit(run(parse_args()))


if __name__ == "__main__":
    main()
