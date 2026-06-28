from fastapi import APIRouter

from app.core.config import settings
from app.data import latest_ons_category_inflation, load_bank_rate_history
from app.schemas.transactions import (
    PersonalInflationRequest,
    PersonalInflationResponse,
    RateImpactRequest,
    RateImpactResponse,
)
from app.services.cost_of_living import (
    calculate_personal_inflation,
    calculate_rate_impact,
    load_category_mapping,
)

router = APIRouter()


@router.post("/cost-of-living/personal-inflation", response_model=PersonalInflationResponse)
def personal_inflation(request: PersonalInflationRequest) -> PersonalInflationResponse:
    inflation = latest_ons_category_inflation(settings.data_dir, index_type=request.index_type)
    mapping = load_category_mapping(settings.config_dir)
    return calculate_personal_inflation(
        transactions=request.transactions,
        inflation=inflation,
        category_mapping=mapping,
        index_type=request.index_type,
    )


@router.post("/cost-of-living/rate-impact", response_model=RateImpactResponse)
def rate_impact(request: RateImpactRequest) -> RateImpactResponse:
    bank_rate = load_bank_rate_history(settings.data_dir).sort_values("date")
    latest_rate = float(bank_rate.iloc[-1]["policy_rate"])
    return calculate_rate_impact(request, current_bank_rate_pct=latest_rate)
