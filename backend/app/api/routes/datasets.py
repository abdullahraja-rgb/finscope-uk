from fastapi import APIRouter

from app.core.config import settings
from app.data import dataset_statuses, load_bank_rate_history, load_synthetic_transactions, load_uk_hpi

router = APIRouter()


@router.get("/datasets/status")
def datasets_status() -> dict[str, object]:
    statuses = [status.model_dump() for status in dataset_statuses(settings.data_dir)]
    return {"datasets": statuses}


@router.get("/datasets/summary")
def datasets_summary() -> dict[str, object]:
    transactions = load_synthetic_transactions(settings.data_dir)
    bank_rate = load_bank_rate_history(settings.data_dir)
    uk_hpi = load_uk_hpi(settings.data_dir)

    latest_rate = bank_rate.sort_values("date").iloc[-1]
    latest_hpi_date = uk_hpi["date"].max()

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
    }
