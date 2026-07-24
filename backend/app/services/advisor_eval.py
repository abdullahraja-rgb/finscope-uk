from __future__ import annotations

from dataclasses import dataclass, field

from app.services.advisor_embeddings import EmbeddingModel
from app.services.advisor_intent import route_sections
from app.services.advisor_retrieval import retrieve_advisor_chunks


@dataclass(frozen=True)
class EvalCase:
    """One labelled question.

    ``expected_sources`` lists the documents that should be retrieved (any one
    counts as a hit). ``expected_section`` is the dashboard section the intent
    router should pick, or ``None`` for questions about the app itself rather
    than a section of the user's dashboard.
    """

    question: str
    expected_sources: tuple[str, ...]
    expected_section: str | None = None


EVAL_CASES: tuple[EvalCase, ...] = (
    # Cost of living / personal inflation
    EvalCase("How is my personal inflation calculated?", ("cost-of-living-engine.md",), "inflation"),
    EvalCase("Why is my personal inflation higher than the UK figure?", ("cost-of-living-engine.md",), "inflation"),
    EvalCase("How do you map my spending to ONS categories?", ("cost-of-living-engine.md",), "inflation"),
    EvalCase("Are rising prices hitting me harder than average?", ("cost-of-living-engine.md",), "inflation"),
    # Forecasting
    EvalCase("How do you forecast next month's spending?", ("spend-forecasting.md",), "forecast"),
    EvalCase("Why can I not use a random train test split for forecasting?", ("spend-forecasting.md",), "forecast"),
    EvalCase("What baseline does the forecast compare against?", ("spend-forecasting.md",), "forecast"),
    EvalCase("How far ahead can you predict my spending?", ("spend-forecasting.md",), "forecast"),
    # Financial health score
    EvalCase("What does my financial health score mean?", ("financial-health-score.md",), "health"),
    EvalCase("Which component drags my health score down?", ("financial-health-score.md",), "health"),
    EvalCase("How is the emergency fund buffer scored?", ("financial-health-score.md",), None),
    # Rate impact
    EvalCase("How does the Bank Rate affect my debt?", ("rate-impact-engine.md",), "rate_impact"),
    EvalCase("What happens to my mortgage if interest rates rise?", ("rate-impact-engine.md",), "rate_impact"),
    EvalCase("Will my repayments climb if borrowing gets more expensive?", ("rate-impact-engine.md",), None),
    # Recommendations
    EvalCase("How are recommendations generated?", ("recommendations-engine.md",), "recommendations"),
    EvalCase("What actions should I prioritise first?", ("recommendations-engine.md",), "recommendations"),
    # Categorisation
    EvalCase("How are my transactions categorised?", ("transaction-categorisation.md",), "transactions"),
    EvalCase("How accurate is the merchant classification?", ("transaction-categorisation.md",), None),
    # App flow
    EvalCase("What happens when I upload a CSV?", ("upload-analysis-flow.md", "dashboard-data-flow.md"), None),
    EvalCase("How does data flow from upload to the dashboard?", ("dashboard-data-flow.md", "upload-analysis-flow.md"), None),
    # Advisor guardrails
    EvalCase("What guardrails does the advisor follow?", ("advisor-context.md",), None),
    EvalCase("What does the advisor do when data is missing?", ("advisor-context.md",), None),
)


@dataclass
class RetrievalEvalReport:
    mode: str
    k: int
    cases: int
    recall_at_k: float
    mrr: float
    routing_accuracy: float
    retrieval_failures: list[str] = field(default_factory=list)
    routing_failures: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"mode={self.mode} k={self.k} cases={self.cases} "
            f"recall@k={self.recall_at_k:.2f} mrr={self.mrr:.2f} routing={self.routing_accuracy:.2f}"
        )


def first_expected_rank(sources: list[str], expected: tuple[str, ...]) -> int | None:
    for position, source in enumerate(sources, start=1):
        if source in expected:
            return position
    return None


def evaluate_retrieval(
    docs_dir: str,
    cases: tuple[EvalCase, ...] = EVAL_CASES,
    k: int = 4,
    embedder: EmbeddingModel | None = None,
) -> RetrievalEvalReport:
    hits = 0
    reciprocal_total = 0.0
    routed_total = 0
    routed_hits = 0
    retrieval_failures: list[str] = []
    routing_failures: list[str] = []

    for case in cases:
        response = retrieve_advisor_chunks(
            case.question,
            docs_dir=docs_dir,
            max_chunks=k,
            embedder=embedder,
        )
        sources = [chunk.source for chunk in response.chunks]
        rank = first_expected_rank(sources, case.expected_sources)
        if rank is None:
            retrieval_failures.append(f"{case.question} -> got {sources or 'nothing'}")
        else:
            hits += 1
            reciprocal_total += 1.0 / rank

        if case.expected_section is not None:
            routed_total += 1
            routed = route_sections(case.question)
            if routed and routed[0] == case.expected_section:
                routed_hits += 1
            else:
                routing_failures.append(
                    f"{case.question} -> {routed[0] if routed else 'none'} (wanted {case.expected_section})"
                )

    total = len(cases) or 1
    return RetrievalEvalReport(
        mode="hybrid" if embedder is not None else "lexical",
        k=k,
        cases=len(cases),
        recall_at_k=hits / total,
        mrr=reciprocal_total / total,
        routing_accuracy=routed_hits / routed_total if routed_total else 1.0,
        retrieval_failures=retrieval_failures,
        routing_failures=routing_failures,
    )


def distinctness(texts: list[str]) -> float:
    """Share of unique outputs. Guards the bug where every question answered the same."""
    if not texts:
        return 0.0
    return len(set(texts)) / len(texts)
