from dataclasses import dataclass

from app.domain.answering.entities import GroundedAnswerCitation
from app.domain.retrieval.entities import RetrievedChunk


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


class ProvenanceValidationError(Exception):
    def __init__(self, message: str) -> None:
        ensure_not_blank(message, "message")
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ProposedCitation:
    candidate_id: str
    evidence_span: str

    def __post_init__(self) -> None:
        ensure_not_blank(self.candidate_id, "candidate_id")


@dataclass(frozen=True, slots=True)
class GeneratedAnswerDraft:
    answer: str
    citations: tuple[ProposedCitation, ...]

    def __post_init__(self) -> None:
        ensure_not_blank(self.answer, "answer")


@dataclass(frozen=True, slots=True)
class _SnapshotCandidate:
    rank: int
    chunk: RetrievedChunk


class ProvenanceValidator:
    """Deterministically validate model-proposed provenance against a retrieval snapshot.

    Verifies that each proposed citation references a candidate present in the
    immutable retrieval snapshot used for generation and that the evidence span
    occurs verbatim in that candidate's stored text.

    Does not prove semantic entailment or factual correctness.
    """

    def validate(
        self,
        *,
        draft: GeneratedAnswerDraft,
        retrieval_snapshot: tuple[RetrievedChunk, ...],
    ) -> tuple[GroundedAnswerCitation, ...]:
        if not draft.citations:
            raise ProvenanceValidationError(
                "provenance validation failed: proposed citations must not be empty",
            )

        snapshot_by_candidate_id = {
            str(chunk.chunk_version_id): _SnapshotCandidate(rank=rank, chunk=chunk)
            for rank, chunk in enumerate(retrieval_snapshot, start=1)
        }

        validated: list[GroundedAnswerCitation] = []

        for index, proposed in enumerate(draft.citations, start=1):
            snapshot_candidate = snapshot_by_candidate_id.get(proposed.candidate_id)

            if snapshot_candidate is None:
                raise ProvenanceValidationError(
                    "provenance validation failed: candidate_id "
                    f"{proposed.candidate_id!r} is not present in the retrieval "
                    "snapshot used for generation",
                )

            evidence_span = proposed.evidence_span.strip()

            if not evidence_span:
                raise ProvenanceValidationError(
                    "provenance validation failed: evidence_span must not be empty "
                    f"(citation {index})",
                )

            if evidence_span not in snapshot_candidate.chunk.content:
                raise ProvenanceValidationError(
                    "provenance validation failed: evidence_span is not a verbatim "
                    f"substring of the referenced candidate (citation {index})",
                )

            chunk = snapshot_candidate.chunk

            validated.append(
                GroundedAnswerCitation(
                    rank=snapshot_candidate.rank,
                    vector_index_entry_id=chunk.vector_index_entry_id,
                    source_document_id=chunk.source_document_id,
                    document_version_id=chunk.document_version_id,
                    section_version_id=chunk.section_version_id,
                    chunk_version_id=chunk.chunk_version_id,
                    embedding_record_id=chunk.embedding_record_id,
                    stable_section_key=chunk.stable_section_key,
                    chunk_index=chunk.chunk_index,
                    heading_context=chunk.heading_context,
                    quote=evidence_span,
                    distance=chunk.distance,
                ),
            )

        return tuple(validated)
