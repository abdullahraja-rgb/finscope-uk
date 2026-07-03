from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import TransactionIn
from app.services.categorisation import (
    categorise_transactions,
    evaluate_categorisation_model,
    save_categorisation_model,
)


def labelled_transactions() -> list[TransactionIn]:
    rows = [
        ("Tesco Superstore", -42.5, "groceries"),
        ("Aldi Stores", -31.2, "groceries"),
        ("Sainsbury Local", -18.4, "groceries"),
        ("TfL Travel Charge", -7.2, "transport"),
        ("Trainline Tickets", -41.0, "transport"),
        ("Shell Service Station", -64.0, "transport"),
        ("Netflix", -15.99, "subscriptions"),
        ("Spotify", -10.99, "subscriptions"),
        ("Disney Plus", -7.99, "subscriptions"),
        ("Salary Payroll", 3200.0, "income"),
        ("Monthly Salary", 3150.0, "income"),
        ("Savings Interest", 24.0, "income"),
    ]
    return [
        TransactionIn(
            date=date(2026, 6, 1),
            description=description,
            amount=amount,
            category=category,
        )
        for description, amount, category in rows
    ]


def test_evaluate_categorisation_model_returns_holdout_metrics() -> None:
    response = evaluate_categorisation_model(labelled_transactions(), test_size=0.33, random_state=2)

    assert response.training_rows == 8
    assert response.test_rows == 4
    assert 0 <= response.accuracy <= 1
    assert {metric.category for metric in response.per_class} == {
        "groceries",
        "income",
        "subscriptions",
        "transport",
    }
    assert len(response.confusion_matrix) == 4


def test_saved_categorisation_model_is_used_for_predictions(tmp_path) -> None:
    model_path = tmp_path / "categorisation_model.joblib"
    save_categorisation_model(labelled_transactions(), model_path)

    results = categorise_transactions(
        [
            TransactionIn(
                date=date(2026, 6, 10),
                description="Tesco Express",
                amount=-22.4,
            )
        ],
        model_path,
    )

    assert results[0].predicted_category == "groceries"
    assert results[0].confidence > 0


def test_rule_fallback_covers_common_uk_merchants() -> None:
    results = categorise_transactions(
        [
            TransactionIn(date=date(2026, 6, 10), description="Waitrose Food & Home", amount=-38.2),
            TransactionIn(date=date(2026, 6, 11), description="Virgin Media Broadband", amount=-42.0),
            TransactionIn(date=date(2026, 6, 12), description="Specsavers Opticians", amount=-89.0),
            TransactionIn(date=date(2026, 6, 13), description="Amazon Prime", amount=-8.99),
        ]
    )

    assert [result.predicted_category for result in results] == [
        "groceries",
        "utilities",
        "health",
        "subscriptions",
    ]
    assert all(result.confidence >= 0.8 for result in results)


def test_positive_merchant_refund_keeps_merchant_category() -> None:
    result = categorise_transactions(
        [
            TransactionIn(
                date=date(2026, 6, 10),
                description="Tesco Refund",
                amount=12.5,
            )
        ]
    )[0]

    assert result.predicted_category == "groceries"
    assert result.confidence < 0.8


def test_uncategorised_fallback_stays_low_confidence() -> None:
    result = categorise_transactions(
        [
            TransactionIn(
                date=date(2026, 6, 10),
                description="Unknown Card Payment",
                amount=-17.4,
            )
        ]
    )[0]

    assert result.predicted_category == "uncategorised"
    assert result.confidence < 0.4


def test_categorise_evaluate_endpoint_rejects_tiny_batches() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/categorise/evaluate",
        json={
            "transactions": [
                {
                    "date": "2026-06-01",
                    "description": "Tesco",
                    "amount": -10,
                    "category": "groceries",
                }
            ]
        },
    )

    assert response.status_code == 422
    assert "At least eight" in response.json()["detail"]
