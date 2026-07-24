# Advisor Evaluation

I added an evaluation harness so "the advisor got better" is a number I can check, not a feeling.

Without it, every retrieval or routing change is a guess. With it, a regression shows up as a failing test.

## What It Measures

The harness runs a labelled question set through retrieval and the intent router.

- `recall@k`: the share of questions where an expected source document appears in the top `k` chunks.
- `mrr`: mean reciprocal rank of the first expected source, so ranking quality counts, not just presence.
- `routing_accuracy`: how often the intent router picks the dashboard section the question is really about.
- `distinctness`: the share of unique answers across the question set. This guards the bug where every question returned the same body.

## The Question Set

`EVAL_CASES` lives in:

```text
backend/app/services/advisor_eval.py
```

Each case labels a question with the documents that should be retrieved and, where it applies, the dashboard section the router should choose. Questions about the app itself rather than a section of the user's dashboard leave the section unset, so routing is only scored where a correct answer exists.

## Running It

```text
cd backend
python ../scripts/evaluate_advisor.py --hybrid
```

The report prints each mode's metrics plus the specific questions that missed, so a failure points at a question rather than a percentage.

## Baseline

Measured on 22 cases at `k=4`:

| Mode | recall@k | MRR | routing |
| --- | --- | --- | --- |
| Lexical | 0.91 | 0.84 | 1.00 |
| Hybrid | 0.95 | 0.91 | 1.00 |

Answer distinctness is 1.00 in both modes: all 22 questions produce different answers.

## What The Harness Caught

The first run scored routing at 0.87. Two questions, "How do you map my spending to ONS categories?" and "How far ahead can you predict my spending?", were routed to cash flow because unweighted keyword overlap let the generic word "spending" tie with the far more specific "ONS" and "predict".

I split the router's keywords into core and support terms with different weights. Routing went to 1.00.

Hybrid retrieval then fixed the "predict my spending" retrieval miss that lexical alone could not.

## Known Gap

One case still misses in both modes: "How are my transactions categorised?" retrieves the upload and dashboard flow documents instead of `transaction-categorisation.md`. The categorisation document describes the model rather than answering the user's phrasing, so this is a knowledge-base gap rather than a scoring bug.

## Guarding It

```text
backend/tests/test_advisor_eval.py
```

The tests assert thresholds below the measured baseline so they catch regressions without breaking on small, legitimate changes. The hybrid comparison test skips automatically when the optional embedding dependency is absent.
