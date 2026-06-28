from datetime import date

import pandas as pd
from fastapi.testclient import TestClient

from app.api.routes import cost_of_living as cost_of_living_route
from app.main import app
from app.schemas.transactions import RateImpactRequest, TransactionIn
from app.services.cost_of_living import (
    calculate_personal_inflation,
    calculate_rate_impact,
    repayment_mortgage_payment,
)


def inflation_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "index_type": "cpih",
                "date": pd.Timestamp("2026-05-01"),
                "coicop_code": None,
                "category": "CPIH (overall index)",
                "category_level": "overall",
                "weight": 1000,
                "annual_change_pct": 3.0,
            },
            {
                "index_type": "cpih",
                "date": pd.Timestamp("2026-05-01"),
                "coicop_code": "01",
                "category": "Food and non-alcoholic beverages",
                "category_level": "division",
                "weight": 86.5,
                "annual_change_pct": 2.0,
            },
            {
                "index_type": "cpih",
                "date": pd.Timestamp("2026-05-01"),
                "coicop_code": "07",
                "category": "Transport",
                "category_level": "division",
                "weight": 111.3,
                "annual_change_pct": 6.0,
            },
        ]
    )


def test_calculate_personal_inflation_weights_spend_mix() -> None:
    response = calculate_personal_inflation(
        transactions=[
            TransactionIn(
                date=date(2026, 6, 1),
                description="Tesco",
                amount=-100,
                category="groceries",
            ),
            TransactionIn(
                date=date(2026, 6, 2),
                description="Trainline",
                amount=-100,
                category="transport",
            ),
        ],
        inflation=inflation_fixture(),
        category_mapping={
            "groceries": "01 Food and non-alcoholic beverages",
            "transport": "07 Transport",
        },
        index_type="cpih",
    )

    assert response.period == "2026-05-01"
    assert response.total_spend == 200
    assert response.personal_inflation_pct == 4.0
    assert response.national_inflation_pct == 3.0
    assert response.difference_pct_points == 1.0


def test_calculate_personal_inflation_excludes_unmapped_spend() -> None:
    response = calculate_personal_inflation(
        transactions=[
            TransactionIn(
                date=date(2026, 6, 1),
                description="Unknown merchant",
                amount=-50,
                category="uncategorised",
            )
        ],
        inflation=inflation_fixture(),
        category_mapping={},
        index_type="cpih",
    )

    assert response.personal_inflation_pct == 0
    assert response.categories[0].annual_change_pct is None
    assert response.notes == ["No ONS mapping found for uncategorised; excluded from weighted rate."]


def test_personal_inflation_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        cost_of_living_route,
        "latest_ons_category_inflation",
        lambda data_dir, index_type: inflation_fixture(),
    )
    monkeypatch.setattr(
        cost_of_living_route,
        "load_category_mapping",
        lambda config_dir: {
            "groceries": "01 Food and non-alcoholic beverages",
            "transport": "07 Transport",
        },
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/cost-of-living/personal-inflation",
        json={
            "index_type": "cpih",
            "transactions": [
                {
                    "date": "2026-06-01",
                    "description": "Tesco",
                    "amount": -80,
                    "category": "groceries",
                },
                {
                    "date": "2026-06-02",
                    "description": "Trainline",
                    "amount": -20,
                    "category": "transport",
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["personal_inflation_pct"] == 2.8
    assert payload["national_inflation_pct"] == 3.0


def test_repayment_mortgage_payment_zero_rate() -> None:
    assert repayment_mortgage_payment(balance=120_000, annual_rate_pct=0, years_remaining=10) == 1000


def test_calculate_rate_impact_combines_savings_debt_and_mortgage() -> None:
    response = calculate_rate_impact(
        RateImpactRequest(
            savings_balance=6000,
            variable_debt_balance=2400,
            mortgage_balance=180000,
            mortgage_years_remaining=22,
            current_mortgage_rate_pct=5.0,
            bank_rate_change_pct_points=0.25,
        ),
        current_bank_rate_pct=3.75,
    )

    assert response.current_bank_rate_pct == 3.75
    assert response.scenario_bank_rate_pct == 4.0
    assert response.monthly_net_cashflow_delta < 0
    assert {line.name for line in response.lines} == {
        "Savings interest",
        "Variable debt cost",
        "Repayment mortgage",
    }


def test_calculate_rate_impact_skips_mortgage_without_current_rate() -> None:
    response = calculate_rate_impact(
        RateImpactRequest(
            savings_balance=0,
            variable_debt_balance=0,
            mortgage_balance=180000,
            bank_rate_change_pct_points=0.25,
        ),
        current_bank_rate_pct=3.75,
    )

    assert response.notes == ["Mortgage impact skipped because current_mortgage_rate_pct was not provided."]
    assert all(line.name != "Repayment mortgage" for line in response.lines)


def test_rate_impact_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        cost_of_living_route,
        "load_bank_rate_history",
        lambda data_dir: pd.DataFrame(
            [{"date": pd.Timestamp("2026-06-18"), "policy_rate": 3.75}]
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/cost-of-living/rate-impact",
        json={
            "savings_balance": 6000,
            "variable_debt_balance": 2400,
            "mortgage_balance": 0,
            "bank_rate_change_pct_points": 0.25,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_bank_rate_pct"] == 4.0
    assert payload["monthly_net_cashflow_delta"] == 0.75
