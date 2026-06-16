from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.transactions.document_ingestion import (
    DocumentIngestionTransaction,
)
from app.domain.documents.entities import (
    ChunkVersion,
    DocumentVersion,
    SectionVersion,
    SourceDocument,
    VectorIndexEntry,
)


@dataclass(frozen=True, slots=True)
class VectorIndexingSummary:
    vector_entries_created: int
    vector_entries_updated: int
    vector_entries_deactivated: int


@dataclass(frozen=True, slots=True)
class SectionChunks:
    section: SectionVersion
    chunks: list[ChunkVersion]


class VectorIndexingService:
    def ensure_current_index_for_document(
        self,
        *,
        source_document: SourceDocument,
        document_version: DocumentVersion,
        section_chunks: list[SectionChunks],
        transaction: DocumentIngestionTransaction,
    ) -> VectorIndexingSummary:
        vector_entries_created = 0
        vector_entries_updated = 0
        touched_logical_keys: set[tuple[str, int, str, str]] = set()

        for section_chunk_group in section_chunks:
            section = section_chunk_group.section

            for chunk in section_chunk_group.chunks:
                link = transaction.chunk_embedding_links.get_by_chunk_version_id(
                    chunk.id,
                )

                if link is None:
                    raise ValueError("chunk embedding link is required before indexing")

                embedding_record = transaction.embedding_records.get_by_id(
                    link.embedding_record_id,
                )

                if embedding_record is None:
                    raise ValueError("embedding record not found for chunk link")

                logical_key = (
                    section.stable_section_key,
                    chunk.chunk_index,
                    embedding_record.provider,
                    embedding_record.model_name,
                )
                touched_logical_keys.add(logical_key)

                existing_entry = (
                    transaction.vector_index_entries.get_by_logical_identity(
                        source_document_id=source_document.id,
                        stable_section_key=section.stable_section_key,
                        chunk_index=chunk.chunk_index,
                        provider=embedding_record.provider,
                        model_name=embedding_record.model_name,
                    )
                )

                if existing_entry is None:
                    transaction.vector_index_entries.save(
                        VectorIndexEntry(
                            id=uuid4(),
                            source_document_id=source_document.id,
                            document_version_id=document_version.id,
                            section_version_id=section.id,
                            chunk_version_id=chunk.id,
                            embedding_record_id=embedding_record.id,
                            stable_section_key=section.stable_section_key,
                            chunk_index=chunk.chunk_index,
                            provider=embedding_record.provider,
                            model_name=embedding_record.model_name,
                            embedding_input_hash=embedding_record.embedding_input_hash,
                            content=chunk.content,
                            heading_context=chunk.heading_context,
                            embedding_vector=embedding_record.embedding_vector,
                            dimensions=embedding_record.dimensions,
                        )
                    )
                    vector_entries_created += 1
                    continue

                if self._entry_matches_current_projection(
                    entry=existing_entry,
                    document_version=document_version,
                    section=section,
                    chunk=chunk,
                    embedding_record_id=embedding_record.id,
                    embedding_input_hash=embedding_record.embedding_input_hash,
                    embedding_vector=embedding_record.embedding_vector,
                    dimensions=embedding_record.dimensions,
                ):
                    continue

                existing_entry.update_current_projection(
                    document_version_id=document_version.id,
                    section_version_id=section.id,
                    chunk_version_id=chunk.id,
                    embedding_record_id=embedding_record.id,
                    embedding_input_hash=embedding_record.embedding_input_hash,
                    content=chunk.content,
                    heading_context=chunk.heading_context,
                    embedding_vector=embedding_record.embedding_vector,
                    dimensions=embedding_record.dimensions,
                )
                transaction.vector_index_entries.save(existing_entry)
                vector_entries_updated += 1

        vector_entries_deactivated = self._deactivate_stale_entries(
            source_document=source_document,
            touched_logical_keys=touched_logical_keys,
            transaction=transaction,
        )

        transaction.flush()

        return VectorIndexingSummary(
            vector_entries_created=vector_entries_created,
            vector_entries_updated=vector_entries_updated,
            vector_entries_deactivated=vector_entries_deactivated,
        )

    def _deactivate_stale_entries(
        self,
        *,
        source_document: SourceDocument,
        touched_logical_keys: set[tuple[str, int, str, str]],
        transaction: DocumentIngestionTransaction,
    ) -> int:
        active_entries = transaction.vector_index_entries.list_active_for_source_document(
            source_document.id,
        )

        deactivated_count = 0

        for entry in active_entries:
            logical_key = (
                entry.stable_section_key,
                entry.chunk_index,
                entry.provider,
                entry.model_name,
            )

            if logical_key in touched_logical_keys:
                continue

            entry.deactivate()
            transaction.vector_index_entries.save(entry)
            deactivated_count += 1

        return deactivated_count

    def _entry_matches_current_projection(
        self,
        *,
        entry: VectorIndexEntry,
        document_version: DocumentVersion,
        section: SectionVersion,
        chunk: ChunkVersion,
        embedding_record_id: UUID,
        embedding_input_hash: str,
        embedding_vector: tuple[float, ...],
        dimensions: int,
    ) -> bool:
        return (
            entry.is_active
            and entry.document_version_id == document_version.id
            and entry.section_version_id == section.id
            and entry.chunk_version_id == chunk.id
            and entry.embedding_record_id == embedding_record_id
            and entry.embedding_input_hash == embedding_input_hash
            and entry.content == chunk.content
            and entry.heading_context == chunk.heading_context
            and entry.embedding_vector == embedding_vector
            and entry.dimensions == dimensions
        )