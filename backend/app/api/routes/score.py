from fastapi import APIRouter

from app.core.config import settings
from app.data import load_family_spending_benchmarks
from app.schemas.transactions import (
    DerivedHealthScoreRequest,
    DerivedHealthScoreResponse,
    HealthScoreRequest,
    HealthScoreResponse,
)
from app.services.cost_of_living import load_category_mapping
from app.services.scoring import calculate_health_score, derive_health_score

router = APIRouter()


@router.post("/score", response_model=HealthScoreResponse)
def score(request: HealthScoreRequest) -> HealthScoreResponse:
    return calculate_health_score(request)


@router.post("/score/from-transactions", response_model=DerivedHealthScoreResponse)
def score_from_transactions(request: DerivedHealthScoreRequest) -> DerivedHealthScoreResponse:
    mapping = load_category_mapping(settings.config_dir)
    benchmarks = load_family_spending_benchmarks(settings.data_dir)
    return derive_health_score(request, category_mapping=mapping, benchmarks=benchmarks)
