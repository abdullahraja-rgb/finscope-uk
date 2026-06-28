# Upload Analysis Flow

I use `/api/v1/transactions/analyse` as the dashboard entry point for uploaded CSVs.

The flow is:

1. Read and validate the CSV.
2. Convert rows into typed transactions.
3. Predict categories where the CSV does not already have them.
4. Reuse the same categorised transactions for forecasting, personal inflation, and the financial-health score.
5. Return one response that the dashboard can use to refresh the main panels.

This avoids parsing the same file several times in the frontend. It also keeps category handling consistent: the forecast, inflation engine, and health score all work from the same transaction labels.

Current limitation: the endpoint is still stateless. It analyses the uploaded file and returns results immediately, but it does not persist the upload or create a user account/session yet.
