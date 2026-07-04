# Advisor Context Pack

I built the advisor context as a deterministic backend layer before adding any LLM calls.

The point is simple: the LLM should explain the dashboard, not calculate the dashboard. All numbers the future advisor can mention should come from this context pack first.

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
- A markdown context block ready for a future prompt.
- Missing-data warnings.
- A list of allowed numbers.
- Guardrails for the future LLM.
- A source map explaining where each source comes from.

## Why I Built It This Way

I do not want the advisor to invent calculations. The backend already has deterministic services for spend, forecast, inflation, rate impact, scoring, debt, and goals. The advisor context gathers those outputs into one controlled object.

That means the future RAG advisor can work like this:

```text
dashboard data -> advisor context -> retrieve docs -> LLM explanation
```

The context pack becomes the boundary between calculated facts and generated explanation.

## Sections

The context builder creates these sections:

- Cash Flow: income, spend, disposable income, savings rate, housing-to-income, and emergency cover.
- Financial Health: score, band, weakest component, and score notes.
- Transaction Coverage: row count, month count, and largest spending categories.
- Forecast: period, months used, expected spend, upper estimate, and largest forecast category.
- Cost Of Living: personal inflation, UK inflation, inflation gap, and largest inflation contributor.
- Rate Impact: current Bank Rate, scenario rate, monthly cash-flow impact, and line-item effects.
- Net Worth, Debt, And Goals: assets, liabilities, net worth, consumer debt, debt payoff time, emergency gap, and savings-goal gap.
- Recommendations: existing deterministic next actions.

Each fact has:

- `id`
- `label`
- `value`
- `formatted`
- `source`
- `citation`
- `unit`

I use both raw values and formatted values because the app needs structured data, while the prompt needs readable text.

## Missing Data

The builder also flags gaps before the advisor answers.

Examples:

- Missing profile setup.
- Missing monthly income.
- No transaction rows.
- Missing forecast output.
- Missing personal inflation output.
- Missing health score.
- Missing Bank Rate impact.
- Missing category coverage such as groceries, transport, utilities, housing, or subscriptions.

This matters because the advisor should say "I do not have transport spending yet" instead of pretending the user spends nothing on transport.

## Guardrails

The context includes these rules for the future LLM:

- Use only the facts and numbers in this context pack.
- If a number is missing, say what is missing instead of estimating it.
- Give budgeting guidance, not regulated financial advice.
- Do not recommend specific investments, credit products, or providers.
- Cite the source label beside any important claim.

These rules are intentionally simple. I want the first advisor to be reliable before making it clever.

## Files Added

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

## What I Tested

The tests check that:

- Core facts are calculated correctly.
- The markdown context includes the allowed numbers.
- Missing profile, transaction, forecast, inflation, score, and rate data are flagged.
- Missing category coverage is flagged without falsely flagging supplied categories.
- The FastAPI endpoint returns the context pack.

## Next Step

The next layer is retrieval. I will add a small local knowledge base from project docs, split it into chunks, and retrieve the most relevant chunks for a question. Only after that should the LLM response endpoint be added.
