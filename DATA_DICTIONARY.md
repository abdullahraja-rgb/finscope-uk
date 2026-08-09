# Data Dictionary

This file records the project datasets, expected local paths, refresh cadence, licences, and how each source is used inside FinScope UK.

Raw downloads stay under `data/raw/` and are excluded from Git. Processed outputs are only suitable for committing when they are small, reproducible, and safe to share.

## Core Datasets

| Dataset | Source | Local path | Format | Update cadence | Licence | FinScope use |
|---|---|---|---|---|---|---|
| Synthetic transactions | `scripts/generate_synthetic_transactions.py` | `data/sample/synthetic_transactions.csv` | CSV | Created on demand | Project-owned sample | Demo uploads, classifier baseline, dashboard testing |
| Consumer Price Inflation tables | Office for National Statistics: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation | `data/raw/ons/consumer_price_inflation_tables.xlsx` | XLSX | Monthly; checked release 17 June 2026 | Open Government Licence v3.0 | CPIH/CPI/RPI category inflation and personal inflation |
| Official Bank Rate history | Bank of England: https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate | `data/raw/boe/bank_rate_history.*` | HTML/CSV/XLS depending on download route | MPC decision schedule; checked page 18 June 2026 | Bank of England terms | Savings, debt, and mortgage rate scenarios |
| Family Spending workbook 1 | Office for National Statistics: https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/datasets/familyspendingworkbook1detailedexpenditureandtrends | `data/raw/ons/family_spending_workbook_1.xlsx` | XLSX | Annual; checked FYE 2025 release 11 June 2026 | Open Government Licence v3.0 | Household spending benchmarks and category shares |
| UK House Price Index | HM Land Registry/GOV.UK: https://www.gov.uk/government/collections/uk-house-price-index-reports | `data/raw/housing/uk_hpi_full_file.csv` | CSV | Monthly; checked April 2026 data release 17 June 2026 | Open Government Licence v3.0 | Regional housing pressure and affordability context |
| Private rental market summary statistics | Office for National Statistics: https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland | `data/raw/ons/private_rental_market_summary_statistics.xlsx` | XLS/XLSX | Discontinued; latest listed release 20 December 2023 | Open Government Licence v3.0 | Historic rent benchmarks; candidate source for rental context |

## Transaction Schema

Synthetic samples and demo uploads use this public-safe schema:

| Column | Type | Required | Notes |
|---|---|---|---|
| `date` | ISO date | Yes | Transaction date |
| `description` | string | Yes | Merchant or transfer description |
| `amount` | decimal | Yes | Expenses are negative, income is positive |
| `category` | string | Optional for uploads, required for training labels | App-level category |
| `transaction_type` | string | Yes | `income`, `expense`, or `transfer` |
| `account` | string | Optional | Example: `current`, `credit_card`, `savings` |

## Category Mapping

`config/category_mapping.yml` maps app categories to ONS COICOP divisions. The mapping is intentionally explicit because it is the bridge between user spending categories and official inflation categories.

## Data Loading

`backend/app/data/loaders.py` contains the reproducible data-loading layer:

- `load_synthetic_transactions` reads generated demo transactions.
- `load_ons_category_inflation` extracts CPIH/CPI category inflation from ONS reference tables.
- `latest_ons_category_inflation` returns the latest available ONS month per category.
- `load_uk_hpi` normalises UK HPI date, region, price, index, and percentage-change columns.
- `load_bank_rate_history` reads the Bank of England `Raw Data` sheet into a unified `policy_rate` column.
- `dataset_statuses` reports whether expected official raw files are present.

## Model Inputs

The transaction categoriser trains from labelled transaction rows and writes ignored artifacts under `data/models/`. The committed sample CSVs are synthetic and should not be replaced with real bank exports.

## Benchmarks

Personal inflation is calculated by mapping app spending categories to ONS COICOP divisions, then weighting the latest CPIH category inflation by the user's spend share.

The financial-health benchmark compares mapped user spending shares against ONS Family Spending `Table 4.1`, using the latest `2024-25` all-household average.
