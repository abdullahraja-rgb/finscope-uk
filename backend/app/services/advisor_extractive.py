from __future__ import annotations

import math
import re

from app.schemas.transactions import AdvisorKnowledgeChunk
from app.services.advisor_retrieval import tokenize


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
MIN_SENTENCE_CHARS = 20
MIN_SENTENCE_TOKENS = 4


def chunk_body(chunk: AdvisorKnowledgeChunk) -> str:
    # Chunk text is stored as "Heading > Sub\n\nbody"; drop the heading path line
    # so we quote the explanation itself, not the breadcrumb.
    parts = chunk.text.split("\n\n", 1)
    return parts[1] if len(parts) == 2 else chunk.text


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*#> ").strip()
        if not stripped:
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
