# Cost Of Living Engine

I calculate personal inflation by weighting ONS category inflation by the user's own spending mix.

The first version uses:

- User transaction categories from uploaded CSVs or form-entered transaction rows.
- `config/category_mapping.yml` to map app categories to ONS COICOP divisions.
- Latest CPIH category inflation from the ONS detailed reference tables.

Formula:

```text
personal inflation = sum(category spend share * ONS category annual inflation rate)
```

Example:

```text
groceries spend share 20% * food inflation 2.2% = 0.44 percentage points
```

I compare the weighted personal rate against the latest CPIH headline rate. Unmapped spending is listed in the response notes and excluded from the weighted rate until I add a defended mapping.

Current limitation: this is a category-level estimate, not a true item-level inflation model. That is fine for the MVP because bank transaction data usually has merchant/category detail rather than item baskets.
