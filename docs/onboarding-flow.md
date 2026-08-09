# Onboarding Flow

The app starts with a short local setup flow instead of authentication.

The first step asks for a name and caches it in session storage for a few hours. That keeps the setup flow personal without adding accounts or a profile table.

The detail steps open one section at a time. Inputs start blank and use placeholders as examples, so the dashboard is not seeded with fake personal balances.

- Cash flow: monthly income, rent or mortgage, and monthly debt payment.
- Assets: liquid savings, investments, pension balance, and property value.
- Debts: mortgage balance, credit card balance, loan balance, and average debt APR.
- Goals: emergency fund target, savings goal target, and monthly goal contribution.

Setup values are saved in local storage. The Profile page can edit them later, and the Net Worth, Debt Payoff, and Savings Goals pages link back to the relevant setup section.

Core cash-flow values are sent with CSV uploads so the backend can calculate a better health score. The remaining profile values stay in the frontend for now and power the net-worth, debt-payoff, savings-goals, rate-impact, and simulator pages.

## Limitations

Setup values are local to the current browser. They are not synced across devices, and there is no server-side profile table yet.
