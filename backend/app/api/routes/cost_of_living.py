import pandas as pd
from fastapi import APIRouter

from app.core.config import settings
from app.data import latest_ons_category_inflation, load_bank_rate_history
from app.data.fallbacks import demo_bank_rate_history, demo_latest_inflation
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


def latest_inflation_or_demo(index_type: str) -> tuple[pd.DataFrame, bool]:
    try:
        return latest_ons_category_inflation(settings.data_dir, index_type=index_type), False
    except (FileNotFoundError, ValueError):
        return demo_latest_inflation(index_type=index_type), True


def bank_rate_or_demo() -> tuple[pd.DataFrame, bool]:
    try:
        return load_bank_rate_history(settings.data_dir).sort_values("date"), False
    except (FileNotFoundError, ValueError):
        return demo_bank_rate_history().sort_values("date"), True


@router.post("/cost-of-living/personal-inflation", response_model=PersonalInflationResponse)
def personal_inflation(request: PersonalInflationRequest) -> PersonalInflationResponse:
    inflation, used_demo = latest_inflation_or_demo(request.index_type)
    mapping = load_category_mapping(settings.config_dir)
    response = calculate_personal_inflation(
        transactions=request.transactions,
        inflation=inflation,
        category_mapping=mapping,
        index_type=request.index_type,
    )
    if used_demo:
        response.notes.append("Using bundled demo inflation data because the raw ONS workbook is unavailable.")
    return response


@router.post("/cost-of-living/rate-impact", response_model=RateImpactResponse)
def rate_impact(request: RateImpactRequest) -> RateImpactResponse:
    bank_rate, used_demo = bank_rate_or_demo()
    latest_rate = float(bank_rate.iloc[-1]["policy_rate"])
    response = calculate_rate_impact(request, current_bank_rate_pct=latest_rate)
    if used_demo:
        response.notes.append("Using bundled demo Bank Rate data because the raw BoE file is unavailable.")
    return response
