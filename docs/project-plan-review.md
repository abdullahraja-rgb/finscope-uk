# Project Scope

FinScope UK is scoped around an end-to-end analytics path before advanced modelling polish: ingest transactions, classify them, forecast spend, add public UK macro context, expose the results through an API, and make the workflow usable in the dashboard.

## Scope Choices

- Public UK datasets give the project stronger context than a single generic transaction CSV.
- Backend services and API contracts are built before dashboard polish, so the app is not just a notebook or static UI.
- Baselines, error analysis, and time-aware backtesting are included for the modelling work.
- Synthetic transactions are used for public demos because real banking data is sensitive.
- Housing context is split between house-price pressure and rental benchmarks.

## Build Order

1. Repo skeleton, synthetic data generator, FastAPI health endpoint, and Next.js dashboard shell.
2. CSV upload and transaction preview.
3. Rule-based categorisation baseline, then supervised classifier.
4. Spend aggregation and naive forecast, then rolling backtests.
5. ONS and Bank of England loaders with the personal-inflation engine.
6. Health score, recommendations, and advisor context.

## Risk Register

| Risk | Mitigation |
|---|---|
| Modelling takes attention before the app works | Keep an end-to-end path running and replace provisional services incrementally |
| Public transaction data does not resemble UK banking text | Generate synthetic UK merchant data and inspect labels manually |
| ONS workbooks change sheet names | Keep raw files local and cover loaders with schema tests |
| Forecasts look more precise than they are | Show baseline comparisons and forecast intervals |
| Advisor answers invent numbers | Restrict answers to context-pack numbers and validate provider output |
