from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class MerchantPattern:
    description: str
    category: str
    account: str
    min_amount: float
    max_amount: float
    monthly_probability: float


MERCHANTS = [
    MerchantPattern("Tesco Superstore", "groceries", "current", 12, 95, 0.95),
    MerchantPattern("Sainsbury's Local", "groceries", "current", 8, 75, 0.85),
    MerchantPattern("Aldi Stores", "groceries", "current", 15, 90, 0.75),
    MerchantPattern("Pret A Manger", "eating_out", "current", 4, 18, 0.75),
    MerchantPattern("Deliveroo", "eating_out", "credit_card", 12, 42, 0.65),
    MerchantPattern("TfL Travel Charge", "transport", "current", 3, 16, 0.9),
    MerchantPattern("Trainline", "transport", "credit_card", 12, 85, 0.35),
    MerchantPattern("Shell Service Station", "transport", "credit_card", 35, 95, 0.3),
    MerchantPattern("Netflix", "subscriptions", "current", 10.99, 17.99, 0.95),
    MerchantPattern("Spotify", "subscriptions", "current", 9.99, 16.99, 0.9),
    MerchantPattern("Amazon Marketplace", "shopping", "credit_card", 8, 120, 0.75),
    MerchantPattern("Boots Pharmacy", "health", "current", 5, 55, 0.45),
    MerchantPattern("Octopus Energy", "utilities", "current", 75, 190, 0.98),
    MerchantPattern("Thames Water", "utilities", "current", 28, 62, 0.95),
    MerchantPattern("Rent Payment", "housing", "current", 850, 1350, 1.0),
    MerchantPattern("Council Tax", "housing", "current", 105, 185, 0.98),
]


def month_starts(start: date, end: date) -> list[date]:
    cursor = date(start.year, start.month, 1)
    months: list[date] = []
    while cursor <= end:
        months.append(cursor)
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = date(year, month, 1)
    return months


def random_day_in_month(month_start: date) -> date:
    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    days = (next_month - month_start).days
    return month_start + timedelta(days=random.randint(0, days - 1))


def build_transactions(years: int, seed: int) -> list[dict[str, str]]:
    random.seed(seed)
    today = date.today()
    start = date(today.year - years, today.month, 1)
    rows: list[dict[str, str]] = []

    for month_start in month_starts(start, today):
        salary = random.uniform(2450, 3550)
        rows.append(
            {
                "date": month_start.replace(day=25).isoformat(),
                "description": "Salary Payroll",
                "amount": f"{salary:.2f}",
                "category": "income",
                "transaction_type": "income",
                "account": "current",
            }
        )

        for pattern in MERCHANTS:
            if random.random() > pattern.monthly_probability:
                continue
            repeats = 1
            if pattern.category in {"groceries", "eating_out", "transport", "shopping"}:
                repeats = random.randint(1, 5)

            for _ in range(repeats):
                amount = random.uniform(pattern.min_amount, pattern.max_amount)
                if pattern.category == "housing" and pattern.description == "Rent Payment":
                    txn_date = month_start.replace(day=1)
                else:
                    txn_date = random_day_in_month(month_start)
                rows.append(
                    {
                        "date": txn_date.isoformat(),
                        "description": pattern.description,
                        "amount": f"{-amount:.2f}",
                        "category": pattern.category,
                        "transaction_type": "expense",
                        "account": pattern.account,
                    }
                )

    rows.sort(key=lambda row: row["date"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic UK transaction data.")
    parser.add_argument("--output", default="data/sample/synthetic_transactions.csv")
    parser.add_argument("--years", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = build_transactions(years=args.years, seed=args.seed)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["date", "description", "amount", "category", "transaction_type", "account"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} transactions to {output}")


if __name__ == "__main__":
    main()
