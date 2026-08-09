# Datasets To Download

FinScope UK uses public UK macro and household datasets. Personal banking examples are synthetic until private data handling is needed locally.

Source check date: 25 June 2026.

## Download First

| Priority | Dataset | Link | Save as | Use |
|---|---|---|---|---|
| 1 | ONS Consumer Price Inflation tables | https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation | `data/raw/ons/consumer_price_inflation_tables.xlsx` | CPIH/CPI/RPI trends and personal inflation |
| 2 | Bank of England Official Bank Rate history | https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate | `data/raw/boe/bank_rate_history.*` | Savings, debt, and mortgage rate scenarios |
| 3 | ONS Family Spending workbook 1 | https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/datasets/familyspendingworkbook1detailedexpenditureandtrends | `data/raw/ons/family_spending_workbook_1.xlsx` | Household spending benchmarks |
| 4 | UK House Price Index data downloads | https://www.gov.uk/government/collections/uk-house-price-index-reports | `data/raw/housing/uk_hpi_full_file.csv` | Regional house-price pressure and affordability context |
| 5 | ONS Private rental market summary statistics | https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland | `data/raw/ons/private_rental_market_summary_statistics.xlsx` | Historic rental benchmark context |

## Generate Instead Of Downloading

The starter transaction dataset is:

```text
data/sample/synthetic_transactions.csv
```

Recreate it with:

```zsh
python scripts/generate_synthetic_transactions.py --output data/sample/synthetic_transactions.csv
```

## Folder Setup

Official downloads live under source-specific folders:

```text
data/raw/ons/
data/raw/boe/
data/raw/housing/
```

Those folders are ignored by Git.
