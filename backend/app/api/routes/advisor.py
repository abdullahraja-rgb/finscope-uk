from fastapi import APIRouter

from app.schemas.transactions import AdvisorContextRequest, AdvisorContextResponse
from app.services.advisor_context import build_advisor_context

router = APIRouter()


@router.post("/advisor/context", response_model=AdvisorContextResponse)
def advisor_context(request: AdvisorContextRequest) -> AdvisorContextResponse:
    return build_advisor_context(request)
