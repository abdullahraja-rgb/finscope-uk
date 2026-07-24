from __future__ import annotations

from dataclasses import dataclass

from app.services.advisor_retrieval import tokenize


# When a question does not clearly map to any section, fall back to this order so
# the advisor still answers with the most broadly useful facts first.
DEFAULT_SECTION_ORDER = [
    "cash_flow",
    "health",
    "forecast",
    "inflation",
    "rate_impact",
    "wealth",
]


# Keywords are weighted by how strongly they identify a section. Defining terms
# ("ons", "predict") must outrank generic ones ("spending") that appear in many
# kinds of question - the eval harness showed unweighted overlap misrouting
# "map my spending to ONS categories" and "predict my spending" to cash flow.
CORE_WEIGHT = 2.0
SUPPORT_WEIGHT = 1.0

SECTION_CORE_KEYWORDS: dict[str, set[str]] = {
    "cash_flow": {
        "cash", "flow", "disposable", "surplus", "deficit", "outgoings",
        "income", "salary", "wage", "wages",
    },
    "health": {"health", "score", "band", "wellbeing", "rating"},
    "transactions": {
        "transaction", "transactions", "merchant",
        "categorise", "categorised", "categorisation",
    },
    "forecast": {
        "forecast", "forecasts", "forecasting", "predict", "prediction",
        "projected", "projection", "estimate",
    },
    "inflation": {"inflation", "cpi", "cpih", "ons", "basket"},
    "rate_impact": {"rate", "rates", "interest", "boe", "mortgage", "tracker"},
    "wealth": {
        "worth", "wealth", "assets", "asset", "liabilities", "debt", "debts",
        "loan", "loans", "pension", "payoff", "repay", "borrowing",
    },
    "recommendations": {
        "recommendation", "recommendations", "recommend",
        "advice", "advise", "suggest", "suggestion",
    },
}

SECTION_SUPPORT_KEYWORDS: dict[str, set[str]] = {
    "cash_flow": {
        "spend", "spending", "expenses", "budget", "pay", "paid",
        "leftover", "left", "afford", "affordable",
    },
    "health": {"overall", "strong", "strongest", "weak", "weakest", "component", "components"},
    "transactions": {
        "category", "categories", "breakdown", "biggest", "largest", "top", "where", "most",
    },
    "forecast": {"next", "upcoming", "future", "month", "coming", "expected"},
    "inflation": {"cost", "living", "prices", "price", "national", "personal", "rising", "dearer"},
    "rate_impact": {"bank", "base", "variable", "hike", "hikes", "cut", "cuts", "rise"},
    "wealth": {
        "net", "credit", "card", "emergency", "fund", "buffer", "goal", "goals",
        "investment", "investments", "savings", "saving",
    },
    "recommendations": {
        "action", "actions", "fix", "improve", "priority", "prioritise", "focus", "step", "steps",
    },
}

# Combined view, useful for inspection and tests.
SECTION_KEYWORDS: dict[str, set[str]] = {
    section_id: SECTION_CORE_KEYWORDS[section_id] | SECTION_SUPPORT_KEYWORDS[section_id]
    for section_id in SECTION_CORE_KEYWORDS
}


# Ordered fact ids to surface per section, most explanatory first. Facts that do
# not exist for a given user are skipped by the selector.
SECTION_FACT_PRIORITY: dict[str, list[str]] = {
    "cash_flow": [
        "monthly_income", "monthly_spend", "disposable_income",
        "savings_rate", "rent_to_income", "emergency_fund_months",
    ],
    "health": ["health_score", "health_band", "weakest_health_component"],
    "transactions": [
        "top_spend_category_1", "top_spend_category_2", "top_spend_category_3",
        "transaction_months", "transaction_rows",
    ],
    "forecast": [
        "forecast_expected_total", "forecast_upper_total",
        "largest_forecast_category", "forecast_period", "forecast_months_used",
    ],
    "inflation": [
        "personal_inflation", "national_inflation", "inflation_gap",
        "largest_inflation_contributor",
    ],
    "rate_impact": [
        "monthly_rate_cashflow_delta", "current_bank_rate", "scenario_bank_rate",
    ],
    "wealth": [
        "net_worth", "consumer_debt", "debt_payoff_time", "emergency_gap",
        "months_to_emergency", "total_assets", "total_liabilities",
        "savings_goal_gap", "months_to_savings_goal",
    ],
    "recommendations": ["recommendation_1", "recommendation_2", "recommendation_3"],
}


SECTION_TOPIC_LABELS: dict[str, str] = {
    "cash_flow": "cash flow",
    "health": "financial health",
    "transactions": "spending mix",
    "forecast": "spending forecast",
    "inflation": "cost of living",
    "rate_impact": "interest-rate exposure",
    "wealth": "net worth, debt, and goals",
    "recommendations": "recommended actions",
}


@dataclass(frozen=True)
class QuestionIntent:
    kind: str
    sections: list[str]
    topic_label: str


def detect_intent_kind(question: str) -> str:
    lowered = question.lower()
    if any(phrase in lowered for phrase in ("how much", "how many", "how big", "what is my", "what's my", "whats my")):
        return "how_much"
    if any(
        phrase in lowered
        for phrase in ("should i", "what should", "how do i", "how can i", "what can i", "how to", "help me", "reduce", "improve", "fix")
    ):
        return "what_should_i_do"
    if lowered.strip().startswith("why") or " why " in lowered:
        return "why"
    return "explain"


def route_sections(question: str) -> list[str]:
    tokens = set(tokenize(question))
    scored: list[tuple[float, int, str]] = []
    for order, section_id in enumerate(SECTION_CORE_KEYWORDS):
        score = (
            len(tokens & SECTION_CORE_KEYWORDS[section_id]) * CORE_WEIGHT
            + len(tokens & SECTION_SUPPORT_KEYWORDS[section_id]) * SUPPORT_WEIGHT
        )
        if score:
            # Sort by score desc, then by declaration order so ties are stable.
            scored.append((score, -order, section_id))
    scored.sort(reverse=True)
    return [section_id for _, _, section_id in scored]


def build_question_intent(question: str) -> QuestionIntent:
    sections = route_sections(question)
    if sections:
        topic_label = SECTION_TOPIC_LABELS.get(sections[0], "financial dashboard")
    else:
        sections = list(DEFAULT_SECTION_ORDER)
        topic_label = "financial dashboard"
    return QuestionIntent(kind=detect_intent_kind(question), sections=sections, topic_label=topic_label)
