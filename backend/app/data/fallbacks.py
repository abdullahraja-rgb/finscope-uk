from __future__ import annotations

import pandas as pd


def demo_latest_inflation(index_type: str = "cpih") -> pd.DataFrame:
    index_key = index_type.lower()
    date = pd.Timestamp("2026-05-01")
    rows = [
        (None, "CPIH demo overall index", "overall", 1000.0, 3.0),
        ("01", "Food and non-alcoholic beverages", "division", 86.5, 4.5),
        ("04", "Housing, water, electricity, gas and other fuels", "division", 130.0, 3.8),
        ("05", "Furniture, household equipment and maintenance", "division", 45.0, 2.4),
        ("06", "Health", "division", 22.0, 2.0),
        ("07", "Transport", "division", 111.3, 2.7),
        ("09", "Recreation and culture", "division", 105.0, 3.1),
        ("11", "Restaurants and hotels", "division", 102.0, 5.2),
    ]
    return pd.DataFrame(
        [
            {
                "index_type": index_key,
                "date": date,
                "coicop_code": coicop_code,
                "category": category,
                "category_level": level,
                "weight": weight,
                "annual_change_pct": annual_change,
                "source_sheet": "demo",
            }
            for coicop_code, category, level, weight, annual_change in rows
        ]
    )


def demo_family_spending_benchmarks() -> pd.DataFrame:
    rows = [
        ("01", "Food & non-alcoholic drinks", 73.7, 0.1265),
        ("04", "Housing (net), fuel & power", 118.4, 0.2033),
        ("05", "Household goods and services", 37.6, 0.0645),
        ("06", "Health", 10.5, 0.0180),
        ("07", "Transport", 96.4, 0.1655),
        ("09", "Recreation and culture", 70.8, 0.1215),
        ("11", "Restaurants and hotels", 57.1, 0.0980),
    ]
    return pd.DataFrame(
        [
            {
                "period": "demo",
                "coicop_code": coicop_code,
                "category": category,
                "average_weekly_spend": weekly_spend,
                "benchmark_share": benchmark_share,
                "source_sheet": "demo",
            }
            for coicop_code, category, weekly_spend, benchmark_share in rows
        ]
    )


def demo_bank_rate_history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-06-01"),
                "official_bank_rate": 3.75,
                "repo_rate": None,
                "min_band_1_dealing_rate": None,
                "min_lending_rate": None,
                "bank_rate": None,
                "policy_rate": 3.75,
            }
        ]
    )


def demo_uk_hpi() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-04-01"),
                "region_name": "England",
                "area_code": "E92000001",
                "average_price": 290000.0,
                "index": 150.2,
                "monthly_change_pct": 0.4,
                "annual_change_pct": 3.1,
            }
        ]
    )
