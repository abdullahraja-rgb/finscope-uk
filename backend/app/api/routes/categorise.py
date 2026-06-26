from fastapi import APIRouter

from app.schemas.transactions import CategorisationResponse, TransactionBatch
from app.services.categorisation import categorise_transactions

router = APIRouter()


@router.post("/categorise", response_model=CategorisationResponse)
def categorise(batch: TransactionBatch) -> CategorisationResponse:
    return CategorisationResponse(transactions=categorise_transactions(batch.transactions))
