from pathlib import Path

from app.application.services.demo_dataset_loader import DemoDatasetLoader
from app.application.services.demo_retrieval_evaluation_cases import (
    DemoRetrievalEvaluationCaseDefinition,
    get_demo_retrieval_evaluation_case_definitions,
)
from app.application.services.markdown_section_extraction_service import (
    MarkdownSectionExtractionService,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_CASE_NAMES = {
    "Project Atlas ownership",
    "Project Atlas overview",
    "Support escalation checklist",
    "Incident severity levels",
    "Engineering first week",
}


def _extracted_stable_section_keys_by_document() -> dict[str, set[str]]:
    dataset = DemoDatasetLoader(repo_root=REPO_ROOT).load()
    extraction_service = MarkdownSectionExtractionService()
    keys_by_document: dict[str, set[str]] = {}

    for document in dataset.documents:
        sections = extraction_service.extract(
            content=document.content,
            fallback_title=document.title,
        )
        keys_by_document[document.external_id] = {
            section.stable_section_key for section in sections
        }

    return keys_by_document


def test_definitions_are_non_empty() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()

    assert definitions
    assert all(
        isinstance(definition, DemoRetrievalEvaluationCaseDefinition)
        for definition in definitions
    )


def test_definition_names_are_unique() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()
    names = [definition.name for definition in definitions]

    assert len(names) == len(set(names))


def test_definition_queries_are_non_empty() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()

    for definition in definitions:
        assert definition.query.strip()


def test_definition_expected_stable_section_keys_are_non_empty() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()

    for definition in definitions:
        assert definition.expected_stable_section_keys
        assert all(key.strip() for key in definition.expected_stable_section_keys)


def test_definition_expected_stable_section_keys_are_unique_per_case() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()

    for definition in definitions:
        keys = definition.expected_stable_section_keys

        assert len(keys) == len(set(keys))


def test_definition_tags_are_deterministic() -> None:
    first_definitions = get_demo_retrieval_evaluation_case_definitions()
    second_definitions = get_demo_retrieval_evaluation_case_definitions()

    first_tags = tuple(definition.tags for definition in first_definitions)
    second_tags = tuple(definition.tags for definition in second_definitions)

    assert first_tags == second_tags

    for definition in first_definitions:
        assert definition.tags
        assert all(tag.strip() for tag in definition.tags)
        assert "demo" in definition.tags
        assert "retrieval-evaluation" in definition.tags


def test_definitions_include_important_demo_questions() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()
    names = {definition.name for definition in definitions}

    assert names == EXPECTED_CASE_NAMES


def test_expected_stable_section_keys_exist_in_demo_documents() -> None:
    definitions = get_demo_retrieval_evaluation_case_definitions()
    extracted_keys = {
        key
        for keys in _extracted_stable_section_keys_by_document().values()
        for key in keys
    }

    for definition in definitions:
        for key in definition.expected_stable_section_keys:
            assert key in extracted_keys, (
                f"{definition.name} references missing stable section key: {key}"
            )
