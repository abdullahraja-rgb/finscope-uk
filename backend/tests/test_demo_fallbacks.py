import pandas as pd
from fastapi.testclient import TestClient

from app.api.routes import cost_of_living as cost_of_living_route
from app.api.routes import datasets as datasets_route
from app.main import app


def test_latest_inflation_endpoint_uses_demo_when_raw_file_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        datasets_route,
        "latest_ons_category_inflation",
        lambda data_dir, index_type: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    client = TestClient(app)
    response = client.get("/api/v1/datasets/inflation/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"]
    assert "demo inflation data" in payload["notes"][0]


def test_personal_inflation_endpoint_uses_demo_when_raw_file_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        cost_of_living_route,
        "latest_ons_category_inflation",
        lambda data_dir, index_type: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/cost-of-living/personal-inflation",
        json={
            "transactions": [
                {
                    "date": "2026-06-01",
                    "description": "Tesco",
                    "amount": -80,
                    "category": "groceries",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["personal_inflation_pct"] > 0
    assert "demo inflation data" in payload["notes"][-1]


def test_rate_impact_endpoint_uses_demo_when_raw_file_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        cost_of_living_route,
        "load_bank_rate_history",
        lambda data_dir: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/cost-of-living/rate-impact",
        json={"savings_balance": 6000, "variable_debt_balance": 2400},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_bank_rate_pct"] == 3.75
    assert "demo Bank Rate data" in payload["notes"][-1]


def test_datasets_summary_uses_demo_macro_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        datasets_route,
        "load_bank_rate_history",
        lambda data_dir: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    monkeypatch.setattr(
        datasets_route,
        "load_uk_hpi",
        lambda data_dir: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    monkeypatch.setattr(
        datasets_route,
        "latest_ons_category_inflation",
        lambda data_dir, index_type: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    monkeypatch.setattr(
        datasets_route,
        "load_synthetic_transactions",
        lambda data_dir: pd.DataFrame(
            [
                {
                    "date": pd.Timestamp("2026-01-01"),
                    "amount": -10,
                    "category": "groceries",
                }
            ]
        ),
    )

    client = TestClient(app)
    response = client.get("/api/v1/datasets/summary")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["notes"]) == 3
    assert payload["bank_rate"]["latest_policy_rate"] == 3.75
