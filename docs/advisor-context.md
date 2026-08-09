# Advisor Context Pack

The advisor context pack is a deterministic backend layer between dashboard calculations and advisor answers.

The advisor explains the dashboard; it does not calculate financial values. Numbers that appear in advisor output must come from the context pack first.

## Endpoint

```text
POST /api/v1/advisor/context
```

This endpoint accepts the current dashboard state:

- Profile setup values.
- Transaction rows.
- Forecast output.
- Personal inflation output.
- Financial-health score output.
- Bank Rate impact output.
- Deterministic recommendations.

It returns:

- Structured sections.
- Individual facts with source labels.
- A markdown context block for prompt construction.
- Missing-data warnings.
- A list of allowed numbers.
- Guardrails for generated answers.
- A source map explaining where each source comes from.

## Design

The backend already owns the deterministic services for spend, forecast, inflation, rate impact, scoring, debt, and goals. The context pack gathers those outputs into one controlled object before retrieval or optional LLM wording happens.

```text
dashboard data -> advisor context -> retrieve docs -> answer generation
```

The context pack is the boundary between calculated facts and generated explanation.

## Sections

The context builder creates these sections:

- Cash Flow: income, spend, disposable income, savings rate, housing-to-income, and emergency cover.
- Financial Health: score, band, weakest component, and score notes.
- Transaction Coverage: row count, month count, and largest spending categories.
- Forecast: period, months used, expected spend, upper estimate, and largest forecast category.
- Cost Of Living: personal inflation, UK inflation, inflation gap, and largest inflation contributor.
- Rate Impact: current Bank Rate, scenario rate, monthly cash-flow impact, and line-item effects.
- Net Worth, Debt, And Goals: assets, liabilities, net worth, consumer debt, debt payoff time, emergency gap, and savings-goal gap.
- Recommendations: deterministic next actions.

Each fact has:

- `id`
- `label`
- `value`
- `formatted`
- `source`
- `citation`
- `unit`

Raw values support structured UI logic. Formatted values support readable advisor text.

## Missing Data

The builder flags gaps before the advisor answers.

Examples:

- Missing profile setup.
- Missing monthly income.
- No transaction rows.
- Missing forecast output.
- Missing personal inflation output.
- Missing health score.
- Missing Bank Rate impact.
- Missing category coverage such as groceries, transport, utilities, housing, or subscriptions.

This lets the advisor say what is missing instead of treating unknown values as zero.

## Guardrails

Generated answers must:

- Use only facts and numbers in the context pack.
- Say what is missing instead of estimating unavailable numbers.
- Give budgeting guidance, not regulated financial advice.
- Avoid recommending specific investments, credit products, or providers.
- Cite source labels beside important claims.

## Files

Backend service:

```text
backend/app/services/advisor_context.py
```

API route:

```text
backend/app/api/routes/advisor.py
```

Schema additions:

```text
backend/app/schemas/transactions.py
```

Tests:

```text
backend/tests/test_advisor_context.py
```

## Test Coverage

The tests check that:

- Core facts are calculated correctly.
- The markdown context includes the allowed numbers.
- Missing profile, transaction, forecast, inflation, score, and rate data are flagged.
- Missing category coverage is flagged without falsely flagging supplied categories.
- The FastAPI endpoint returns the context pack.
