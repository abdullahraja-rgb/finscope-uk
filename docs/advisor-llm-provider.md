# Advisor LLM Provider

The live provider sits behind the deterministic context, retrieval, and answer contract.

The model does not calculate finance values. The backend calculates those values; the provider only turns supplied facts and retrieved notes into a clearer explanation.

## Runtime Choice

The default provider is:

```text
deterministic_fallback
```

Live provider configuration:

```text
ADVISOR_LLM_PROVIDER=openai
ADVISOR_LLM_API_KEY=...
ADVISOR_LLM_MODEL=gpt-4.1-mini
```

If those values are not set, the app uses the deterministic fallback with no network call.

## Flow

```text
dashboard state
-> advisor context pack
-> markdown retrieval
-> guarded prompt
-> optional LLM provider
-> backend validation
-> structured advisor response
```

The frontend still calls only:

```text
POST /api/v1/advisor/ask
```

## Structured Output

The live provider has to return JSON with:

- `answer`
- `summary_bullets`
- `citation_chunk_ids`
- `used_numbers`
- `confidence`

The backend fills the rest of the response from trusted local data: citations, missing-data warnings, retrieved chunks, and guardrails.

## Number Guardrail

Numbers are treated as controlled data, not wording.

The context pack creates an allowed-number list such as:

```text
Monthly spend: GBP 1,420 [health_score]
```

The live answer must copy `used_numbers` exactly from that list. The backend also scans generated answer text and bullets for numeric tokens. If the model introduces a number that was not in the allowed list, the endpoint rejects that answer and returns the deterministic fallback.

That strictness is intentional: a shorter answer is better than a confident answer with invented figures.

## Provider Boundary

The live provider is in:

```text
backend/app/services/advisor_llm.py
```

The orchestration remains in:

```text
backend/app/services/advisor_answer.py
```

The boundary keeps the design swappable if another provider is added later.
