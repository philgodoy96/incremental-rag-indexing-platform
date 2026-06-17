from uuid import uuid4

import pytest

from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswer,
    GroundedAnswerCitation,
    GroundedAnswerRequest,
)
from app.domain.answering.enums import GroundedAnswerStatus


def make_citation(rank: int = 1, distance: float = 0.12) -> GroundedAnswerCitation:
    return GroundedAnswerCitation(
        rank=rank,
        vector_index_entry_id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        heading_context=("Project Atlas Status", "Summary"),
        quote="Status: At Risk",
        distance=distance,
    )


def test_grounded_answer_request_accepts_valid_input() -> None:
    request = GroundedAnswerRequest(
        question="What is Project Atlas status?",
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
    )

    assert request.question == "What is Project Atlas status?"
    assert request.top_k == 5
    assert request.provider == "fake"
    assert request.model_name == "fake-embedding-v1"


def test_grounded_answer_request_rejects_blank_question() -> None:
    with pytest.raises(ValueError, match="question must not be blank"):
        GroundedAnswerRequest(
            question=" ",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        )


def test_grounded_answer_request_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be greater"):
        GroundedAnswerRequest(
            question="What is Project Atlas status?",
            top_k=0,
            provider="fake",
            model_name="fake-embedding-v1",
        )


def test_grounded_answer_citation_rejects_invalid_rank() -> None:
    with pytest.raises(ValueError, match="rank must be greater"):
        make_citation(rank=0)


def test_grounded_answer_citation_rejects_negative_distance() -> None:
    with pytest.raises(ValueError, match="distance must not be negative"):
        make_citation(distance=-0.01)


def test_answered_grounded_answer_requires_citations() -> None:
    with pytest.raises(
        ValueError,
        match="answered grounded answer must include citations",
    ):
        GroundedAnswer.answered(
            question="What is Project Atlas status?",
            answer="Project Atlas is at risk.",
            query_trace_id=uuid4(),
            citations=(),
        )


def test_answered_grounded_answer_accepts_citations() -> None:
    answer = GroundedAnswer.answered(
        question="What is Project Atlas status?",
        answer="Project Atlas is at risk.",
        query_trace_id=uuid4(),
        citations=(make_citation(),),
    )

    assert answer.status == GroundedAnswerStatus.ANSWERED
    assert answer.answer == "Project Atlas is at risk."
    assert len(answer.citations) == 1


def test_insufficient_context_answer_has_no_citations() -> None:
    answer = GroundedAnswer.insufficient_context(
        question="What is Project Phoenix budget?",
        query_trace_id=uuid4(),
    )

    assert answer.status == GroundedAnswerStatus.INSUFFICIENT_CONTEXT
    assert answer.citations == ()
    assert "not have enough retrieved context" in answer.answer


def test_answer_record_can_be_created_from_grounded_answer() -> None:
    request = GroundedAnswerRequest(
        question="What is Project Atlas status?",
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
    )
    grounded_answer = GroundedAnswer.answered(
        question="What is Project Atlas status?",
        answer="Project Atlas is at risk.",
        query_trace_id=uuid4(),
        citations=(make_citation(),),
    )

    record = AnswerRecord.from_grounded_answer(
        grounded_answer=grounded_answer,
        request=request,
    )

    assert record.question == grounded_answer.question
    assert record.answer == grounded_answer.answer
    assert record.status == GroundedAnswerStatus.ANSWERED
    assert record.query_trace_id == grounded_answer.query_trace_id
    assert record.top_k == 5
    assert record.provider == "fake"
    assert record.model_name == "fake-embedding-v1"


def test_answer_record_rejects_blank_answer() -> None:
    with pytest.raises(ValueError, match="answer must not be blank"):
        AnswerRecord(
            id=uuid4(),
            question="What is Project Atlas status?",
            answer=" ",
            status=GroundedAnswerStatus.ANSWERED,
            query_trace_id=uuid4(),
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        )


def test_answer_citation_record_can_be_created_from_grounded_citation() -> None:
    answer_id = uuid4()
    citation = make_citation()

    record = AnswerCitationRecord.from_grounded_citation(
        answer_id=answer_id,
        citation=citation,
    )

    assert record.answer_id == answer_id
    assert record.rank == citation.rank
    assert record.chunk_version_id == citation.chunk_version_id
    assert record.stable_section_key == citation.stable_section_key
    assert record.quote == citation.quote
    assert record.distance == citation.distance


def test_answer_citation_record_rejects_invalid_rank() -> None:
    citation = make_citation(rank=1)

    with pytest.raises(ValueError, match="rank must be greater"):
        AnswerCitationRecord(
            id=uuid4(),
            answer_id=uuid4(),
            rank=0,
            vector_index_entry_id=citation.vector_index_entry_id,
            source_document_id=citation.source_document_id,
            document_version_id=citation.document_version_id,
            section_version_id=citation.section_version_id,
            chunk_version_id=citation.chunk_version_id,
            embedding_record_id=citation.embedding_record_id,
            stable_section_key=citation.stable_section_key,
            chunk_index=citation.chunk_index,
            heading_context=citation.heading_context,
            quote=citation.quote,
            distance=citation.distance,
        )


def test_answer_citation_record_rejects_negative_distance() -> None:
    citation = make_citation(rank=1)

    with pytest.raises(ValueError, match="distance must not be negative"):
        AnswerCitationRecord(
            id=uuid4(),
            answer_id=uuid4(),
            rank=1,
            vector_index_entry_id=citation.vector_index_entry_id,
            source_document_id=citation.source_document_id,
            document_version_id=citation.document_version_id,
            section_version_id=citation.section_version_id,
            chunk_version_id=citation.chunk_version_id,
            embedding_record_id=citation.embedding_record_id,
            stable_section_key=citation.stable_section_key,
            chunk_index=citation.chunk_index,
            heading_context=citation.heading_context,
            quote=citation.quote,
            distance=-0.01,
        )