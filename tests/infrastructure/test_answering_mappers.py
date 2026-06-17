from uuid import UUID, uuid4

from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswerCitation,
)
from app.domain.answering.enums import GroundedAnswerStatus
from app.infrastructure.db.mappers import (
    answer_citation_record_from_model,
    answer_citation_record_to_model,
    answer_record_from_model,
    answer_record_to_model,
)


def make_citation_record(answer_id: UUID) -> AnswerCitationRecord:
    citation = GroundedAnswerCitation(
        rank=1,
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
        distance=0.12,
    )

    return AnswerCitationRecord.from_grounded_citation(
        answer_id=answer_id,
        citation=citation,
    )


def test_answer_record_mapper_round_trips_entity() -> None:
    record = AnswerRecord(
        id=uuid4(),
        question="What is Project Atlas status?",
        answer="Project Atlas is at risk.",
        status=GroundedAnswerStatus.ANSWERED,
        query_trace_id=uuid4(),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
    )

    model = answer_record_to_model(record)
    mapped_record = answer_record_from_model(model)

    assert mapped_record == record


def test_answer_citation_record_mapper_round_trips_entity() -> None:
    record = make_citation_record(answer_id=uuid4())

    model = answer_citation_record_to_model(record)
    mapped_record = answer_citation_record_from_model(model)

    assert mapped_record == record