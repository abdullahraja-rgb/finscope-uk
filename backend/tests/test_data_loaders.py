from pathlib import Path

import pandas as pd

from app.data.loaders import (
    find_raw_file,
    latest_ons_category_inflation,
    load_bank_rate_history,
    load_family_spending_benchmarks,
    load_ons_category_inflation,
    load_uk_hpi,
    summarise_workbook,
)


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


def test_load_ons_category_inflation_from_cpih_table(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (tmp_path / "sample").mkdir()
    source = raw / "consumerpriceinflationdetailedreferencetables.xlsx"

    frame = pd.DataFrame(index=range(12), columns=range(24))
    frame.at[4, 15] = "Percentage change over 12 months"
    frame.at[7, 7] = 2026
    frame.at[8, 7] = "Feb-Dec"
    frame.at[7, 15] = 2026
    frame.at[8, 15] = "May"
    frame.at[10, 5] = "CPIH (overall index)"
    frame.at[10, 7] = 1000
    frame.at[10, 15] = 3.0
    frame.at[11, 0] = "L5CZ"
    frame.at[11, 1] = "L523"
    frame.at[11, 2] = "L59D"
    frame.at[11, 3] = "L55P"
    frame.at[11, 5] = "01    Food and non-alcoholic beverages"
    frame.at[11, 7] = 86.5
    frame.at[11, 15] = 2.2

    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Table 3", index=False, header=False)

    loaded = load_ons_category_inflation(tmp_path, index_type="cpih")

    food = loaded.loc[loaded["coicop_code"].eq("01")].iloc[0]
    assert food["category"] == "Food and non-alcoholic beverages"
    assert food["category_level"] == "division"
    assert food["annual_change_pct"] == 2.2
    assert food["date"].strftime("%Y-%m") == "2026-05"


def test_latest_ons_category_inflation_returns_latest_month(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (tmp_path / "sample").mkdir()
    source = raw / "consumerpriceinflationdetailedreferencetables.xlsx"

    frame = pd.DataFrame(index=range(12), columns=range(24))
    frame.at[4, 15] = "Percentage change over 12 months"
    frame.at[7, 7] = 2026
    frame.at[8, 7] = "Feb-Dec"
    frame.at[7, 15] = 2026
    frame.at[8, 15] = "Apr"
    frame.at[7, 16] = 2026
    frame.at[8, 16] = "May"
    frame.at[10, 5] = "CPIH (overall index)"
    frame.at[10, 7] = 1000
    frame.at[10, 15] = 2.8
    frame.at[10, 16] = 3.0

    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Table 3", index=False, header=False)

    latest = latest_ons_category_inflation(tmp_path, index_type="cpih")

    assert latest["date"].dt.strftime("%Y-%m").unique().tolist() == ["2026-05"]
    assert latest.iloc[0]["annual_change_pct"] == 3.0


def test_load_family_spending_benchmarks_latest_period(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "workbook1detailedexpenditureandtrends.xlsx"

    frame = pd.DataFrame(index=range(52), columns=range(30))
    frame.at[6, 29] = "2024-25"
    frame.at[20, 0] = "1"
    frame.at[20, 1] = "Food & non-alcoholic drinks"
    frame.at[20, 29] = 73.7
    frame.at[26, 0] = "4"
    frame.at[26, 1] = "Housing (net), fuel & power"
    frame.at[26, 29] = 118.4
    frame.at[45, 0] = "1-12"
    frame.at[45, 1] = "All expenditure groups"
    frame.at[45, 29] = 582.5

    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="4.1", index=False, header=False)

    loaded = load_family_spending_benchmarks(tmp_path)

    food = loaded.loc[loaded["coicop_code"].eq("01")].iloc[0]
    assert food["period"] == "2024-25"
    assert food["average_weekly_spend"] == 73.7
    assert round(food["benchmark_share"], 4) == 0.1265
