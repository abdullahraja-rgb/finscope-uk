from fastapi import APIRouter

from app.schemas.transactions import HealthScoreRequest, HealthScoreResponse
from app.services.scoring import calculate_health_score

router = APIRouter()


@router.post("/score", response_model=HealthScoreResponse)
def score(request: HealthScoreRequest) -> HealthScoreResponse:
    return calculate_health_score(request)
