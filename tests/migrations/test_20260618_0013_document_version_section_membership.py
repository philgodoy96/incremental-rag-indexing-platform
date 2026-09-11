from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "20260618_0013_document_version_section_membership.py"
)


def _load_migration_module() -> ModuleType:
    spec = spec_from_file_location(
        "migration_20260618_0013_document_version_section_membership",
        MIGRATION_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_section_membership_migration_downgrade_is_irreversible() -> None:
    migration = _load_migration_module()

    with pytest.raises(RuntimeError, match="irreversible") as raised:
        migration.downgrade()

    message = str(raised.value)
    assert "document_version_sections" in message
    assert "backup/restore" in message or "roll-forward" in message
    assert message == migration.IRREVERSIBLE_DOWNGRADE_MESSAGE


def test_section_membership_migration_downgrade_does_not_mutate_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _load_migration_module()
    mutation_calls: list[str] = []

    def record_mutation(name: str) -> Callable[..., Any]:
        def _recorder(*args: object, **kwargs: object) -> None:
            mutation_calls.append(name)
            raise AssertionError(f"unexpected migration mutation: {name}")

        return _recorder

    monkeypatch.setattr(migration.op, "add_column", record_mutation("add_column"))
    monkeypatch.setattr(migration.op, "execute", record_mutation("execute"))
    monkeypatch.setattr(migration.op, "alter_column", record_mutation("alter_column"))
    monkeypatch.setattr(migration.op, "drop_table", record_mutation("drop_table"))
    monkeypatch.setattr(migration.op, "drop_index", record_mutation("drop_index"))
    monkeypatch.setattr(
        migration.op,
        "create_foreign_key",
        record_mutation("create_foreign_key"),
    )
    monkeypatch.setattr(
        migration.op,
        "create_unique_constraint",
        record_mutation("create_unique_constraint"),
    )
    monkeypatch.setattr(migration.op, "create_index", record_mutation("create_index"))

    with pytest.raises(RuntimeError, match="irreversible"):
        migration.downgrade()

    assert mutation_calls == []
