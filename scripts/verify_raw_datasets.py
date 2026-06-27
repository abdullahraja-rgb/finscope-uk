from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SAMPLE_DIR = ROOT / "data" / "sample"


EXPECTED = {
    "consumer_price_inflation": {
        "pattern": "consumerpriceinflation*detailed*reference*tables*.xlsx",
        "required_sheets": 3,
    },
    "bank_rate": {
        "pattern": "baserate*.xls",
        "required_sheets": 1,
    },
    "family_spending": {
        "pattern": "workbook1*detailed*expenditure*trends*.xlsx",
        "required_sheets": 1,
    },
    "uk_hpi": {
        "pattern": "UK-HPI-full-file-*.csv",
        "required_columns": {"Date", "RegionName", "AreaCode", "AveragePrice", "Index", "12m%Change"},
    },
    "private_rents": {
        "pattern": "privaterentalmarketstatistics*.xls",
        "required_sheets": 1,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_files(pattern: str) -> list[Path]:
    return sorted(path for path in RAW_DIR.glob(pattern) if path.is_file())


def inspect_workbook(path: Path, min_sheets: int) -> dict[str, object]:
    workbook = pd.ExcelFile(path)
    first_sheet = workbook.sheet_names[0]
    preview = pd.read_excel(path, sheet_name=first_sheet, nrows=30, header=None)
    non_empty_rows = int(preview.dropna(how="all").shape[0])
    status = "ok" if len(workbook.sheet_names) >= min_sheets and non_empty_rows > 0 else "check"
    return {
        "status": status,
        "sheets": len(workbook.sheet_names),
        "first_sheet": first_sheet,
        "preview_rows": non_empty_rows,
    }


def inspect_csv(path: Path, required_columns: set[str]) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    missing = sorted(required_columns - set(header))
    row_count = 0
    min_date = None
    max_date = None
    regions: set[str] = set()

    for chunk in pd.read_csv(path, usecols=["Date", "RegionName"], chunksize=100_000):
        row_count += len(chunk)
        dates = pd.to_datetime(chunk["Date"], dayfirst=True, errors="coerce")
        chunk_min = dates.min()
        chunk_max = dates.max()
        if pd.notna(chunk_min):
            min_date = chunk_min if min_date is None else min(min_date, chunk_min)
        if pd.notna(chunk_max):
            max_date = chunk_max if max_date is None else max(max_date, chunk_max)
        regions.update(chunk["RegionName"].dropna().astype(str).unique().tolist())

    status = "ok" if not missing and row_count > 0 else "check"
    return {
        "status": status,
        "columns": len(header),
        "missing_columns": missing,
        "rows": row_count,
        "date_min": min_date.date().isoformat() if min_date is not None else None,
        "date_max": max_date.date().isoformat() if max_date is not None else None,
        "regions": len(regions),
    }


def inspect_transactions(path: Path) -> dict[str, object]:
    required = {"date", "description", "amount", "category", "transaction_type", "account"}
    frame = pd.read_csv(path)
    missing = sorted(required - set(frame.columns))
    return {
        "status": "ok" if not missing and len(frame) > 0 else "check",
        "rows": int(len(frame)),
        "missing_columns": missing,
        "date_min": str(frame["date"].min()) if "date" in frame else None,
        "date_max": str(frame["date"].max()) if "date" in frame else None,
        "categories": int(frame["category"].nunique()) if "category" in frame else 0,
    }


def main() -> None:
    print(f"Raw data folder: {RAW_DIR}")
    print()

    hashes: dict[str, list[Path]] = {}
    for path in sorted(RAW_DIR.glob("*")):
        if path.is_file() and path.name != ".gitkeep":
            hashes.setdefault(sha256(path), []).append(path)

    for name, spec in EXPECTED.items():
        matches = find_files(spec["pattern"])
        print(f"[{name}]")
        if not matches:
            print("  status: missing")
            continue

        for path in matches:
            print(f"  file: {path.relative_to(ROOT)}")
            print(f"  size_mb: {path.stat().st_size / 1024 / 1024:.2f}")
            try:
                if path.suffix.lower() == ".csv":
                    result = inspect_csv(path, spec["required_columns"])
                else:
                    result = inspect_workbook(path, spec["required_sheets"])
                for key, value in result.items():
                    print(f"  {key}: {value}")
            except Exception as exc:
                print(f"  status: error")
                print(f"  error: {exc}")
        print()

    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    print("[duplicates]")
    if not duplicate_groups:
        print("  none")
    for paths in duplicate_groups:
        print("  duplicate_set:")
        for path in paths:
            print(f"    - {path.relative_to(ROOT)}")

    sample_path = SAMPLE_DIR / "synthetic_transactions.csv"
    print()
    print("[synthetic_transactions]")
    if sample_path.exists():
        for key, value in inspect_transactions(sample_path).items():
            print(f"  {key}: {value}")
    else:
        print("  status: missing")


if __name__ == "__main__":
    main()
