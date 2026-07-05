from fastapi import APIRouter

from app.core.config import settings
from app.schemas.transactions import (
    AdvisorAskRequest,
    AdvisorAskResponse,
    AdvisorContextRequest,
    AdvisorContextResponse,
    AdvisorRetrieveRequest,
    AdvisorRetrieveResponse,
)
from app.services.advisor_answer import answer_advisor_question
from app.services.advisor_context import build_advisor_context
from app.services.advisor_retrieval import retrieve_advisor_chunks

router = APIRouter()


@router.post("/advisor/context", response_model=AdvisorContextResponse)
def advisor_context(request: AdvisorContextRequest) -> AdvisorContextResponse:
    return build_advisor_context(request)


@router.post("/advisor/retrieve", response_model=AdvisorRetrieveResponse)
def advisor_retrieve(request: AdvisorRetrieveRequest) -> AdvisorRetrieveResponse:
    return retrieve_advisor_chunks(
        question=request.question,
        docs_dir=settings.docs_dir,
        max_chunks=request.max_chunks,
        min_score=request.min_score,
        sources=request.sources,
    )


@router.post("/advisor/ask", response_model=AdvisorAskResponse)
def advisor_ask(request: AdvisorAskRequest) -> AdvisorAskResponse:
    return answer_advisor_question(request, docs_dir=settings.docs_dir)
