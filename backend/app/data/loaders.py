from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DatasetStatus:
    name: str
    status: str
    path: str | None
    notes: list[str]

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class WorkbookSummary:
    path: str
    sheets: list[str]
    first_sheet: str
    preview_rows: int

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


RAW_DATASETS = {
    "consumer_price_inflation": "consumerpriceinflation*detailed*reference*tables*.xlsx",
    "bank_rate": "baserate*.xls*",
    "family_spending": "workbook1*detailed*expenditure*trends*.xlsx",
    "uk_hpi": "UK-HPI-full-file-*.csv",
    "private_rents": "privaterentalmarketstatistics*.xls",
}

HPI_COLUMNS = {
    "Date": "date",
    "RegionName": "region_name",
    "AreaCode": "area_code",
    "AveragePrice": "average_price",
    "Index": "index",
    "1m%Change": "monthly_change_pct",
    "12m%Change": "annual_change_pct",
}


def raw_data_dir(data_dir: str | Path) -> Path:
    return Path(data_dir).resolve() / "raw"


def sample_data_dir(data_dir: str | Path) -> Path:
    return Path(data_dir).resolve() / "sample"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_raw_file(data_dir: str | Path, pattern: str, preferred_name: str | None = None) -> Path:
    matches = sorted(path for path in raw_data_dir(data_dir).glob(pattern) if path.is_file())
    if not matches:
        raise FileNotFoundError(f"No raw file matched {pattern}")

    if preferred_name:
        preferred = [path for path in matches if path.name == preferred_name]
        if preferred:
            return preferred[0]

    if len(matches) == 1:
        return matches[0]

    hashes = {file_hash(path) for path in matches}
    if len(hashes) == 1:
        clean_names = [path for path in matches if " (" not in path.stem]
        return clean_names[0] if clean_names else matches[0]

    names = ", ".join(path.name for path in matches)
    raise ValueError(f"Multiple different raw files matched {pattern}: {names}")


def load_synthetic_transactions(data_dir: str | Path) -> pd.DataFrame:
    path = sample_data_dir(data_dir) / "synthetic_transactions.csv"
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    return frame


def load_uk_hpi(data_dir: str | Path, region_name: str | None = None) -> pd.DataFrame:
    path = find_raw_file(data_dir, RAW_DATASETS["uk_hpi"])
    frame = pd.read_csv(path, usecols=list(HPI_COLUMNS))
    frame = frame.rename(columns=HPI_COLUMNS)
    frame["date"] = pd.to_datetime(frame["date"], dayfirst=True, errors="coerce")

    for column in ["average_price", "index", "monthly_change_pct", "annual_change_pct"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if region_name:
        frame = frame.loc[frame["region_name"].eq(region_name)].copy()

    return frame.sort_values(["region_name", "date"]).reset_index(drop=True)


def load_bank_rate_history(data_dir: str | Path) -> pd.DataFrame:
    path = find_raw_file(data_dir, RAW_DATASETS["bank_rate"], preferred_name="baserate.xls")
    frame = pd.read_excel(path, sheet_name="Raw Data", header=1)
    frame = frame.rename(
        columns={
            "Date": "date",
            "Official Bank Rate": "official_bank_rate",
            "Repo Rate": "repo_rate",
            "Min Band 1 Dealing Rate": "min_band_1_dealing_rate",
            "Min Lending Rate": "min_lending_rate",
            "Bank Rate": "bank_rate",
        }
    )
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

    rate_columns = [
        "official_bank_rate",
        "repo_rate",
        "min_band_1_dealing_rate",
        "min_lending_rate",
        "bank_rate",
    ]
    for column in rate_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["policy_rate"] = frame[rate_columns].bfill(axis=1).iloc[:, 0]
    return frame.loc[
        frame["date"].notna() & frame["policy_rate"].notna(),
        ["date", *rate_columns, "policy_rate"],
    ]


def summarise_workbook(path: Path) -> WorkbookSummary:
    workbook = pd.ExcelFile(path)
    first_sheet = workbook.sheet_names[0]
    preview = pd.read_excel(path, sheet_name=first_sheet, nrows=30, header=None)
    preview_rows = int(preview.dropna(how="all").shape[0])
    return WorkbookSummary(
        path=str(path),
        sheets=workbook.sheet_names,
        first_sheet=first_sheet,
        preview_rows=preview_rows,
    )


def dataset_statuses(data_dir: str | Path) -> list[DatasetStatus]:
    statuses: list[DatasetStatus] = []
    for name, pattern in RAW_DATASETS.items():
        try:
            path = find_raw_file(
                data_dir,
                pattern,
                preferred_name="baserate.xls" if name == "bank_rate" else None,
            )
        except FileNotFoundError:
            statuses.append(DatasetStatus(name=name, status="missing", path=None, notes=[]))
            continue
        except ValueError as exc:
            statuses.append(DatasetStatus(name=name, status="check", path=None, notes=[str(exc)]))
            continue

        notes: list[str] = []
        matches = sorted(raw_data_dir(data_dir).glob(pattern))
        if len(matches) > 1 and len({file_hash(path) for path in matches}) == 1:
            notes.append("duplicate download detected; using the clean filename")

        statuses.append(DatasetStatus(name=name, status="ok", path=str(path), notes=notes))

    return statuses
