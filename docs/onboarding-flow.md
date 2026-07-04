# Onboarding Flow

I start the app with a short local setup flow instead of authentication.

The first step asks for the user's name and greets them in the rest of the setup. I only cache that name in session storage for a few hours so the flow feels personal without adding accounts or a profile table yet.

The detail steps then open one section at a time. The inputs start blank and use placeholders as examples, so the dashboard is not seeded with fake personal balances.

- Cash flow: monthly income, rent or mortgage, and monthly debt payment.
- Assets: liquid savings, investments, pension balance, and property value.
- Debts: mortgage balance, credit card balance, loan balance, and average debt APR.
- Goals: emergency fund target, savings goal target, and monthly goal contribution.

The setup values are saved in this browser's local storage. The Profile page lets me edit them later without starting the whole app again, and the Net Worth, Debt Payoff, and Savings Goals pages link straight back to the relevant setup section.

The core cash-flow values are sent with the CSV upload so the backend can calculate a better health score. The extra profile values stay in the frontend for now and power the net-worth, debt-payoff, savings-goals, rate-impact, and simulator pages.

I keep this local for now because the MVP is about the analytics flow, not account management. Refreshing the browser keeps the setup values, but they are not synced across devices yet.

Authentication can come back later once I add persisted user data and backend token checks. Until then, the app should feel usable without asking for an account too early.
