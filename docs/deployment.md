# Deployment

The app deploys as two services:

- FastAPI backend on Render or Railway.
- Next.js frontend on Vercel.

## Backend

The backend Dockerfile lives at `backend/Dockerfile`. It copies:

- `backend/app`
- `backend/requirements.txt`
- `config`
- `data/sample`

It does not copy `data/raw`, `data/processed`, or `data/models`. Raw official datasets and trained model artifacts stay out of Git and out of the public image.

Recommended backend environment:

```text
DATA_DIR=/app/data
CONFIG_DIR=/app/config
CORS_ORIGINS=https://your-vercel-domain.vercel.app
```

Render can use `render.yaml` from the repo root. After deployment, check:

```text
https://your-backend-url/health
https://your-backend-url/docs
```

Hosted demos use bundled fallback macro data when raw ONS or Bank of England files are absent. API response notes label fallback data clearly.

## Frontend

The frontend is a standard Next.js app in `frontend`.

Vercel settings:

```text
Root directory: frontend
Build command: npm run build
Install command: npm ci
Output: Next.js default
```

Frontend environment:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url
```

After deployment, upload `data/sample/synthetic_transactions.csv` through the dashboard and confirm that forecasts, inflation, health score, and recommendations update from the uploaded file.

## Pre-Deploy Checklist

- Backend tests pass.
- Frontend lint passes.
- Frontend typecheck passes.
- Frontend build passes.
- `CORS_ORIGINS` matches the deployed frontend URL.
- No raw bank statements or raw official datasets are committed.
