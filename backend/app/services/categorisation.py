from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.schemas.transactions import (
    CategorisationEvaluationResponse,
    CategorisationMetric,
    CategorisedTransaction,
    ConfusionMatrixRow,
    MisclassifiedTransaction,
    TransactionIn,
)


KEYWORDS: dict[str, tuple[str, ...]] = {
    "groceries": ("tesco", "sainsbury", "aldi", "lidl", "asda", "morrisons"),
    "eating_out": ("pret", "costa", "deliveroo", "uber eats", "nando"),
    "transport": ("tfl", "trainline", "uber", "shell", "bp", "rail"),
    "housing": ("rent", "mortgage", "council tax"),
    "utilities": ("octopus", "british gas", "thames water", "water", "energy"),
    "subscriptions": ("netflix", "spotify", "disney", "prime"),
    "shopping": ("amazon", "argos", "ikea", "john lewis"),
    "health": ("boots", "superdrug", "pharmacy"),
    "income": ("salary", "payroll", "interest"),
}

MODEL_FILENAME = "categorisation_model.joblib"


def predict_category(description: str, amount: float) -> tuple[str, float]:
    text = description.lower()
    for category, keywords in KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category, 0.82
    if amount > 0:
        return "income", 0.65
    return "uncategorised", 0.35


def categorisation_model_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / "models" / MODEL_FILENAME


def transaction_features(transactions: list[TransactionIn]) -> pd.DataFrame:
    rows = []
    for transaction in transactions:
        amount = float(transaction.amount)
        rows.append(
            {
                "description": transaction.description.lower().strip(),
                "amount": amount,
                "amount_abs": abs(amount),
                "is_income": 1 if amount > 0 else 0,
            }
        )
    return pd.DataFrame(rows, columns=["description", "amount", "amount_abs", "is_income"])


def labelled_training_frame(transactions: list[TransactionIn]) -> pd.DataFrame:
    features = transaction_features(transactions)
    labels = [transaction.category for transaction in transactions]
    features["category"] = labels
    frame = features.dropna(subset=["category"]).copy()
    frame["category"] = frame["category"].astype(str).str.strip()
    frame = frame.loc[frame["category"].ne("")]

    if len(frame) < 8:
        raise ValueError("At least eight labelled transactions are needed for evaluation.")
    if frame["category"].nunique() < 2:
        raise ValueError("At least two categories are needed for a classifier.")

    return frame


def build_classifier() -> Pipeline:
    features = ColumnTransformer(
        transformers=[
            (
                "description",
                TfidfVectorizer(ngram_range=(1, 2), min_df=1),
                "description",
            ),
            ("amount", StandardScaler(), ["amount", "amount_abs", "is_income"]),
        ]
    )

    return Pipeline(
        steps=[
            ("features", features),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=1000),
            ),
        ]
    )


def stratify_labels(labels: pd.Series, test_size: float) -> pd.Series | None:
    class_count = labels.nunique()
    test_count = max(1, round(len(labels) * test_size))
    train_count = len(labels) - test_count
    if labels.value_counts().min() < 2:
        return None
    if test_count < class_count or train_count < class_count:
        return None
    return labels


def save_categorisation_model(transactions: list[TransactionIn], output_path: str | Path) -> dict[str, object]:
    frame = labelled_training_frame(transactions)
    model = build_classifier()
    model.fit(frame.drop(columns=["category"]), frame["category"])

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = sorted(frame["category"].unique().tolist())
    joblib.dump(
        {
            "model": model,
            "labels": labels,
            "training_rows": int(len(frame)),
        },
        path,
    )
    load_categorisation_model.cache_clear()
    return {"model_path": str(path), "training_rows": int(len(frame)), "labels": labels}


@lru_cache
def load_categorisation_model(model_path: str) -> object | None:
    path = Path(model_path)
    if not path.exists():
        return None

    artifact = joblib.load(path)
    if isinstance(artifact, dict) and "model" in artifact:
        return artifact["model"]
    return artifact


def model_predictions(
    transactions: list[TransactionIn],
    model: object,
) -> list[tuple[str, float]]:
    features = transaction_features(transactions)
    predictions = list(model.predict(features))

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)
        confidences = probabilities.max(axis=1).tolist()
    else:
        confidences = [0.7 for _ in predictions]

    return [(str(category), round(float(confidence), 3)) for category, confidence in zip(predictions, confidences)]


def evaluate_categorisation_model(
    transactions: list[TransactionIn],
    test_size: float = 0.25,
    random_state: int = 42,
) -> CategorisationEvaluationResponse:
    frame = labelled_training_frame(transactions)
    labels = frame["category"]
    train_frame, test_frame = train_test_split(
        frame,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_labels(labels, test_size),
    )

    model = build_classifier()
    model.fit(train_frame.drop(columns=["category"]), train_frame["category"])

    actual = test_frame["category"]
    predicted = model.predict(test_frame.drop(columns=["category"]))
    labels_sorted = sorted(frame["category"].unique().tolist())
    report = classification_report(actual, predicted, output_dict=True, zero_division=0)
    matrix = confusion_matrix(actual, predicted, labels=labels_sorted)

    per_class = []
    for label in labels_sorted:
        metric = report.get(label, {"precision": 0, "recall": 0, "f1-score": 0, "support": 0})
        per_class.append(
            CategorisationMetric(
                category=label,
                precision=round(float(metric["precision"]), 3),
                recall=round(float(metric["recall"]), 3),
                f1=round(float(metric["f1-score"]), 3),
                support=int(metric["support"]),
            )
        )

    confusion_rows = []
    for index, label in enumerate(labels_sorted):
        confusion_rows.append(
            ConfusionMatrixRow(
                actual=label,
                predicted={labels_sorted[col]: int(value) for col, value in enumerate(matrix[index])},
            )
        )

    misclassified = []
    for row, prediction in zip(test_frame.to_dict(orient="records"), predicted):
        if row["category"] == prediction:
            continue
        misclassified.append(
            MisclassifiedTransaction(
                description=str(row["description"]),
                amount=float(row["amount"]),
                actual_category=str(row["category"]),
                predicted_category=str(prediction),
            )
        )

    return CategorisationEvaluationResponse(
        training_rows=int(len(train_frame)),
        test_rows=int(len(test_frame)),
        accuracy=round(float(accuracy_score(actual, predicted)), 3),
        macro_f1=round(float(f1_score(actual, predicted, average="macro", zero_division=0)), 3),
        weighted_f1=round(float(f1_score(actual, predicted, average="weighted", zero_division=0)), 3),
        per_class=per_class,
        confusion_matrix=confusion_rows,
        misclassified=misclassified[:12],
    )


def categorise_transactions(
    transactions: list[TransactionIn],
    model_path: str | Path | None = None,
) -> list[CategorisedTransaction]:
    model = load_categorisation_model(str(model_path)) if model_path else None
    if model is not None:
        predictions = model_predictions(transactions, model)
    else:
        predictions = [
            predict_category(transaction.description, transaction.amount) for transaction in transactions
        ]

    results: list[CategorisedTransaction] = []
    for transaction, (category, confidence) in zip(transactions, predictions):
        results.append(
            CategorisedTransaction(
                **transaction.model_dump(),
                predicted_category=category,
                confidence=confidence,
            )
        )
    return results
