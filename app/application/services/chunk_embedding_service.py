from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.markdown_chunking_service import (
    calculate_embedding_input_hash,
)
from app.application.transactions.document_ingestion import (
    DocumentIngestionTransaction,
)
from app.domain.documents.entities import (
    ChunkEmbeddingLink,
    ChunkVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
)
from app.providers.embeddings import EmbeddingProvider


@dataclass(frozen=True, slots=True)
class EmbeddingGenerationSummary:
    embeddings_created: int
    embeddings_reused: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int


def build_embedding_input(chunk: ChunkVersion) -> str:
    return "\n".join([*chunk.heading_context, chunk.content])


class ChunkEmbeddingService:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    def ensure_embeddings_for_chunks(
        self,
        *,
        chunks: list[ChunkVersion],
        ingestion_run_id: UUID,
        transaction: DocumentIngestionTransaction,
    ) -> EmbeddingGenerationSummary:
        embedding_records_to_create: list[EmbeddingRecord] = []
        links_to_create: list[ChunkEmbeddingLink] = []
        cost_records_to_create: list[EmbeddingCostRecord] = []

        embeddings_created = 0
        embeddings_reused = 0
        embedding_tokens_processed = 0
        estimated_embedding_cost_usd_micros = 0

        for chunk in chunks:
            existing_link = transaction.chunk_embedding_links.get_by_chunk_version_id(
                chunk.id,
            )

            if existing_link is not None:
                continue

            existing_embedding = (
                transaction.embedding_records.get_by_embedding_identity(
                    provider=self._provider.provider,
                    model_name=self._provider.model_name,
                    embedding_input_hash=chunk.embedding_input_hash,
                )
            )

            if existing_embedding is not None:
                links_to_create.append(
                    ChunkEmbeddingLink(
                        id=uuid4(),
                        chunk_version_id=chunk.id,
                        embedding_record_id=existing_embedding.id,
                    )
                )
                embeddings_reused += 1
                continue

            embedding_input = build_embedding_input(chunk)
            calculated_input_hash = calculate_embedding_input_hash(
                heading_context=chunk.heading_context,
                content=chunk.content,
            )

            if calculated_input_hash != chunk.embedding_input_hash:
                raise ValueError("chunk embedding_input_hash does not match input text")

            embedding_response = self._provider.embed(embedding_input)
            embedding_vector = tuple(embedding_response.embedding_vector)

            embedding_record = EmbeddingRecord(
                id=uuid4(),
                chunk_version_id=chunk.id,
                provider=self._provider.provider,
                model_name=self._provider.model_name,
                embedding_input_hash=chunk.embedding_input_hash,
                embedding_vector=embedding_vector,
                dimensions=len(embedding_vector),
                input_token_estimate=chunk.token_estimate,
            )

            embedding_records_to_create.append(embedding_record)
            links_to_create.append(
                ChunkEmbeddingLink(
                    id=uuid4(),
                    chunk_version_id=chunk.id,
                    embedding_record_id=embedding_record.id,
                )
            )

            cost_record = EmbeddingCostRecord(
                id=uuid4(),
                ingestion_run_id=ingestion_run_id,
                embedding_record_id=embedding_record.id,
                provider=self._provider.provider,
                model_name=self._provider.model_name,
                input_token_estimate=chunk.token_estimate,
                estimated_cost_usd_micros=0,
            )
            cost_records_to_create.append(cost_record)

            embeddings_created += 1
            embedding_tokens_processed += chunk.token_estimate

        if embedding_records_to_create:
            transaction.embedding_records.save_many(embedding_records_to_create)
            transaction.flush()

        if links_to_create:
            transaction.chunk_embedding_links.save_many(links_to_create)
            transaction.flush()

        if cost_records_to_create:
            transaction.embedding_cost_records.save_many(cost_records_to_create)
            transaction.flush()

        return EmbeddingGenerationSummary(
            embeddings_created=embeddings_created,
            embeddings_reused=embeddings_reused,
            embedding_tokens_processed=embedding_tokens_processed,
            estimated_embedding_cost_usd_micros=estimated_embedding_cost_usd_micros,
        )