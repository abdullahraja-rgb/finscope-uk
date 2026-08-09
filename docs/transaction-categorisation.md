# Transaction Categorisation

Transaction categorisation has two paths: a rule-based fallback and a supervised model upgrade.

The fallback is UK merchant-focused. It covers common names such as Tesco, Sainsbury's, Waitrose, TfL, Trainline, Octopus, Virgin Media, Netflix, Spotify, Amazon Prime, Boots, and Specsavers. Positive merchant refunds keep the merchant category with lower confidence, while genuinely unknown spending stays `uncategorised`.

The model version uses:

- TF-IDF features from the transaction description.
- Numeric amount features: signed amount, absolute amount, and whether it is income.
- Logistic Regression with balanced class weights.
- Holdout evaluation with accuracy, macro F1, weighted F1, per-class metrics, a confusion matrix, and example mistakes.

F1 is more useful than raw accuracy here because spending categories are imbalanced. A model can get common classes right while still missing smaller categories such as subscriptions or transport.

Train the model from the project root:

```zsh
python scripts/train_categorisation_model.py
```

The script reads `data/sample/synthetic_transactions.csv` by default and writes the ignored model artifact to `data/models/categorisation_model.joblib`.

`/api/v1/categorise` uses the saved model when it exists and falls back to keyword rules when no artifact is present.

## Limitations

The synthetic data is deliberately clean. A stronger model would need noisier merchant text, ambiguous descriptions, and an error-analysis pass on misclassified rows.
