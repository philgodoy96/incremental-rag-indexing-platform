from pathlib import Path

from app.application.services.demo_dataset_discovery_service import (
    DemoDatasetDiscoveryService,
)
from app.domain.documents.enums import SourceSystem

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_demo_dataset_discovery_service_maps_manifest_into_four_candidates() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    assert result.source_system == SourceSystem.DEMO_DOCUMENTS
    assert result.document_count == 4
    assert result.source_path.endswith("demo/documents/manifest.json")


def test_demo_dataset_discovery_service_preserves_manifest_external_ids() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    external_ids = {document.external_id for document in result.documents}

    assert external_ids == {
        "demo/project-atlas-brief",
        "demo/incident-response-playbook",
        "demo/customer-support-escalation-policy",
        "demo/engineering-onboarding-guide",
    }


def test_demo_dataset_discovery_service_preserves_manifest_titles() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    titles = {document.title for document in result.documents}

    assert titles == {
        "Project Atlas Brief",
        "Incident Response Playbook",
        "Customer Support Escalation Policy",
        "Engineering Onboarding Guide",
    }


def test_demo_dataset_discovery_service_preserves_demo_source_uri_scheme() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    source_uris = {document.source_uri for document in result.documents}

    assert source_uris == {
        "demo://project-atlas-brief",
        "demo://incident-response-playbook",
        "demo://customer-support-escalation-policy",
        "demo://engineering-onboarding-guide",
    }


def test_demo_dataset_discovery_service_preserves_manifest_tags() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    tags_by_external_id = {
        document.external_id: document.tags
        for document in result.documents
    }

    assert tags_by_external_id["demo/project-atlas-brief"] == (
        "project-atlas",
        "platform",
        "ai-infrastructure",
    )
    assert tags_by_external_id["demo/incident-response-playbook"] == (
        "incident-response",
        "operations",
        "reliability",
    )


def test_demo_dataset_discovery_service_does_not_write_to_database() -> None:
    result = DemoDatasetDiscoveryService(repo_root=REPO_ROOT).discover()

    assert result.documents
    assert all(document.raw_content.strip() for document in result.documents)
    assert all(document.content_checksum for document in result.documents)
    assert all(document.metadata_checksum for document in result.documents)
