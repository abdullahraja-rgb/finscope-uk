from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.data import latest_ons_category_inflation, load_family_spending_benchmarks
from app.schemas.transactions import (
    CategorisedTransaction,
    DerivedHealthScoreRequest,
    TransactionAnalysisResponse,
    TransactionIn,
    TransactionPreviewResponse,
)
from app.services.categorisation import categorisation_model_path, categorise_transactions
from app.services.cost_of_living import calculate_personal_inflation, load_category_mapping
from app.services.forecasting import forecast_next_month
from app.services.scoring import derive_health_score

router = APIRouter()

REQUIRED_COLUMNS = {"date", "description", "amount"}
OPTIONAL_COLUMNS = ["category", "transaction_type", "account"]


async def uploaded_csv_frame(file: UploadFile) -> pd.DataFrame:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")

    content = await file.read()
    try:
        frame = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not parse CSV file.") from exc

    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required columns: {', '.join(missing)}")

    return frame


def clean_transaction_frame(frame: pd.DataFrame) -> pd.DataFrame:
    clean = frame.copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce").dt.date
    clean["amount"] = pd.to_numeric(clean["amount"], errors="coerce")
    clean["description"] = clean["description"].fillna("").astype(str).str.strip()

    for column in OPTIONAL_COLUMNS:
        if column not in clean.columns:
            clean[column] = None
        clean[column] = clean[column].where(clean[column].notna(), None)
        clean[column] = clean[column].apply(
            lambda value: None if value is None or str(value).strip() == "" else str(value).strip()
        )

    invalid = clean["date"].isna() | clean["amount"].isna() | clean["description"].eq("")
    if invalid.any():
        raise HTTPException(
            status_code=422,
            detail=f"{int(invalid.sum())} rows have an invalid date, description, or amount.",
        )

    return clean


def transactions_from_frame(frame: pd.DataFrame) -> list[TransactionIn]:
    rows = frame[["date", "description", "amount", *OPTIONAL_COLUMNS]].to_dict(orient="records")
    return [TransactionIn(**row) for row in rows]


def preview_response(frame: pd.DataFrame, columns: list[str]) -> TransactionPreviewResponse:
    total_income = float(frame.loc[frame["amount"] > 0, "amount"].sum())
    total_spend = float(-frame.loc[frame["amount"] < 0, "amount"].sum())
    preview = frame.head(10).copy()
    preview["date"] = preview["date"].astype(str)

    return TransactionPreviewResponse(
        rows=int(len(frame)),
        columns=columns,
        total_income=round(total_income, 2),
        total_spend=round(total_spend, 2),
        preview=preview.fillna("").to_dict(orient="records"),
    )


def apply_predicted_categories(
    transactions: list[TransactionIn],
    categorised: list[CategorisedTransaction],
) -> list[TransactionIn]:
    enriched: list[TransactionIn] = []
    for transaction, prediction in zip(transactions, categorised):
        payload = transaction.model_dump()
        payload["category"] = transaction.category or prediction.predicted_category
        enriched.append(TransactionIn(**payload))
    return enriched


@router.post("/transactions/preview", response_model=TransactionPreviewResponse)
async def preview_transactions(file: UploadFile = File(...)) -> TransactionPreviewResponse:
    raw = await uploaded_csv_frame(file)
    clean = clean_transaction_frame(raw)
    return preview_response(clean, columns=list(raw.columns))


@router.post("/transactions/analyse", response_model=TransactionAnalysisResponse)
async def analyse_transactions(
    file: UploadFile = File(...),
    liquid_savings: float = Form(default=0),
    monthly_debt_payment: float = Form(default=0),
) -> TransactionAnalysisResponse:
    raw = await uploaded_csv_frame(file)
    clean = clean_transaction_frame(raw)
    transactions = transactions_from_frame(clean)
    model_path = categorisation_model_path(settings.data_dir)
    categorised = categorise_transactions(transactions, model_path=model_path)
    enriched_transactions = apply_predicted_categories(transactions, categorised)
    base = preview_response(clean, columns=list(raw.columns))
    notes: list[str] = []

    mapping = load_category_mapping(settings.config_dir)
    forecast = forecast_next_month(enriched_transactions)

    try:
        inflation = latest_ons_category_inflation(settings.data_dir, index_type="cpih")
        personal_inflation = calculate_personal_inflation(
            transactions=enriched_transactions,
            inflation=inflation,
            category_mapping=mapping,
            index_type="cpih",
        )
    except Exception as exc:
        personal_inflation = None
        notes.append(f"Personal inflation skipped: {exc}")

    try:
        benchmarks = load_family_spending_benchmarks(settings.data_dir)
        health_score = derive_health_score(
            DerivedHealthScoreRequest(
                transactions=enriched_transactions,
                liquid_savings=liquid_savings,
                monthly_debt_payment=monthly_debt_payment,
            ),
            category_mapping=mapping,
            benchmarks=benchmarks,
        )
    except Exception as exc:
        health_score = None
        notes.append(f"Financial health score skipped: {exc}")

    return TransactionAnalysisResponse(
        **base.model_dump(),
        transactions=[
            CategorisedTransaction(
                **transaction.model_dump(),
                predicted_category=prediction.predicted_category,
                confidence=prediction.confidence,
            )
            for transaction, prediction in zip(enriched_transactions, categorised)
        ],
        forecast=forecast,
        personal_inflation=personal_inflation,
        health_score=health_score,
        notes=notes,
    )
