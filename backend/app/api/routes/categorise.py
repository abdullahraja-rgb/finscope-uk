from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.transactions import (
    CategorisationEvaluationRequest,
    CategorisationEvaluationResponse,
    CategorisationResponse,
    TransactionBatch,
)
from app.services.categorisation import (
    categorisation_model_path,
    categorise_transactions,
    evaluate_categorisation_model,
)

router = APIRouter()


@router.post("/categorise", response_model=CategorisationResponse)
def categorise(batch: TransactionBatch) -> CategorisationResponse:
    model_path = categorisation_model_path(settings.data_dir)
    return CategorisationResponse(transactions=categorise_transactions(batch.transactions, model_path))


@router.post("/categorise/evaluate", response_model=CategorisationEvaluationResponse)
def evaluate_categoriser(request: CategorisationEvaluationRequest) -> CategorisationEvaluationResponse:
    try:
        return evaluate_categorisation_model(
            request.transactions,
            test_size=request.test_size,
            random_state=request.random_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
