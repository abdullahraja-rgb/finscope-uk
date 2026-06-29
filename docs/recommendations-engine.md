# Recommendations Engine

I generate the first recommendations with deterministic rules rather than an LLM.

The engine reads the outputs the app already calculated:

- Financial-health score.
- Forecast intervals.
- Personal inflation.
- Bank Rate impact when available.

Each recommendation includes a title, detail, action, priority, and source. I keep the source explicit so the dashboard advice can be traced back to a number in the app.

This is deliberately simple for the MVP. It gives useful guidance without inventing facts, and it leaves a clean path for the later grounded advisor: the LLM can explain these same calculated facts in a richer style once the app has retrieval and guardrails.
