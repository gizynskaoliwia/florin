# Florin — Data Model Reference

This document describes the JSON data structures used by Florin for persistence.

---

## Monthly Data File — `data/YYYY-MM.json`

One file per month. Auto-created on first launch for the current month.

```json
{
  "month": "2026-04",
  "business": {
    "gross_invoice": 13000.00,
    "vat_deducted": 2430.89,
    "income_tax_deducted": 2008.13,
    "zus_deducted": 1600.00,
    "net_income": 6960.98
  },
  "additional_income": [
    {
      "id": "uuid",
      "amount": 500.00,
      "description": "Freelance project",
      "target_category": null,
      "date": "2026-04-05"
    }
  ],
  "categories": [
    { "id": "daily_life", "name": "Daily Life",  "percent": 40, "color": "#C9A86B" },
    { "id": "shared",     "name": "Shared",       "percent": 20, "color": "#6B98C9" },
    { "id": "saved",      "name": "Saved",         "percent": 20, "color": "#6BAD8A" },
    { "id": "pleasure",   "name": "Pleasure",      "percent": 20, "color": "#C96B98" }
  ],
  "expenses": [
    {
      "id": "uuid",
      "date": "2026-04-10",
      "amount": 10.00,
      "description": "Nails",
      "subcategory": "Beauty",
      "category_id": "pleasure",
      "tags": ["beauty", "personal"],
      "notes": ""
    }
  ],
  "cashflow_buffer": {
    "minimums": {
      "daily_life": 2000.00,
      "pleasure": 1100.00,
      "business_expenses": 2760.00
    },
    "current_on_account": {
      "daily_life": 0.0,
      "pleasure": 0.0,
      "business_expenses": 0.0
    }
  }
}
```

### Field notes

| Field | Description |
|---|---|
| `business.net_income` | Auto-calculated: `gross − vat − tax − zus` |
| `additional_income[].target_category` | `null` = distribute proportionally; otherwise a category `id` |
| `categories[].percent` | Must sum to 100 across all categories for the month |
| `expenses[].category_id` | Must match a `categories[].id` in the same file |
| `cashflow_buffer.minimums` | Editable in Settings; keys are category IDs or custom buffer names |

---

## History File — `data/history.json`

Stores monthly snapshots for the History tab. Written when user clicks "Save Snapshot".

```json
{
  "months": [
    {
      "month": "2026-04",
      "label": "April 2026",
      "category_remainders": {
        "daily_life": 450.00,
        "shared": 200.00,
        "saved": 1200.00,
        "pleasure": 320.00
      },
      "cash": 300.00,
      "bank_accounts": [
        { "name": "mBank Main", "balance": 3200.00 },
        { "name": "Revolut",    "balance": 500.00 }
      ],
      "business_account": 5500.00,
      "savings": [
        { "name": "Lokata 6M",      "balance": 15000.00 },
        { "name": "Emergency Fund",  "balance": 5000.00 }
      ]
    }
  ]
}
```

---

## Config File — `config.json` _(gitignored)_

Stores user preferences. Auto-created on first launch.

```json
{
  "last_month": "2026-04",
  "window_geometry": "1100x720"
}
```

This file is **gitignored** — it's machine-specific and contains the last-used month.
