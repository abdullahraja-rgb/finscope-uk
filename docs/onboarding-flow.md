# Onboarding Flow

I start the app with a short local setup step instead of authentication.

The user enters:

- Cash flow: monthly income, rent or mortgage, and monthly debt payment.
- Assets: liquid savings, investments, pension balance, and property value.
- Debts: mortgage balance, credit card balance, loan balance, and average debt APR.
- Goals: emergency fund target, savings goal target, and monthly goal contribution.

The core cash-flow values are sent with the CSV upload so the backend can calculate a better health score. The extra profile values stay in the frontend for now and power the net-worth, debt-payoff, and savings-goals pages.

I keep this local for now because the MVP is about the analytics flow, not account management.

Authentication can come back later once I add persisted user data and backend token checks. Until then, the app should feel usable without asking for an account too early.
