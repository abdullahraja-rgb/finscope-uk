# Engineering Notes

Short implementation notes for the major technical decisions in FinScope UK.

## Transaction Categorisation

- A keyword categoriser ships as the fallback path so the upload flow works even before a trained model artifact exists.
- The supervised path uses TF-IDF merchant-description features, amount features, and Logistic Regression with balanced class weights.
- Evaluation reports macro F1, weighted F1, a confusion matrix, and example mistakes because category imbalance can hide weak performance behind ordinary accuracy.
- The fallback rules include UK merchants and lower-confidence handling for positive merchant refunds.

## Spend Forecasting

- Forecasting runs on monthly category totals rather than individual card rows.
- Candidate methods include last-month naive, moving average, trend regression, and seasonal naive where enough history exists.
- Rolling backtests preserve time order and avoid training on future data.
- Forecast intervals use backtest residuals when possible, with a conservative fallback margin for thin histories.

## Cost Of Living

- App categories are mapped to ONS COICOP divisions through `config/category_mapping.yml`.
- Personal inflation is a spend-weighted category estimate, not an item-level inflation model.
- Bank Rate scenarios use the latest Bank of England policy rate plus user-supplied balances to estimate monthly cash-flow impact.

## Financial Health

- The score is built from savings rate, housing burden, debt load, emergency cover, subscription leakage, and spending volatility.
- ONS Family Spending benchmarks provide a broad all-household comparison for spending mix.
- The scoring output keeps component-level notes so the dashboard can show why a score moved.

## Advisor

- The advisor path separates deterministic calculations from generated explanation.
- The context pack supplies approved facts and numbers.
- Retrieval adds implementation context from selected docs.
- The optional live LLM provider must return structured JSON and cannot introduce numbers that are absent from the context pack.

## Deployment

- Raw official datasets and trained model files stay outside the Docker image and outside Git.
- Hosted demos use clearly labelled fallback macro data when raw ONS or Bank of England files are unavailable.
- CI runs backend tests, frontend linting, frontend typechecking, and a production frontend build.
