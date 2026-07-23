from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.transactions import (
    AdvisorAskRequest,
    AdvisorAskResponse,
    AdvisorCitation,
    AdvisorContextResponse,
    AdvisorContextSection,
    AdvisorFact,
    AdvisorKnowledgeChunk,
)
from app.services.advisor_context import build_advisor_context
from app.services.advisor_retrieval import retrieve_advisor_chunks


@dataclass(frozen=True)
class AdvisorPrompt:
    system: str
    user: str


class AdvisorAnswerClient(Protocol):
    provider: str

    def answer(
        self,
        request: AdvisorAskRequest,
        context: AdvisorContextResponse,
        chunks: list[AdvisorKnowledgeChunk],
        prompt: AdvisorPrompt,
    ) -> AdvisorAskResponse:
        ...


def build_advisor_prompt(
    request: AdvisorAskRequest,
    context: AdvisorContextResponse,
    chunks: list[AdvisorKnowledgeChunk],
) -> AdvisorPrompt:
    retrieved_context = "\n\n".join(
        f"[{chunk.source} > {' > '.join(chunk.heading_path)}]\n{chunk.text}"
        for chunk in chunks
    )
    system = "\n".join(
        [
            "You are the FinScope UK advisor.",
            "Explain the user's dashboard using only the supplied context pack and retrieved project knowledge.",
            "Do not invent numbers. Do not give regulated financial advice.",
            "Use plain financial language. Never expose internal field names, snake_case identifiers, API paths, or implementation details.",
            "Return structured output with answer, bullets, citations, used numbers, missing data, and confidence.",
        ]
    )
    user = "\n\n".join(
        [
            f"Question: {request.question}",
            "Context pack:",
            context.context_markdown,
            "Retrieved knowledge:",
            retrieved_context or "No retrieved knowledge chunks.",
        ]
    )
    return AdvisorPrompt(system=system, user=user)


def facts_by_id(context: AdvisorContextResponse) -> dict[str, AdvisorFact]:
    facts: dict[str, AdvisorFact] = {}
    for section in context.sections:
        for item in section.facts:
            facts[item.id] = item
    return facts


def section_by_id(context: AdvisorContextResponse, section_id: str) -> AdvisorContextSection | None:
    for section in context.sections:
        if section.id == section_id:
            return section
    return None


def fact_sentence(fact: AdvisorFact | None) -> str | None:
    if fact is None:
        return None
    return f"{fact.label} is {fact.formatted}."


def citation_from_chunk(chunk: AdvisorKnowledgeChunk) -> AdvisorCitation:
    return AdvisorCitation(
        source=chunk.source,
        title=chunk.title,
        chunk_id=chunk.id,
        heading_path=chunk.heading_path,
    )


def relevant_used_numbers(context: AdvisorContextResponse, selected_fact_ids: list[str]) -> list[str]:
    selected_labels = {facts_by_id(context)[fact_id].label for fact_id in selected_fact_ids if fact_id in facts_by_id(context)}
    return [
        item
        for item in context.allowed_numbers
        if item.split(":", 1)[0] in selected_labels
    ]


