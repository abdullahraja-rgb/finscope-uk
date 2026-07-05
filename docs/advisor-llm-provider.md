# Advisor LLM Provider

I added the live provider after the deterministic context, retrieval, and answer contract were already working.

The point is not to let the model calculate finance values. The backend already calculates those. The provider's job is only to turn supplied facts and retrieved project notes into a clearer explanation.

## Runtime Choice

The default remains:

```text
deterministic_fallback
```

To use the live provider locally, I set:

```text
ADVISOR_LLM_PROVIDER=openai
ADVISOR_LLM_API_KEY=...
ADVISOR_LLM_MODEL=gpt-4.1-mini
```

If those are not set, the app uses the deterministic fallback with no network call.

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

I treat numbers as controlled data, not wording.

The context pack creates an allowed-number list such as:

```text
Monthly spend: GBP 1,420 [health_score]
```

The live answer must copy `used_numbers` exactly from that list. The backend also scans the generated answer and bullets for numeric tokens. If the model introduces a number that was not in the allowed list, I reject that answer and return the deterministic fallback.

That is deliberately strict. It is better for the advisor to be less chatty than to sound confident with an invented figure.

## Provider Boundary

The live provider is in:

```text
backend/app/services/advisor_llm.py
```

The orchestration remains in:

```text
backend/app/services/advisor_answer.py
```

That keeps the design swappable. I can later add Anthropic, Ollama, or another local provider without changing the frontend or the endpoint contract.
