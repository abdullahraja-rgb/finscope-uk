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

These come from the local onboarding flow before the dashboard opens. They feed the health score, dashboard metric cards, rate scenario assumptions, upload analysis, net-worth page, debt-payoff page, and savings-goals page.

## Live From The Backend

These update from FastAPI:

- CSV upload analysis.
- Transaction categorisation.
- Forecasts and forecast intervals.
- Personal inflation.
- Financial-health score.
- ONS benchmark comparison.
- Recommendations.
- Bank Rate impact.

When a CSV is uploaded, the dashboard refreshes its main analysis from the uploaded transactions.

The header shows whether the dashboard is using the demo baseline or an uploaded CSV. I keep that visible so the page does not feel like unexplained sample numbers.

## Demo-Seeded

The dashboard still uses demo transactions before the first upload so the page does not open empty. These demo values power:

- First-load spending chart.
- First-load cost-of-living chart.
- First-load financial-health score.
- First-load recommendations.

After upload, those panels switch to the uploaded file where the backend response includes replacement data.

## Dashboard Sections

- Overview: income, spend, disposable cash, health score, data status, pressure points, and first action.
- Spending: current category spend against the next-month forecast.
- Cost of living: personal inflation against the UK figure and Bank Rate pressure.
- Net worth: assets, liabilities, and net worth from setup balances.
- Debt payoff: consumer debt payoff estimate and debt mix.
- Savings goals: emergency fund progress and the main savings target.
- Next actions: recommendation list and the rate scenario snapshot.

## Not Built Yet

- Authentication.
- Profile table.
- Persisted uploaded transactions.
- User-specific dashboard history across devices.
