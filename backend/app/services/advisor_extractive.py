from __future__ import annotations

import math
import re

from app.schemas.transactions import AdvisorKnowledgeChunk
from app.services.advisor_retrieval import tokenize


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
MIN_SENTENCE_CHARS = 20
MIN_SENTENCE_TOKENS = 6

# Bullet and numbered list items in this knowledge base are terse notes
# ("Three-month moving average."), not prose, so they read badly when quoted
# back to a user. Only full paragraph lines are used as explanation text.
LIST_ITEM_PATTERN = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
BLOCK_PREFIXES = ("#", ">", "|", "```")

# The knowledge base is written as engineering notes, so quoted sentences must
# be screened before they reach a dashboard user. Anything mentioning internals
# is dropped rather than reworded, keeping the quote faithful to its source.
DEV_TERMS = frozenset(
    {
        "api",
        "endpoint",
        "endpoints",
        "backend",
        "frontend",
        "schema",
        "payload",
        "module",
        "repo",
        "repository",
        "function",
        "parameter",
        "parameters",
        "config",
        "database",
        "pipeline",
        "deploy",
        "classifier",
        "regression",
        "backtest",
        "backtests",
        "backtesting",
        "leakage",
        "naive",
        "prompt",
        "row",
        "rows",
        "field",
        "fields",
        # Project-internal vocabulary: the knowledge base is written as
        # engineering notes about this system, so its own terms leak easily.
        "chunk",
        "chunks",
        "retrieval",
        "retriever",
        "embedding",
        "embeddings",
        "deterministic",
        "fallback",
        "provider",
        "guardrail",
        "guardrails",
        "methodology",
        "markdown",
        "llm",
        "synthesiser",
        "synthesizer",
        # The advisor speaks to the reader, so third-person "the user" reads as
        # system documentation rather than advice.
        "user",
        "users",
        "engine",
        "engines",
    }
)

# Extracted sentences must stand on their own. Ones opening with a back
# reference ("It also keeps ...") lose their subject once lifted out of context.
DANGLING_STARTS = (
    "it ", "this ", "that ", "these ", "those ", "they ",
    "instead", "however", "also ", "then ", "here ", "there ",
)

# Internal terms that only read as jargon as a phrase.
DEV_PHRASES = ("context pack", "knowledge base", "transaction row", "data gap", "source label")

# Acronyms a dashboard user can reasonably be expected to read.
ALLOWED_ACRONYMS = frozenset({"GBP", "UK", "ONS", "CPI", "CPIH", "APR", "ISA", "CSV", "PDF"})

ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")
SNAKE_CASE_PATTERN = re.compile(r"\b[a-z]+_[a-z_]+\b")
# Markdown definition-style bullets ("Spending: current category spend ...") read
# as UI notes rather than prose, so they are dropped alongside trailing colons.
LABEL_PREFIX_PATTERN = re.compile(r"^[A-Za-z][\w /-]{0,24}:\s")
INTERNAL_MARKERS = ("`", ".md", "http", "/api", "()", "{", "}")
# Formulas ("personal inflation = sum(spend share * rate)") are documentation,
# not an explanation a dashboard user can read.
FORMULA_PATTERN = re.compile(r"=|\w\(|\s\*\s|\s/\s")


def is_user_friendly(sentence: str) -> bool:
    """Reject sentences that would expose internals to a dashboard user."""
    stripped = sentence.strip()
    if stripped.endswith(":") or LABEL_PREFIX_PATTERN.match(stripped):
        return False
    lowered = sentence.lower()
    if lowered.startswith(DANGLING_STARTS):
        return False
    if any(marker in lowered for marker in INTERNAL_MARKERS):
        return False
    if any(phrase in lowered for phrase in DEV_PHRASES):
        return False
    if FORMULA_PATTERN.search(sentence):
        return False
    if SNAKE_CASE_PATTERN.search(sentence):
        return False
    if any(acronym not in ALLOWED_ACRONYMS for acronym in ACRONYM_PATTERN.findall(sentence)):
        return False
    return not DEV_TERMS.intersection(re.findall(r"[a-z]+", lowered))


def chunk_body(chunk: AdvisorKnowledgeChunk) -> str:
    # Chunk text is stored as "Heading > Sub\n\nbody"; drop the heading path line
    # so we quote the explanation itself, not the breadcrumb.
    parts = chunk.text.split("\n\n", 1)
    return parts[1] if len(parts) == 2 else chunk.text


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if LIST_ITEM_PATTERN.match(line) or stripped.startswith(BLOCK_PREFIXES):
            continue
        for piece in SENTENCE_SPLIT.split(stripped):
            piece = piece.strip()
            # Skip fragments that are too short, bullet noise, or that contain any
            # digit. Numbers must come only from the trusted context pack, never
            # from quoted methodology text, so a digit-free filter keeps the
            # extractive body grounded.
            if len(piece) < MIN_SENTENCE_CHARS:
                continue
            if re.search(r"\d", piece):
                continue
            if len(tokenize(piece)) < MIN_SENTENCE_TOKENS:
                continue
            if not is_user_friendly(piece):
                continue
            sentences.append(piece)
    return sentences


def collect_sentences(chunks: list[AdvisorKnowledgeChunk]) -> list[tuple[str, AdvisorKnowledgeChunk]]:
    seen: set[str] = set()
    items: list[tuple[str, AdvisorKnowledgeChunk]] = []
    for chunk in chunks:
        for sentence in split_sentences(chunk_body(chunk)):
            key = sentence.lower()
            if key in seen:
                continue
            seen.add(key)
            items.append((sentence, chunk))
    return items


def sentence_idf(token_lists: list[list[str]]) -> dict[str, float]:
    document_count = len(token_lists)
    frequencies: dict[str, int] = {}
    for tokens in token_lists:
        for token in set(tokens):
            frequencies[token] = frequencies.get(token, 0) + 1
    return {
        token: math.log((document_count + 1) / (frequency + 1)) + 1
        for token, frequency in frequencies.items()
    }


def extractive_explanation(
    question: str,
    chunks: list[AdvisorKnowledgeChunk],
    limit: int = 2,
) -> list[tuple[str, AdvisorKnowledgeChunk]]:
    """Pick the sentences from retrieved chunks most relevant to the question.

    This is what makes the deterministic answer vary per question: instead of
    naming chunk sources, it quotes the specific methodology sentences that
    match the query, scored by IDF-weighted token overlap.
    """
    items = collect_sentences(chunks)
    query_tokens = set(tokenize(question))
    if not items or not query_tokens:
        return []

    token_lists = [tokenize(sentence) for sentence, _ in items]
    idf = sentence_idf(token_lists)

    scored: list[tuple[float, str, AdvisorKnowledgeChunk]] = []
    for (sentence, chunk), tokens in zip(items, token_lists):
        shared = query_tokens & set(tokens)
        if not shared:
            continue
        score = sum(idf.get(token, 1.0) for token in shared) / math.sqrt(len(tokens) or 1)
        scored.append((score, sentence, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [(sentence, chunk) for _, sentence, chunk in scored[:limit]]
