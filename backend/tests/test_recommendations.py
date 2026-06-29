from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import (
    DerivedHealthScoreResponse,
    ForecastPoint,
    ForecastResponse,
    PersonalInflationCategory,
    PersonalInflationResponse,
    ScoreComponent,
)
from app.services.recommendations import generate_recommendations


def health_fixture() -> DerivedHealthScoreResponse:
    return DerivedHealthScoreResponse(
        score=61,
        band="Stable",
        components=[
            ScoreComponent(name="Emergency fund", score=30, weight=0.2, note=""),
            ScoreComponent(name="Savings rate", score=70, weight=0.25, note=""),
        ],
        monthly_income=3200,
        monthly_spend=2400,
        savings_rate=0.25,
        rent_to_income=0.38,
        emergency_fund_months=1.8,
        spending_volatility=120,
        benchmarks=[],
        notes=[],
    )


def forecast_fixture() -> ForecastResponse:
    return ForecastResponse(
        period="2026-07",
        forecasts=[
            ForecastPoint(
                category="groceries",
                expected_spend=420,
                lower_bound=360,
                upper_bound=510,
                model="three-month moving average",
            )
        ],
        baseline="last-month naive",
        generated_from_months=6,
    )


def inflation_fixture() -> PersonalInflationResponse:
    return PersonalInflationResponse(
        index_type="cpih",
        period="2026-05-01",
        total_spend=1500,
        personal_inflation_pct=4.2,
        national_inflation_pct=3.0,
        difference_pct_points=1.2,
        categories=[
            PersonalInflationCategory(
                app_category="groceries",
                spend=420,
                spend_share=0.28,
                ons_category="Food and non-alcoholic beverages",
                coicop_code="01",
                annual_change_pct=6.0,
                contribution_pct_points=1.68,
            )
        ],
        notes=[],
    )


def test_generate_recommendations_uses_calculated_outputs() -> None:
    response = generate_recommendations(
        forecast=forecast_fixture(),
        personal_inflation=inflation_fixture(),
        health_score=health_fixture(),
    )

    titles = [item.title for item in response.recommendations]
    assert "Build the emergency buffer first" in titles
    assert "Check the housing burden" in titles
    assert any(item.source == "Inflation" for item in response.recommendations)


def test_recommendations_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/recommendations",
        json={
            "forecast": forecast_fixture().model_dump(mode="json"),
            "personal_inflation": inflation_fixture().model_dump(mode="json"),
            "health_score": health_fixture().model_dump(mode="json"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendations"]
    assert payload["recommendations"][0]["priority"] in {"high", "medium", "low"}
