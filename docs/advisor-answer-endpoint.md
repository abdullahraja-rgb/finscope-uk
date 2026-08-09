# Advisor Answer Endpoint

The answer endpoint gives the frontend one place to send a dashboard question and receive a structured advisor response. It supports an optional live LLM provider, while the deterministic fallback remains the default for local development and tests.

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
- `missing_data`: gaps the advisor should mention.
- `retrieved_chunks`: knowledge chunks used.
- `guardrails`: answer rules.
- `confidence`: high, medium, or low.
- `provider`: answer client used.
- `notes`: implementation notes, including fallback behaviour.

## Providers

The default provider is:

```text
deterministic_fallback
```

It does not call an LLM. It builds a plain-English response from supplied context facts and retrieved chunks, which keeps local development and tests network-free.

The optional live provider is:

```text
openai_responses
```

Configuration:

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

`AdvisorAnswerClient` is the common interface. The OpenAI Responses client implements that interface and returns the same `AdvisorAskResponse` shape as the fallback provider, so the frontend does not need provider-specific logic.

## Number Guardrail

The answer endpoint does not let a provider calculate financial values itself.

The context pack supplies:

- structured facts
- formatted numbers
- allowed numbers
- missing-data warnings

The provider should only use those values. If something is missing, the answer should say it is missing.

For the live provider:

- `used_numbers` must be copied exactly from the context pack's allowed-number list.
- answer text and bullets cannot introduce numeric tokens absent from the allowed-number list.

If either check fails, the live answer is discarded and the deterministic fallback is returned.

## Tests

The tests check that:

- the answer is structured
- citations are returned
- used numbers come from the context pack
- missing data is reported
- the FastAPI endpoint returns the same structured shape
- the live provider accepts a valid structured response
- the live provider falls back when it invents an unsupported number
