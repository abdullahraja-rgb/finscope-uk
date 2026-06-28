from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_score_endpoint() -> None:
    response = client.post(
        "/api/v1/score",
        json={
            "monthly_income": 3200,
            "monthly_spend": 2400,
            "rent_or_mortgage": 950,
            "monthly_debt_payment": 120,
            "liquid_savings": 6000,
            "subscriptions": 55,
            "spend_volatility": 180,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["score"] <= 100
    assert payload["band"] in {"Strong", "Stable", "Watch", "At risk"}


def test_categorise_endpoint() -> None:
    response = client.post(
        "/api/v1/categorise",
        json={
            "transactions": [
                {
                    "date": "2026-06-01",
                    "description": "Tesco Superstore",
                    "amount": -42.5,
                    "category": None,
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["transactions"][0]["predicted_category"] == "groceries"


def test_forecast_endpoint() -> None:
    response = client.post(
        "/api/v1/forecast",
        json={
            "transactions": [
                {
                    "date": "2026-04-03",
                    "description": "Tesco",
                    "amount": -100,
                    "category": "groceries",
                },
                {
                    "date": "2026-05-03",
                    "description": "Tesco",
                    "amount": -120,
                    "category": "groceries",
                },
                {
                    "date": "2026-06-03",
                    "description": "Tesco",
                    "amount": -140,
                    "category": "groceries",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline"] == "last-month naive"
    assert payload["forecasts"][0]["expected_spend"] == 120


def test_scenario_endpoint() -> None:
    response = client.post(
        "/api/v1/scenario",
        json={
            "monthly_income": 3200,
            "monthly_spend": 2400,
            "rent_or_mortgage": 1000,
            "savings_balance": 5000,
            "variable_debt_balance": 1200,
            "food_spend": 400,
            "rent_change_pct": 8,
            "food_change_pct": 10,
            "bank_rate_change_pct_points": 0.25,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["new_monthly_spend"] > 2400
    assert payload["debt_cost_delta_monthly"] == 0.25


def test_transactions_preview_rejects_missing_columns() -> None:
    response = client.post(
        "/api/v1/transactions/preview",
        files={"file": ("transactions.csv", b"date,amount\n2026-06-01,-10\n", "text/csv")},
    )

    assert response.status_code == 422
    assert "description" in response.json()["detail"]
