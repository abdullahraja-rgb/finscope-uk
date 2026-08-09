# Recommendations Engine

Recommendations are generated with deterministic rules rather than an LLM.

The engine reads outputs the app has already calculated:

- Financial-health score.
- Forecast intervals.
- Personal inflation.
- Bank Rate impact when available.

Each recommendation includes a title, detail, action, priority, and source. The source remains explicit so dashboard advice can be traced back to a calculated value.

This keeps the first recommendation layer predictable. The advisor can later explain the same calculated facts in a richer style, but it should not invent new financial values.
