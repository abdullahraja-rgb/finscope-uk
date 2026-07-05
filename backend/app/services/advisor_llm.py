from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import httpx

from app.core.config import Settings
from app.schemas.transactions import (
    AdvisorAskRequest,
    AdvisorAskResponse,
    AdvisorContextResponse,
    AdvisorKnowledgeChunk,
)
from app.services.advisor_answer import (
    AdvisorAnswerClient,
    AdvisorPrompt,
    DeterministicAdvisorClient,
    citation_from_chunk,
)


PostJson = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {"type": "string"},
        "summary_bullets": {"type": "array", "items": {"type": "string"}},
        "citation_chunk_ids": {"type": "array", "items": {"type": "string"}},
        "used_numbers": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["answer", "summary_bullets", "citation_chunk_ids", "used_numbers", "confidence"],
}


NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])(?:GBP\s*)?[+-]?\d[\d,]*(?:\.\d+)?%?")


@dataclass(frozen=True)
class OpenAIResponsesConfig:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float
    max_output_tokens: int
    temperature: float | None


def normalise_number_token(token: str) -> str | None:
    cleaned = token.upper().replace("GBP", "").replace("%", "").replace(",", "").strip()
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None

    normalised = format(number.normalize(), "f")
    if "." in normalised:
        normalised = normalised.rstrip("0").rstrip(".")
    return normalised or "0"


def number_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for match in NUMBER_PATTERN.finditer(text):
        token = normalise_number_token(match.group(0))
        if token is not None:
            tokens.add(token)
    return tokens


def allowed_number_tokens(context: AdvisorContextResponse) -> set[str]:
    return number_tokens("\n".join(context.allowed_numbers))


def unsupported_number_tokens(text: str, context: AdvisorContextResponse) -> set[str]:
    return number_tokens(text) - allowed_number_tokens(context)


def extract_response_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                return text

    raise ValueError("The provider response did not include output text.")


def parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("The provider response was not a JSON object.")
    return payload


def validated_strings(payload: dict[str, Any], key: str, max_items: int) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list.")
    return [str(item).strip() for item in value if str(item).strip()][:max_items]


class OpenAIResponsesAdvisorClient:
    provider = "openai_responses"

    def __init__(
        self,
        config: OpenAIResponsesConfig,
        post_json: PostJson | None = None,
        fallback: AdvisorAnswerClient | None = None,
    ) -> None:
        self.config = config
        self.post_json = post_json or self._post_json
        self.fallback = fallback or DeterministicAdvisorClient()

    def answer(
        self,
        request: AdvisorAskRequest,
        context: AdvisorContextResponse,
        chunks: list[AdvisorKnowledgeChunk],
        prompt: AdvisorPrompt,
    ) -> AdvisorAskResponse:
        try:
            payload = self.post_json(
                f"{self.config.base_url.rstrip('/')}/responses",
                {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                self.request_body(prompt),
                self.config.timeout_seconds,
            )
            model_response = parse_json_text(extract_response_text(payload))
            return self.response_from_model(model_response, request, context, chunks)
        except Exception as exc:
            response = self.fallback.answer(request, context, chunks, prompt)
            response.notes.insert(0, f"Live provider fallback used: {exc}")
            return response

    def request_body(self, prompt: AdvisorPrompt) -> dict[str, Any]:
        system = "\n".join(
            [
                prompt.system,
                "Return only JSON that matches the supplied schema.",
                "Use citation_chunk_ids from the retrieved chunk ids only.",
                "Copy used_numbers exactly from the allowed numbers list.",
                "Do not introduce any numeric value that is not in the allowed numbers list.",
            ]
        )
        body: dict[str, Any] = {
            "model": self.config.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt.user}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "finscope_advisor_answer",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                }
            },
            "max_output_tokens": self.config.max_output_tokens,
        }
        if self.config.temperature is not None:
            body["temperature"] = self.config.temperature
        return body

    def response_from_model(
        self,
        payload: dict[str, Any],
        request: AdvisorAskRequest,
        context: AdvisorContextResponse,
        chunks: list[AdvisorKnowledgeChunk],
    ) -> AdvisorAskResponse:
        answer = str(payload.get("answer", "")).strip()
        if not answer:
            raise ValueError("answer must not be empty.")

        bullets = validated_strings(payload, "summary_bullets", 6)
        used_numbers = validated_strings(payload, "used_numbers", 16)
        invalid_numbers = [item for item in used_numbers if item not in context.allowed_numbers]
        if invalid_numbers:
            raise ValueError(f"used_numbers contains unsupported entries: {invalid_numbers}")

        unsupported = unsupported_number_tokens("\n".join([answer, *bullets]), context)
        if unsupported:
            raise ValueError(f"answer introduced unsupported numbers: {sorted(unsupported)}")

        chunk_map = {chunk.id: chunk for chunk in chunks}
        citation_ids = validated_strings(payload, "citation_chunk_ids", 8)
        citations = [citation_from_chunk(chunk_map[chunk_id]) for chunk_id in citation_ids if chunk_id in chunk_map]
        if chunks and not citations:
            raise ValueError("No valid citation chunk ids were returned.")

        confidence = str(payload.get("confidence", "medium")).strip().lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"

        return AdvisorAskResponse(
            answer=answer,
            summary_bullets=bullets,
            citations=citations,
            used_numbers=used_numbers,
            missing_data=context.missing_data,
            retrieved_chunks=chunks,
            guardrails=context.guardrails,
            confidence=confidence,
            provider=self.provider,
            notes=[
                f"Live provider returned a structured response with model {self.config.model}.",
                "The backend checked that used numbers came from the advisor context pack.",
            ],
        )

    def _post_json(
        self,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(url, headers=headers, json=json_body)
            response.raise_for_status()
            return response.json()


def configured_advisor_client(settings: Settings) -> AdvisorAnswerClient | None:
    provider = settings.advisor_llm_provider.strip().lower()
    if provider in {"", "none", "deterministic", "deterministic_fallback"}:
        return None
    if provider != "openai":
        return None
    if not settings.advisor_llm_api_key:
        return None

    return OpenAIResponsesAdvisorClient(
        OpenAIResponsesConfig(
            api_key=settings.advisor_llm_api_key,
            model=settings.advisor_llm_model,
            base_url=settings.advisor_llm_base_url,
            timeout_seconds=settings.advisor_llm_timeout_seconds,
            max_output_tokens=settings.advisor_llm_max_output_tokens,
            temperature=settings.advisor_llm_temperature,
        )
    )
