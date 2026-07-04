from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import (
    AdvisorContextRequest,
    AdvisorProfile,
    DerivedHealthScoreResponse,
    ForecastPoint,
    ForecastResponse,
    PersonalInflationCategory,
    PersonalInflationResponse,
    RateImpactLine,
    RateImpactResponse,
    Recommendation,
    ScoreComponent,
    TransactionIn,
)
from app.services.advisor_context import build_advisor_context


def profile_fixture() -> AdvisorProfile:
    return AdvisorProfile(
        monthly_income=3200,
        rent_or_mortgage=1000,
        monthly_debt_payment=200,
        liquid_savings=5000,
        investment_balance=2000,
        pension_balance=10000,
        property_value=0,
        mortgage_balance=0,
        credit_card_balance=600,
        loan_balance=1400,
        average_debt_apr=18,
        emergency_fund_target=9000,
        savings_goal_target=15000,
        monthly_goal_contribution=250,
    )


def transaction_fixture() -> list[TransactionIn]:
    return [
        TransactionIn(date=date(2026, 5, 25), description="Salary Payroll", amount=3200, category="income"),
        TransactionIn(date=date(2026, 6, 1), description="Rent Payment", amount=-1000, category="housing"),
        TransactionIn(date=date(2026, 6, 3), description="Tesco", amount=-240, category="groceries"),
        TransactionIn(date=date(2026, 6, 8), description="Octopus Energy", amount=-160, category="utilities"),
        TransactionIn(date=date(2026, 6, 10), description="Netflix", amount=-20, category="subscriptions"),
    ]


def health_fixture() -> DerivedHealthScoreResponse:
    return DerivedHealthScoreResponse(
        score=68,
        band="Stable",
        components=[
            ScoreComponent(name="Savings rate", score=70, weight=0.25, note=""),
            ScoreComponent(name="Emergency fund", score=45, weight=0.2, note=""),
        ],
        monthly_income=3200,
        monthly_spend=1420,
        savings_rate=0.5563,
        rent_to_income=0.3125,
        emergency_fund_months=3.52,
        spending_volatility=120,
        benchmarks=[],
        notes=[],
    )


def forecast_fixture() -> ForecastResponse:
    return ForecastResponse(
        period="2026-07",
        baseline="last-month naive",
        generated_from_months=6,
        forecasts=[
            ForecastPoint(
                category="housing",
                expected_spend=1000,
                lower_bound=950,
                upper_bound=1050,
                model="three-month moving average",
            ),
            ForecastPoint(
                category="groceries",
                expected_spend=260,
                lower_bound=220,
                upper_bound=330,
                model="three-month moving average",
            ),
        ],
    )


def inflation_fixture() -> PersonalInflationResponse:
    return PersonalInflationResponse(
        index_type="cpih",
        period="2026-05-01",
        total_spend=1420,
        personal_inflation_pct=4.2,
        national_inflation_pct=3.0,
        difference_pct_points=1.2,
        categories=[
            PersonalInflationCategory(
                app_category="housing",
                spend=1000,
                spend_share=0.7042,
                ons_category="Housing, water, electricity, gas and other fuels",
                coicop_code="04",
                annual_change_pct=4.8,
                contribution_pct_points=3.38,
            )
        ],
        notes=[],
    )


def rate_fixture() -> RateImpactResponse:
    return RateImpactResponse(
        current_bank_rate_pct=3.75,
        scenario_bank_rate_pct=4.0,
        bank_rate_change_pct_points=0.25,
        effective_rate_change_pct_points=0.25,
        monthly_net_cashflow_delta=-0.42,
        annual_net_cashflow_delta=-5.04,
        lines=[
            RateImpactLine(name="Savings interest", monthly_delta=1.04, annual_delta=12.48, note=""),
            RateImpactLine(name="Variable debt cost", monthly_delta=-1.46, annual_delta=-17.52, note=""),
        ],
        notes=[],
    )


def recommendation_fixture() -> list[Recommendation]:
    return [
        Recommendation(
            title="Build the emergency buffer first",
            detail="Emergency savings cover 3.5 months of spend.",
            action="Keep monthly savings moving until the target is covered.",
            priority="medium",
            source="Health score",
        )
    ]


def full_context_request() -> AdvisorContextRequest:
    return AdvisorContextRequest(
        question="Why is my budget under pressure?",
        profile=profile_fixture(),
        transactions=transaction_fixture(),
        forecast=forecast_fixture(),
        personal_inflation=inflation_fixture(),
        health_score=health_fixture(),
        rate_impact=rate_fixture(),
        recommendations=recommendation_fixture(),
    )


def fact_by_id(response, fact_id: str):
    for section in response.sections:
        for item in section.facts:
            if item.id == fact_id:
                return item
    raise AssertionError(f"Missing fact {fact_id}")


def test_build_advisor_context_calculates_core_facts() -> None:
    response = build_advisor_context(full_context_request())

    assert fact_by_id(response, "disposable_income").formatted == "GBP 1,780"
    assert fact_by_id(response, "forecast_expected_total").formatted == "GBP 1,260"
    assert fact_by_id(response, "largest_inflation_contributor").formatted == "housing: 3.38 percentage points"
    assert fact_by_id(response, "net_worth").formatted == "GBP 15,000"
    assert "Net worth: GBP 15,000 [profile]" in response.allowed_numbers
    assert "Use only the facts and numbers in this context pack." in response.guardrails
    assert "Disposable income: GBP 1,780 [health_score]" in response.context_markdown


def test_build_advisor_context_flags_missing_inputs() -> None:
    response = build_advisor_context(AdvisorContextRequest())
    missing_keys = {item.key for item in response.missing_data}

    assert "profile" in missing_keys
    assert "monthly_income" in missing_keys
    assert "transactions" in missing_keys
    assert "forecast" in missing_keys
    assert "personal_inflation" in missing_keys
    assert "health_score" in missing_keys
    assert "rate_impact" in missing_keys


def test_build_advisor_context_flags_missing_categories() -> None:
    response = build_advisor_context(full_context_request())
    missing_keys = {item.key for item in response.missing_data}

    assert "category_transport" in missing_keys
    assert "category_groceries" not in missing_keys
    assert "category_housing" not in missing_keys


def test_advisor_context_endpoint_returns_context_pack() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/advisor/context",
        json=full_context_request().model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sections"]
    assert payload["source_map"]["forecast"] == "Backend spend forecast and rolling backtest output."
    assert "Advisor Context Pack" in payload["context_markdown"]
