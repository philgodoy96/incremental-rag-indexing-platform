from uuid import UUID, uuid4

import pytest

from app.domain.answering.provenance import (
    GeneratedAnswerDraft,
    ProposedCitation,
    ProvenanceValidationError,
    ProvenanceValidator,
)
from app.domain.retrieval.entities import RetrievedChunk


def make_retrieved_chunk(
    *,
    content: str = "Status: At Risk. Owner: Platform Team.",
    distance: float = 0.12,
    chunk_version_id: UUID | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        vector_index_entry_id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=chunk_version_id or uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        content=content,
        heading_context=("Project Atlas Status", "Summary"),
        distance=distance,
    )


def test_provenance_validator_accepts_valid_candidate_and_verbatim_span() -> None:
    chunk = make_retrieved_chunk()
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(
            ProposedCitation(
                candidate_id=str(chunk.chunk_version_id),
                evidence_span="Status: At Risk",
            ),
        ),
    )

    citations = ProvenanceValidator().validate(
        draft=draft,
        retrieval_snapshot=(chunk,),
    )

    assert len(citations) == 1
    assert citations[0].chunk_version_id == chunk.chunk_version_id
    assert citations[0].quote == "Status: At Risk"
    assert citations[0].document_version_id == chunk.document_version_id
    assert citations[0].rank == 1


def test_provenance_validator_rejects_candidate_outside_retrieval_snapshot() -> None:
    snapshot_chunk = make_retrieved_chunk()
    outside_chunk = make_retrieved_chunk(content="Status: At Risk")

    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(
            ProposedCitation(
                candidate_id=str(outside_chunk.chunk_version_id),
                evidence_span="Status: At Risk",
            ),
        ),
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="not present in the retrieval snapshot",
    ):
        ProvenanceValidator().validate(
            draft=draft,
            retrieval_snapshot=(snapshot_chunk,),
        )


def test_provenance_validator_rejects_fabricated_evidence_span() -> None:
    chunk = make_retrieved_chunk()
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(
            ProposedCitation(
                candidate_id=str(chunk.chunk_version_id),
                evidence_span="Status: Completely Fabricated",
            ),
        ),
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="not a verbatim substring",
    ):
        ProvenanceValidator().validate(
            draft=draft,
            retrieval_snapshot=(chunk,),
        )


def test_provenance_validator_rejects_empty_evidence_span() -> None:
    chunk = make_retrieved_chunk()
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(
            ProposedCitation(
                candidate_id=str(chunk.chunk_version_id),
                evidence_span="   ",
            ),
        ),
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="evidence_span must not be empty",
    ):
        ProvenanceValidator().validate(
            draft=draft,
            retrieval_snapshot=(chunk,),
        )


def test_provenance_validator_accepts_multiple_valid_citations() -> None:
    first = make_retrieved_chunk(content="Status: At Risk")
    second = make_retrieved_chunk(
        content="Owner: Platform Team",
        distance=0.20,
    )
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk and owned by Platform Team.",
        citations=(
            ProposedCitation(
                candidate_id=str(first.chunk_version_id),
                evidence_span="Status: At Risk",
            ),
            ProposedCitation(
                candidate_id=str(second.chunk_version_id),
                evidence_span="Owner: Platform Team",
            ),
        ),
    )

    citations = ProvenanceValidator().validate(
        draft=draft,
        retrieval_snapshot=(first, second),
    )

    assert len(citations) == 2
    assert citations[0].chunk_version_id == first.chunk_version_id
    assert citations[0].quote == "Status: At Risk"
    assert citations[0].rank == 1
    assert citations[1].chunk_version_id == second.chunk_version_id
    assert citations[1].quote == "Owner: Platform Team"
    assert citations[1].rank == 2
    assert citations[1].distance == 0.20


def test_provenance_validator_fails_closed_on_mixed_valid_and_invalid() -> None:
    valid = make_retrieved_chunk(content="Status: At Risk")
    draft = GeneratedAnswerDraft(
        answer="Mixed provenance.",
        citations=(
            ProposedCitation(
                candidate_id=str(valid.chunk_version_id),
                evidence_span="Status: At Risk",
            ),
            ProposedCitation(
                candidate_id=str(uuid4()),
                evidence_span="Status: At Risk",
            ),
        ),
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="not present in the retrieval snapshot",
    ):
        ProvenanceValidator().validate(
            draft=draft,
            retrieval_snapshot=(valid,),
        )


def test_provenance_validator_rejects_empty_citation_list() -> None:
    chunk = make_retrieved_chunk()
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(),
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="proposed citations must not be empty",
    ):
        ProvenanceValidator().validate(
            draft=draft,
            retrieval_snapshot=(chunk,),
        )


def test_provenance_validator_preserves_source_version_identifiers() -> None:
    chunk = make_retrieved_chunk()
    draft = GeneratedAnswerDraft(
        answer="Project Atlas is at risk.",
        citations=(
            ProposedCitation(
                candidate_id=str(chunk.chunk_version_id),
                evidence_span="Status: At Risk",
            ),
        ),
    )

    citations = ProvenanceValidator().validate(
        draft=draft,
        retrieval_snapshot=(chunk,),
    )

    citation = citations[0]

    assert citation.vector_index_entry_id == chunk.vector_index_entry_id
    assert citation.source_document_id == chunk.source_document_id
    assert citation.document_version_id == chunk.document_version_id
    assert citation.section_version_id == chunk.section_version_id
    assert citation.chunk_version_id == chunk.chunk_version_id
    assert citation.embedding_record_id == chunk.embedding_record_id
    assert citation.stable_section_key == chunk.stable_section_key
