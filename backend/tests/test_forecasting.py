from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import TransactionIn
from app.services.forecasting import backtest_forecasts, forecast_next_month, monthly_spend_frame


def monthly_transactions() -> list[TransactionIn]:
    spends = [100, 120, 110, 130, 125, 140, 135, 145]
    return [
        TransactionIn(
            date=date(2026, month, 3),
            description="Tesco",
            amount=-spend,
            category="groceries",
        )
        for month, spend in enumerate(spends, start=1)
    ]


def test_monthly_spend_frame_fills_missing_months() -> None:
    frame = monthly_spend_frame(
        [
            TransactionIn(
                date=date(2026, 1, 3),
                description="Tesco",
                amount=-100,
                category="groceries",
            ),
            TransactionIn(
                date=date(2026, 3, 3),
                description="Tesco",
                amount=-120,
                category="groceries",
            ),
        ]
    )

    assert frame["spend"].tolist() == [100, 0, 120]


def test_forecast_next_month_reports_interval_and_backtest_context() -> None:
    response = forecast_next_month(monthly_transactions())
    grocery = response.forecasts[0]

    assert response.period == "2026-09"
    assert response.generated_from_months == 8
    assert grocery.category == "groceries"
    assert grocery.expected_spend > 0
    assert grocery.lower_bound <= grocery.expected_spend <= grocery.upper_bound
    assert grocery.model in {
        "three-month moving average",
        "six-month trend regression",
        "seasonal naive",
    }
    assert grocery.baseline_expected_spend == 145


def test_backtest_forecasts_returns_time_aware_metrics() -> None:
    response = backtest_forecasts(monthly_transactions(), min_train_months=4)

    assert response.baseline == "last-month naive"
    assert response.metrics
    assert {metric.model for metric in response.metrics} == {
        "three-month moving average",
        "six-month trend regression",
        "seasonal naive",
    }
    assert all(metric.windows == 4 for metric in response.metrics)


def test_forecast_backtest_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/forecast/backtest",
        json={
            "min_train_months": 4,
            "transactions": [
                {
                    "date": transaction.date.isoformat(),
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "category": transaction.category,
                }
                for transaction in monthly_transactions()
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline"] == "last-month naive"
    assert payload["metrics"][0]["windows"] == 4
