# Spend Forecasting

Spend forecasts are generated from monthly category totals rather than individual transactions.

The first version compares simple, explainable methods:

- Last-month naive baseline.
- Three-month moving average.
- Six-month trend regression.
- Seasonal naive when enough history exists.

Random train/test splits are avoided because they leak future behaviour into training. Rolling backtests train on earlier months, predict the next month, then move the window forward.

The API reports MAE, RMSE, MAPE, backtest windows, and whether each candidate beats the naive baseline. `/api/v1/forecast` also returns an interval around each forecast. The interval uses backtest residuals when enough history exists and a conservative fallback margin when it does not.

## Limitations

This is still a baseline forecasting engine. It is intentionally easy to inspect and does not yet include ARIMA, Prophet, external macro features, or separate treatment for irregular annual payments.
