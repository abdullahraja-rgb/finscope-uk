# Datasets To Download

I am starting with a small, credible set of public UK datasets. I will use synthetic transactions for the personal banking side until the app is safe and useful enough to test with private data locally.

Source check date: 25 June 2026.

## Download First

| Priority | Dataset | Link | Save as | Why I need it |
|---|---|---|---|---|
| 1 | ONS Consumer Price Inflation tables | https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation | `data/raw/ons/consumer_price_inflation_tables.xlsx` | Latest checked release: 17 June 2026. This drives CPIH/CPI/RPI trends and the personal inflation engine. |
| 2 | Bank of England Official Bank Rate history | https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate | `data/raw/boe/bank_rate_history.*` | Latest checked page: 18 June 2026, Bank Rate 3.75%. This drives savings, debt, and mortgage rate scenarios. |
| 3 | ONS Family Spending workbook 1 | https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/datasets/familyspendingworkbook1detailedexpenditureandtrends | `data/raw/ons/family_spending_workbook_1.xlsx` | Latest checked release: 11 June 2026, FYE 2025 edition. This gives me household spending benchmarks for the score and comparison views. |
| 4 | UK House Price Index data downloads | https://www.gov.uk/government/collections/uk-house-price-index-reports | `data/raw/housing/uk_hpi_full_file.csv` | Latest checked update: 17 June 2026, April 2026 data. This gives me regional house-price pressure and affordability context. |
| 5 | ONS Private rental market summary statistics | https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland | `data/raw/ons/private_rental_market_summary_statistics.xlsx` | Latest checked release: 20 December 2023, now discontinued. This is useful historic rental benchmark data, but I will replace or supplement it if I find a better current rent series. |

## Generate Instead Of Downloading

The starter transaction dataset is here:

```text
data/sample/synthetic_transactions.csv
```

I can recreate it with:

```powershell
python scripts/generate_synthetic_transactions.py --output data/sample/synthetic_transactions.csv
```

## Folder Setup

I keep official downloads under source-specific folders:

```text
data/raw/ons/
data/raw/boe/
data/raw/housing/
```

Those folders are ignored by Git, so the public repo stays clean.
