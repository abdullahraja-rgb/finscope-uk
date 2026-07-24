from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.schemas.transactions import AdvisorKnowledgeChunk, AdvisorRetrieveResponse
from app.services.advisor_embeddings import EmbeddingModel


# Reciprocal Rank Fusion damping and the depth of each ranked list to fuse.
RRF_K = 60
RRF_TOP_N = 10

# Chunk size bounds. Keeping passages focused sharpens both citations and
# embedding vectors, which blur when one chunk spans several topics.
MAX_CHUNK_WORDS = 280
CHUNK_OVERLAP_WORDS = 40

# Chunk embeddings are stable per (docs_dir, model); cache them across requests.
_EMBED_CACHE: dict[tuple[str, str], dict[str, list[float]]] = {}


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

# Plain-English names shown to users in place of internal document filenames.
SOURCE_LABELS: dict[str, str] = {
    "advisor-context.md": "How this advisor works",
    "cost-of-living-engine.md": "Cost of living",
    "financial-health-score.md": "Financial health score",
    "rate-impact-engine.md": "Bank Rate impact",
    "recommendations-engine.md": "Recommendations",
    "spend-forecasting.md": "Spending forecast",
    "transaction-categorisation.md": "Spending categories",
    "dashboard-data-flow.md": "Your dashboard",
    "upload-analysis-flow.md": "Statement uploads",
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


def source_label(source: str) -> str:
    """User-facing name for a document. Never expose the filename itself."""
    return SOURCE_LABELS.get(source, title_from_source(source))


def chunk_body_text(text: str) -> str:
    """Strip the internal heading breadcrumb from chunk text for display."""
    parts = text.split("\n\n", 1)
    return parts[1] if len(parts) == 2 else text


def source_allowed(source: str, sources: list[str] | None) -> bool:
    if not sources:
        return True
    wanted = {item.lower() for item in sources}
    return source.lower() in wanted or source.removesuffix(".md").lower() in wanted


def split_into_units(body: str) -> list[str]:
    """Split a section body into paragraph/list blocks separated by blank lines."""
    units: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            units.append("\n".join(current))
            current = []
    if current:
        units.append("\n".join(current))
    return units


def normalise_units(units: list[str], max_words: int) -> list[str]:
    """Break oversized blocks (such as long bullet lists) down to line units."""
    result: list[str] = []
    for unit in units:
        if len(unit.split()) <= max_words:
            result.append(unit)
            continue
        result.extend(line for line in unit.splitlines() if line.strip())
    return result


def pack_units(units: list[str], max_words: int, overlap_words: int) -> list[str]:
    """Greedily pack units into windows, carrying an overlap into the next window.

    The overlap keeps a passage's lead-in with its continuation so a sentence
    split across a boundary is still retrievable from either side.
    """
    windows: list[str] = []
    current: list[str] = []
    current_words = 0

    for unit in units:
        unit_words = len(unit.split())
        if current and current_words + unit_words > max_words:
            windows.append("\n\n".join(current))
            carry: list[str] = []
            carried = 0
            for previous in reversed(current):
                if carried >= overlap_words:
                    break
                carry.insert(0, previous)
                carried += len(previous.split())
            current = carry
            current_words = sum(len(item.split()) for item in current)
        current.append(unit)
        current_words += unit_words

    if current:
        windows.append("\n\n".join(current))
    return windows


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
        breadcrumb = " > ".join(current_path)
        units = normalise_units(split_into_units(body), MAX_CHUNK_WORDS)
        for window in pack_units(units, MAX_CHUNK_WORDS, CHUNK_OVERLAP_WORDS):
            chunk_text = f"{breadcrumb}\n\n{window}".strip()
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


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    k: int = RRF_K,
    top_n: int = RRF_TOP_N,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking[:top_n]):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


def cosine_scores(query_vector: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = float(np.linalg.norm(query_vector))
    row_norms = np.linalg.norm(matrix, axis=1)
    denominator = row_norms * query_norm
    dots = matrix @ query_vector
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator > 0, dots / denominator, 0.0)


