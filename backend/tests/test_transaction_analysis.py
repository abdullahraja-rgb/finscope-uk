import pandas as pd
from fastapi.testclient import TestClient

from app.api.routes import transactions as transactions_route
from app.main import app


def inflation_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "index_type": "cpih",
                "date": pd.Timestamp("2026-05-01"),
                "coicop_code": None,
                "category": "CPIH",
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
                "coicop_code": "04",
                "category": "Housing, water, electricity, gas and other fuels",
                "category_level": "division",
                "weight": 130.0,
                "annual_change_pct": 4.0,
            },
        ]
    )


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
        ]
    )


def upload_csv() -> bytes:
    return "\n".join(
        [
            "date,description,amount",
            "2026-01-25,Salary Payroll,3200",
            "2026-01-01,Rent Payment,-1000",
            "2026-01-03,Tesco Superstore,-120",
            "2026-02-25,Salary Payroll,3200",
            "2026-02-01,Rent Payment,-1000",
            "2026-02-03,Tesco Superstore,-140",
            "2026-03-25,Salary Payroll,3200",
            "2026-03-01,Rent Payment,-1000",
            "2026-03-03,Tesco Superstore,-130",
            "2026-04-25,Salary Payroll,3200",
            "2026-04-01,Rent Payment,-1000",
            "2026-04-03,Tesco Superstore,-150",
            "2026-05-25,Salary Payroll,3200",
            "2026-05-01,Rent Payment,-1000",
            "2026-05-03,Tesco Superstore,-160",
        ]
    ).encode()


def test_transactions_analyse_runs_dashboard_services(monkeypatch) -> None:
    monkeypatch.setattr(
        transactions_route,
        "categorisation_model_path",
        lambda data_dir: "missing-model.joblib",
    )
    monkeypatch.setattr(
        transactions_route,
        "load_category_mapping",
        lambda config_dir: {
            "groceries": "01 Food and non-alcoholic beverages",
            "housing": "04 Housing, water, electricity, gas and other fuels",
            "income": None,
        },
    )
    monkeypatch.setattr(
        transactions_route,
        "latest_ons_category_inflation",
        lambda data_dir, index_type: inflation_fixture(),
    )
    monkeypatch.setattr(
        transactions_route,
        "load_family_spending_benchmarks",
        lambda data_dir: benchmark_fixture(),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/transactions/analyse",
        files={"file": ("transactions.csv", upload_csv(), "text/csv")},
        data={"liquid_savings": "4800", "monthly_debt_payment": "100"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == 15
    assert payload["transactions"][1]["category"] == "housing"
    assert payload["transactions"][2]["category"] == "groceries"
    assert payload["forecast"]["forecasts"]
    assert payload["personal_inflation"]["personal_inflation_pct"] > 0
    assert payload["health_score"]["monthly_income"] == 3200


def test_transactions_analyse_rejects_bad_rows() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/transactions/analyse",
        files={
            "file": (
                "transactions.csv",
                b"date,description,amount\nnot-a-date,Tesco,-10\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert "invalid date" in response.json()["detail"]
