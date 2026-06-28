from fastapi import APIRouter

from app.core.config import settings
from app.data import latest_ons_category_inflation
from app.schemas.transactions import PersonalInflationRequest, PersonalInflationResponse
from app.services.cost_of_living import calculate_personal_inflation, load_category_mapping

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
