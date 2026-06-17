from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_answering_transaction,
    get_semantic_retrieval_service,
)
from app.api.schemas.evaluation import (
    RetrievalEvaluationCaseCreateRequest,
    RetrievalEvaluationCaseListResponse,
    RetrievalEvaluationCaseResponse,
    RetrievalEvaluationCaseResultListResponse,
    RetrievalEvaluationCaseResultResponse,
    RetrievalEvaluationRunRequest,
    RetrievalEvaluationRunResponse,
    to_retrieval_evaluation_case_response,
    to_retrieval_evaluation_case_result_response,
    to_retrieval_evaluation_run_summary_response,
)
from app.application.services.retrieval_evaluation_runner import (
    RetrievalEvaluationRunner,
    SemanticRetriever,
)
from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.application.transactions.evaluation import EvaluationTransaction
from app.domain.evaluation.entities import RetrievalEvaluationCase
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post(
    "/cases",
    response_model=RetrievalEvaluationCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_retrieval_evaluation_case(
    request: RetrievalEvaluationCaseCreateRequest,
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
) -> RetrievalEvaluationCaseResponse:
    evaluation_case = RetrievalEvaluationCase.create(
        name=request.name,
        query=request.query,
        expected_chunk_version_ids=tuple(request.expected_chunk_version_ids),
        tags=tuple(request.tags),
    )

    transaction.retrieval_evaluation_cases.save(evaluation_case)
    transaction.commit()

    return to_retrieval_evaluation_case_response(evaluation_case)


@router.get("/cases", response_model=RetrievalEvaluationCaseListResponse)
def list_retrieval_evaluation_cases(
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tag: str | None = Query(default=None, min_length=1),
) -> RetrievalEvaluationCaseListResponse:
    evaluation_cases = transaction.retrieval_evaluation_cases.list_recent(
        limit=limit,
        offset=offset,
        tag=tag,
    )

    return RetrievalEvaluationCaseListResponse(
        items=[
            to_retrieval_evaluation_case_response(evaluation_case)
            for evaluation_case in evaluation_cases
        ],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/cases/{evaluation_case_id}",
    response_model=RetrievalEvaluationCaseResponse,
)
def get_retrieval_evaluation_case(
    evaluation_case_id: UUID,
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
) -> RetrievalEvaluationCaseResponse:
    evaluation_case = transaction.retrieval_evaluation_cases.get_by_id(
        evaluation_case_id,
    )

    if evaluation_case is None:
        raise HTTPException(
            status_code=404,
            detail="Retrieval evaluation case not found",
        )

    return to_retrieval_evaluation_case_response(evaluation_case)


@router.get(
    "/cases/{evaluation_case_id}/results",
    response_model=RetrievalEvaluationCaseResultListResponse,
)
def list_retrieval_evaluation_case_results_for_case(
    evaluation_case_id: UUID,
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RetrievalEvaluationCaseResultListResponse:
    evaluation_case = transaction.retrieval_evaluation_cases.get_by_id(
        evaluation_case_id,
    )

    if evaluation_case is None:
        raise HTTPException(
            status_code=404,
            detail="Retrieval evaluation case not found",
        )

    results = transaction.retrieval_evaluation_case_results.list_by_case_id(
        evaluation_case_id,
    )
    paginated_results = results[offset : offset + limit]

    return RetrievalEvaluationCaseResultListResponse(
        items=[
            to_retrieval_evaluation_case_result_response(result)
            for result in paginated_results
        ],
        limit=limit,
        offset=offset,
    )


@router.get("/results", response_model=RetrievalEvaluationCaseResultListResponse)
def list_retrieval_evaluation_case_results(
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: RetrievalEvaluationCaseResultStatus | None = None,
) -> RetrievalEvaluationCaseResultListResponse:
    results = transaction.retrieval_evaluation_case_results.list_recent(
        limit=limit,
        offset=offset,
        status=status.value if status is not None else None,
    )

    return RetrievalEvaluationCaseResultListResponse(
        items=[
            to_retrieval_evaluation_case_result_response(result)
            for result in results
        ],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/results/{evaluation_case_result_id}",
    response_model=RetrievalEvaluationCaseResultResponse,
)
def get_retrieval_evaluation_case_result(
    evaluation_case_result_id: UUID,
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
) -> RetrievalEvaluationCaseResultResponse:
    result = transaction.retrieval_evaluation_case_results.get_by_id(
        evaluation_case_result_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Retrieval evaluation case result not found",
        )

    return to_retrieval_evaluation_case_result_response(result)


@router.post("/runs", response_model=RetrievalEvaluationRunResponse)
def run_retrieval_evaluation(
    request: RetrievalEvaluationRunRequest,
    transaction: Annotated[
        EvaluationTransaction,
        Depends(get_answering_transaction),
    ],
    retriever: Annotated[
        SemanticRetrievalService,
        Depends(get_semantic_retrieval_service),
    ],
) -> RetrievalEvaluationRunResponse:
    evaluation_cases = []

    for evaluation_case_id in request.evaluation_case_ids:
        evaluation_case = transaction.retrieval_evaluation_cases.get_by_id(
            evaluation_case_id,
        )

        if evaluation_case is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Retrieval evaluation case not found: "
                    f"{evaluation_case_id}"
                ),
            )

        evaluation_cases.append(evaluation_case)

    runner = RetrievalEvaluationRunner(
        retriever=cast(SemanticRetriever, retriever),
    )

    run_result = runner.run_cases(
        evaluation_cases=tuple(evaluation_cases),
        top_k=request.top_k,
        provider=request.provider,
        model_name=request.model_name,
        transaction=transaction,
    )

    return RetrievalEvaluationRunResponse(
        results=[
            to_retrieval_evaluation_case_result_response(result)
            for result in run_result.results
        ],
        summary=to_retrieval_evaluation_run_summary_response(
            run_result.summary,
        ),
    )