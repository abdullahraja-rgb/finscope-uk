# Financial Health Score

I calculate the first financial-health score from six components:

- Savings rate.
- Housing burden.
- Debt load.
- Emergency fund months.
- Subscription leakage.
- Spending volatility.

The score is deliberately transparent. Each component has a score from 0 to 100 and a weight, then the final score is the weighted average.

The transaction-derived endpoint estimates monthly spend, housing spend, subscriptions, and volatility from transaction history. I can still pass income, savings, and debt payments directly because those are not always visible from card or current-account transactions.

I compare the user's spending mix with ONS Family Spending `Table 4.1`. The first benchmark compares app categories mapped to COICOP divisions against the latest all-household average spending shares.

Current limitation: the benchmark is broad and all-household, not matched to age, region, household size, or income decile yet. I will tighten that later if the dashboard needs more precise peer comparisons.
