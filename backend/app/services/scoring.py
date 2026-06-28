from __future__ import annotations

import pandas as pd

from app.schemas.transactions import (
    DerivedHealthScoreRequest,
    DerivedHealthScoreResponse,
    HealthScoreRequest,
    HealthScoreResponse,
    ScoreComponent,
    SpendingBenchmark,
    TransactionIn,
)
from app.services.cost_of_living import coicop_code_from_mapping


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def calculate_health_score(request: HealthScoreRequest) -> HealthScoreResponse:
    savings_rate = (request.monthly_income - request.monthly_spend) / request.monthly_income
    rent_ratio = request.rent_or_mortgage / request.monthly_income
    debt_ratio = request.monthly_debt_payment / request.monthly_income
    emergency_months = request.liquid_savings / max(request.monthly_spend, 1)
    subscription_ratio = request.subscriptions / request.monthly_income
    volatility_ratio = request.spend_volatility / max(request.monthly_spend, 1)

    components = [
        ScoreComponent(
            name="Savings rate",
            score=clamp(savings_rate / 0.25 * 100),
            weight=0.25,
            note="Target uses a 25 percent savings rate as full score.",
        ),
        ScoreComponent(
            name="Housing burden",
            score=clamp(100 - max(0, rent_ratio - 0.25) / 0.25 * 100),
            weight=0.2,
            note="Score declines once housing exceeds 25 percent of income.",
        ),
        ScoreComponent(
            name="Debt load",
            score=clamp(100 - debt_ratio / 0.2 * 100),
            weight=0.2,
            note="Score declines as monthly debt payments approach 20 percent of income.",
        ),
        ScoreComponent(
            name="Emergency fund",
            score=clamp(emergency_months / 6 * 100),
            weight=0.2,
            note="Six months of spending receives full score.",
        ),
        ScoreComponent(
            name="Subscription leakage",
            score=clamp(100 - subscription_ratio / 0.08 * 100),
            weight=0.075,
            note="Score declines as subscriptions approach 8 percent of income.",
        ),
        ScoreComponent(
            name="Spending volatility",
            score=clamp(100 - volatility_ratio / 0.35 * 100),
            weight=0.075,
            note="Score declines as month-to-month spend variability rises.",
        ),
    ]

    total = sum(component.score * component.weight for component in components)
    if total >= 80:
        band = "Strong"
    elif total >= 60:
        band = "Stable"
    elif total >= 40:
        band = "Watch"
    else:
        band = "At risk"

    return HealthScoreResponse(score=round(total, 1), band=band, components=components)


def transactions_frame(transactions: list[TransactionIn]) -> pd.DataFrame:
    rows = [transaction.model_dump() for transaction in transactions]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["date", "amount", "category", "month"])

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame["category"] = frame["category"].fillna("uncategorised")
    frame["month"] = frame["date"].dt.to_period("M").astype(str)
    return frame


def average_monthly_amount(frame: pd.DataFrame, mask: pd.Series) -> float:
    if frame.empty:
        return 0.0
    months = max(int(frame["month"].nunique()), 1)
    return float(frame.loc[mask, "amount"].abs().sum()) / months


def benchmark_comparisons(
    frame: pd.DataFrame,
    category_mapping: dict[str, str | None],
    benchmarks: pd.DataFrame,
) -> list[SpendingBenchmark]:
    expenses = frame.loc[frame["amount"] < 0].copy()
    if expenses.empty or benchmarks.empty:
        return []

    expenses["coicop_code"] = expenses["category"].map(category_mapping).map(coicop_code_from_mapping)
    mapped = expenses.loc[expenses["coicop_code"].notna()].copy()
    if mapped.empty:
        return []

    spend_by_code = mapped.groupby("coicop_code")["amount"].sum().abs()
    total_spend = float(spend_by_code.sum())
    results: list[SpendingBenchmark] = []

    for coicop_code, spend in spend_by_code.items():
        benchmark = benchmarks.loc[benchmarks["coicop_code"].eq(coicop_code)]
        if benchmark.empty:
            continue
        benchmark_row = benchmark.iloc[0]
        user_share = float(spend) / total_spend if total_spend else 0.0
        benchmark_share = float(benchmark_row["benchmark_share"])
        difference = (user_share - benchmark_share) * 100
        results.append(
            SpendingBenchmark(
                coicop_code=str(coicop_code),
                ons_category=str(benchmark_row["category"]),
                user_share=round(user_share, 4),
                benchmark_share=round(benchmark_share, 4),
                difference_pct_points=round(difference, 2),
                note="Positive means this budget is more concentrated than the ONS all-household benchmark.",
            )
        )

    return sorted(results, key=lambda item: abs(item.difference_pct_points), reverse=True)


def derive_health_score(
    request: DerivedHealthScoreRequest,
    category_mapping: dict[str, str | None],
    benchmarks: pd.DataFrame,
) -> DerivedHealthScoreResponse:
    frame = transactions_frame(request.transactions)
    notes: list[str] = []

    income_mask = frame["amount"] > 0
    expense_mask = frame["amount"] < 0
    monthly_income = (
        request.monthly_income
        if request.monthly_income is not None
        else average_monthly_amount(frame, income_mask)
    )
    if monthly_income <= 0:
        monthly_income = 1.0
        notes.append("Monthly income was missing, so ratios use 1.0 to avoid division by zero.")

    monthly_spend = average_monthly_amount(frame, expense_mask)
    housing_mask = expense_mask & frame["category"].isin(["housing", "rent", "mortgage"])
    rent_or_mortgage = (
        request.rent_or_mortgage
        if request.rent_or_mortgage is not None
        else average_monthly_amount(frame, housing_mask)
    )
    subscriptions = average_monthly_amount(frame, expense_mask & frame["category"].eq("subscriptions"))

    monthly_totals = frame.loc[expense_mask].groupby("month")["amount"].sum().abs()
    spend_volatility = float(monthly_totals.std(ddof=0)) if len(monthly_totals) > 1 else 0.0

    score_request = HealthScoreRequest(
        monthly_income=monthly_income,
        monthly_spend=monthly_spend,
        rent_or_mortgage=rent_or_mortgage,
        monthly_debt_payment=request.monthly_debt_payment,
        liquid_savings=request.liquid_savings,
        subscriptions=subscriptions,
        spend_volatility=spend_volatility,
    )
    score = calculate_health_score(score_request)

    savings_rate = (monthly_income - monthly_spend) / monthly_income
    rent_to_income = rent_or_mortgage / monthly_income
    emergency_fund_months = request.liquid_savings / max(monthly_spend, 1)

    return DerivedHealthScoreResponse(
        score=score.score,
        band=score.band,
        components=score.components,
        monthly_income=round(monthly_income, 2),
        monthly_spend=round(monthly_spend, 2),
        savings_rate=round(savings_rate, 4),
        rent_to_income=round(rent_to_income, 4),
        emergency_fund_months=round(emergency_fund_months, 2),
        spending_volatility=round(spend_volatility, 2),
        benchmarks=benchmark_comparisons(frame, category_mapping, benchmarks),
        notes=notes,
    )
