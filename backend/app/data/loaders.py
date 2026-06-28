from __future__ import annotations

import hashlib
import re
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

CPI_TABLES = {
    "cpih": {"sheet": "Table 3", "overall_label": "CPIH"},
    "cpi": {"sheet": "Table 4", "overall_label": "CPI"},
}

MONTH_LOOKUP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
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


def parse_ons_category_label(label: object) -> tuple[str | None, str, str]:
    text = " ".join(str(label).split())
    match = re.match(r"^(?P<code>\d{2}(?:\.\d+)*)\s+(?P<name>.+)$", text)
    if not match:
        return None, text, "overall"

    code = match.group("code")
    name = match.group("name")
    if "." not in code:
        level = "division"
    elif code.count(".") == 1:
        level = "group"
    else:
        level = "class"
    return code, name, level


def find_cpi_category_column(frame: pd.DataFrame) -> int:
    for row_index in range(min(20, len(frame))):
        for column, value in frame.loc[row_index].items():
            text = str(value).lower()
            if "overall index" in text or "food and non-alcoholic beverages" in text:
                return int(column)
    raise ValueError("Could not find the ONS category column")


def find_cpi_weight_column(frame: pd.DataFrame, category_col: int) -> int:
    for column, value in frame.loc[8].items():
        if column > category_col and "feb-dec" in str(value).lower():
            return int(column)
    raise ValueError("Could not find the ONS weight column")


def find_cpi_annual_change_columns(frame: pd.DataFrame) -> list[int]:
    start_col: int | None = None
    for row_index in [4, 5]:
        for column, value in frame.loc[row_index].items():
            if "over 12 months" in str(value).lower():
                start_col = int(column)
                break
        if start_col is not None:
            break

    if start_col is None:
        raise ValueError("Could not find the annual inflation columns")

    columns: list[int] = []
    for column in frame.columns:
        if column < start_col:
            continue
        year = pd.to_numeric(frame.at[7, column], errors="coerce")
        month_text = str(frame.at[8, column]).strip()[:3].lower()
        if pd.notna(year) and month_text in MONTH_LOOKUP:
            columns.append(int(column))
    return columns


def load_ons_category_inflation(data_dir: str | Path, index_type: str = "cpih") -> pd.DataFrame:
    index_key = index_type.lower()
    if index_key not in CPI_TABLES:
        expected = ", ".join(sorted(CPI_TABLES))
        raise ValueError(f"index_type must be one of: {expected}")

    path = find_raw_file(data_dir, RAW_DATASETS["consumer_price_inflation"])
    table = CPI_TABLES[index_key]
    frame = pd.read_excel(path, sheet_name=table["sheet"], header=None)

    category_col = find_cpi_category_column(frame)
    weight_col = find_cpi_weight_column(frame, category_col)
    annual_cols = find_cpi_annual_change_columns(frame)

    rows: list[dict[str, object]] = []
    for row_index in range(10, len(frame)):
        label = frame.at[row_index, category_col] if category_col in frame.columns else None
        if pd.isna(label):
            continue

        coicop_code, category, category_level = parse_ons_category_label(label)
        if not category or category.lower().startswith("source:"):
            continue

        weight = pd.to_numeric(frame.at[row_index, weight_col], errors="coerce")
        for column in annual_cols:
            year = int(float(frame.at[7, column]))
            month = MONTH_LOOKUP[str(frame.at[8, column]).strip()[:3].lower()]
            annual_change = pd.to_numeric(frame.at[row_index, column], errors="coerce")
            if pd.isna(annual_change):
                continue

            rows.append(
                {
                    "index_type": index_key,
                    "date": pd.Timestamp(year=year, month=month, day=1),
                    "coicop_code": coicop_code,
                    "category": category,
                    "category_level": category_level,
                    "weight": float(weight) if pd.notna(weight) else None,
                    "annual_change_pct": float(annual_change),
                    "weight_series_id": frame.at[row_index, 0],
                    "index_series_id": frame.at[row_index, 1],
                    "month_rate_series_id": frame.at[row_index, 2],
                    "annual_rate_series_id": frame.at[row_index, 3],
                    "source_sheet": table["sheet"],
                }
            )

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    return result.sort_values(["date", "category_level", "coicop_code"], na_position="first").reset_index(
        drop=True
    )


def latest_ons_category_inflation(data_dir: str | Path, index_type: str = "cpih") -> pd.DataFrame:
    frame = load_ons_category_inflation(data_dir, index_type=index_type)
    if frame.empty:
        return frame

    latest_date = frame["date"].max()
    return frame.loc[frame["date"].eq(latest_date)].reset_index(drop=True)


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
