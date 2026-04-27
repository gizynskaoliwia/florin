# Florin — Architecture & Developer Notes

## Module Overview

```
florin/
├── main.py           ← All UI views and the app controller
├── data_manager.py   ← All file I/O, no UI logic
├── theme.py          ← Design tokens (colors, fonts)
└── docs/             ← Documentation
```

---

## `theme.py` — Design System

Defines all colors and font tuples used throughout the app. Always import via `from theme import *`.

Key constants:

| Constant | Description |
|---|---|
| `COLOR_BG` | App background |
| `COLOR_SURFACE` | Card backgrounds |
| `COLOR_PRIMARY` | Brand rose/pink |
| `COLOR_INCOME` | Teal-green for income amounts |
| `COLOR_EXPENSE` | Rose for expense amounts |
| `COLOR_SUCCESS` | Green for positive remainders |
| `COLOR_ERROR` | Red for warnings / overspent |
| `FONT_MONO` | Monospaced font for all PLN amounts |
| `FONT_MONO_LG` | Large mono font for net income display |

---

## `data_manager.py` — Data Layer

**Rules:**
- Views **never** read or write files directly
- All persistence goes through `data_manager`
- `save_data()` is called via `controller.save_data()` from views

**Key functions:**

| Function | Description |
|---|---|
| `load_month(month_str)` | Load or create `data/YYYY-MM.json` |
| `save_month(month_str, data)` | Write monthly data to JSON |
| `get_config()` | Load `config.json` (creates defaults if missing) |
| `save_config(cfg)` | Persist config |
| `generate_id()` | Returns a short UUID string for new records |

---

## `main.py` — UI Architecture

The app uses a single `CTk` root window (`FlorinApp`) with a sidebar nav and a main content area that swaps between view frames.

### `FlorinApp` (controller)

- Owns `self.data` — the current month's data dict
- Owns `self.current_month` — string like `"2026-04"`
- `show_view(name)` — lifts the requested view to front, calls `view.refresh()`
- `save_data()` — calls `dm.save_month(...)` without triggering any UI refresh

### Views

Each view is a `CTkFrame` subclass registered in `self.views`:

| View class | Nav label | Responsibility |
|---|---|---|
| `DashboardView` | Dashboard | Summary cards, quick-add expense |
| `IncomeView` | Income | Business income + category split + extra income |
| `ExpensesView` | Expenses | Expense list + add form |
| `CashFlowView` | Cash Flow | Buffer rows + savings remainder |
| `HistoryView` | History | _(stub — to be implemented)_ |
| `SettingsView` | Settings | _(stub — to be implemented)_ |

Each view must implement `refresh()` — called by the controller when the view becomes active.

---

## Input Validation Pattern

All numeric fields use `ctk.StringVar` + two bindings:

```python
entry.bind("<KeyRelease>", self.on_key)   # strip invalid chars live
entry.bind("<FocusOut>",   self.on_blur)  # format to N decimal places on exit
```

The sanitize pattern used everywhere:

```python
def sanitize_number(raw: str) -> str:
    clean = "".join(c for c in raw.replace(",", ".") if c.isdigit() or c == ".")
    parts = clean.split(".")
    if len(parts) > 2:
        clean = parts[0] + "." + "".join(parts[1:])
    return clean
```

---

## Auto-Save Strategy

- No explicit "Save" button
- `save_data()` is called after every validated field change
- Category split saves only when percentages sum to 100%
- Expense list saves on add/delete

---

## Adding a New View

1. Create a class `MyView(ctk.CTkFrame)` with `__init__(self, parent, controller)` and a `refresh(self)` method
2. Register it in `FlorinApp.setup_views()`:
   ```python
   self.views["MyView"] = MyView(self.main_container, self)
   ```
3. Add it to the `nav_items` list in `setup_sidebar()`
