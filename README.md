# FinScope UK

FinScope UK is a full-stack personal finance dashboard for UK spending data. It lets a user upload transactions or enter rows manually, then turns that data into category analysis, short-term spend forecasts, cost-of-living context, financial-health scoring, and grounded recommendations.

## What It Does

- Analyses uploaded CSV transactions and form-entered rows through one backend flow.
- Categorises merchant descriptions with a rule-based fallback and an optional trained scikit-learn model.
- Forecasts next-month category spend with baseline comparisons and uncertainty intervals.
- Maps spending categories to ONS inflation divisions to estimate personal inflation.
- Estimates Bank Rate changes across savings, variable debt, and repayment mortgage scenarios.
- Builds financial-health scores from savings rate, housing burden, debt load, emergency cover, subscriptions, and volatility.
- Provides deterministic recommendations and an optional grounded advisor response.

## Stack

- Backend: FastAPI, Pydantic, pandas, scikit-learn, pytest.
- Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts.
- Data: synthetic transaction samples, ONS inflation data, Bank of England Bank Rate history, ONS Family Spending benchmarks, UK House Price Index.
- Deployment: Docker backend, Render/Railway-compatible config, Vercel frontend.

## Repository Layout

```text
.
|-- backend/              # FastAPI routes, services, schemas, and tests
|-- frontend/             # Next.js dashboard
|-- config/               # Category mappings and app configuration
|-- data/                 # Sample data plus ignored raw/processed/model folders
|-- docs/                 # Design notes and implementation references
|-- notebooks/            # Ignored local analysis notebooks
|-- scripts/              # Data generation, training, and verification scripts
|-- DATA_DICTIONARY.md
`-- ENGINEERING_NOTES.md
```

## Local Setup

Backend:

```zsh
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Frontend:

```zsh
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000` by default. Override it with `NEXT_PUBLIC_API_BASE_URL` when needed.

## Quality Checks

Backend:

```zsh
cd backend
python -m pytest
```

Frontend:

```zsh
cd frontend
npm run lint
npm run typecheck
npm run build
```

GitHub Actions runs the same backend and frontend checks on push and pull request.

## Data Policy

Real bank statements, raw official downloads, trained model artifacts, local databases, and uploaded files are excluded from Git. Public demo data lives under `data/sample/` and is synthetic.

Raw source files belong under ignored folders such as `data/raw/ons/`, `data/raw/boe/`, and `data/raw/housing/`. See `DATA_DICTIONARY.md` for dataset links, licence notes, and expected local filenames.

## API Surface

- `POST /api/v1/transactions/analyse`
- `GET /api/v1/datasets/inflation/latest`
- `POST /api/v1/categorise`
- `POST /api/v1/categorise/evaluate`
- `POST /api/v1/forecast`
- `POST /api/v1/forecast/backtest`
- `POST /api/v1/cost-of-living/personal-inflation`
- `POST /api/v1/cost-of-living/rate-impact`
- `POST /api/v1/score/from-transactions`
- `POST /api/v1/recommendations`
- `POST /api/v1/advisor/context`
- `POST /api/v1/advisor/retrieve`
- `POST /api/v1/advisor/ask`

## Deployment

The backend can run as a Dockerised FastAPI service, while the frontend can be deployed as a Vercel Next.js app. The backend image includes sample data and labelled fallback macro data for hosted demos when raw ONS or Bank of England files are not available.

See `docs/deployment.md` for deployment settings and environment variables.
