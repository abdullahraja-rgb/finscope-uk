# Learning Log

I use this log as my interview prep. For each topic, I write what it is, why I used it, what surprised me, and how I would explain the decision out loud.

## Phase 0 - Foundations

- I will add this after the first setup commit.

## Phase 1 - pandas and EDA

- I will add this after the first EDA pass.

## Phase 2 - Data Layer

- I will add this after I load the first official datasets.

## Phase 3 - Classification

- I started with a keyword categoriser so the product flow worked before the ML was ready, then added a TF-IDF plus Logistic Regression pipeline as the first supervised model. I chose this because merchant descriptions are short text snippets and the model is easy to inspect, train quickly, and explain. The main thing I need to watch is class imbalance: groceries and income are easy to make common, while smaller categories can disappear inside overall accuracy, so I report macro F1, weighted F1, a confusion matrix, and misclassified examples.

## Phase 4 - Forecasting

- I added a first forecasting layer with a naive baseline, moving average, trend regression, seasonal naive, and rolling backtests. The key lesson is that time series validation has to respect time order: if I randomly split months, the model can learn from future behaviour and the score becomes misleading. I report MAE, RMSE, MAPE, and whether each candidate beats last-month naive because a forecast that cannot beat a simple baseline should not be presented as a smart model.

## Phase 5 - Cost of Living Engine

- I will add this after the personal inflation calculation.

## Phase 6 - Financial Health Score

- I will add this after I choose the first score weights.

## Phase 7 - FastAPI

- I will add this after the first endpoint tests pass.

## Phase 8 - Next.js Dashboard

- I connected the upload flow to the real analysis stack instead of stopping at CSV preview. The important design choice was to analyse the file once on the backend, then return the preview, categorised transactions, forecast, personal inflation, and health score together. That keeps the frontend simpler and avoids slightly different category assumptions leaking into different dashboard panels.
