from __future__ import annotations

from functools import lru_cache
from typing import Protocol, Sequence


class EmbeddingModel(Protocol):
    name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class FastEmbedModel:
    """Local, offline sentence embeddings via fastembed (ONNX runtime, no torch).

    fastembed is an optional dependency. It is imported lazily so the app runs
    with pure-lexical retrieval when the package or its model is not present.
    """

    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding  # optional dependency, imported lazily

        self.name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [list(map(float, vector)) for vector in self._model.embed(list(texts))]


@lru_cache
def configured_embedder(mode: str, model_name: str) -> EmbeddingModel | None:
    """Return a local embedding model only when hybrid retrieval is enabled.

    Defaults are safe. Unless ``mode`` is ``hybrid`` (or ``auto`` with fastembed
    installed), this returns ``None`` and retrieval stays purely lexical. Any
    failure to import fastembed or load the model also returns ``None`` so the
    advisor never breaks because of an optional dependency.
    """
    normalised = mode.strip().lower()
    if normalised not in {"hybrid", "auto"}:
        return None
    try:
        return FastEmbedModel(model_name)
    except Exception:
        return None
