# Spend Forecasting

I forecast next-month spend from monthly category totals rather than individual transactions.

The first version compares simple, explainable methods:

- Last-month naive baseline.
- Three-month moving average.
- Six-month trend regression.
- Seasonal naive when enough history exists.

I do not use a random train/test split for this work because it would leak the future. Instead, I use rolling backtests: train on earlier months, predict the next month, then move the window forward.

The API reports MAE, RMSE, MAPE, backtest windows, and whether each candidate beats the naive baseline. The `/api/v1/forecast` endpoint also returns an interval around each forecast. The interval uses backtest residuals when there is enough history and a simple fallback margin when there is not.

Current limitation: this is still a baseline forecasting engine. It is deliberately honest and easy to explain, but it does not yet include ARIMA, Prophet, external macro features, or separate treatment for irregular annual payments.
