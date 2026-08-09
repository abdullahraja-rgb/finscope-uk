# Cost Of Living Engine

The cost-of-living engine estimates personal inflation by weighting ONS category inflation against the user's own spending mix.

Inputs:

- User transaction categories from uploaded CSVs or form-entered rows.
- `config/category_mapping.yml` for mapping app categories to ONS COICOP divisions.
- Latest CPIH category inflation from the ONS detailed reference tables.

Formula:

```text
personal inflation = sum(category spend share * ONS category annual inflation rate)
```

Example:

```text
groceries spend share 20% * food inflation 2.2% = 0.44 percentage points
```

The weighted personal rate is compared with the latest CPIH headline rate. Unmapped spending is listed in response notes and excluded from the weighted rate until a defensible mapping exists.

## Limitations

This is a category-level estimate, not an item-level inflation model. That matches the available transaction data, which usually contains merchant and category information rather than basket-level item prices.
