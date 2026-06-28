from datetime import date

import pandas as pd
from fastapi.testclient import TestClient

from app.api.routes import cost_of_living as cost_of_living_route
from app.main import app
from app.schemas.transactions import TransactionIn
from app.services.cost_of_living import calculate_personal_inflation


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
