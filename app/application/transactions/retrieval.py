from typing import Protocol

from app.domain.documents.repositories import VectorIndexEntryRepository


class RetrievalTransaction(Protocol):
    vector_index_entries: VectorIndexEntryRepository