from fastapi import APIRouter

from app.schemas.transactions import RecommendationsRequest, RecommendationsResponse
from app.services.recommendations import generate_recommendations

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationsResponse)
def recommendations(request: RecommendationsRequest) -> RecommendationsResponse:
    return generate_recommendations(
        forecast=request.forecast,
        personal_inflation=request.personal_inflation,
        health_score=request.health_score,
        rate_impact=request.rate_impact,
    )
