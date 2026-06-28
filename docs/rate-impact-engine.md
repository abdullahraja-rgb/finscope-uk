# Rate Impact Engine

I estimate how a Bank Rate move changes monthly cashflow across savings, variable debt, and a repayment mortgage.

The first version uses:

- Latest Bank Rate from the Bank of England workbook.
- A scenario change in percentage points, such as `+0.25`.
- A pass-through percentage, defaulting to `100%`.
- User balances for savings, variable debt, and mortgage.

Cashflow convention:

```text
positive monthly_delta = cashflow improves
negative monthly_delta = cashflow gets worse
```

Savings and variable debt use simple monthly interest deltas:

```text
monthly delta = balance * rate change / 12
```

The repayment mortgage uses the standard amortising payment formula:

```text
payment = principal * monthly_rate * factor / (factor - 1)
factor = (1 + monthly_rate) ^ months_remaining
```

Current limitation: this is a scenario estimate. Real lenders may pass through rate changes differently, and fixed-rate mortgage users may not see an immediate monthly change.
