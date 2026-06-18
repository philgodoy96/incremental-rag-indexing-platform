import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_seed_demo_dataset_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "seed_demo_dataset.py"
    module_name = "seed_demo_dataset"
    spec = importlib.util.spec_from_file_location(module_name, module_path)

    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load seed_demo_dataset module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_args_defaults_to_repo_manifest() -> None:
    module = _load_seed_demo_dataset_module()

    options = module.parse_args([])

    assert options.manifest_path == module.DEFAULT_MANIFEST_PATH.resolve()
    assert options.dry_run is False


def test_parse_args_accepts_manifest_path_and_dry_run() -> None:
    module = _load_seed_demo_dataset_module()
    manifest_path = REPO_ROOT / "demo" / "documents" / "manifest.json"

    options = module.parse_args(
        ["--manifest-path", str(manifest_path), "--dry-run"],
    )

    assert options.manifest_path == manifest_path.resolve()
    assert options.dry_run is True


def test_dry_run_discovers_demo_documents_without_database_writes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_seed_demo_dataset_module()

    exit_code = module.run(
        module.SeedDemoDatasetOptions(
            manifest_path=module.DEFAULT_MANIFEST_PATH,
            dry_run=True,
        ),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Dry run only" in captured.out
    assert "Discovered documents: 4" in captured.out
    assert "Project Atlas Brief" in captured.out
