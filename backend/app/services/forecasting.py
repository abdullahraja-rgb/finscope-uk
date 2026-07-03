from __future__ import annotations

import math
from datetime import date
from typing import Callable

import numpy as np
import pandas as pd

from app.schemas.transactions import (
    ForecastBacktestResponse,
    ForecastMetric,
    ForecastPoint,
    ForecastResponse,
    TransactionIn,
)

BASELINE_MODEL = "last-month naive"
MOVING_AVERAGE_MODEL = "three-month moving average"
TREND_MODEL = "six-month trend regression"
SEASONAL_MODEL = "seasonal naive"
CANDIDATE_MODELS = [MOVING_AVERAGE_MODEL, TREND_MODEL, SEASONAL_MODEL]


def monthly_spend_frame(transactions: list[TransactionIn]) -> pd.DataFrame:
    rows = []
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        rows.append(
            {
                "month": pd.Period(transaction.date, freq="M"),
                "category": transaction.category or "uncategorised",
                "spend": abs(float(transaction.amount)),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["category", "month", "spend"])

    frame = pd.DataFrame(rows)
    grouped = frame.groupby(["category", "month"], as_index=False)["spend"].sum()
    all_months = pd.period_range(grouped["month"].min(), grouped["month"].max(), freq="M")

    complete_rows = []
    for category, category_frame in grouped.groupby("category"):
        monthly = category_frame.set_index("month")["spend"].reindex(all_months, fill_value=0)
        for month, spend in monthly.items():
            complete_rows.append({"category": category, "month": month, "spend": float(spend)})

    return pd.DataFrame(complete_rows)


def monthly_series_by_category(transactions: list[TransactionIn]) -> dict[str, pd.Series]:
    frame = monthly_spend_frame(transactions)
    if frame.empty:
        return {}

    return {
        category: category_frame.sort_values("month").set_index("month")["spend"]
        for category, category_frame in frame.groupby("category")
    }


def next_forecast_period(series_by_category: dict[str, pd.Series]) -> str:
    periods = [series.index.max() for series in series_by_category.values() if not series.empty]
    if not periods:
        today = date.today()
        current = pd.Period(today, freq="M")
        return str(current + 1)
    return str(max(periods) + 1)


def last_month_naive(values: list[float]) -> float:
    return float(values[-1]) if values else 0.0


def moving_average(values: list[float], window: int = 3) -> float:
    if not values:
        return 0.0
    recent = values[-window:]
    return float(sum(recent) / len(recent))


def trend_regression(values: list[float], lookback: int = 6) -> float:
    if len(values) < 2:
        return moving_average(values)

    recent = np.array(values[-lookback:], dtype=float)
    x_values = np.arange(len(recent), dtype=float)
    slope, intercept = np.polyfit(x_values, recent, 1)
    forecast = intercept + slope * len(recent)
    return float(max(forecast, 0))


def seasonal_naive(values: list[float], season_length: int = 12) -> float:
    if len(values) >= season_length:
        return float(values[-season_length])
    return moving_average(values)


FORECASTERS: dict[str, Callable[[list[float]], float]] = {
    BASELINE_MODEL: last_month_naive,
    MOVING_AVERAGE_MODEL: moving_average,
    TREND_MODEL: trend_regression,
    SEASONAL_MODEL: seasonal_naive,
}


def backtest_predictions(
    values: list[float],
    model_name: str,
    min_train_months: int,
) -> list[tuple[float, float]]:
    if len(values) <= min_train_months:
        return []

    forecaster = FORECASTERS[model_name]
    predictions = []
    for split_index in range(min_train_months, len(values)):
        train_values = values[:split_index]
        actual = float(values[split_index])
        predicted = max(float(forecaster(train_values)), 0.0)
        predictions.append((actual, predicted))
    return predictions


def error_metrics(predictions: list[tuple[float, float]]) -> tuple[float, float, float | None]:
    if not predictions:
        return 0.0, 0.0, None

    absolute_errors = [abs(actual - predicted) for actual, predicted in predictions]
    squared_errors = [(actual - predicted) ** 2 for actual, predicted in predictions]
    percentage_errors = [
        abs(actual - predicted) / actual for actual, predicted in predictions if actual > 0
    ]

    mae = sum(absolute_errors) / len(absolute_errors)
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    mape = sum(percentage_errors) / len(percentage_errors) if percentage_errors else None
    return mae, rmse, mape


def metric_for_model(
    category: str,
    values: list[float],
    model_name: str,
    min_train_months: int,
) -> tuple[ForecastMetric | None, list[tuple[float, float]]]:
    predictions = backtest_predictions(values, model_name, min_train_months)
    baseline_predictions = backtest_predictions(values, BASELINE_MODEL, min_train_months)
    if not predictions or not baseline_predictions:
        return None, predictions

    mae, rmse, mape = error_metrics(predictions)
    baseline_mae, _, _ = error_metrics(baseline_predictions)

    return (
        ForecastMetric(
            category=category,
            model=model_name,
            baseline=BASELINE_MODEL,
            windows=len(predictions),
            mae=round(mae, 2),
            rmse=round(rmse, 2),
            mape=round(mape, 4) if mape is not None else None,
            baseline_mae=round(baseline_mae, 2),
            beats_baseline=mae < baseline_mae,
        ),
        predictions,
    )


def best_model_for_series(
    category: str,
    series: pd.Series,
    min_train_months: int,
) -> tuple[str, ForecastMetric | None, list[tuple[float, float]]]:
    values = [float(value) for value in series.tolist()]
    scored_models = []

    for model_name in CANDIDATE_MODELS:
        metric, predictions = metric_for_model(category, values, model_name, min_train_months)
        if metric is not None:
            scored_models.append((metric, predictions))

    if not scored_models:
        return MOVING_AVERAGE_MODEL, None, []

    metric, predictions = min(scored_models, key=lambda item: item[0].mae)
    return metric.model, metric, predictions


def prediction_interval(
    expected: float,
    predictions: list[tuple[float, float]],
) -> tuple[float, float, float]:
    if predictions:
        residuals = [actual - predicted for actual, predicted in predictions]
        mean_error = sum(residuals) / len(residuals)
        variance = sum((error - mean_error) ** 2 for error in residuals) / len(residuals)
        margin = max(abs(mean_error), 1.96 * math.sqrt(variance), 5.0)
    else:
        margin = max(expected * 0.25, 15.0)

    lower = max(expected - margin, 0.0)
    upper = expected + margin
    return round(lower, 2), round(upper, 2), round(margin, 2)


def forecast_next_month(transactions: list[TransactionIn]) -> ForecastResponse:
    series_by_category = monthly_series_by_category(transactions)
    period = next_forecast_period(series_by_category)
    if not series_by_category:
        return ForecastResponse(
            period=period,
            forecasts=[],
            baseline=BASELINE_MODEL,
            notes=["No expense transactions were available for forecasting."],
        )

    forecasts: list[ForecastPoint] = []
    used_fallback_interval = False
    for category, series in sorted(series_by_category.items()):
        values = [float(value) for value in series.tolist()]
        model_name, metric, predictions = best_model_for_series(category, series, min_train_months=4)
        expected = max(FORECASTERS[model_name](values), 0.0)
        baseline_expected = max(last_month_naive(values), 0.0)
        lower, upper, margin = prediction_interval(expected, predictions)
        used_fallback_interval = used_fallback_interval or metric is None

        forecasts.append(
            ForecastPoint(
                category=category,
                expected_spend=round(expected, 2),
                lower_bound=lower,
                upper_bound=upper,
                model=model_name,
                baseline_expected_spend=round(baseline_expected, 2),
                error_margin=margin,
                backtest_mae=metric.mae if metric else None,
                baseline_mae=metric.baseline_mae if metric else None,
                beats_baseline=metric.beats_baseline if metric else None,
            )
        )

    forecasts.sort(key=lambda item: item.expected_spend, reverse=True)
    month_count = max(len(series.index) for series in series_by_category.values())
    notes = [
        "Forecasts are based only on earlier months in each rolling backtest window.",
        "Intervals use backtest residuals where available and a simple fallback margin otherwise.",
    ]
    if used_fallback_interval:
        notes.append("Some categories have too little history for backtesting, so their intervals are deliberately wider.")

    return ForecastResponse(
        period=period,
        forecasts=forecasts,
        baseline=BASELINE_MODEL,
        generated_from_months=month_count,
        notes=notes,
    )


def backtest_forecasts(
    transactions: list[TransactionIn],
    min_train_months: int = 4,
) -> ForecastBacktestResponse:
    series_by_category = monthly_series_by_category(transactions)
    metrics: list[ForecastMetric] = []

    for category, series in sorted(series_by_category.items()):
        values = [float(value) for value in series.tolist()]
        for model_name in CANDIDATE_MODELS:
            metric, _ = metric_for_model(category, values, model_name, min_train_months)
            if metric is not None:
                metrics.append(metric)

    notes = []
    if not metrics:
        notes.append("Not enough monthly history for rolling backtests.")
    else:
        notes.append("Each backtest window trains on past months and predicts the next month.")

    return ForecastBacktestResponse(
        baseline=BASELINE_MODEL,
        candidate_models=CANDIDATE_MODELS,
        metrics=metrics,
        notes=notes,
    )
