from fastapi import APIRouter

from app.schemas.transactions import ForecastBacktestRequest, ForecastBacktestResponse, ForecastResponse, TransactionBatch
from app.services.forecasting import backtest_forecasts, forecast_next_month

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
def forecast(batch: TransactionBatch) -> ForecastResponse:
    return forecast_next_month(batch.transactions)


@router.post("/forecast/backtest", response_model=ForecastBacktestResponse)
def backtest(request: ForecastBacktestRequest) -> ForecastBacktestResponse:
    return backtest_forecasts(request.transactions, min_train_months=request.min_train_months)
