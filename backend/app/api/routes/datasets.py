import pandas as pd
from fastapi import APIRouter

from app.core.config import settings
from app.data import (
    dataset_statuses,
    latest_ons_category_inflation,
    load_bank_rate_history,
    load_synthetic_transactions,
    load_uk_hpi,
)

router = APIRouter()


def dataframe_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    records = frame.copy()
    if "date" in records:
        records["date"] = records["date"].dt.date.astype(str)
    return records.to_dict(orient="records")


@router.get("/datasets/status")
def datasets_status() -> dict[str, object]:
    statuses = [status.model_dump() for status in dataset_statuses(settings.data_dir)]
    return {"datasets": statuses}


@router.get("/datasets/summary")
def datasets_summary() -> dict[str, object]:
    transactions = load_synthetic_transactions(settings.data_dir)
    bank_rate = load_bank_rate_history(settings.data_dir)
    uk_hpi = load_uk_hpi(settings.data_dir)
    cpih = latest_ons_category_inflation(settings.data_dir, index_type="cpih")

    latest_rate = bank_rate.sort_values("date").iloc[-1]
    latest_hpi_date = uk_hpi["date"].max()
    latest_cpih_date = cpih["date"].max()

    return {
        "synthetic_transactions": {
            "rows": int(len(transactions)),
            "date_min": transactions["date"].min().date().isoformat(),
            "date_max": transactions["date"].max().date().isoformat(),
            "categories": int(transactions["category"].nunique()),
        },
        "bank_rate": {
            "rows": int(len(bank_rate)),
            "latest_date": latest_rate["date"].date().isoformat(),
            "latest_policy_rate": float(latest_rate["policy_rate"]),
        },
        "uk_hpi": {
            "rows": int(len(uk_hpi)),
            "latest_date": latest_hpi_date.date().isoformat(),
            "regions": int(uk_hpi["region_name"].nunique()),
        },
        "cpih": {
            "latest_date": latest_cpih_date.date().isoformat(),
            "categories": int(len(cpih)),
            "division_categories": int(cpih["category_level"].eq("division").sum()),
        },
    }


@router.get("/datasets/inflation/latest")
def latest_inflation(index_type: str = "cpih") -> dict[str, object]:
    frame = latest_ons_category_inflation(settings.data_dir, index_type=index_type)
    divisions = frame.loc[frame["category_level"].eq("division")].copy()
    return {
        "index_type": index_type.lower(),
        "date": frame["date"].max().date().isoformat() if not frame.empty else None,
        "categories": dataframe_records(divisions),
    }
