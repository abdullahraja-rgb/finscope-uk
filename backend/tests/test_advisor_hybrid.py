from pathlib import Path

import numpy as np

from app.services.advisor_embeddings import configured_embedder
from app.services.advisor_retrieval import (
    cosine_scores,
    reciprocal_rank_fusion,
    retrieve_advisor_chunks,
)


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


# Concept dimensions used by the stub so tests exercise the dense path without
# any real model, dependency, or network download.
STUB_CONCEPTS = {
    "inflation": {"inflation", "cost", "living", "prices", "price", "cpih"},
    "forecast": {"forecast", "forecasting", "spend", "next", "predict", "backtest"},
    "rate": {"rate", "interest", "mortgage", "bank", "debt"},
    "health": {"health", "score", "savings", "emergency", "buffer"},
}


class StubEmbedder:
    name = "stub-concept-embedder"

    def embed(self, texts):
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        lowered = text.lower()
        return [float(sum(1 for word in words if word in lowered)) for words in STUB_CONCEPTS.values()]


class BrokenEmbedder:
    name = "broken-embedder"

    def embed(self, texts):
        raise RuntimeError("model unavailable")


def test_reciprocal_rank_fusion_combines_rankings() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]], k=60)

    # "b" is rank 1 then rank 0; "a" is rank 0 then rank 1 — both beat singletons.
    ranked = sorted(fused, key=lambda key: fused[key], reverse=True)
    assert set(ranked[:2]) == {"a", "b"}
    assert fused["a"] > fused["c"]
    assert fused["b"] > fused["d"]


def test_cosine_scores_matches_expected() -> None:
    query = np.array([1.0, 0.0])
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    scores = cosine_scores(query, matrix)

    assert scores[0] == 1.0
    assert scores[1] == 0.0
    assert abs(scores[2] - (1 / np.sqrt(2))) < 1e-9


def test_hybrid_retrieval_returns_citation_ready_chunks() -> None:
    response = retrieve_advisor_chunks(
        "Why are rising living prices squeezing my budget?",
        docs_dir=str(DOCS_DIR),
        max_chunks=4,
        embedder=StubEmbedder(),
    )

    assert response.chunks
    assert len(response.chunks) <= 4
    assert any("Hybrid retrieval" in note for note in response.notes)
    assert {"id", "source", "text", "score", "heading_path"}.issubset(response.chunks[0].model_dump().keys())
    # Concept stub aligns the query with the cost-of-living document.
    assert "cost-of-living-engine.md" in {chunk.source for chunk in response.chunks}


def test_hybrid_falls_back_to_lexical_on_embed_error() -> None:
    response = retrieve_advisor_chunks(
        "How does Bank Rate affect my debt?",
        docs_dir=str(DOCS_DIR),
        max_chunks=3,
        embedder=BrokenEmbedder(),
    )

    assert response.chunks  # still answered via lexical
    assert any("used lexical only" in note for note in response.notes)
    assert not any("Hybrid retrieval" in note for note in response.notes)


def test_lexical_and_hybrid_can_differ() -> None:
    question = "Why are rising living prices squeezing my budget?"
    lexical = retrieve_advisor_chunks(question, docs_dir=str(DOCS_DIR), max_chunks=4)
    hybrid = retrieve_advisor_chunks(question, docs_dir=str(DOCS_DIR), max_chunks=4, embedder=StubEmbedder())

    assert lexical.chunks
    assert hybrid.chunks
    # The dense signal is allowed to reorder or swap results; at minimum the
    # hybrid path is annotated so the source of ranking is auditable.
    assert any("Hybrid retrieval" in note for note in hybrid.notes)
    assert not any("Hybrid retrieval" in note for note in lexical.notes)


def test_configured_embedder_is_disabled_by_default() -> None:
    assert configured_embedder("lexical", "BAAI/bge-small-en-v1.5") is None
    # Hybrid with a nonexistent model degrades to None rather than raising,
    # whether or not fastembed is installed.
    assert configured_embedder("hybrid", "definitely-not-a-real-model-xyz") is None
