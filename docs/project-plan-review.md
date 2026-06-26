# Project Plan Review

I like this plan because it builds the product spine before the advanced features: data ingestion, modelling, API, UI, deployment, and then explainability or LLM work. That order keeps the project shippable.

## Keep

- The gated phases. I have to understand each layer before moving on.
- The public-data angle. ONS and Bank of England data make the project more credible than a single Kaggle CSV.
- The backend/API phase before the dashboard polish. It prevents a notebook-only portfolio.
- Error analysis, baselines, and time-aware backtesting. These are interview-grade signals.
- `LEARNING_LOG.md`. I treat it as an interview answer bank.

## Adjust

- I should build the end-to-end thin slice earlier. I will keep the Phase 0 to 2 setup, but ship a placeholder upload-to-dashboard flow before heavy ML, then replace placeholder services with trained models.
- I should use synthetic transactions first. Real banking data is sensitive and public transaction datasets are often weak for UK budgeting categories.
- I should split housing into house prices and rents. UK HPI is clean and current; ONS private rental summary tables are useful historically but discontinued, so I will treat them as a starter dataset rather than the final rental source.
- I should pin the MVP to six visible features: upload, summary, categorise, forecast, personal inflation, financial health score.

## Suggested MVP Order

1. Repo skeleton, synthetic data generator, FastAPI health endpoint, Next.js dashboard shell.
2. CSV upload and transaction preview.
3. Rule-based categorisation baseline, then supervised classifier.
4. Spend aggregation and naive forecast, then time-series backtests.
5. ONS/Bank of England loaders and personal inflation engine.
6. Health score and case-study README.

## Risk Register

| Risk | Mitigation |
|---|---|
| Spending too long on ML before the app works | I keep placeholder services and replace one at a time |
| Public transaction data does not match UK banking text | Generate synthetic data with UK merchants and manually inspect labels |
| ONS workbooks change sheet names | Cache raw files and write loaders with explicit schema tests |
| Forecasting overclaims precision | Always show baseline and error interval |
| LLM advisor hallucinates numbers | Only pass retrieved numeric facts and require structured citations |
