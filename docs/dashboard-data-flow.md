# Dashboard Data Flow

The dashboard currently has three kinds of data.

## User-Entered

- Monthly income.
- Liquid savings.
- Monthly debt payment.
- Rent or mortgage.
- Investment balance.
- Pension balance.
- Property value.
- Mortgage balance.
- Credit card balance.
- Loan balance.
- Average debt APR.
- Emergency fund target.
- Savings goal target.
- Monthly goal contribution.

These come from the local setup flow before the dashboard opens, then stay editable on the Profile page. The values are saved in local storage in this browser and can be cleared by starting setup again.

They feed the health score, dashboard metric cards, rate scenario assumptions, upload analysis, net-worth page, debt-payoff page, savings-goals page, and simulator.

## Live From The Backend

These update from FastAPI:

- CSV upload analysis.
- Form-entered transaction analysis.
- Transaction categorisation.
- Forecasts and forecast intervals.
- Personal inflation.
- Financial-health score.
- ONS benchmark comparison.
- Recommendations.
- Bank Rate impact.

When a CSV is uploaded, the dashboard refreshes its main analysis from the uploaded transactions. When the user enters rows through the form, the frontend converts those rows into the same CSV shape and sends them through the same analysis endpoint.

The header shows whether the dashboard has no transactions yet, is using uploaded CSV data, or is using form-entered rows. Updating the Profile page refreshes the analysis against the current transaction rows.

## Empty Until Transactions

The dashboard no longer fills spending, forecasts, inflation, health score, or recommendations with sample transactions before the user provides data.

Before a CSV upload or form entry:

- Spending shows a prompt to enter transactions or upload a CSV.
- Forecast, personal inflation, and recommendations stay empty.
- Setup-only sections such as net worth, debt payoff, savings goals, and rate-impact assumptions still use onboarding inputs.
- If setup values are also empty, Overview prompts the user to finish financial setup instead of pretending GBP 0 values are meaningful.

## Dashboard Sections

- Overview: income, spend, disposable cash, health score, and a larger pressure-points panel.
- Spending: current category spend against the next-month forecast, or a transaction-entry prompt when no rows exist.
- Cost of living: personal inflation against the UK figure and Bank Rate pressure.
- Net worth: assets, liabilities, and net worth from setup balances.
- Debt payoff: consumer debt payoff estimate and debt mix.
- Savings goals: emergency fund progress and the main savings target.
- Simulator: rent, food, bills, debt-payment, and savings assumptions with a monthly cash-flow impact.
- Next actions: recommendation list and the rate scenario snapshot.
- Profile: editable cash-flow, asset, debt, and goal setup values.

## Out Of Scope For Now

- Authentication.
- Server-side profile table.
- Persisted uploaded transactions.
- User-specific dashboard history across devices.
