# Advisor Plain Language

The advisor answers a person looking at their own money. Nothing in a response should reveal how the system is built.

This matters more here than in most projects, because the knowledge base is written as engineering notes about this codebase. Quoting it without screening leaks internal vocabulary straight into the answer.

## The Rule

A user-facing response never contains:

- document filenames, headings, or internal identifiers
- internal vocabulary: chunk, retrieval, embedding, prompt, provider, guardrail, context pack, engine
- formulas, code, endpoints, or acronyms outside a small allowed set
- third-person references to "the user", because the advisor is talking to them

Internal values still travel in the payload for debugging. They are simply never rendered.

## Friendly Source Names

Each document has a plain-English name in `SOURCE_LABELS`:

| Internal document | Shown to the user |
| --- | --- |
| `cost-of-living-engine.md` | Cost of living |
| `spend-forecasting.md` | Spending forecast |
| `financial-health-score.md` | Financial health score |
| `rate-impact-engine.md` | Bank Rate impact |
| `transaction-categorisation.md` | Spending categories |

Responses carry both. `source` and `title` stay for debugging; `source_label` is what the panel renders.

## Screening Quoted Text

Background sentences are quoted from the knowledge base, so each one is screened before it reaches the answer. A sentence is dropped when it contains internal vocabulary, a formula, an unknown acronym, or an internal identifier, and also when it is not prose a person can read on its own:

- bullet and numbered list items, which are terse notes rather than sentences
- label-style fragments and anything ending in a colon
- sentences opening with a back reference such as "It also ...", which lose their subject once lifted out of context

Sentences are dropped rather than reworded. Rewriting a quote would break the link between the answer and its source.

## Leading With What Was Asked

Facts are ordered by how well their label matches the question, so "which component drags my score down" opens on the weakest component rather than the headline score. This also keeps answers distinct when two questions land on the same part of the dashboard.

## Guarding It

```text
backend/tests/test_advisor_plain_language.py
```

The tests run every evaluation question and assert that no rendered string contains banned terminology, internal identifiers, unknown acronyms, formulas, or third-person framing. Because the checks run across the whole question set, a single unfriendly sentence anywhere in the knowledge base fails the suite.

## Known Gap

The knowledge base still contains design commentary written for a developer audience, such as notes about intent rather than method. Screening removes the clearly internal cases, but the durable fix is rewriting the documents in user-facing language rather than filtering engineering notes after the fact.
