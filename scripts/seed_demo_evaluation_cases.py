from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.application.services.demo_retrieval_evaluation_cases import (
    DemoRetrievalEvaluationCaseDefinition,
    get_demo_retrieval_evaluation_case_definitions,
)
from app.domain.documents.enums import SourceSystem
from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.evaluation.entities import RetrievalEvaluationCase
from app.domain.evaluation.repositories import RetrievalEvaluationCaseRepository

DEFAULT_PROVIDER = "fake"
DEFAULT_MODEL_NAME = "fake-embedding-v1"
EVALUATION_CASE_LIST_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class SeedDemoEvaluationCasesOptions:
    dry_run: bool
    provider: str
    model_name: str


@dataclass(frozen=True, slots=True)
class EvaluationCaseSeedPlan:
    definition: DemoRetrievalEvaluationCaseDefinition
    expected_chunk_version_ids: tuple[UUID, ...]
    action: Literal["create", "skip", "conflict"]
    conflict_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SeedDemoEvaluationCasesSummary:
    total_definitions: int
    created_count: int
    skipped_count: int
    conflict_count: int
    missing_stable_section_keys: tuple[str, ...]
    plans: tuple[EvaluationCaseSeedPlan, ...]
    dry_run: bool
    provider: str
    model_name: str


def parse_args(argv: list[str] | None = None) -> SeedDemoEvaluationCasesOptions:
    parser = argparse.ArgumentParser(
        description=(
            "Seed retrieval evaluation cases for the deterministic demo dataset."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve expected chunks and print a summary without writing to the database.",
    )
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        help=(
            "Embedding provider used when resolving active vector index entries "
            f"(default: {DEFAULT_PROVIDER})."
        ),
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL_NAME,
        help=(
            "Embedding model name used when resolving active vector index entries "
            f"(default: {DEFAULT_MODEL_NAME})."
        ),
    )

    args = parser.parse_args(argv)

    return SeedDemoEvaluationCasesOptions(
        dry_run=args.dry_run,
        provider=args.provider,
        model_name=args.model_name,
    )


