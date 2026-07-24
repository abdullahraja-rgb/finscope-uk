from pathlib import Path

import pytest

from app.schemas.transactions import AdvisorAskRequest
from app.services.advisor_answer import answer_advisor_question
from app.services.advisor_embeddings import configured_embedder
from app.services.advisor_eval import EVAL_CASES, distinctness, evaluate_retrieval
from tests.test_advisor_context import full_context_request


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Thresholds sit below the measured baseline so these act as regression guards
# rather than brittle exact-value assertions.
# Measured 2026-07-23: lexical recall@4=0.91, mrr=0.84, routing=1.00, distinctness=1.00.
MIN_RECALL_AT_K = 0.85
MIN_MRR = 0.75
MIN_ROUTING_ACCURACY = 0.90
MIN_DISTINCTNESS = 0.95


def test_eval_set_is_meaningful() -> None:
    assert len(EVAL_CASES) >= 20
    for case in EVAL_CASES:
        assert case.question.strip()
        assert case.expected_sources
        assert all(source.endswith(".md") for source in case.expected_sources)


def test_lexical_retrieval_meets_quality_bar() -> None:
    report = evaluate_retrieval(str(DOCS_DIR))

    assert report.mode == "lexical"
    assert report.recall_at_k >= MIN_RECALL_AT_K, report.retrieval_failures
    assert report.mrr >= MIN_MRR, report.retrieval_failures


def test_intent_routing_meets_quality_bar() -> None:
    report = evaluate_retrieval(str(DOCS_DIR))

    assert report.routing_accuracy >= MIN_ROUTING_ACCURACY, report.routing_failures


def test_answers_stay_distinct_across_the_eval_set() -> None:
    answers = []
    for case in EVAL_CASES:
        payload = full_context_request().model_dump()
        payload["question"] = case.question
        answers.append(answer_advisor_question(AdvisorAskRequest(**payload), docs_dir=str(DOCS_DIR)).answer)

    assert distinctness(answers) >= MIN_DISTINCTNESS


def test_distinctness_helper() -> None:
    assert distinctness(["a", "b", "c"]) == 1.0
    assert distinctness(["a", "a", "a"]) == pytest.approx(1 / 3)
    assert distinctness([]) == 0.0


@pytest.mark.skipif(
    configured_embedder("hybrid", EMBEDDING_MODEL) is None,
    reason="fastembed or the embedding model is not available",
)
def test_hybrid_is_at_least_as_good_as_lexical() -> None:
    lexical = evaluate_retrieval(str(DOCS_DIR))
    hybrid = evaluate_retrieval(str(DOCS_DIR), embedder=configured_embedder("hybrid", EMBEDDING_MODEL))

    assert hybrid.mode == "hybrid"
    assert hybrid.recall_at_k >= lexical.recall_at_k
    assert hybrid.mrr >= lexical.mrr
