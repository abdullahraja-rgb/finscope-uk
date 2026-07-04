# Transaction Categorisation

I use a rule-based categoriser as the fallback and a supervised model as the upgrade path.

The fallback is deliberately UK merchant-focused. It covers common names such as Tesco, Sainsbury's, Waitrose, TfL, Trainline, Octopus, Virgin Media, Netflix, Spotify, Amazon Prime, Boots, and Specsavers. Positive merchant refunds keep the merchant category with lower confidence, while genuinely unknown spending stays `uncategorised` with low confidence.

The model version uses:

- TF-IDF features from the transaction description.
- Numeric amount features: signed amount, absolute amount, and whether it is income.
- Logistic Regression with balanced class weights.
- A holdout evaluation with accuracy, macro F1, weighted F1, per-class metrics, a confusion matrix, and example mistakes.

I care more about F1 than raw accuracy because spending categories are not equally common. A model that gets groceries and income right but misses subscriptions or transport could still look accurate if those smaller classes are rare.

Train the model from the project root:

```powershell
python scripts/train_categorisation_model.py
```

That reads `data/sample/synthetic_transactions.csv` by default and writes the ignored model artifact to `data/models/categorisation_model.joblib`.

The `/api/v1/categorise` endpoint uses the saved model when it exists. If there is no model artifact yet, it falls back to the keyword baseline so the dashboard still works.

Current limitation: the synthetic data is deliberately clean. Before treating the model as realistic, I need more noisy merchant text, ambiguous descriptions, and a proper error-analysis pass on misclassified rows.
