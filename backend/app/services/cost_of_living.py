from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

from app.schemas.transactions import (
    PersonalInflationCategory,
    PersonalInflationResponse,
    RateImpactLine,
    RateImpactRequest,
    RateImpactResponse,
    TransactionIn,
)


def load_category_mapping(config_dir: str | Path) -> dict[str, str | None]:
    path = Path(config_dir).resolve() / "category_mapping.yml"
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    categories = payload.get("categories", {})
    return {name: details.get("ons_coicop") for name, details in categories.items()}


def coicop_code_from_mapping(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    match = re.match(r"^(?P<code>\d{2}(?:\.\d+)*)\b", text)
    return match.group("code") if match else None


def spend_by_category(transactions: list[TransactionIn]) -> pd.DataFrame:
    rows = [
        {"category": transaction.category or "uncategorised", "spend": abs(transaction.amount)}
        for transaction in transactions
        if transaction.amount < 0 and transaction.transaction_type != "transfer"
    ]
    if not rows:
        return pd.DataFrame(columns=["category", "spend"])

    frame = pd.DataFrame(rows)
    return frame.groupby("category", as_index=False)["spend"].sum().sort_values("spend", ascending=False)


def calculate_personal_inflation(
    transactions: list[TransactionIn],
    inflation: pd.DataFrame,
    category_mapping: dict[str, str | None],
    index_type: str = "cpih",
) -> PersonalInflationResponse:
    spend = spend_by_category(transactions)
    latest_date = inflation["date"].max()
    latest = inflation.loc[inflation["date"].eq(latest_date)].copy()
    overall = latest.loc[latest["category_level"].eq("overall")]
    national_rate = float(overall.iloc[0]["annual_change_pct"]) if not overall.empty else 0.0

    total_spend = float(spend["spend"].sum()) if not spend.empty else 0.0
    categories: list[PersonalInflationCategory] = []
    weighted_rate = 0.0
    notes: list[str] = []

    for row in spend.to_dict(orient="records"):
        app_category = str(row["category"])
        category_spend = float(row["spend"])
        spend_share = category_spend / total_spend if total_spend else 0.0
        mapped_label = category_mapping.get(app_category)
        coicop_code = coicop_code_from_mapping(mapped_label)

        ons_row = pd.DataFrame()
        if coicop_code:
            ons_row = latest.loc[
                latest["coicop_code"].eq(coicop_code) & latest["category_level"].eq("division")
            ]

        if ons_row.empty:
            notes.append(f"No ONS mapping found for {app_category}; excluded from weighted rate.")
            categories.append(
                PersonalInflationCategory(
                    app_category=app_category,
                    spend=round(category_spend, 2),
                    spend_share=round(spend_share, 4),
                    ons_category=mapped_label,
                    coicop_code=coicop_code,
                    annual_change_pct=None,
                    contribution_pct_points=None,
                )
            )
            continue

        annual_change = float(ons_row.iloc[0]["annual_change_pct"])
        contribution = spend_share * annual_change
        weighted_rate += contribution
        categories.append(
            PersonalInflationCategory(
                app_category=app_category,
                spend=round(category_spend, 2),
                spend_share=round(spend_share, 4),
                ons_category=str(ons_row.iloc[0]["category"]),
                coicop_code=coicop_code,
                annual_change_pct=round(annual_change, 2),
                contribution_pct_points=round(contribution, 3),
            )
        )

    return PersonalInflationResponse(
        index_type=index_type.lower(),
        period=latest_date.date().isoformat(),
        total_spend=round(total_spend, 2),
        personal_inflation_pct=round(weighted_rate, 2),
        national_inflation_pct=round(national_rate, 2),
        difference_pct_points=round(weighted_rate - national_rate, 2),
        categories=categories,
        notes=notes,
    )


def repayment_mortgage_payment(balance: float, annual_rate_pct: float, years_remaining: float) -> float:
    months = int(round(years_remaining * 12))
    if balance <= 0 or months <= 0:
        return 0.0

    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate == 0:
        return balance / months

    factor = (1 + monthly_rate) ** months
    return balance * monthly_rate * factor / (factor - 1)


def calculate_rate_impact(
    request: RateImpactRequest,
    current_bank_rate_pct: float,
) -> RateImpactResponse:
    effective_change = request.bank_rate_change_pct_points * (request.pass_through_pct / 100)
    scenario_bank_rate = current_bank_rate_pct + request.bank_rate_change_pct_points
    lines: list[RateImpactLine] = []
    notes: list[str] = []

    savings_delta = request.savings_balance * (effective_change / 100) / 12
    lines.append(
        RateImpactLine(
            name="Savings interest",
            monthly_delta=round(savings_delta, 2),
            annual_delta=round(savings_delta * 12, 2),
            note="Positive means the savings balance earns more interest.",
        )
    )

    debt_delta = -(request.variable_debt_balance * (effective_change / 100) / 12)
    lines.append(
        RateImpactLine(
            name="Variable debt cost",
            monthly_delta=round(debt_delta, 2),
            annual_delta=round(debt_delta * 12, 2),
            note="Negative means variable-rate debt costs more.",
        )
    )

    if request.mortgage_balance > 0:
        if request.current_mortgage_rate_pct is None:
            notes.append("Mortgage impact skipped because current_mortgage_rate_pct was not provided.")
        else:
            current_payment = repayment_mortgage_payment(
                request.mortgage_balance,
                request.current_mortgage_rate_pct,
                request.mortgage_years_remaining,
            )
            scenario_payment = repayment_mortgage_payment(
                request.mortgage_balance,
                request.current_mortgage_rate_pct + effective_change,
                request.mortgage_years_remaining,
            )
            mortgage_delta = -(scenario_payment - current_payment)
            lines.append(
                RateImpactLine(
                    name="Repayment mortgage",
                    monthly_delta=round(mortgage_delta, 2),
                    annual_delta=round(mortgage_delta * 12, 2),
                    note="Negative means the monthly repayment rises.",
                )
            )

    monthly_net = sum(line.monthly_delta for line in lines)
    return RateImpactResponse(
        current_bank_rate_pct=round(current_bank_rate_pct, 2),
        scenario_bank_rate_pct=round(scenario_bank_rate, 2),
        bank_rate_change_pct_points=round(request.bank_rate_change_pct_points, 2),
        effective_rate_change_pct_points=round(effective_change, 2),
        monthly_net_cashflow_delta=round(monthly_net, 2),
        annual_net_cashflow_delta=round(monthly_net * 12, 2),
        lines=lines,
        notes=notes,
    )
