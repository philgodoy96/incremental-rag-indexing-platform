from typing import Protocol

from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.retrieval.repositories import (
    QueryTraceHitRepository,
    QueryTraceRepository,
)


class RetrievalTransaction(Protocol):
    vector_index_entries: VectorIndexEntryRepository
    query_traces: QueryTraceRepository
    query_trace_hits: QueryTraceHitRepository

    def flush(self) -> None:
        raise NotImplementedError

    def commit(self) -> None:
        raise NotImplementedError
