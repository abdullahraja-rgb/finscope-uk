from fastapi import APIRouter

from app.schemas.transactions import ForecastResponse, TransactionBatch
from app.services.forecasting import forecast_next_month

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
def forecast(batch: TransactionBatch) -> ForecastResponse:
    return forecast_next_month(batch.transactions)
