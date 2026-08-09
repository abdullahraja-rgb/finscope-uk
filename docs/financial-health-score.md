# Financial Health Score

The financial-health score combines six components:

- Savings rate.
- Housing burden.
- Debt load.
- Emergency fund months.
- Subscription leakage.
- Spending volatility.

Each component has a score from 0 to 100 and a weight. The final score is the weighted average.

The transaction-derived endpoint estimates monthly spend, housing spend, subscriptions, and volatility from transaction history. Income, savings, and debt payments can still be supplied directly because they are not always visible in card or current-account exports.

Spending mix is compared with ONS Family Spending `Table 4.1`. The benchmark maps app categories to COICOP divisions and compares them with the latest all-household average spending shares.

## Limitations

The benchmark is broad and all-household. It is not yet adjusted by age, region, household size, or income decile.