def chunk_embeddings(docs_dir: str, embedder: EmbeddingModel) -> dict[str, list[float]]:
    # Embed the full document set (not the source-filtered subset) so the cache
    # key stays stable regardless of per-request source filters.
    key = (docs_dir, embedder.name)
    cached = _EMBED_CACHE.get(key)
    if cached is None:
        full_chunks = load_knowledge_chunks(docs_dir)
        vectors = embedder.embed([chunk.text for chunk in full_chunks])
        cached = {chunk.id: vector for chunk, vector in zip(full_chunks, vectors)}
        _EMBED_CACHE[key] = cached
    return cached


def _to_chunk_model(score: float, chunk: KnowledgeChunk) -> AdvisorKnowledgeChunk:
    return AdvisorKnowledgeChunk(
        id=chunk.id,
        title=chunk.title,
        source=chunk.source,
        source_label=source_label(chunk.source),
        heading_path=list(chunk.heading_path),
        text=chunk.text,
        body=chunk_body_text(chunk.text),
        score=round(float(score), 4),
        tags=list(chunk.tags),
    )


def _lexical_only_response(
    question: str,
    lexical_scored: list[tuple[float, KnowledgeChunk]],
    max_chunks: int,
    min_score: float,
    notes: list[str],
) -> AdvisorRetrieveResponse:
    matches = [(score, chunk) for score, chunk in lexical_scored if score >= min_score][:max_chunks]
    if not matches:
        notes.append("No strong knowledge match was found for the question.")
    return AdvisorRetrieveResponse(
        query=question,
        chunks=[_to_chunk_model(score, chunk) for score, chunk in matches],
        notes=notes,
    )


def retrieve_advisor_chunks(
    question: str,
    docs_dir: str,
    max_chunks: int = 4,
    min_score: float = 0.05,
    sources: list[str] | None = None,
    embedder: EmbeddingModel | None = None,
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
    lexical_scored = sorted(
        ((score_chunk(question, query_tokens, idf, chunk), chunk) for chunk in all_chunks),
        key=lambda item: item[0],
        reverse=True,
    )

    # Default, dependency-free path: pure lexical retrieval (unchanged behaviour).
    if embedder is None:
        return _lexical_only_response(question, lexical_scored, max_chunks, min_score, notes)

    # Hybrid path: fuse the lexical ranking with a dense embedding ranking. Any
    # embedding failure degrades gracefully to lexical so a bad model never
    # takes the advisor down.
    try:
        embeddings = chunk_embeddings(docs_dir, embedder)
        chunk_ids = [chunk.id for chunk in all_chunks]
        matrix = np.asarray([embeddings[chunk_id] for chunk_id in chunk_ids], dtype=float)
        query_vector = np.asarray(embedder.embed([question])[0], dtype=float)
        dense_scores = cosine_scores(query_vector, matrix)
    except Exception as exc:  # noqa: BLE001 - degrade to lexical on any embedding error
        notes.append(f"Embedding retrieval unavailable, used lexical only ({exc}).")
        return _lexical_only_response(question, lexical_scored, max_chunks, min_score, notes)

    dense_ranked_ids = [
        chunk_id
        for chunk_id, _ in sorted(zip(chunk_ids, dense_scores), key=lambda item: item[1], reverse=True)
    ]
    lexical_ranked_ids = [chunk.id for score, chunk in lexical_scored if score > 0]

    fused = reciprocal_rank_fusion([lexical_ranked_ids, dense_ranked_ids])
    chunk_by_id = {chunk.id: chunk for chunk in all_chunks}
    ordered = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:max_chunks]
    matches = [(score, chunk_by_id[chunk_id]) for chunk_id, score in ordered if chunk_id in chunk_by_id]

    notes.append(f"Hybrid retrieval fused lexical scores with {embedder.name} embeddings.")
    if not matches:
        notes.append("No strong knowledge match was found for the question.")

    return AdvisorRetrieveResponse(
        query=question,
        chunks=[_to_chunk_model(score, chunk) for score, chunk in matches],
        notes=notes,
    )
