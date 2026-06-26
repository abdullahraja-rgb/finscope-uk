from app.schemas.transactions import CategorisedTransaction, TransactionIn


KEYWORDS: dict[str, tuple[str, ...]] = {
    "groceries": ("tesco", "sainsbury", "aldi", "lidl", "asda", "morrisons"),
    "eating_out": ("pret", "costa", "deliveroo", "uber eats", "nando"),
    "transport": ("tfl", "trainline", "uber", "shell", "bp", "rail"),
    "housing": ("rent", "mortgage", "council tax"),
    "utilities": ("octopus", "british gas", "thames water", "water", "energy"),
    "subscriptions": ("netflix", "spotify", "disney", "prime"),
    "shopping": ("amazon", "argos", "ikea", "john lewis"),
    "health": ("boots", "superdrug", "pharmacy"),
    "income": ("salary", "payroll", "interest"),
}


def predict_category(description: str, amount: float) -> tuple[str, float]:
    text = description.lower()
    for category, keywords in KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category, 0.82
    if amount > 0:
        return "income", 0.65
    return "uncategorised", 0.35


def categorise_transactions(transactions: list[TransactionIn]) -> list[CategorisedTransaction]:
    results: list[CategorisedTransaction] = []
    for transaction in transactions:
        category, confidence = predict_category(transaction.description, transaction.amount)
        results.append(
            CategorisedTransaction(
                **transaction.model_dump(),
                predicted_category=category,
                confidence=confidence,
            )
        )
    return results
