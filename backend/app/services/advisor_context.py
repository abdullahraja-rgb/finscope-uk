from __future__ import annotations

import math

from app.schemas.transactions import (
    AdvisorContextRequest,
    AdvisorContextResponse,
    AdvisorContextSection,
    AdvisorFact,
    AdvisorMissingData,
    AdvisorProfile,
    ForecastPoint,
    PersonalInflationCategory,
    Recommendation,
    TransactionIn,
)


GUARDRAILS = [
    "Use only the facts and numbers in this context pack.",
    "If a number is missing, say what is missing instead of estimating it.",
    "Give budgeting guidance, not regulated financial advice.",
    "Do not recommend specific investments, credit products, or providers.",
    "Cite the source label beside any important claim.",
]

SOURCE_MAP = {
    "profile": "Financial setup values entered in the app.",
    "transactions": "Uploaded or manually entered transaction rows.",
    "health_score": "Backend financial-health score derived from transactions and setup values.",
    "forecast": "Backend spend forecast and rolling backtest output.",
    "inflation": "Personal inflation engine using category spend and ONS category mapping.",
    "rate_impact": "Bank Rate scenario engine.",
    "recommendations": "Deterministic recommendation rules.",
}

SOURCE_LABELS = {
    "profile": "financial setup",
    "transactions": "transaction analysis",
    "health_score": "financial health calculation",
    "forecast": "spending forecast",
    "inflation": "personal inflation calculation",
    "rate_impact": "Bank Rate scenario",
    "recommendations": "dashboard recommendations",
}


def format_gbp(value: float | None) -> str:
    if value is None:
        return "not available"
    return f"GBP {round(value):,}"


