"""Print an advisor retrieval quality report.

Usage (from the backend directory so the app package is importable):

    python ../scripts/evaluate_advisor.py
    python ../scripts/evaluate_advisor.py --k 3 --hybrid

Compares lexical retrieval against hybrid retrieval when the optional
fastembed dependency is installed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.advisor_embeddings import configured_embedder  # noqa: E402
from app.services.advisor_eval import RetrievalEvalReport, evaluate_retrieval  # noqa: E402


DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


def print_report(report: RetrievalEvalReport) -> None:
    print(f"\n{report.summary()}")
    if report.retrieval_failures:
        print("  retrieval misses:")
        for failure in report.retrieval_failures:
            print(f"    - {failure}")
    if report.routing_failures:
        print("  routing misses:")
        for failure in report.routing_failures:
            print(f"    - {failure}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=4, help="chunks retrieved per question")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="embedding model for hybrid mode")
    parser.add_argument("--hybrid", action="store_true", help="also evaluate hybrid retrieval")
    args = parser.parse_args()

    print_report(evaluate_retrieval(str(DOCS_DIR), k=args.k))

    if args.hybrid:
        embedder = configured_embedder("hybrid", args.model)
        if embedder is None:
            print("\nHybrid skipped: fastembed or the model is unavailable.")
            return 0
        print_report(evaluate_retrieval(str(DOCS_DIR), k=args.k, embedder=embedder))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
