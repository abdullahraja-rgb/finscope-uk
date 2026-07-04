from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.schemas.transactions import AdvisorKnowledgeChunk, AdvisorRetrieveResponse


DOC_SOURCES: dict[str, list[str]] = {
    "advisor-context.md": ["advisor", "context", "guardrails", "missing-data"],
    "cost-of-living-engine.md": ["inflation", "ons", "cost-of-living", "personal-inflation"],
    "financial-health-score.md": ["health-score", "savings", "debt", "housing", "benchmarks"],
    "rate-impact-engine.md": ["bank-rate", "interest-rates", "mortgage", "debt", "savings"],
    "recommendations-engine.md": ["recommendations", "actions", "rules"],
    "spend-forecasting.md": ["forecasting", "time-series", "backtesting", "baseline"],
    "transaction-categorisation.md": ["categorisation", "classification", "f1", "merchant"],
    "dashboard-data-flow.md": ["dashboard", "data-flow", "profile", "transactions"],
    "upload-analysis-flow.md": ["upload", "csv", "analysis", "transactions"],
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "use",
    "what",
    "when",
    "why",
    "with",
}

TAG_ALIASES: dict[str, set[str]] = {
    "inflation": {"inflation", "cost", "living", "cpi", "cpih", "ons", "prices"},
    "personal-inflation": {"personal", "inflation", "basket", "weighted"},
    "forecasting": {"forecast", "forecasting", "predict", "next", "month", "spend"},
    "time-series": {"time", "series", "seasonality", "trend"},
    "backtesting": {"backtest", "backtesting", "validation", "random", "split", "future", "leakage"},
    "baseline": {"baseline", "naive"},
    "health-score": {"health", "score", "financial", "component"},
    "savings": {"saving", "savings", "emergency", "buffer"},
    "debt": {"debt", "loan", "card", "overdraft", "apr"},
    "housing": {"housing", "rent", "mortgage"},
    "bank-rate": {"bank", "rate", "boe", "interest"},
    "categorisation": {"categorise", "categorisation", "category", "merchant"},
    "classification": {"classification", "classifier", "model"},
    "f1": {"f1", "accuracy", "precision", "recall", "confusion"},
    "advisor": {"advisor", "rag", "llm", "answer"},
    "context": {"context", "fact", "number", "citation"},
    "guardrails": {"guardrail", "guardrails", "invent", "advice"},
    "transactions": {"transaction", "transactions", "csv", "upload", "row"},
}


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    title: str
    source: str
    heading_path: tuple[str, ...]
    text: str
    tags: tuple[str, ...]
    tokens: tuple[str, ...]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def title_from_source(source: str) -> str:
    return source.removesuffix(".md").replace("-", " ").title()


def source_tags(source: str) -> tuple[str, ...]:
    return tuple(DOC_SOURCES.get(source, []))


def source_allowed(source: str, sources: list[str] | None) -> bool:
    if not sources:
        return True
    wanted = {item.lower() for item in sources}
    return source.lower() in wanted or source.removesuffix(".md").lower() in wanted


def chunk_markdown(source: str, text: str) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    heading_stack: list[tuple[int, str]] = []
    current_heading = title_from_source(source)
    current_lines: list[str] = []
    current_path: tuple[str, ...] = (current_heading,)

    def flush() -> None:
        body = "\n".join(line for line in current_lines).strip()
        if not body:
            return
        chunk_title = current_path[-1] if current_path else current_heading
        chunk_text = f"{' > '.join(current_path)}\n\n{body}".strip()
        chunk_id = f"{source}:{slugify(' '.join(current_path))}:{len(chunks) + 1}"
        chunks.append(
            KnowledgeChunk(
                id=chunk_id,
                title=chunk_title,
                source=source,
                heading_path=current_path,
                text=chunk_text,
                tags=source_tags(source),
                tokens=tuple(tokenize(chunk_text + " " + " ".join(source_tags(source)))),
            )
        )

    for line in text.splitlines():
        match = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if match:
            flush()
            current_lines = []
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_stack = [item for item in heading_stack if item[0] < level]
            heading_stack.append((level, heading))
            current_path = tuple(item[1] for item in heading_stack)
            continue
        current_lines.append(line)

    flush()
    return chunks


@lru_cache
def load_knowledge_chunks(docs_dir: str) -> tuple[KnowledgeChunk, ...]:
    base = Path(docs_dir).resolve()
    chunks: list[KnowledgeChunk] = []
    for source in DOC_SOURCES:
        path = base / source
        if not path.exists():
            continue
        chunks.extend(chunk_markdown(source, path.read_text(encoding="utf-8")))
    return tuple(chunks)


def idf_by_token(chunks: list[KnowledgeChunk]) -> dict[str, float]:
    document_count = len(chunks)
    frequencies: dict[str, int] = {}
    for chunk in chunks:
        for token in set(chunk.tokens):
            frequencies[token] = frequencies.get(token, 0) + 1
    return {
        token: math.log((document_count + 1) / (frequency + 1)) + 1
        for token, frequency in frequencies.items()
    }


def tag_boost(query_tokens: set[str], chunk: KnowledgeChunk) -> float:
    boost = 0.0
    for tag in chunk.tags:
        aliases = TAG_ALIASES.get(tag, {tag})
        if query_tokens.intersection(aliases):
            boost += 0.3
    return boost


def score_chunk(query: str, query_tokens: list[str], idf: dict[str, float], chunk: KnowledgeChunk) -> float:
    if not query_tokens:
        return 0.0

    chunk_text = chunk.text.lower()
    token_counts: dict[str, int] = {}
    for token in chunk.tokens:
        token_counts[token] = token_counts.get(token, 0) + 1

    query_token_set = set(query_tokens)
    score = 0.0
    for token in query_token_set:
        score += min(token_counts.get(token, 0), 3) * idf.get(token, 1.0)

    if query.lower().strip() in chunk_text:
        score += 2.0

    two_word_phrases = zip(query_tokens, query_tokens[1:])
    for first, second in two_word_phrases:
        if f"{first} {second}" in chunk_text:
            score += 0.7

    score += tag_boost(query_token_set, chunk)
    return score / max(len(query_token_set), 1)


def retrieve_advisor_chunks(
    question: str,
    docs_dir: str,
    max_chunks: int = 4,
    min_score: float = 0.05,
    sources: list[str] | None = None,
) -> AdvisorRetrieveResponse:
    all_chunks = [
        chunk
        for chunk in load_knowledge_chunks(docs_dir)
        if source_allowed(chunk.source, sources)
    ]
    notes: list[str] = []
    if not all_chunks:
        return AdvisorRetrieveResponse(
            query=question,
            chunks=[],
            notes=["No advisor knowledge documents were available."],
        )

    query_tokens = tokenize(question)
    idf = idf_by_token(all_chunks)
    scored = [
        (score_chunk(question, query_tokens, idf, chunk), chunk)
        for chunk in all_chunks
    ]
    matches = [
        (score, chunk)
        for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True)
        if score >= min_score
    ][:max_chunks]

    if not matches:
        notes.append("No strong knowledge match was found for the question.")

    return AdvisorRetrieveResponse(
        query=question,
        chunks=[
            AdvisorKnowledgeChunk(
                id=chunk.id,
                title=chunk.title,
                source=chunk.source,
                heading_path=list(chunk.heading_path),
                text=chunk.text,
                score=round(score, 4),
                tags=list(chunk.tags),
            )
            for score, chunk in matches
        ],
        notes=notes,
    )