def collect_unique_stable_section_keys(
    definitions: tuple[DemoRetrievalEvaluationCaseDefinition, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered_keys: list[str] = []

    for definition in definitions:
        for stable_section_key in definition.expected_stable_section_keys:
            if stable_section_key not in seen:
                seen.add(stable_section_key)
                ordered_keys.append(stable_section_key)

    return tuple(ordered_keys)


def build_expected_chunk_version_ids(
    definition: DemoRetrievalEvaluationCaseDefinition,
    resolved_chunk_version_ids: dict[str, tuple[UUID, ...]],
) -> tuple[UUID, ...]:
    chunk_version_ids: list[UUID] = []

    for stable_section_key in definition.expected_stable_section_keys:
        chunk_version_ids.extend(resolved_chunk_version_ids[stable_section_key])

    return tuple(chunk_version_ids)


def find_missing_stable_section_keys(
    stable_section_keys: tuple[str, ...],
    resolved_chunk_version_ids: dict[str, tuple[UUID, ...]],
) -> tuple[str, ...]:
    return tuple(
        stable_section_key
        for stable_section_key in stable_section_keys
        if not resolved_chunk_version_ids.get(stable_section_key)
    )


def evaluation_cases_are_equivalent(
    *,
    existing: RetrievalEvaluationCase,
    query: str,
    tags: tuple[str, ...],
    expected_chunk_version_ids: tuple[UUID, ...],
) -> bool:
    return (
        existing.query == query
        and tuple(sorted(existing.tags)) == tuple(sorted(tags))
        and existing.expected_chunk_version_ids == expected_chunk_version_ids
    )


def plan_evaluation_case_seed(
    *,
    definition: DemoRetrievalEvaluationCaseDefinition,
    expected_chunk_version_ids: tuple[UUID, ...],
    existing_by_name: dict[str, RetrievalEvaluationCase],
    duplicate_names: set[str],
) -> EvaluationCaseSeedPlan:
    if definition.name in duplicate_names:
        return EvaluationCaseSeedPlan(
            definition=definition,
            expected_chunk_version_ids=expected_chunk_version_ids,
            action="conflict",
            conflict_reason=(
                f"Multiple evaluation cases named {definition.name!r} already exist"
            ),
        )

    existing = existing_by_name.get(definition.name)

    if existing is None:
        return EvaluationCaseSeedPlan(
            definition=definition,
            expected_chunk_version_ids=expected_chunk_version_ids,
            action="create",
        )

    if evaluation_cases_are_equivalent(
        existing=existing,
        query=definition.query,
        tags=definition.tags,
        expected_chunk_version_ids=expected_chunk_version_ids,
    ):
        return EvaluationCaseSeedPlan(
            definition=definition,
            expected_chunk_version_ids=expected_chunk_version_ids,
            action="skip",
        )

    return EvaluationCaseSeedPlan(
        definition=definition,
        expected_chunk_version_ids=expected_chunk_version_ids,
        action="conflict",
        conflict_reason=(
            f"Evaluation case named {definition.name!r} already exists with "
            "different query, tags, or expected chunk version IDs"
        ),
    )


def build_seed_plans(
    definitions: tuple[DemoRetrievalEvaluationCaseDefinition, ...],
    resolved_chunk_version_ids: dict[str, tuple[UUID, ...]],
    existing_by_name: dict[str, RetrievalEvaluationCase],
    duplicate_names: set[str],
) -> tuple[EvaluationCaseSeedPlan, ...]:
    return tuple(
        plan_evaluation_case_seed(
            definition=definition,
            expected_chunk_version_ids=build_expected_chunk_version_ids(
                definition,
                resolved_chunk_version_ids,
            ),
            existing_by_name=existing_by_name,
            duplicate_names=duplicate_names,
        )
        for definition in definitions
    )


def build_seed_summary(
    *,
    plans: tuple[EvaluationCaseSeedPlan, ...],
    missing_stable_section_keys: tuple[str, ...],
    options: SeedDemoEvaluationCasesOptions,
) -> SeedDemoEvaluationCasesSummary:
    created_count = sum(1 for plan in plans if plan.action == "create")
    skipped_count = sum(1 for plan in plans if plan.action == "skip")
    conflict_count = sum(1 for plan in plans if plan.action == "conflict")

    return SeedDemoEvaluationCasesSummary(
        total_definitions=len(plans),
        created_count=created_count,
        skipped_count=skipped_count,
        conflict_count=conflict_count,
        missing_stable_section_keys=missing_stable_section_keys,
        plans=plans,
        dry_run=options.dry_run,
        provider=options.provider,
        model_name=options.model_name,
    )


def load_evaluation_cases_by_name(
    repository: RetrievalEvaluationCaseRepository,
    *,
    names: set[str],
) -> tuple[dict[str, RetrievalEvaluationCase], set[str]]:
    if not names:
        return {}, set()

    existing_by_name: dict[str, RetrievalEvaluationCase] = {}
    duplicate_names: set[str] = set()
    offset = 0

    while True:
        batch = repository.list_recent(
            limit=EVALUATION_CASE_LIST_PAGE_SIZE,
            offset=offset,
            tag="retrieval-evaluation",
        )

        if not batch:
            break

        for evaluation_case in batch:
            if evaluation_case.name not in names:
                continue

            if evaluation_case.name in existing_by_name:
                duplicate_names.add(evaluation_case.name)
                continue

            existing_by_name[evaluation_case.name] = evaluation_case

        if len(batch) < EVALUATION_CASE_LIST_PAGE_SIZE:
            break

        offset += EVALUATION_CASE_LIST_PAGE_SIZE

    return existing_by_name, duplicate_names


def resolve_demo_chunk_version_ids(
    vector_index_entry_repository: VectorIndexEntryRepository,
    *,
    stable_section_keys: tuple[str, ...],
    provider: str,
    model_name: str,
) -> dict[str, tuple[UUID, ...]]:
    return vector_index_entry_repository.list_current_chunk_version_ids_by_stable_section_keys(
        stable_section_keys=stable_section_keys,
        source_system=SourceSystem.DEMO_DOCUMENTS,
        provider=provider,
        model_name=model_name,
    )


def print_missing_chunks_error(missing_stable_section_keys: tuple[str, ...]) -> None:
    print(
        "Error: Could not resolve expected demo chunks for the following "
        "stable section keys:",
        file=sys.stderr,
    )

    for stable_section_key in missing_stable_section_keys:
        print(f"- {stable_section_key}", file=sys.stderr)

    print(file=sys.stderr)
    print(
        "Index the demo dataset first, then rerun this command:",
        file=sys.stderr,
    )
    print("  python scripts/seed_demo_dataset.py", file=sys.stderr)


def print_conflict_errors(plans: tuple[EvaluationCaseSeedPlan, ...]) -> None:
    conflict_plans = [plan for plan in plans if plan.action == "conflict"]

    print("Error: Conflicting evaluation cases detected:", file=sys.stderr)

    for plan in conflict_plans:
        print(f"- {plan.definition.name}: {plan.conflict_reason}", file=sys.stderr)


def print_summary(summary: SeedDemoEvaluationCasesSummary) -> None:
    print("Demo retrieval evaluation case seeding")
    print(f"Provider: {summary.provider}")
    print(f"Model: {summary.model_name}")
    print()

    if summary.dry_run:
        print("Dry run only; no database writes were performed.")
        print()

    print(f"Total definitions: {summary.total_definitions}")
    print(f"Created: {summary.created_count}")
    print(f"Skipped (identical existing): {summary.skipped_count}")
    print(f"Conflicts: {summary.conflict_count}")

    if summary.missing_stable_section_keys:
        print()
        print("Missing stable section keys:")
        for stable_section_key in summary.missing_stable_section_keys:
            print(f"- {stable_section_key}")

    print()
    print("Cases:")

    for plan in summary.plans:
        action_label = {
            "create": "create",
            "skip": "skip (identical existing)",
            "conflict": "conflict",
        }[plan.action]
        expected_chunk_count = len(plan.expected_chunk_version_ids)

        print(
            f"- {plan.definition.name}: {action_label} "
            f"({expected_chunk_count} expected chunk(s))",
        )

    print()
    print(
        "Next: run retrieval evaluation through the API, for example "
        "POST /api/v1/evaluation/runs with provider "
        f"{summary.provider!r} and model_name {summary.model_name!r}.",
    )


def seed_demo_evaluation_cases(
    *,
    options: SeedDemoEvaluationCasesOptions,
    vector_index_entry_repository: VectorIndexEntryRepository,
    evaluation_case_repository: RetrievalEvaluationCaseRepository,
    commit: Callable[[], None],
) -> SeedDemoEvaluationCasesSummary:
    definitions = get_demo_retrieval_evaluation_case_definitions()
    stable_section_keys = collect_unique_stable_section_keys(definitions)

    resolved_chunk_version_ids = resolve_demo_chunk_version_ids(
        vector_index_entry_repository,
        stable_section_keys=stable_section_keys,
        provider=options.provider,
        model_name=options.model_name,
    )

    missing_stable_section_keys = find_missing_stable_section_keys(
        stable_section_keys,
        resolved_chunk_version_ids,
    )

    if missing_stable_section_keys:
        summary = SeedDemoEvaluationCasesSummary(
            total_definitions=len(definitions),
            created_count=0,
            skipped_count=0,
            conflict_count=0,
            missing_stable_section_keys=missing_stable_section_keys,
            plans=(),
            dry_run=options.dry_run,
            provider=options.provider,
            model_name=options.model_name,
        )
        print_missing_chunks_error(missing_stable_section_keys)
        return summary

    definition_names = {definition.name for definition in definitions}
    existing_by_name, duplicate_names = load_evaluation_cases_by_name(
        evaluation_case_repository,
        names=definition_names,
    )

    plans = build_seed_plans(
        definitions,
        resolved_chunk_version_ids,
        existing_by_name,
        duplicate_names,
    )

    summary = build_seed_summary(
        plans=plans,
        missing_stable_section_keys=missing_stable_section_keys,
        options=options,
    )

    if summary.conflict_count > 0:
        print_conflict_errors(plans)
        return summary

    if not options.dry_run:
        for plan in plans:
            if plan.action != "create":
                continue

            evaluation_case = RetrievalEvaluationCase.create(
                name=plan.definition.name,
                query=plan.definition.query,
                expected_chunk_version_ids=plan.expected_chunk_version_ids,
                tags=plan.definition.tags,
            )
            evaluation_case_repository.save(evaluation_case)

        commit()

    return summary


def run(options: SeedDemoEvaluationCasesOptions) -> int:
    try:
        from app.infrastructure.db.session import SessionLocal
        from app.infrastructure.repositories import (
            SqlAlchemyRetrievalEvaluationCaseRepository,
            SqlAlchemyVectorIndexEntryRepository,
        )

        with SessionLocal() as session:
            vector_index_entry_repository = SqlAlchemyVectorIndexEntryRepository(
                session,
            )
            evaluation_case_repository = SqlAlchemyRetrievalEvaluationCaseRepository(
                session,
            )

            summary = seed_demo_evaluation_cases(
                options=options,
                vector_index_entry_repository=vector_index_entry_repository,
                evaluation_case_repository=evaluation_case_repository,
                commit=session.commit,
            )

        print_summary(summary)

        if summary.missing_stable_section_keys or summary.conflict_count > 0:
            return 1

        return 0

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def main() -> None:
    sys.exit(run(parse_args()))


if __name__ == "__main__":
    main()
