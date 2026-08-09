# Advisor Evaluation

The advisor evaluation harness turns retrieval and routing quality into repeatable checks.

Without it, changes to retrieval or routing are hard to judge. With it, regressions show up as test failures and metric drops.

## Metrics

The harness runs a labelled question set through retrieval and the intent router.

- `recall@k`: share of questions where an expected source document appears in the top `k` chunks.
- `mrr`: mean reciprocal rank of the first expected source.
- `routing_accuracy`: how often the intent router picks the relevant dashboard section.
- `distinctness`: share of unique answers across the question set, guarding against every question returning the same body.

## Question Set

`EVAL_CASES` lives in:

```text
backend/app/services/advisor_eval.py
```

Each case labels a question with expected source documents and, where relevant, the dashboard section the router should choose. Questions about the app itself leave the section unset, so routing is scored only when a correct section exists.

## Running It

```zsh
cd backend
python ../scripts/evaluate_advisor.py --hybrid
```

The report prints each mode's metrics plus specific missed questions.

## Baseline

Measured on 22 cases at `k=4`:

| Mode | recall@k | MRR | routing |
| --- | --- | --- | --- |
| Lexical | 0.91 | 0.84 | 1.00 |
| Hybrid | 0.95 | 0.91 | 1.00 |

Answer distinctness is 1.00 in both modes: all 22 questions produce different answers.

## Findings

The first routing pass scored 0.87. Two questions, "How do you map my spending to ONS categories?" and "How far ahead can you predict my spending?", were routed to cash flow because unweighted keyword overlap let the generic word "spending" tie with more specific terms.

Splitting router keywords into core and support groups raised routing to 1.00.

Hybrid retrieval fixed the "predict my spending" retrieval miss that lexical mode alone could not handle.

## Known Gap

One case still misses in both modes: "How are my transactions categorised?" retrieves the upload and dashboard flow documents instead of `transaction-categorisation.md`. The categorisation document describes model mechanics more than the user's phrasing, so this is a knowledge-base gap rather than a scoring bug.

## Guarding It

```text
backend/tests/test_advisor_eval.py
```

The tests assert thresholds below the measured baseline so they catch regressions without failing on small legitimate changes. The hybrid comparison test skips automatically when the optional embedding dependency is absent.
