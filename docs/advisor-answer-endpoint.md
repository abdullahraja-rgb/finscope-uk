# Advisor Answer Endpoint

I added the answer endpoint after the context pack and retrieval layer were working.

This endpoint gives the frontend one place to ask a question and get back a structured advisor response. It now supports an optional live LLM provider, but the deterministic fallback remains the default for local development and tests.

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

## Providers

The default provider is:

```text
deterministic_fallback
```

It does not call an LLM. It builds a plain-English response from the supplied context facts and retrieved chunks. This lets me test grounding without network calls, API keys, or provider-specific behaviour.

The optional live provider is:

```text
openai_responses
```

I enable it with environment variables:

```text
ADVISOR_LLM_PROVIDER=openai
ADVISOR_LLM_API_KEY=...
ADVISOR_LLM_MODEL=gpt-4.1-mini
```

If the provider is not configured, or if its response fails validation, the endpoint falls back to `deterministic_fallback`.

## Provider Boundary

The provider boundary lives in:

```text
backend/app/services/advisor_answer.py
backend/app/services/advisor_llm.py
```

The key interface is `AdvisorAnswerClient`. The OpenAI Responses client implements that interface and returns the same `AdvisorAskResponse` shape.

That means the frontend does not need to change when I switch between fallback and live answers.

## Guarding Against Hallucinated Numbers

The answer endpoint does not let the provider calculate financial values itself.

The context pack supplies:

- structured facts
- formatted numbers
- allowed numbers
- missing-data warnings

The provider should only use those values. If something is missing, the answer should say it is missing.

For the live provider, I add two backend checks after the model returns:

- `used_numbers` must be copied exactly from the context pack's allowed-number list.
- the answer text and bullets cannot introduce numeric tokens that are not present in the allowed-number list.

If either check fails, I discard the live answer and return the deterministic fallback.

## Tests

The tests check that:

- the answer is structured
- citations are returned
- used numbers come from the context pack
- missing data is reported
- the FastAPI endpoint returns the same structured shape
- the live provider accepts a valid structured response
- the live provider falls back when it invents an unsupported number
