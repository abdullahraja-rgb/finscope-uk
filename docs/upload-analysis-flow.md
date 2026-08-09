# Upload Analysis Flow

`/api/v1/transactions/analyse` is the dashboard entry point for uploaded CSVs and form-entered transaction rows.

The flow is:

1. Read and validate the CSV.
2. Convert rows into typed transactions.
3. Predict categories where the CSV does not already have them.
4. Reuse the same categorised transactions for forecasting, personal inflation, and the financial-health score.
5. Return one response that refreshes the main dashboard panels.

For manual entry, the frontend converts rows into the same CSV columns before sending them to this endpoint. CSV upload and form entry therefore share one analysis path.

This avoids parsing the same file several times in the frontend and keeps category handling consistent across forecasting, inflation, and scoring.

## Limitations

The endpoint is stateless. It analyses the uploaded file and returns results immediately, but it does not persist uploads or create a user account/session.