class DeterministicAdvisorClient:
    provider = "deterministic_fallback"

    def answer(
        self,
        request: AdvisorAskRequest,
        context: AdvisorContextResponse,
        chunks: list[AdvisorKnowledgeChunk],
        prompt: AdvisorPrompt,
    ) -> AdvisorAskResponse:
        facts = facts_by_id(context)
        selected_fact_ids = [
            "monthly_income",
            "monthly_spend",
            "disposable_income",
            "health_score",
            "weakest_health_component",
            "forecast_expected_total",
            "forecast_upper_total",
            "largest_forecast_category",
            "personal_inflation",
            "national_inflation",
            "inflation_gap",
            "monthly_rate_cashflow_delta",
            "net_worth",
            "consumer_debt",
            "emergency_gap",
        ]
        selected_facts = [facts[fact_id] for fact_id in selected_fact_ids if fact_id in facts]

        opening = "I can explain this from the supplied FinScope facts and project methodology."
        if context.missing_data:
            opening += " Some inputs are missing, so I would treat this as a partial view."

        bullets = self.summary_bullets(facts)
        answer_parts = [opening]
        for item in bullets[:5]:
            answer_parts.append(item)

        if chunks:
            cited_sources = ", ".join(dict.fromkeys(chunk.source for chunk in chunks[:3]))
            answer_parts.append(f"For the methodology behind this, I would cite {cited_sources}.")
        if context.missing_data:
            top_missing = context.missing_data[0]
            answer_parts.append(f"The first data gap to fix is {top_missing.label}: {top_missing.action}")

        confidence = "high"
        if context.missing_data:
            confidence = "medium" if selected_facts else "low"
        if not chunks:
            confidence = "low"

        return AdvisorAskResponse(
            answer=" ".join(answer_parts),
            summary_bullets=bullets,
            citations=[citation_from_chunk(chunk) for chunk in chunks],
            used_numbers=relevant_used_numbers(context, selected_fact_ids),
            missing_data=context.missing_data,
            retrieved_chunks=chunks,
            guardrails=context.guardrails,
            confidence=confidence,
            provider=self.provider,
            notes=[
                "This response used the deterministic fallback. A live LLM provider can replace it behind the same response contract.",
                f"Prompt prepared with {len(prompt.user)} user-context characters.",
            ],
        )

    def summary_bullets(self, facts: dict[str, AdvisorFact]) -> list[str]:
        bullets: list[str] = []

        cash_parts = [
            fact_sentence(facts.get("monthly_income")),
            fact_sentence(facts.get("monthly_spend")),
            fact_sentence(facts.get("disposable_income")),
        ]
        cash_sentence = " ".join(part for part in cash_parts if part)
        if cash_sentence:
            bullets.append(cash_sentence)

        health_parts = [
            fact_sentence(facts.get("health_score")),
            fact_sentence(facts.get("weakest_health_component")),
        ]
        health_sentence = " ".join(part for part in health_parts if part)
        if health_sentence:
            bullets.append(health_sentence)

        forecast_parts = [
            fact_sentence(facts.get("forecast_expected_total")),
            fact_sentence(facts.get("forecast_upper_total")),
            fact_sentence(facts.get("largest_forecast_category")),
        ]
        forecast_sentence = " ".join(part for part in forecast_parts if part)
        if forecast_sentence:
            bullets.append(forecast_sentence)

        inflation_parts = [
            fact_sentence(facts.get("personal_inflation")),
            fact_sentence(facts.get("national_inflation")),
            fact_sentence(facts.get("inflation_gap")),
        ]
        inflation_sentence = " ".join(part for part in inflation_parts if part)
        if inflation_sentence:
            bullets.append(inflation_sentence)

        rate_sentence = fact_sentence(facts.get("monthly_rate_cashflow_delta"))
        if rate_sentence:
            bullets.append(rate_sentence)

        wealth_parts = [
            fact_sentence(facts.get("net_worth")),
            fact_sentence(facts.get("consumer_debt")),
            fact_sentence(facts.get("emergency_gap")),
        ]
        wealth_sentence = " ".join(part for part in wealth_parts if part)
        if wealth_sentence:
            bullets.append(wealth_sentence)

        return bullets or ["I do not have enough supplied facts to explain the dashboard yet."]


def answer_advisor_question(
    request: AdvisorAskRequest,
    docs_dir: str,
    client: AdvisorAnswerClient | None = None,
) -> AdvisorAskResponse:
    context = build_advisor_context(request)
    retrieval = retrieve_advisor_chunks(
        question=request.question,
        docs_dir=docs_dir,
        max_chunks=request.max_chunks,
        min_score=request.min_retrieval_score,
    )
    chunks = retrieval.chunks
    prompt = build_advisor_prompt(request, context, chunks)
    answer_client = client or DeterministicAdvisorClient()
    response = answer_client.answer(request, context, chunks, prompt)
    response.notes.extend(retrieval.notes)
    return response
