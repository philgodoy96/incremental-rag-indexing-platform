from pathlib import Path

from app.infrastructure.sources.local_markdown_source import (
    LocalMarkdownSource,
    extract_markdown_title,
)


def test_local_markdown_source_discovers_markdown_files(tmp_path: Path) -> None:
    (tmp_path / "project-atlas-status.md").write_text(
        "# Project Atlas Status\n\nStatus: On Track\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text(
        "This should not be discovered.",
        encoding="utf-8",
    )

    source = LocalMarkdownSource(base_path=tmp_path)

    candidates = source.discover()

    assert len(candidates) == 1
    assert candidates[0].external_id == "project-atlas-status.md"
    assert candidates[0].source_uri == "seed_documents/project-atlas-status.md"
    assert candidates[0].title == "Project Atlas Status"


def test_local_markdown_source_discovers_nested_markdown_files(tmp_path: Path) -> None:
    nested_dir = tmp_path / "runbooks"
    nested_dir.mkdir()

    (nested_dir / "redis-queue-backlog-runbook.md").write_text(
        "# Redis Queue Backlog Runbook\n\nCheck queue depth first.\n",
        encoding="utf-8",
    )

    source = LocalMarkdownSource(base_path=tmp_path)

    candidates = source.discover()

    assert len(candidates) == 1
    assert candidates[0].external_id == "runbooks/redis-queue-backlog-runbook.md"
    assert (
        candidates[0].source_uri
        == "seed_documents/runbooks/redis-queue-backlog-runbook.md"
    )


def test_local_markdown_source_ignores_empty_markdown_files(tmp_path: Path) -> None:
    (tmp_path / "empty.md").write_text("   \n", encoding="utf-8")

    source = LocalMarkdownSource(base_path=tmp_path)

    assert source.discover() == []


def test_local_markdown_source_returns_empty_list_when_directory_does_not_exist(
    tmp_path: Path,
) -> None:
    source = LocalMarkdownSource(base_path=tmp_path / "missing")

    assert source.discover() == []


def test_extract_markdown_title_uses_first_h1() -> None:
    content = "Intro\n\n## Not H1\n\n# Actual Title\n\nBody."

    assert extract_markdown_title(content, fallback="fallback-title") == "Actual Title"


def test_extract_markdown_title_falls_back_to_file_stem() -> None:
    content = "No heading here."

    assert (
        extract_markdown_title(content, fallback="redis-queue-backlog-runbook")
        == "Redis Queue Backlog Runbook"
    )