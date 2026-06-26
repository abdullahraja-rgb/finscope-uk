from fastapi import APIRouter

from app.schemas.transactions import ScenarioRequest, ScenarioResponse
from app.services.scenario import run_scenario

router = APIRouter()


@router.post("/scenario", response_model=ScenarioResponse)
def scenario(request: ScenarioRequest) -> ScenarioResponse:
    return run_scenario(request)
