# Data Folder

I keep raw downloaded datasets out of Git.

```text
data/
├── raw/         # Original downloaded files, ignored
├── external/    # Third-party derived data, ignored
├── processed/   # Reproducible cleaned outputs, ignored by default
├── models/      # Trained model artifacts, ignored
└── sample/      # Small synthetic/demo files safe to commit
```

Generate a sample transaction file:

```powershell
python scripts/generate_synthetic_transactions.py --output data/sample/synthetic_transactions.csv
```
