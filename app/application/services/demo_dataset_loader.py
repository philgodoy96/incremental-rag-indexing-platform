import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DemoDocumentSpec:
    external_id: str
    title: str
    file_path: Path
    source_uri: str
    tags: tuple[str, ...]
    content: str
    content_checksum: str


@dataclass(frozen=True, slots=True)
class DemoDataset:
    name: str
    version: str
    manifest_path: Path
    documents: tuple[DemoDocumentSpec, ...]


class DemoDatasetLoader:
    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        manifest_path: Path | None = None,
    ) -> None:
        self._repo_root = (repo_root or Path.cwd()).resolve()
        self._manifest_path = (
            manifest_path
            or self._repo_root / "demo" / "documents" / "manifest.json"
        ).resolve()

    def load(self) -> DemoDataset:
        manifest = self._load_manifest()

        dataset_name = self._required_string(manifest, "dataset_name")
        dataset_version = self._required_string(manifest, "dataset_version")
        documents_data = manifest.get("documents")

        if not isinstance(documents_data, list) or not documents_data:
            raise ValueError("manifest documents must be a non-empty list")

        documents = tuple(
            self._load_document(document_data)
            for document_data in documents_data
        )

        self._ensure_unique(
            [document.external_id for document in documents],
            "external_id",
        )
        self._ensure_unique(
            [document.source_uri for document in documents],
            "source_uri",
        )
        self._ensure_unique(
            [str(document.file_path) for document in documents],
            "file_path",
        )

        return DemoDataset(
            name=dataset_name,
            version=dataset_version,
            manifest_path=self._manifest_path,
            documents=documents,
        )

    def _load_manifest(self) -> dict[str, Any]:
        if not self._manifest_path.exists():
            raise FileNotFoundError(f"manifest not found: {self._manifest_path}")

        raw_manifest = self._manifest_path.read_text(encoding="utf-8")

        try:
            manifest = json.loads(raw_manifest)
        except json.JSONDecodeError as error:
            raise ValueError("manifest must be valid JSON") from error

        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")

        return manifest

    def _load_document(self, document_data: object) -> DemoDocumentSpec:
        if not isinstance(document_data, dict):
            raise ValueError("manifest document entry must be an object")

        external_id = self._required_string(document_data, "external_id")
        title = self._required_string(document_data, "title")
        raw_file_path = self._required_string(document_data, "file_path")
        source_uri = self._required_string(document_data, "source_uri")
        tags = self._required_string_list(document_data, "tags")

        file_path = (self._repo_root / raw_file_path).resolve()

        if not self._is_relative_to(file_path, self._repo_root):
            raise ValueError(f"document file_path escapes repo root: {raw_file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"demo document not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            raise ValueError(f"demo document must not be empty: {file_path}")

        return DemoDocumentSpec(
            external_id=external_id,
            title=title,
            file_path=file_path,
            source_uri=source_uri,
            tags=tuple(tags),
            content=content,
            content_checksum=self._sha256(content),
        )

    def _required_string(
        self,
        data: dict[str, Any],
        field_name: str,
    ) -> str:
        value = data.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

        return value

    def _required_string_list(
        self,
        data: dict[str, Any],
        field_name: str,
    ) -> list[str]:
        value = data.get(field_name)

        if not isinstance(value, list) or not value:
            raise ValueError(f"{field_name} must be a non-empty list")

        values = []

        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{field_name} items must be non-empty strings")

            values.append(item)

        return values

    def _ensure_unique(self, values: list[str], field_name: str) -> None:
        duplicated_values = {
            value
            for value in values
            if values.count(value) > 1
        }

        if duplicated_values:
            formatted_values = ", ".join(sorted(duplicated_values))
            raise ValueError(
                f"{field_name} values must be unique: {formatted_values}",
            )

    def _is_relative_to(self, path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False

        return True

    def _sha256(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()