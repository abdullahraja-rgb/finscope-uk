from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.schemas.transactions import TransactionIn
from app.services.categorisation import (
    evaluate_categorisation_model,
    save_categorisation_model,
)


def load_transactions(path: Path) -> list[TransactionIn]:
    frame = pd.read_csv(path)
    required = {"date", "description", "amount", "category"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame = frame.dropna(subset=["date", "description", "amount", "category"])
    return [TransactionIn(**row) for row in frame.to_dict(orient="records")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the FinScope transaction categoriser.")
    parser.add_argument("--input", default="data/sample/synthetic_transactions.csv")
    parser.add_argument("--output", default="data/models/categorisation_model.joblib")
    parser.add_argument("--test-size", type=float, default=0.25)
    args = parser.parse_args()

    transactions = load_transactions(PROJECT_ROOT / args.input)
    evaluation = evaluate_categorisation_model(transactions, test_size=args.test_size)
    metadata = save_categorisation_model(transactions, PROJECT_ROOT / args.output)

    print(f"Trained on {metadata['training_rows']} labelled transactions")
    print(f"Saved model to {metadata['model_path']}")
    print(f"Holdout accuracy: {evaluation.accuracy}")
    print(f"Holdout macro F1: {evaluation.macro_f1}")
    print(f"Holdout weighted F1: {evaluation.weighted_f1}")


if __name__ == "__main__":
    main()
