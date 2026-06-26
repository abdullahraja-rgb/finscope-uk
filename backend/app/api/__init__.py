from fastapi import APIRouter

from app.api.routes import categorise, forecast, scenario, score, transactions

api_router = APIRouter()
api_router.include_router(transactions.router, tags=["transactions"])
api_router.include_router(categorise.router, tags=["categorisation"])
api_router.include_router(forecast.router, tags=["forecast"])
api_router.include_router(score.router, tags=["score"])
api_router.include_router(scenario.router, tags=["scenario"])
