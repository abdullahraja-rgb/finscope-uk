from fastapi.testclient import TestClient
import pandas as pd

from app.api.routes import score as score_route
from app.main import app
from app.schemas.transactions import DerivedHealthScoreRequest, TransactionIn
from app.services.scoring import derive_health_score


def benchmark_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "period": "2024-25",
                "coicop_code": "01",
                "category": "Food & non-alcoholic drinks",
                "average_weekly_spend": 73.7,
                "benchmark_share": 0.1265,
            },
            {
                "period": "2024-25",
                "coicop_code": "04",
                "category": "Housing (net), fuel & power",
                "average_weekly_spend": 118.4,
                "benchmark_share": 0.2033,
            },
            {
                "period": "2024-25",
                "coicop_code": "07",
                "category": "Transport",
                "average_weekly_spend": 96.4,
                "benchmark_share": 0.1655,
            },
        ]
    )


def sample_transactions() -> list[TransactionIn]:
    return [
        TransactionIn(date="2026-06-25", description="Salary", amount=3200, category="income"),
        TransactionIn(date="2026-06-01", description="Rent", amount=-1000, category="housing"),
        TransactionIn(date="2026-06-02", description="Tesco", amount=-400, category="groceries"),
        TransactionIn(date="2026-06-03", description="Trainline", amount=-150, category="transport"),
        TransactionIn(date="2026-06-04", description="Netflix", amount=-50, category="subscriptions"),
    ]


def test_derive_health_score_from_transactions() -> None:
    response = derive_health_score(
        DerivedHealthScoreRequest(
            transactions=sample_transactions(),
            liquid_savings=4800,
            monthly_debt_payment=100,
        ),
        category_mapping={
            "groceries": "01 Food and non-alcoholic beverages",
            "housing": "04 Housing, water, electricity, gas and other fuels",
            "transport": "07 Transport",
            "subscriptions": "09 Recreation and culture",
        },
        benchmarks=benchmark_fixture(),
    )

    assert response.monthly_income == 3200
    assert response.monthly_spend == 1600
    assert response.emergency_fund_months == 3
    assert response.score > 0
    assert response.benchmarks[0].difference_pct_points != 0


def test_score_from_transactions_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        score_route,
        "load_category_mapping",
        lambda config_dir: {
            "groceries": "01 Food and non-alcoholic beverages",
            "housing": "04 Housing, water, electricity, gas and other fuels",
            "transport": "07 Transport",
            "subscriptions": "09 Recreation and culture",
        },
    )
    monkeypatch.setattr(score_route, "load_family_spending_benchmarks", lambda data_dir: benchmark_fixture())

    client = TestClient(app)
    response = client.post(
        "/api/v1/score/from-transactions",
        json={
            "liquid_savings": 4800,
            "monthly_debt_payment": 100,
            "transactions": [
                {
                    "date": transaction.date.isoformat(),
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "category": transaction.category,
                }
                for transaction in sample_transactions()
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["monthly_spend"] == 1600
    assert payload["benchmarks"]
