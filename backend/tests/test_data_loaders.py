from pathlib import Path

import pandas as pd

from app.data.loaders import find_raw_file, load_bank_rate_history, load_uk_hpi, summarise_workbook


def test_load_uk_hpi_tidy_columns(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (tmp_path / "sample").mkdir()
    source = raw / "UK-HPI-full-file-2026-04.csv"
    source.write_text(
        "Date,RegionName,AreaCode,AveragePrice,Index,1m%Change,12m%Change\n"
        "01/04/2026,England,E92000001,290000,150.2,0.4,3.1\n",
        encoding="utf-8",
    )

    frame = load_uk_hpi(tmp_path)

    assert list(frame.columns) == [
        "date",
        "region_name",
        "area_code",
        "average_price",
        "index",
        "monthly_change_pct",
        "annual_change_pct",
    ]
    assert frame.loc[0, "region_name"] == "England"
    assert frame.loc[0, "date"].year == 2026


def test_load_bank_rate_history_uses_policy_rate(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (tmp_path / "sample").mkdir()
    source = raw / "baserate.xlsx"
    frame = pd.DataFrame(
        {
            "Date": ["2026-06-17", "2026-06-18"],
            "Bank Rate": [None, None],
            "Zero line": [0, 0],
            "Min Lending Rate": [None, None],
            "Min Band 1 Dealing Rate": [None, None],
            "Repo Rate": [None, None],
            "Official Bank Rate": [4.0, 3.75],
        }
    )
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Raw Data", index=False, startrow=1)

    loaded = load_bank_rate_history(tmp_path)

    assert loaded["policy_rate"].tolist() == [4.0, 3.75]
    assert loaded["date"].dt.year.tolist() == [2026, 2026]


def test_find_raw_file_prefers_clean_duplicate_name(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "baserate.xls").write_text("same", encoding="utf-8")
    (raw / "baserate (1).xls").write_text("same", encoding="utf-8")

    found = find_raw_file(tmp_path, "baserate*.xls")

    assert found.name == "baserate.xls"


def test_summarise_workbook(tmp_path: Path) -> None:
    source = tmp_path / "workbook.xlsx"
    frame = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Contents", index=False)

    summary = summarise_workbook(source)

    assert summary.first_sheet == "Contents"
    assert summary.preview_rows > 0
