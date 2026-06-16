from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.markdown_chunking_service import (
    calculate_embedding_input_hash,
)
from app.application.transactions import DocumentIngestionTransaction
from app.domain.documents.entities import (
    ChunkVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
)
from app.providers import EmbeddingProvider, FakeEmbeddingProvider


@dataclass(frozen=True, slots=True)
class EmbeddingGenerationSummary:
    embeddings_created: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int


class ChunkEmbeddingService:
    """Ensures ChunkVersions have persisted embedding records."""

    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self._provider = provider or FakeEmbeddingProvider()

    def ensure_embeddings_for_chunks(
        self,
        *,
        chunks: list[ChunkVersion],
        ingestion_run_id: UUID,
        transaction: DocumentIngestionTransaction,
    ) -> EmbeddingGenerationSummary:
        embedding_records: list[EmbeddingRecord] = []
        cost_records: list[EmbeddingCostRecord] = []

        for chunk in chunks:
            existing_embedding = transaction.embedding_records.get_by_chunk_identity(
                chunk_version_id=chunk.id,
                provider=self._provider.provider,
                model_name=self._provider.model_name,
                embedding_input_hash=chunk.embedding_input_hash,
            )

            if existing_embedding is not None:
                continue

            embedding_input = build_embedding_input(chunk)

            expected_hash = calculate_embedding_input_hash(
                heading_context=chunk.heading_context,
                content=chunk.content,
            )

            if expected_hash != chunk.embedding_input_hash:
                raise ValueError("chunk embedding_input_hash does not match input")

            provider_response = self._provider.embed(embedding_input)

            embedding_record = EmbeddingRecord(
                id=uuid4(),
                chunk_version_id=chunk.id,
                provider=provider_response.provider,
                model_name=provider_response.model_name,
                embedding_input_hash=chunk.embedding_input_hash,
                embedding_vector=provider_response.embedding_vector,
                dimensions=provider_response.dimensions,
                input_token_estimate=chunk.token_estimate,
            )
            embedding_records.append(embedding_record)

            cost_records.append(
                EmbeddingCostRecord(
                    id=uuid4(),
                    ingestion_run_id=ingestion_run_id,
                    embedding_record_id=embedding_record.id,
                    provider=provider_response.provider,
                    model_name=provider_response.model_name,
                    input_token_estimate=chunk.token_estimate,
                    estimated_cost_usd_micros=estimate_embedding_cost_usd_micros(
                        provider=provider_response.provider,
                        model_name=provider_response.model_name,
                        input_token_estimate=chunk.token_estimate,
                    ),
                )
            )

        if not embedding_records:
            return EmbeddingGenerationSummary(
                embeddings_created=0,
                embedding_tokens_processed=0,
                estimated_embedding_cost_usd_micros=0,
            )

        transaction.embedding_records.save_many(embedding_records)
        transaction.flush()

        transaction.embedding_cost_records.save_many(cost_records)
        transaction.flush()

        return EmbeddingGenerationSummary(
            embeddings_created=len(embedding_records),
            embedding_tokens_processed=sum(
                record.input_token_estimate for record in embedding_records
            ),
            estimated_embedding_cost_usd_micros=sum(
                record.estimated_cost_usd_micros for record in cost_records
            ),
        )


def build_embedding_input(chunk: ChunkVersion) -> str:
    return "\n".join([*chunk.heading_context, chunk.content])


def estimate_embedding_cost_usd_micros(
    *,
    provider: str,
    model_name: str,
    input_token_estimate: int,
) -> int:
    if provider == "fake" and model_name == "fake-embedding-v1":
        return 0

    return input_token_estimate * 0