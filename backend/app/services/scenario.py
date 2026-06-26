from app.schemas.transactions import ScenarioRequest, ScenarioResponse


def run_scenario(request: ScenarioRequest) -> ScenarioResponse:
    rent_delta = request.rent_or_mortgage * (request.rent_change_pct / 100)
    food_delta = request.food_spend * (request.food_change_pct / 100)
    savings_interest_delta = (
        request.savings_balance * (request.bank_rate_change_pct_points / 100) / 12
    )
    debt_cost_delta = (
        request.variable_debt_balance * (request.bank_rate_change_pct_points / 100) / 12
    )

    new_monthly_spend = request.monthly_spend + rent_delta + food_delta + debt_cost_delta
    disposable_income = request.monthly_income - new_monthly_spend + savings_interest_delta

    notes = [
        f"Rent/mortgage change adds {rent_delta:.2f} per month.",
        f"Food change adds {food_delta:.2f} per month.",
        f"Bank Rate change adds {debt_cost_delta:.2f} debt cost and {savings_interest_delta:.2f} savings interest per month.",
    ]

    return ScenarioResponse(
        new_monthly_spend=round(new_monthly_spend, 2),
        disposable_income=round(disposable_income, 2),
        savings_interest_delta_monthly=round(savings_interest_delta, 2),
        debt_cost_delta_monthly=round(debt_cost_delta, 2),
        notes=notes,
    )
