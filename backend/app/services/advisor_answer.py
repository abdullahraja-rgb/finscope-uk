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
from app.services.advisor_extractive import extractive_explanation
from app.services.advisor_intent import (
    SECTION_FACT_PRIORITY,
    QuestionIntent,
    build_question_intent,
)
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


# Opening lines vary by detected intent so answers read differently for
# "why", "how much", advice, and plain explanation questions. Every template
# keeps the "supplied FinScope facts" grounding clause.
OPENING_TEMPLATES = {
    "why": "Here is what is driving your {topic}, using the supplied FinScope facts and project methodology.",
    "how_much": "Here are the key figures for your {topic} from the supplied FinScope facts.",
    "what_should_i_do": "Here is what the supplied FinScope facts suggest you focus on for your {topic}.",
    "explain": "Here is an explanation of your {topic} from the supplied FinScope facts and project methodology.",
}


def select_facts_for_intent(
    context: AdvisorContextResponse,
    intent: QuestionIntent,
    limit: int = 6,
) -> list[AdvisorFact]:
    """Choose facts based on where the question routed, not a fixed list.

    First pass takes the prioritised facts for each routed section; the second
    pass backfills any remaining facts from those sections (dynamic ids such as
    top_spend_category_4 or rate_line_*) up to the limit.
    """
    facts = facts_by_id(context)
    selected: list[AdvisorFact] = []
    seen: set[str] = set()

    def take(item: AdvisorFact) -> bool:
        if item.id in seen:
            return False
        selected.append(item)
        seen.add(item.id)
        return len(selected) >= limit

    for section_id in intent.sections:
        for fact_id in SECTION_FACT_PRIORITY.get(section_id, []):
            item = facts.get(fact_id)
            if item is not None and take(item):
                return selected

    for section_id in intent.sections:
        current = section_by_id(context, section_id)
        if current is None:
            continue
        for item in current.facts:
            if take(item):
                return selected

    return selected


class DeterministicAdvisorClient:
    provider = "deterministic_fallback"

    def answer(
        self,
        request: AdvisorAskRequest,
        context: AdvisorContextResponse,
        chunks: list[AdvisorKnowledgeChunk],
        prompt: AdvisorPrompt,
    ) -> AdvisorAskResponse:
        intent = build_question_intent(request.question)
        selected_facts = select_facts_for_intent(context, intent)
        selected_fact_ids = [item.id for item in selected_facts]

        opening = OPENING_TEMPLATES.get(intent.kind, OPENING_TEMPLATES["explain"]).format(topic=intent.topic_label)
        answer_parts = [opening]
        if context.missing_data:
            answer_parts.append("Some inputs are missing, so treat this as a partial view.")

        # Lead with the facts the question actually routed to.
        for item in selected_facts[:3]:
            sentence = fact_sentence(item)
            if sentence:
                answer_parts.append(sentence)

        # Weave in the retrieved methodology sentences that match the question.
        for sentence, chunk in extractive_explanation(request.question, chunks, limit=2):
            answer_parts.append(f"{sentence.rstrip('.')}. This reflects the {chunk.source} methodology.")

        if context.missing_data:
            top_missing = context.missing_data[0]
            answer_parts.append(f"The first data gap to close is {top_missing.label}: {top_missing.action}")

        bullets = [sentence for item in selected_facts if (sentence := fact_sentence(item))]
        if not bullets:
            bullets = ["I do not have enough supplied facts to explain this yet."]

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
                "This response used the deterministic extractive synthesizer (no LLM call).",
                f"Question routed to sections: {', '.join(intent.sections[:3]) or 'none'} (intent: {intent.kind}).",
                f"Prompt prepared with {len(prompt.user)} user-context characters.",
            ],
        )


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
