# Data Dictionary

I use this file to keep every dataset traceable: where I got it, how often it changes, where I store it locally, and why it belongs in the project.

I keep raw data in `data/raw/` and leave it out of Git. I only publish processed outputs when they are small, reproducible, and safe to share.

## Core Datasets

| Dataset | Source | Local path | Format | Update cadence | Licence | FinScope use |
|---|---|---|---|---|---|---|
| Synthetic transactions | `scripts/generate_synthetic_transactions.py` | `data/sample/synthetic_transactions.csv` | CSV | Created on demand | Project-owned sample | Phase 1 EDA, Phase 3 classifier baseline, UI demo |
| Consumer Price Inflation tables | Office for National Statistics: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation | `data/raw/ons/consumer_price_inflation_tables.xlsx` | XLSX | Monthly; checked release 17 June 2026 | Open Government Licence v3.0 | CPIH/CPI/RPI category inflation and personal inflation |
| Official Bank Rate history | Bank of England: https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate | `data/raw/boe/bank_rate_history.*` | HTML/CSV/XLS depending on download route | MPC decision schedule; checked page 18 June 2026 | Bank of England terms | Rate scenarios for savings, debt, and mortgage impact |
| Family Spending workbook 1 | Office for National Statistics: https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/datasets/familyspendingworkbook1detailedexpenditureandtrends | `data/raw/ons/family_spending_workbook_1.xlsx` | XLSX | Annual; checked FYE 2025 release 11 June 2026 | Open Government Licence v3.0 | Household spending benchmarks and category shares |
| UK House Price Index | HM Land Registry/GOV.UK: https://www.gov.uk/government/collections/uk-house-price-index-reports | `data/raw/housing/uk_hpi_full_file.csv` | CSV | Monthly; checked April 2026 data release 17 June 2026 | Open Government Licence v3.0 | Regional housing pressure and affordability context |
| Private rental market summary statistics | Office for National Statistics: https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland | `data/raw/ons/private_rental_market_summary_statistics.xlsx` | XLS/XLSX | Discontinued; latest listed release 20 December 2023 | Open Government Licence v3.0 | Historic rent benchmarks; later replace with a current rental price index if required |

## Transaction Schema

I use this public-safe schema for synthetic data and uploaded demo files:

| Column | Type | Required | Notes |
|---|---|---|---|
| `date` | ISO date | Yes | Transaction date |
| `description` | string | Yes | Merchant or transfer description |
| `amount` | decimal | Yes | Expenses are negative, income is positive |
| `category` | string | Optional for uploads, required for training labels | App-level category |
| `transaction_type` | string | Yes | `income`, `expense`, or `transfer` |
| `account` | string | Optional | Example: `current`, `credit_card`, `savings` |

## Category Mapping

The first mapping from app categories to ONS categories lives in `config/category_mapping.yml`. I keep it explicit because this is the traceability bridge for personal inflation.
