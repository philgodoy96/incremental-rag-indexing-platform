import json
from pathlib import Path

import pytest

from app.application.services.demo_dataset_loader import DemoDatasetLoader

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_demo_dataset_loader_loads_repository_dataset() -> None:
    dataset = DemoDatasetLoader(repo_root=REPO_ROOT).load()

    assert dataset.name == "acme_internal_knowledge_demo"
    assert dataset.version == "1.0.0"
    assert len(dataset.documents) == 4

    titles = {document.title for document in dataset.documents}

    assert titles == {
        "Project Atlas Brief",
        "Incident Response Playbook",
        "Customer Support Escalation Policy",
        "Engineering Onboarding Guide",
    }

    external_ids = {document.external_id for document in dataset.documents}

    assert external_ids == {
        "demo/project-atlas-brief",
        "demo/incident-response-playbook",
        "demo/customer-support-escalation-policy",
        "demo/engineering-onboarding-guide",
    }

    for document in dataset.documents:
        assert document.content.strip()
        assert document.file_path.exists()
        assert document.file_path.is_absolute()
        assert len(document.content_checksum) == 64
        int(document.content_checksum, 16)


def test_demo_dataset_loader_is_deterministic() -> None:
    first_dataset = DemoDatasetLoader(repo_root=REPO_ROOT).load()
    second_dataset = DemoDatasetLoader(repo_root=REPO_ROOT).load()

    first_checksums = {
        document.external_id: document.content_checksum
        for document in first_dataset.documents
    }
    second_checksums = {
        document.external_id: document.content_checksum
        for document in second_dataset.documents
    }

    assert first_checksums == second_checksums


def test_demo_dataset_loader_rejects_missing_manifest(tmp_path: Path) -> None:
    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=tmp_path / "missing-manifest.json",
    )

    with pytest.raises(FileNotFoundError, match="manifest not found"):
        loader.load()


def test_demo_dataset_loader_rejects_invalid_json_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{invalid-json", encoding="utf-8")

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(ValueError, match="manifest must be valid JSON"):
        loader.load()


def test_demo_dataset_loader_rejects_empty_documents_list(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo",
                "dataset_version": "1.0.0",
                "documents": [],
            },
        ),
        encoding="utf-8",
    )

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(
        ValueError,
        match="manifest documents must be a non-empty list",
    ):
        loader.load()


def test_demo_dataset_loader_rejects_duplicate_external_ids(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "document.md"
    document_path.write_text("# Demo Document\n\nContent.", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo",
                "dataset_version": "1.0.0",
                "documents": [
                    {
                        "external_id": "duplicate",
                        "title": "First Document",
                        "file_path": "document.md",
                        "source_uri": "demo://first",
                        "tags": ["demo"],
                    },
                    {
                        "external_id": "duplicate",
                        "title": "Second Document",
                        "file_path": "document.md",
                        "source_uri": "demo://second",
                        "tags": ["demo"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(
        ValueError,
        match="external_id values must be unique: duplicate",
    ):
        loader.load()


def test_demo_dataset_loader_rejects_file_path_that_escapes_repo_root(
    tmp_path: Path,
) -> None:
    outside_document_path = tmp_path.parent / "outside-document.md"
    outside_document_path.write_text("# Outside\n\nContent.", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo",
                "dataset_version": "1.0.0",
                "documents": [
                    {
                        "external_id": "demo/outside",
                        "title": "Outside Document",
                        "file_path": "../outside-document.md",
                        "source_uri": "demo://outside",
                        "tags": ["demo"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(
        ValueError,
        match="document file_path escapes repo root",
    ):
        loader.load()


def test_demo_dataset_loader_rejects_empty_document_content(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "empty.md"
    document_path.write_text("   ", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo",
                "dataset_version": "1.0.0",
                "documents": [
                    {
                        "external_id": "demo/empty",
                        "title": "Empty Document",
                        "file_path": "empty.md",
                        "source_uri": "demo://empty",
                        "tags": ["demo"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(ValueError, match="demo document must not be empty"):
        loader.load()


def test_demo_dataset_loader_rejects_missing_document_file(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo",
                "dataset_version": "1.0.0",
                "documents": [
                    {
                        "external_id": "demo/missing",
                        "title": "Missing Document",
                        "file_path": "missing.md",
                        "source_uri": "demo://missing",
                        "tags": ["demo"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    loader = DemoDatasetLoader(
        repo_root=tmp_path,
        manifest_path=manifest_path,
    )

    with pytest.raises(FileNotFoundError, match="demo document not found"):
        loader.load()