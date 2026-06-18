from pathlib import Path

from app.application.services.demo_dataset_loader import DemoDatasetLoader

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    dataset = DemoDatasetLoader(repo_root=REPO_ROOT).load()

    print(f"Dataset: {dataset.name}")
    print(f"Version: {dataset.version}")
    print(f"Documents: {len(dataset.documents)}")
    print()

    for document in dataset.documents:
        relative_path = document.file_path.relative_to(REPO_ROOT)

        print(f"- {document.title}")
        print(f"  external_id: {document.external_id}")
        print(f"  source_uri: {document.source_uri}")
        print(f"  file_path: {relative_path}")
        print(f"  tags: {', '.join(document.tags)}")
        print(f"  checksum: {document.content_checksum}")
        print()


if __name__ == "__main__":
    main()
