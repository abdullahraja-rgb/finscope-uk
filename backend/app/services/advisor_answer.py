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
from app.services.advisor_embeddings import EmbeddingModel
from app.services.advisor_extractive import extractive_explanation
from app.services.advisor_intent import (
    SECTION_FACT_PRIORITY,
    QuestionIntent,
    build_question_intent,
)
from app.services.advisor_retrieval import retrieve_advisor_chunks, source_label, tokenize


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
    # Some formatted values already end in a full stop; avoid "covered..".
    return f"{fact.label} is {fact.formatted.rstrip('.')}."


def citation_from_chunk(chunk: AdvisorKnowledgeChunk) -> AdvisorCitation:
    return AdvisorCitation(
        source=chunk.source,
        source_label=chunk.source_label or source_label(chunk.source),
        title=chunk.title,
        chunk_id=chunk.id,
        heading_path=chunk.heading_path,
    )


def readable_list(items: list[str]) -> str:
    """Join names the way a person would write them: "a, b and c"."""
    unique = list(dict.fromkeys(item for item in items if item))
    if len(unique) <= 1:
        return unique[0] if unique else ""
    return f"{', '.join(unique[:-1])} and {unique[-1]}"


def relevant_used_numbers(context: AdvisorContextResponse, selected_fact_ids: list[str]) -> list[str]:
    selected_labels = {facts_by_id(context)[fact_id].label for fact_id in selected_fact_ids if fact_id in facts_by_id(context)}
    return [
        item
        for item in context.allowed_numbers
        if item.split(":", 1)[0] in selected_labels
    ]


# Opening lines vary by detected intent so answers read differently for
# "why", "how much", advice, and plain explanation questions. Wording stays in
# everyday language: no internal names, file names, or system terminology.
OPENING_TEMPLATES = {
    "why": "Here is what is driving your {topic}, based on your own figures.",
    "how_much": "Here are the key figures for your {topic}.",
    "what_should_i_do": "Here is what your figures suggest you focus on for your {topic}.",
    "explain": "Here is an explanation of your {topic}, based on your own figures.",
}


def select_facts_for_intent(
    context: AdvisorContextResponse,
    intent: QuestionIntent,
    question: str = "",
    limit: int = 6,
) -> list[AdvisorFact]:
    """Choose facts based on where the question routed, not a fixed list.

    Candidates come from the routed sections, prioritised facts first and any
    remaining section facts after. They are then reordered so the fact the
    question actually names leads the answer: "which component drags my score
    down" opens on the weakest component, not the headline score.
    """
    facts = facts_by_id(context)
    candidates: list[AdvisorFact] = []
    seen: set[str] = set()

    def take(item: AdvisorFact) -> None:
        if item.id not in seen:
            candidates.append(item)
            seen.add(item.id)

    for section_id in intent.sections:
        for fact_id in SECTION_FACT_PRIORITY.get(section_id, []):
            item = facts.get(fact_id)
            if item is not None:
                take(item)

    for section_id in intent.sections:
        current = section_by_id(context, section_id)
        if current is None:
            continue
        for item in current.facts:
            take(item)

    question_tokens = set(tokenize(question))
    if not question_tokens:
        return candidates[:limit]

    def relevance(entry: tuple[int, AdvisorFact]) -> tuple[int, int]:
        position, item = entry
        overlap = len(question_tokens & set(tokenize(item.label)))
        return (-overlap, position)

    ordered = [item for _, item in sorted(enumerate(candidates), key=relevance)]
    return ordered[:limit]


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
        selected_facts = select_facts_for_intent(context, intent, request.question)
        selected_fact_ids = [item.id for item in selected_facts]

        opening = OPENING_TEMPLATES.get(intent.kind, OPENING_TEMPLATES["explain"]).format(topic=intent.topic_label)
        answer_parts = [opening]
        if context.missing_data:
            answer_parts.append("Some details are still missing, so this is a partial picture.")

        # Lead with the facts the question actually routed to.
        for item in selected_facts[:3]:
            sentence = fact_sentence(item)
            if sentence:
                answer_parts.append(sentence)

        # Weave in the background explanation, then attribute it once using
        # friendly topic names rather than internal document names.
        explanation = extractive_explanation(request.question, chunks, limit=2)
        for sentence, _chunk in explanation:
            answer_parts.append(f"{sentence.rstrip('.')}.")
        if explanation:
            topics = readable_list([chunk.source_label or source_label(chunk.source) for _, chunk in explanation])
            if topics:
                answer_parts.append(f"You can read more under {topics}.")

        if context.missing_data:
            top_missing = context.missing_data[0]
            answer_parts.append(f"To improve this, {top_missing.action[0].lower()}{top_missing.action[1:]}")

        bullets = [sentence for item in selected_facts if (sentence := fact_sentence(item))]
        if not bullets:
            bullets = ["There are not enough supplied facts to explain this yet."]

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
    embedder: EmbeddingModel | None = None,
) -> AdvisorAskResponse:
    context = build_advisor_context(request)
    retrieval = retrieve_advisor_chunks(
        question=request.question,
        docs_dir=docs_dir,
        max_chunks=request.max_chunks,
        min_score=request.min_retrieval_score,
        embedder=embedder,
    )
    chunks = retrieval.chunks
    prompt = build_advisor_prompt(request, context, chunks)
    answer_client = client or DeterministicAdvisorClient()
    response = answer_client.answer(request, context, chunks, prompt)
    response.notes.extend(retrieval.notes)
    return response
