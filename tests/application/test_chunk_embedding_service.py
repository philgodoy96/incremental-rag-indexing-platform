from uuid import UUID, uuid4

from app.application.services.chunk_embedding_service import (
    ChunkEmbeddingService,
    build_embedding_input,
)
from app.domain.documents.entities import (
    ChunkEmbeddingLink,
    ChunkVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
)
from app.domain.documents.repositories import (
    ChunkEmbeddingLinkRepository,
    EmbeddingCostRecordRepository,
    EmbeddingRecordRepository,
)
from app.providers.fake_embedding_provider import FakeEmbeddingProvider


class InMemoryEmbeddingRecordRepository(EmbeddingRecordRepository):
    def __init__(self) -> None:
        self.embedding_records: dict[UUID, EmbeddingRecord] = {}

    def get_by_chunk_identity(
        self,
        *,
        chunk_version_id: UUID,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        for record in self.embedding_records.values():
            if (
                record.chunk_version_id == chunk_version_id
                and record.provider == provider
                and record.model_name == model_name
                and record.embedding_input_hash == embedding_input_hash
            ):
                return record

        return None
    
    def get_by_embedding_identity(
        self,
        *,
        provider: str,
        model_name: str,
        embedding_input_hash: str,
    ) -> EmbeddingRecord | None:
        for record in self.embedding_records.values():
            if (
                record.provider == provider
                and record.model_name == model_name
                and record.embedding_input_hash == embedding_input_hash
            ):
                return record

        return None

    def save_many(self, embedding_records: list[EmbeddingRecord]) -> None:
        for embedding_record in embedding_records:
            self.embedding_records[embedding_record.id] = embedding_record


class InMemoryChunkEmbeddingLinkRepository(ChunkEmbeddingLinkRepository):
    def __init__(self) -> None:
        self.links: dict[UUID, ChunkEmbeddingLink] = {}

    def get_by_chunk_version_id(
        self,
        chunk_version_id: UUID,
    ) -> ChunkEmbeddingLink | None:
        for link in self.links.values():
            if link.chunk_version_id == chunk_version_id:
                return link

        return None

    def save_many(self, links: list[ChunkEmbeddingLink]) -> None:
        for link in links:
            self.links[link.id] = link


class InMemoryEmbeddingCostRecordRepository(EmbeddingCostRecordRepository):
    def __init__(self) -> None:
        self.cost_records: dict[UUID, EmbeddingCostRecord] = {}

    def save_many(self, cost_records: list[EmbeddingCostRecord]) -> None:
        for cost_record in cost_records:
            self.cost_records[cost_record.id] = cost_record


class InMemoryEmbeddingTransaction:
    def __init__(self) -> None:
        self.embedding_records = InMemoryEmbeddingRecordRepository()
        self.chunk_embedding_links = InMemoryChunkEmbeddingLinkRepository()
        self.embedding_cost_records = InMemoryEmbeddingCostRecordRepository()
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1


def make_chunk() -> ChunkVersion:
    return ChunkVersion(
        id=uuid4(),
        section_version_id=uuid4(),
        chunk_index=0,
        content="Status: At Risk",
        heading_context=("Project Atlas Status", "Summary"),
        chunk_hash="chunk-hash",
        embedding_input_hash=(
        "78b6875f599bddc580263ca6ee1bc06a707c5d6fb50c6198e720940238d85e02"
    ),
        token_estimate=3,
    )


def test_build_embedding_input_includes_heading_context() -> None:
    chunk = make_chunk()

    assert build_embedding_input(chunk) == (
        "Project Atlas Status\nSummary\nStatus: At Risk"
    )


def test_chunk_embedding_service_creates_embedding_and_cost_record() -> None:
    chunk = make_chunk()
    transaction = InMemoryEmbeddingTransaction()
    service = ChunkEmbeddingService(provider=FakeEmbeddingProvider())

    summary = service.ensure_embeddings_for_chunks(
        chunks=[chunk],
        ingestion_run_id=uuid4(),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert summary.embeddings_created == 1
    assert summary.embeddings_reused == 0
    assert summary.embedding_tokens_processed == 3
    assert summary.estimated_embedding_cost_usd_micros == 0
    assert len(transaction.embedding_records.embedding_records) == 1
    assert len(transaction.chunk_embedding_links.links) == 1
    assert len(transaction.embedding_cost_records.cost_records) == 1


def test_chunk_embedding_service_is_idempotent_for_existing_embedding() -> None:
    chunk = make_chunk()
    transaction = InMemoryEmbeddingTransaction()
    service = ChunkEmbeddingService(provider=FakeEmbeddingProvider())

    service.ensure_embeddings_for_chunks(
        chunks=[chunk],
        ingestion_run_id=uuid4(),
        transaction=transaction,  # type: ignore[arg-type]
    )
    second_summary = service.ensure_embeddings_for_chunks(
        chunks=[chunk],
        ingestion_run_id=uuid4(),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert second_summary.embeddings_created == 0
    assert second_summary.embeddings_reused == 0
    assert second_summary.embedding_tokens_processed == 0
    assert len(transaction.embedding_records.embedding_records) == 1
    assert len(transaction.chunk_embedding_links.links) == 1
    assert len(transaction.embedding_cost_records.cost_records) == 1