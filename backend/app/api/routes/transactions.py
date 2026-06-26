from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

REQUIRED_COLUMNS = {"date", "description", "amount"}


@router.post("/transactions/preview")
async def preview_transactions(file: UploadFile = File(...)) -> dict[str, object]:
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

    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    total_income = float(frame.loc[frame["amount"] > 0, "amount"].sum())
    total_spend = float(-frame.loc[frame["amount"] < 0, "amount"].sum())

    return {
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "total_income": round(total_income, 2),
        "total_spend": round(total_spend, 2),
        "preview": frame.head(10).fillna("").to_dict(orient="records"),
    }
