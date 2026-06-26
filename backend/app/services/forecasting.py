from collections import defaultdict
from datetime import date

from app.schemas.transactions import ForecastPoint, ForecastResponse, TransactionIn


def forecast_next_month(transactions: list[TransactionIn]) -> ForecastResponse:
    monthly_by_category: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        month_key = transaction.date.strftime("%Y-%m")
        category = transaction.category or "uncategorised"
        monthly_by_category[category][month_key] += abs(transaction.amount)

    forecasts: list[ForecastPoint] = []
    for category, monthly_values in sorted(monthly_by_category.items()):
        values = list(monthly_values.values())
        if not values:
            continue
        expected = sum(values[-3:]) / min(len(values), 3)
        forecasts.append(
            ForecastPoint(
                category=category,
                expected_spend=round(expected, 2),
                lower_bound=round(expected * 0.85, 2),
                upper_bound=round(expected * 1.15, 2),
            )
        )

    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1

    return ForecastResponse(
        period=f"{next_year:04d}-{next_month:02d}",
        forecasts=forecasts,
        baseline="three-month moving average",
    )