def format_percent(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "not available"
    return f"{value:.{digits}f}%"


def format_months(months: int | None) -> str:
    if months is None:
        return "not available"
    if months <= 0:
        return "cleared"
    years = months // 12
    remaining = months % 12
    if years == 0:
        return f"{remaining} months"
    if remaining == 0:
        return f"{years} years"
    return f"{years} years {remaining} months"


def round_value(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def fact(
    fact_id: str,
    label: str,
    value: float | str | bool | None,
    formatted: str,
    source: str,
    unit: str | None = None,
) -> AdvisorFact:
    return AdvisorFact(
        id=fact_id,
        label=label,
        value=value,
        formatted=formatted,
        source=source,
        citation=source,
        unit=unit,
    )


def has_profile_values(profile: AdvisorProfile | None) -> bool:
    if profile is None:
        return False
    return any(
        [
            profile.monthly_income,
            profile.rent_or_mortgage,
            profile.monthly_debt_payment,
            profile.liquid_savings,
            profile.investment_balance,
            profile.pension_balance,
            profile.property_value,
            profile.mortgage_balance,
            profile.credit_card_balance,
            profile.loan_balance,
            profile.average_debt_apr,
            profile.emergency_fund_target,
            profile.savings_goal_target,
            profile.monthly_goal_contribution,
        ]
    )


def spend_by_category(transactions: list[TransactionIn]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for transaction in transactions:
        if transaction.amount >= 0 or transaction.transaction_type == "transfer":
            continue
        category = transaction.category or "uncategorised"
        totals[category] = totals.get(category, 0.0) + abs(float(transaction.amount))
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def transaction_month_count(transactions: list[TransactionIn]) -> int:
    return len({transaction.date.strftime("%Y-%m") for transaction in transactions})


def payoff_months(balance: float, monthly_payment: float, apr: float) -> int | None:
    if balance <= 0:
        return 0
    if monthly_payment <= 0:
        return None

    monthly_rate = max(apr, 0) / 100 / 12
    if monthly_rate == 0:
        return math.ceil(balance / monthly_payment)
    if monthly_payment <= balance * monthly_rate:
        return None
    return math.ceil(-math.log(1 - (monthly_rate * balance) / monthly_payment) / math.log(1 + monthly_rate))


def top_forecast_point(request: AdvisorContextRequest) -> ForecastPoint | None:
    if request.forecast is None or not request.forecast.forecasts:
        return None
    return max(request.forecast.forecasts, key=lambda point: point.expected_spend)


def top_inflation_category(request: AdvisorContextRequest) -> PersonalInflationCategory | None:
    if request.personal_inflation is None:
        return None
    mapped = [
        category
        for category in request.personal_inflation.categories
        if category.contribution_pct_points is not None
    ]
    if not mapped:
        return None
    return max(mapped, key=lambda category: abs(category.contribution_pct_points or 0))


def section(section_id: str, title: str, facts: list[AdvisorFact], notes: list[str] | None = None) -> AdvisorContextSection:
    return AdvisorContextSection(id=section_id, title=title, facts=facts, notes=notes or [])


def cash_flow_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    profile = request.profile
    health = request.health_score
    income = health.monthly_income if health else profile.monthly_income if profile else 0
    spend = health.monthly_spend if health else 0
    disposable = income - spend if income or spend else None
    facts = [
        fact("monthly_income", "Monthly income", round_value(income), format_gbp(income), "health_score" if health else "profile", "GBP"),
        fact("monthly_spend", "Monthly spend", round_value(spend), format_gbp(spend), "health_score" if health else "transactions", "GBP"),
    ]
    if disposable is not None:
        facts.append(fact("disposable_income", "Disposable income", round_value(disposable), format_gbp(disposable), "health_score", "GBP"))
    if health:
        facts.extend(
            [
                fact("savings_rate", "Savings rate", round_value(health.savings_rate * 100), format_percent(health.savings_rate * 100), "health_score", "percent"),
                fact("rent_to_income", "Housing to income", round_value(health.rent_to_income * 100), format_percent(health.rent_to_income * 100), "health_score", "percent"),
                fact("emergency_fund_months", "Emergency fund cover", round_value(health.emergency_fund_months), f"{health.emergency_fund_months:.1f} months", "health_score", "months"),
            ]
        )
    return section("cash_flow", "Cash Flow", facts)


def health_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    health = request.health_score
    if health is None:
        return section("health", "Financial Health", [], ["No health score has been supplied yet."])

    facts = [
        fact("health_score", "Health score", round_value(health.score), f"{health.score:.0f}", "health_score"),
        fact("health_band", "Health band", health.band, health.band, "health_score"),
    ]
    if health.components:
        weakest = min(health.components, key=lambda component: component.score)
        facts.append(
            fact(
                "weakest_health_component",
                "Weakest score component",
                weakest.name,
                f"{weakest.name}: {weakest.score:.0f}",
                "health_score",
            )
        )
    return section("health", "Financial Health", facts, health.notes)


def transaction_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    totals = spend_by_category(request.transactions)
    facts = [
        fact("transaction_rows", "Transaction rows", len(request.transactions), str(len(request.transactions)), "transactions"),
        fact("transaction_months", "Transaction months", transaction_month_count(request.transactions), str(transaction_month_count(request.transactions)), "transactions"),
    ]
    for index, (category, spend) in enumerate(list(totals.items())[:5], start=1):
        facts.append(
            fact(
                f"top_spend_category_{index}",
                f"Top spend category {index}",
                round_value(spend),
                f"{category}: {format_gbp(spend)}",
                "transactions",
                "GBP",
            )
        )
    return section("transactions", "Transaction Coverage", facts)


def forecast_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    forecast = request.forecast
    if forecast is None:
        return section("forecast", "Forecast", [], ["No forecast has been supplied yet."])
    top_point = top_forecast_point(request)
    expected_total = sum(point.expected_spend for point in forecast.forecasts)
    upper_total = sum(point.upper_bound for point in forecast.forecasts)
    facts = [
        fact("forecast_period", "Forecast period", forecast.period, forecast.period, "forecast"),
        fact("forecast_months_used", "Months used", forecast.generated_from_months, str(forecast.generated_from_months), "forecast"),
        fact("forecast_expected_total", "Expected forecast spend", round_value(expected_total), format_gbp(expected_total), "forecast", "GBP"),
        fact("forecast_upper_total", "Upper forecast spend", round_value(upper_total), format_gbp(upper_total), "forecast", "GBP"),
    ]
    if top_point:
        facts.append(
            fact(
                "largest_forecast_category",
                "Largest forecast category",
                top_point.category,
                f"{top_point.category}: {format_gbp(top_point.expected_spend)} expected, {format_gbp(top_point.upper_bound)} upper estimate",
                "forecast",
            )
        )
    return section("forecast", "Forecast", facts, forecast.notes)


def inflation_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    inflation = request.personal_inflation
    if inflation is None:
        return section("inflation", "Cost Of Living", [], ["No personal inflation result has been supplied yet."])
    top_category = top_inflation_category(request)
    facts = [
        fact("inflation_period", "Inflation period", inflation.period, inflation.period, "inflation"),
        fact("personal_inflation", "Personal inflation", inflation.personal_inflation_pct, format_percent(inflation.personal_inflation_pct), "inflation", "percent"),
        fact("national_inflation", "UK inflation", inflation.national_inflation_pct, format_percent(inflation.national_inflation_pct), "inflation", "percent"),
        fact("inflation_gap", "Personal inflation gap", inflation.difference_pct_points, f"{inflation.difference_pct_points:+.1f} percentage points", "inflation", "percentage points"),
    ]
    if top_category:
        facts.append(
            fact(
                "largest_inflation_contributor",
                "Largest inflation contributor",
                top_category.app_category,
                f"{top_category.app_category}: {top_category.contribution_pct_points:.2f} percentage points",
                "inflation",
                "percentage points",
            )
        )
    return section("inflation", "Cost Of Living", facts, inflation.notes)


def rate_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    impact = request.rate_impact
    if impact is None:
        return section("rate_impact", "Rate Impact", [], ["No Bank Rate impact result has been supplied yet."])
    facts = [
        fact("current_bank_rate", "Current Bank Rate", impact.current_bank_rate_pct, format_percent(impact.current_bank_rate_pct), "rate_impact", "percent"),
        fact("scenario_bank_rate", "Scenario Bank Rate", impact.scenario_bank_rate_pct, format_percent(impact.scenario_bank_rate_pct), "rate_impact", "percent"),
        fact("monthly_rate_cashflow_delta", "Monthly rate cash-flow change", impact.monthly_net_cashflow_delta, format_gbp(impact.monthly_net_cashflow_delta), "rate_impact", "GBP"),
    ]
    for line in impact.lines:
        facts.append(
            fact(
                f"rate_line_{line.name.lower().replace(' ', '_')}",
                line.name,
                line.monthly_delta,
                f"{line.name}: {format_gbp(line.monthly_delta)} per month",
                "rate_impact",
                "GBP",
            )
        )
    return section("rate_impact", "Rate Impact", facts, impact.notes)


def wealth_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    profile = request.profile
    if profile is None:
        return section("wealth", "Net Worth, Debt, And Goals", [], ["No profile setup has been supplied yet."])

    total_assets = profile.liquid_savings + profile.investment_balance + profile.pension_balance + profile.property_value
    consumer_debt = profile.credit_card_balance + profile.loan_balance
    total_liabilities = profile.mortgage_balance + consumer_debt
    net_worth = total_assets - total_liabilities
    emergency_gap = max(profile.emergency_fund_target - profile.liquid_savings, 0)
    available_for_goal = max(profile.liquid_savings - profile.emergency_fund_target, 0)
    goal_gap = max(profile.savings_goal_target - available_for_goal, 0)
    months_to_emergency = (
        0
        if emergency_gap <= 0
        else math.ceil(emergency_gap / profile.monthly_goal_contribution)
        if profile.monthly_goal_contribution > 0
        else None
    )
    months_to_goal = (
        0
        if goal_gap <= 0
        else math.ceil(goal_gap / profile.monthly_goal_contribution)
        if profile.monthly_goal_contribution > 0
        else None
    )
    payoff = payoff_months(consumer_debt, profile.monthly_debt_payment, profile.average_debt_apr)

    facts = [
        fact("total_assets", "Total assets", round_value(total_assets), format_gbp(total_assets), "profile", "GBP"),
        fact("total_liabilities", "Total liabilities", round_value(total_liabilities), format_gbp(total_liabilities), "profile", "GBP"),
        fact("net_worth", "Net worth", round_value(net_worth), format_gbp(net_worth), "profile", "GBP"),
        fact("consumer_debt", "Consumer debt", round_value(consumer_debt), format_gbp(consumer_debt), "profile", "GBP"),
        fact("debt_payoff_time", "Debt payoff time", payoff, format_months(payoff), "profile", "months"),
        fact("emergency_gap", "Emergency fund gap", round_value(emergency_gap), format_gbp(emergency_gap), "profile", "GBP"),
        fact("months_to_emergency", "Months to emergency target", months_to_emergency, format_months(months_to_emergency), "profile", "months"),
        fact("savings_goal_gap", "Savings goal gap", round_value(goal_gap), format_gbp(goal_gap), "profile", "GBP"),
        fact("months_to_savings_goal", "Months to savings goal", months_to_goal, format_months(months_to_goal), "profile", "months"),
    ]
    return section("wealth", "Net Worth, Debt, And Goals", facts)


def recommendation_section(request: AdvisorContextRequest) -> AdvisorContextSection:
    facts = []
    for index, item in enumerate(request.recommendations[:5], start=1):
        facts.append(recommendation_fact(index, item))
    return section("recommendations", "Recommendations", facts)


def recommendation_fact(index: int, item: Recommendation) -> AdvisorFact:
    return fact(
        f"recommendation_{index}",
        f"Recommendation {index}",
        item.title,
        f"{item.title} ({item.priority}): {item.action}",
        "recommendations",
    )


def missing_data(request: AdvisorContextRequest) -> list[AdvisorMissingData]:
    missing: list[AdvisorMissingData] = []
    profile = request.profile

    if not has_profile_values(profile):
        missing.append(
            AdvisorMissingData(
                key="profile",
                label="Financial setup",
                reason="No profile setup values were supplied.",
                impact="Net worth, debt payoff, savings goals, and some cash-flow explanations will be thin.",
                action="Fill in the Profile setup page.",
            )
        )
    if profile is None or profile.monthly_income <= 0:
        missing.append(
            AdvisorMissingData(
                key="monthly_income",
                label="Monthly income",
                reason="Monthly income is not set.",
                impact="Spend-to-income, savings rate, and disposable income are less useful.",
                action="Add monthly income in Profile setup.",
            )
        )
    if not request.transactions:
        missing.append(
            AdvisorMissingData(
                key="transactions",
                label="Transaction rows",
                reason="No transaction rows were supplied.",
                impact="The advisor cannot explain spending mix, forecasts, or personal inflation properly.",
                action="Upload a CSV or add transaction rows manually.",
            )
        )
    else:
        categories = {
            transaction.category
            for transaction in request.transactions
            if transaction.amount < 0 and transaction.transaction_type != "transfer"
        }
        for category in ["groceries", "transport", "utilities", "housing", "subscriptions"]:
            if category not in categories:
                missing.append(
                    AdvisorMissingData(
                        key=f"category_{category}",
                        label=f"{category.replace('_', ' ').title()} spending",
                        reason=f"No {category.replace('_', ' ')} expense rows were found.",
                        impact="Some category-level explanations may miss this part of the budget.",
                        action=f"Add a {category.replace('_', ' ')} transaction row if this spending exists.",
                    )
                )
    if request.forecast is None or not request.forecast.forecasts:
        missing.append(
            AdvisorMissingData(
                key="forecast",
                label="Forecast",
                reason="No forecast output was supplied.",
                impact="The advisor cannot explain next-month pressure.",
                action="Analyse enough transaction history to generate a forecast.",
            )
        )
    if request.personal_inflation is None:
        missing.append(
            AdvisorMissingData(
                key="personal_inflation",
                label="Personal inflation",
                reason="No personal inflation output was supplied.",
                impact="The advisor cannot compare personal inflation against the UK figure.",
                action="Run the transaction analysis with mapped spending categories.",
            )
        )
    if request.health_score is None:
        missing.append(
            AdvisorMissingData(
                key="health_score",
                label="Health score",
                reason="No health score output was supplied.",
                impact="The advisor cannot explain the strongest and weakest score components.",
                action="Run the transaction analysis with profile values.",
            )
        )
    if request.rate_impact is None:
        missing.append(
            AdvisorMissingData(
                key="rate_impact",
                label="Bank Rate impact",
                reason="No rate-impact output was supplied.",
                impact="The advisor cannot explain interest-rate sensitivity.",
                action="Run the Bank Rate scenario calculation.",
            )
        )
    return missing


def allowed_numbers(sections: list[AdvisorContextSection]) -> list[str]:
    numbers = []
    for item in sections:
        for item_fact in item.facts:
            if isinstance(item_fact.value, (int, float)):
                numbers.append(f"{item_fact.label}: {item_fact.formatted}")
    return numbers


def context_markdown(
    sections: list[AdvisorContextSection],
    missing: list[AdvisorMissingData],
    guardrails: list[str],
) -> str:
    lines = ["# Advisor Context Pack", "", "## Guardrails"]
    lines.extend(f"- {item}" for item in guardrails)
    lines.append("")

    for item in sections:
        lines.append(f"## {item.title}")
        if item.facts:
            lines.extend(
                f"- {item_fact.label}: {item_fact.formatted} (from {SOURCE_LABELS.get(item_fact.source, 'the dashboard')})"
                for item_fact in item.facts
            )
        else:
            lines.append("- No facts supplied.")
        for note in item.notes:
            lines.append(f"- Note: {note}")
        lines.append("")

    lines.append("## Missing Data")
    if missing:
        lines.extend(f"- {item.label}: {item.impact} Action: {item.action}" for item in missing)
    else:
        lines.append("- No major missing data flagged.")
    return "\n".join(lines).strip()


def build_advisor_context(request: AdvisorContextRequest) -> AdvisorContextResponse:
    sections = [
        cash_flow_section(request),
        health_section(request),
        transaction_section(request),
        forecast_section(request),
        inflation_section(request),
        rate_section(request),
        wealth_section(request),
        recommendation_section(request),
    ]
    missing = missing_data(request)

    return AdvisorContextResponse(
        context_markdown=context_markdown(sections, missing, GUARDRAILS),
        sections=sections,
        missing_data=missing,
        allowed_numbers=allowed_numbers(sections),
        source_map=SOURCE_MAP,
        guardrails=GUARDRAILS,
    )
