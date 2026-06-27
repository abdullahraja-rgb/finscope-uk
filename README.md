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
