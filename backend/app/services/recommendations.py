from __future__ import annotations

from app.schemas.transactions import (
    DerivedHealthScoreResponse,
    ForecastPoint,
    ForecastResponse,
    PersonalInflationCategory,
    PersonalInflationResponse,
    RateImpactResponse,
    Recommendation,
    RecommendationsResponse,
)


def priority_rank(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


def weakest_score_component(health_score: DerivedHealthScoreResponse) -> str | None:
    if not health_score.components:
        return None
    return min(health_score.components, key=lambda component: component.score).name


def top_inflation_pressure(response: PersonalInflationResponse) -> PersonalInflationCategory | None:
    mapped = [
        category
        for category in response.categories
        if category.annual_change_pct is not None and category.contribution_pct_points is not None
    ]
    if not mapped:
        return None
    return max(mapped, key=lambda category: abs(category.contribution_pct_points or 0))


def highest_forecast_pressure(forecast: ForecastResponse) -> ForecastPoint | None:
    if not forecast.forecasts:
        return None
    return max(forecast.forecasts, key=lambda point: point.upper_bound)


def add_recommendation(
    recommendations: list[Recommendation],
    title: str,
    detail: str,
    action: str,
    priority: str,
    source: str,
) -> None:
    recommendations.append(
        Recommendation(
            title=title,
            detail=detail,
            action=action,
            priority=priority,
            source=source,
        )
    )


def recommendations_from_health(
    recommendations: list[Recommendation],
    health_score: DerivedHealthScoreResponse,
) -> None:
    if health_score.emergency_fund_months < 3:
        add_recommendation(
            recommendations,
            title="Build the emergency buffer first",
            detail=f"Emergency savings cover {health_score.emergency_fund_months:.1f} months of spend.",
            action="Move a fixed amount to savings after payday until this reaches three months.",
            priority="high",
            source="Health score",
        )

    if health_score.rent_to_income >= 0.35:
        add_recommendation(
            recommendations,
            title="Check the housing burden",
            detail=f"Housing is {health_score.rent_to_income * 100:.0f}% of monthly income.",
            action="Review rent, mortgage, council tax, and utility costs before adding new commitments.",
            priority="high",
            source="Health score",
        )

    weakest = weakest_score_component(health_score)
    if weakest and weakest not in {"Emergency fund", "Housing burden"}:
        add_recommendation(
            recommendations,
            title=f"Target {weakest.lower()}",
            detail=f"{weakest} is the lowest-scoring part of the financial-health score.",
            action="Use this as the first category to inspect when reviewing the budget.",
            priority="medium",
            source="Health score",
        )


def recommendations_from_inflation(
    recommendations: list[Recommendation],
    personal_inflation: PersonalInflationResponse,
) -> None:
    pressure = top_inflation_pressure(personal_inflation)
    if pressure is None:
        return

    if personal_inflation.difference_pct_points > 0.5:
        add_recommendation(
            recommendations,
            title="Focus on the category lifting personal inflation",
            detail=(
                f"Personal inflation is {personal_inflation.difference_pct_points:.1f} percentage points "
                f"above the UK rate, led by {pressure.app_category}."
            ),
            action="Set a monthly check on that category before cutting lower-impact spending.",
            priority="medium",
            source="Inflation",
        )


def recommendations_from_forecast(
    recommendations: list[Recommendation],
    forecast: ForecastResponse,
) -> None:
    pressure = highest_forecast_pressure(forecast)
    if pressure is None:
        return

    if pressure.upper_bound >= pressure.expected_spend * 1.1 and pressure.expected_spend > 0:
        add_recommendation(
            recommendations,
            title=f"Set a guardrail for {pressure.category}",
            detail=(
                f"The {forecast.period} forecast is GBP {pressure.expected_spend:.0f}, "
                f"with an upper estimate of GBP {pressure.upper_bound:.0f}."
            ),
            action="Use the upper estimate as an alert level for next month.",
            priority="medium",
            source="Forecast",
        )


def recommendations_from_rate_impact(
    recommendations: list[Recommendation],
    rate_impact: RateImpactResponse,
) -> None:
    if rate_impact.monthly_net_cashflow_delta <= -20:
        add_recommendation(
            recommendations,
            title="Stress-test the rate scenario",
            detail=f"The Bank Rate scenario changes cash flow by GBP {rate_impact.monthly_net_cashflow_delta:.0f} per month.",
            action="Keep this monthly impact in the buffer before taking on new variable-rate debt.",
            priority="medium",
            source="Rate impact",
        )


def generate_recommendations(
    forecast: ForecastResponse | None = None,
    personal_inflation: PersonalInflationResponse | None = None,
    health_score: DerivedHealthScoreResponse | None = None,
    rate_impact: RateImpactResponse | None = None,
) -> RecommendationsResponse:
    recommendations: list[Recommendation] = []

    if health_score is not None:
        recommendations_from_health(recommendations, health_score)
    if personal_inflation is not None:
        recommendations_from_inflation(recommendations, personal_inflation)
    if forecast is not None:
        recommendations_from_forecast(recommendations, forecast)
    if rate_impact is not None:
        recommendations_from_rate_impact(recommendations, rate_impact)

    if not recommendations:
        add_recommendation(
            recommendations,
            title="Keep the monthly review habit",
            detail="No urgent pressure point stands out from the current analysis.",
            action="Review the forecast and health score again after the next upload.",
            priority="low",
            source="Overall",
        )

    recommendations.sort(key=lambda item: (priority_rank(item.priority), item.title))
    return RecommendationsResponse(recommendations=recommendations[:5])
