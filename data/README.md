# Data Folder

Raw downloads and generated artifacts are kept out of Git.

```text
data/
|-- raw/         # Original downloaded files, ignored
|-- external/    # Third-party derived data, ignored
|-- processed/   # Reproducible cleaned outputs, ignored by default
|-- models/      # Trained model artifacts, ignored
`-- sample/      # Small synthetic/demo files safe to commit
```

Generate a sample transaction file:

```zsh
python scripts/generate_synthetic_transactions.py --output data/sample/synthetic_transactions.csv
```

Verify expected raw downloads:

```zsh
python scripts/verify_raw_datasets.py
```

Train the transaction categoriser:

```zsh
python scripts/train_categorisation_model.py
```

The backend data layer starts in `backend/app/data/loaders.py`. Loader functions handle synthetic transactions, UK HPI, Bank Rate, ONS CPIH/CPI category inflation, and ONS Family Spending benchmarks.
