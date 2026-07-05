# Advisor Answer Endpoint

I added the answer endpoint after the context pack and retrieval layer were working.

This endpoint gives the frontend one place to ask a question and get back a structured advisor response. For now it uses a deterministic fallback answer, not a live LLM call. That is intentional: the API contract, grounding rules, citations, and tests should be stable before I add an external provider.

## Endpoint

```text
POST /api/v1/advisor/ask
```

The request accepts the same dashboard state as the context endpoint, plus:

- `question`
- `max_chunks`
- `min_retrieval_score`

The endpoint then:

1. Builds the deterministic advisor context pack.
2. Retrieves relevant markdown knowledge chunks.
3. Builds a guarded prompt.
4. Sends the prompt to an advisor answer client.
5. Returns a structured response.

## Response Shape

The response includes:

- `answer`: readable explanation text.
- `summary_bullets`: short grounded points.
- `citations`: source file, title, chunk id, and heading path.
- `used_numbers`: numbers copied from the context pack.
- `missing_data`: data gaps the advisor should mention.
- `retrieved_chunks`: the knowledge chunks used.
- `guardrails`: the rules the answer must follow.
- `confidence`: high, medium, or low.
- `provider`: the answer client used.
- `notes`: implementation notes, including whether the deterministic fallback was used.

## Current Provider

The current provider is:

```text
deterministic_fallback
```

It does not call an LLM. It builds a plain-English response from the supplied context facts and retrieved chunks. This lets me test grounding without network calls, API keys, or provider-specific behaviour.

## Provider Boundary

The provider boundary lives in:

```text
backend/app/services/advisor_answer.py
```

The key interface is `AdvisorAnswerClient`. A future OpenAI, Anthropic, or local model client can implement the same method and return the same `AdvisorAskResponse` shape.

That means the frontend does not need to change when I swap the fallback for a real LLM.

## Guarding Against Hallucinated Numbers

The answer endpoint does not let the provider calculate financial values itself.

The context pack supplies:

- structured facts
- formatted numbers
- allowed numbers
- missing-data warnings

The provider should only use those values. If something is missing, the answer should say it is missing.

## Tests

The tests check that:

- the answer is structured
- citations are returned
- used numbers come from the context pack
- missing data is reported
- the FastAPI endpoint returns the same structured shape

## Next Step

The next step is adding a real LLM client behind the `AdvisorAnswerClient` boundary. I would keep the deterministic fallback as the default for tests and local development, then enable the live client only when an API key is configured.
