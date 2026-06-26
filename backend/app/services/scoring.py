from app.schemas.transactions import HealthScoreRequest, HealthScoreResponse, ScoreComponent


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
