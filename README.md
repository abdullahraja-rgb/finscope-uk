# FinScope UK

I am building a UK personal finance and cost-of-living intelligence platform.

FinScope UK helps a user upload spending data, classify transactions, forecast next-month spend, and understand how UK inflation, housing costs, and Bank Rate changes affect their own budget.

The CV line I am working toward:

> Built and deployed a UK personal-finance analytics platform: ML transaction classification, time-series spend forecasting, and a cost-of-living engine integrating live ONS inflation and Bank of England rate data, served via a tested FastAPI backend and Next.js dashboard, with SHAP explainability and an LLM advisor.

## Repo Shape

```text
.
|-- backend/              # FastAPI API, services, schemas, tests
|-- frontend/             # Next.js dashboard
|-- config/               # Category mappings and app configuration
|-- data/                 # Raw/processed/external/sample data folders
|-- docs/                 # Project notes, plan review, architecture decisions
|-- notebooks/            # EDA and modelling notebooks
|-- scripts/              # One-off project utilities
|-- DATA_DICTIONARY.md
`-- LEARNING_LOG.md
```

## Quick Start

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The default frontend API target is `http://localhost:8000`. Override it with `NEXT_PUBLIC_API_BASE_URL`.

## Quality Checks

I run these checks before a commit:

```powershell
cd backend
python -m pytest
cd ..\frontend
npm run lint
npm run typecheck
npm run build
```

GitHub Actions runs the same backend and frontend checks on push and pull request.

## Deployment

I deploy the backend as a Dockerised FastAPI service and the frontend as a Vercel Next.js app. The backend image includes sample data and uses clearly labelled demo macro fallbacks when raw ONS or Bank of England files are not present.

See `docs/deployment.md` for the deploy checklist and environment variables.

## Data Policy

I am not committing real bank statements or raw downloaded datasets. I keep raw files in `data/raw/`, which is ignored by Git, and use synthetic or heavily anonymised samples for public demos.

## First Datasets

I am starting with:

- ONS Consumer Price Inflation tables for CPIH/CPI/RPI.
- Bank of England Official Bank Rate history.
- ONS Family Spending workbook for household benchmarks.
- UK House Price Index CSV downloads for housing pressure.
- Synthetic transaction data from `scripts/generate_synthetic_transactions.py`.

See `DATA_DICTIONARY.md` for links, licence notes, and expected usage.

## Current Build

The backend now has a first cost-of-living engine:

- `POST /api/v1/transactions/analyse` powers the dashboard flow from uploaded CSVs or form-entered transaction rows.
- `GET /api/v1/datasets/inflation/latest` returns latest ONS CPIH/CPI category rates.
- `POST /api/v1/categorise` uses a saved ML model when available and falls back to rules.
- `POST /api/v1/categorise/evaluate` evaluates a labelled transaction batch with F1 and confusion-matrix output.
- `POST /api/v1/forecast` forecasts next-month category spend with uncertainty intervals.
- `POST /api/v1/forecast/backtest` runs rolling time-aware forecast validation.
- `POST /api/v1/cost-of-living/personal-inflation` calculates personal inflation from transaction categories.
- `POST /api/v1/cost-of-living/rate-impact` estimates Bank Rate effects on savings, debt, and repayment mortgages.
- `POST /api/v1/score/from-transactions` derives a financial-health score and ONS spending benchmarks from transactions.
- `POST /api/v1/recommendations` turns calculated outputs into traceable next actions.
- `POST /api/v1/advisor/context` builds the deterministic context pack for the future RAG advisor.
- `POST /api/v1/advisor/retrieve` retrieves citation-ready project knowledge chunks for advisor questions.
- `POST /api/v1/advisor/ask` combines context and retrieval into a structured grounded advisor answer.

The frontend starts with a short local setup flow for cash flow, assets, debts, and savings goals, then keeps those values editable on the Profile page. The dashboard accepts transaction data through CSV upload or a row-entry form, then splits the analysis into overview, spending, cost of living, net worth, debt payoff, savings goals, simulator, next actions, and profile setup. See `docs/onboarding-flow.md` and `docs/dashboard-data-flow.md`.
