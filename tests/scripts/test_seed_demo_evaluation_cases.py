import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from uuid import UUID, uuid4

from app.application.services.demo_retrieval_evaluation_cases import (
    DemoRetrievalEvaluationCaseDefinition,
)
from app.domain.evaluation.entities import RetrievalEvaluationCase

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_seed_demo_evaluation_cases_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "seed_demo_evaluation_cases.py"
    module_name = "seed_demo_evaluation_cases"
    spec = importlib.util.spec_from_file_location(module_name, module_path)

    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load seed_demo_evaluation_cases module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _sample_definition() -> DemoRetrievalEvaluationCaseDefinition:
    return DemoRetrievalEvaluationCaseDefinition(
        name="Project Atlas ownership",
        query="Who owns Project Atlas?",
        expected_stable_section_keys=("project-atlas-brief/ownership",),
        tags=("demo", "project-atlas", "retrieval-evaluation"),
    )


def _sample_case(
    *,
    expected_chunk_version_ids: tuple[UUID, ...] | None = None,
    query: str = "Who owns Project Atlas?",
    tags: tuple[str, ...] = ("demo", "project-atlas", "retrieval-evaluation"),
) -> RetrievalEvaluationCase:
    return RetrievalEvaluationCase.create(
        name="Project Atlas ownership",
        query=query,
        expected_chunk_version_ids=expected_chunk_version_ids or (uuid4(),),
        tags=tags,
    )


def test_parse_args_defaults() -> None:
    module = _load_seed_demo_evaluation_cases_module()

    options = module.parse_args([])

    assert options.dry_run is False
    assert options.provider == module.DEFAULT_PROVIDER
    assert options.model_name == module.DEFAULT_MODEL_NAME


def test_parse_args_accepts_dry_run_and_embedding_filters() -> None:
    module = _load_seed_demo_evaluation_cases_module()

    options = module.parse_args(
        [
            "--dry-run",
            "--provider",
            "fake",
            "--model-name",
            "fake-embedding-v1",
        ],
    )

    assert options.dry_run is True
    assert options.provider == "fake"
    assert options.model_name == "fake-embedding-v1"


def test_evaluation_cases_are_equivalent_ignores_tag_order() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    chunk_version_id = uuid4()
    existing = _sample_case(
        expected_chunk_version_ids=(chunk_version_id,),
        tags=("retrieval-evaluation", "demo"),
    )

    assert module.evaluation_cases_are_equivalent(
        existing=existing,
        query="Who owns Project Atlas?",
        tags=("demo", "retrieval-evaluation"),
        expected_chunk_version_ids=(chunk_version_id,),
    )


def test_plan_evaluation_case_seed_creates_when_missing() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    definition = _sample_definition()
    expected_chunk_version_ids = (uuid4(),)

    plan = module.plan_evaluation_case_seed(
        definition=definition,
        expected_chunk_version_ids=expected_chunk_version_ids,
        existing_by_name={},
        duplicate_names=set(),
    )

    assert plan.action == "create"
    assert plan.expected_chunk_version_ids == expected_chunk_version_ids


def test_plan_evaluation_case_seed_skips_identical_existing_case() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    definition = _sample_definition()
    chunk_version_id = uuid4()
    existing = _sample_case(expected_chunk_version_ids=(chunk_version_id,))

    plan = module.plan_evaluation_case_seed(
        definition=definition,
        expected_chunk_version_ids=(chunk_version_id,),
        existing_by_name={definition.name: existing},
        duplicate_names=set(),
    )

    assert plan.action == "skip"


def test_plan_evaluation_case_seed_conflicts_when_existing_case_differs() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    definition = _sample_definition()
    existing = _sample_case(
        expected_chunk_version_ids=(uuid4(),),
        query="Different query",
    )

    plan = module.plan_evaluation_case_seed(
        definition=definition,
        expected_chunk_version_ids=(uuid4(),),
        existing_by_name={definition.name: existing},
        duplicate_names=set(),
    )

    assert plan.action == "conflict"
    assert plan.conflict_reason is not None


def test_plan_evaluation_case_seed_conflicts_on_duplicate_names() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    definition = _sample_definition()

    plan = module.plan_evaluation_case_seed(
        definition=definition,
        expected_chunk_version_ids=(uuid4(),),
        existing_by_name={},
        duplicate_names={definition.name},
    )

    assert plan.action == "conflict"


def test_build_expected_chunk_version_ids_preserves_definition_order() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    first_chunk_id = uuid4()
    second_chunk_id = uuid4()
    definition = DemoRetrievalEvaluationCaseDefinition(
        name="Incident severity levels",
        query="What is the incident severity process?",
        expected_stable_section_keys=(
            "incident-response-playbook/severity-levels",
            "incident-response-playbook/response-process",
        ),
        tags=("demo", "incident-response", "retrieval-evaluation"),
    )

    expected_chunk_version_ids = module.build_expected_chunk_version_ids(
        definition,
        {
            "incident-response-playbook/severity-levels": (first_chunk_id,),
            "incident-response-playbook/response-process": (second_chunk_id,),
        },
    )

    assert expected_chunk_version_ids == (first_chunk_id, second_chunk_id)


def test_build_seed_summary_counts_actions() -> None:
    module = _load_seed_demo_evaluation_cases_module()
    definition = _sample_definition()
    chunk_version_id = uuid4()
    plans = (
        module.EvaluationCaseSeedPlan(
            definition=definition,
            expected_chunk_version_ids=(chunk_version_id,),
            action="create",
        ),
        module.EvaluationCaseSeedPlan(
            definition=DemoRetrievalEvaluationCaseDefinition(
                name="Project Atlas overview",
                query="What is Project Atlas?",
                expected_stable_section_keys=("project-atlas-brief/overview",),
                tags=("demo", "project-atlas", "retrieval-evaluation"),
            ),
            expected_chunk_version_ids=(uuid4(),),
            action="skip",
        ),
        module.EvaluationCaseSeedPlan(
            definition=DemoRetrievalEvaluationCaseDefinition(
                name="Support escalation checklist",
                query="What should support do before escalating a customer issue?",
                expected_stable_section_keys=(
                    "customer-support-escalation-policy/pre-escalation-checklist",
                ),
                tags=("demo", "support", "retrieval-evaluation"),
            ),
            expected_chunk_version_ids=(uuid4(),),
            action="conflict",
            conflict_reason="conflict",
        ),
    )

    summary = module.build_seed_summary(
        plans=plans,
        missing_stable_section_keys=(),
        options=module.SeedDemoEvaluationCasesOptions(
            dry_run=True,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
    )

    assert summary.total_definitions == 3
    assert summary.created_count == 1
    assert summary.skipped_count == 1
    assert summary.conflict_count == 1


def test_find_missing_stable_section_keys_detects_empty_resolution() -> None:
    module = _load_seed_demo_evaluation_cases_module()

    missing = module.find_missing_stable_section_keys(
        ("project-atlas-brief/ownership", "project-atlas-brief/overview"),
        {
            "project-atlas-brief/ownership": (uuid4(),),
            "project-atlas-brief/overview": (),
        },
    )

    assert missing == ("project-atlas-brief/overview",)
