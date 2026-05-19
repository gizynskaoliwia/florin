# Florin — Architecture Documentation

> **Living Document Rule:** Every code change must update this file in the same commit.
> New function → Section 4. Data change → Section 3. Algorithm change → Section 5.
> UI change → Section 6. Performance change → Section 7.

---

## 1. Project Overview

**Florin** is a desktop budget tracker for freelancers with variable income. Built for a single user, all data stored locally as JSON files.

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI Framework | customtkinter (CTk) + tkinter |
| Data Storage | Local JSON files |
| Excel Import | openpyxl + msoffcrypto-tool |
| Images | Pillow |
| Calendar | tkcalendar |

### Running Locally

```bash
pip install -r requirements.txt
python main.py
```

No build step. No database. No network required.

---

## 2. Directory Structure

```
florin/
├── main.py                  # App entry point + ALL UI views (~2400 lines)
├── data_manager.py          # All data I/O, CRUD, calculations (~600 lines)
├── theme.py                 # Color constants, font definitions, theme setup
├── i18n.py                  # Internationalization: t() string lookup, language switching
├── HELP.md                  # User-facing help documentation (rendered in Help tab)
├── requirements.txt         # Python dependencies (5 packages)
├── config.json              # App config: targets, defaults, last month (gitignored)
├── ARCHITECTURE.md          # This file
├── README.md                # User-facing documentation
├── logo2.png / logo2.ico    # App icon
├── create_shortcut.ps1      # Windows shortcut creator
├── data/                    # Auto-created, gitignored
│   ├── YYYY-MM.json         # Monthly income/expenses/cashflow
│   └── savings_planner.json # Savings categories, grids, actuals
└── docs/
    ├── ARCHITECTURE.md      # (legacy, superseded by root ARCHITECTURE.md)
    └── DATA_MODEL.md        # (legacy)
```

---

## 3. Data Layer

### Storage Location

All data lives in `./data/` (auto-created on first run). Config lives at `./config.json`.

### File Schemas

#### `config.json` — App Configuration

```json
{
  "last_month": "2026-05",
  "theme": "light",
  "business_defaults": { "vat": 0.0, "tax": 0.0, "zus": 0.0 },
  "cashflow_targets": [
    { "id": "uuid", "name": "Daily Life", "target": 2000.0 }
  ],
  "default_income_items": [
    { "id": "uuid", "name": "Gross Invoice", "type": "addition|deduction" }
  ]
}
```

#### `data/YYYY-MM.json` — Monthly Data

```json
{
  "month": "2026-05",
  "income_items": [
    {
      "id": "uuid",
      "name": "Gross Invoice",
      "amount": 15984.81,
      "type": "addition|deduction",
      "category_id": null | "split_category_id"
    }
  ],
  "categories": [
    { "id": "daily_life", "name": "Daily Life", "percent": 40.0, "color": "#C9A86B" }
  ],
  "expense_categories": [
    { "id": "uuid|slug", "name": "Groceries" }
  ],
  "expenses": [
    {
      "id": "uuid",
      "date": "DD/MM/YYYY",
      "amount": 200.0,
      "category_id": "split_category_id" | null,
      "expense_category_id": "uuid",
      "description": "",
      "tags": [],
      "savings_category_id": "uuid" | null
    }
  ],
  "cashflow": {
    "current_accounts": {
      "target_id": { "balance": 0.0, "updated_at": "" }
    },
    "shared_actual": 0.0,
    "shared_assumed": 0.0,
    "saved_assumed": 0.0
  }
}
```

#### `data/savings_planner.json` — Savings Planner

```json
{
  "year": 2026,
  "categories": [
    {
      "id": "uuid",
      "name": "Category Name",
      "target": 1450.0,
      "deadline_month": 1,
      "group_id": "uuid" | null,
      "next_year_target": 200.0 | null
    }
  ],
  "groups": [
    { "id": "uuid", "name": "Group Name" }
  ],
  "grid": {
    "cat_id": { "01": 100.0, "02": 100.0, ... "12": 0.0 }
  },
  "assumed": { "01": 3000.0, ... "12": 3000.0 },
  "actual_grid": {
    "cat_id": { "01": 200.0, "02": 18.0, ... }
  },
  "actual_available": { "01": 3000.0, ... }
}
```

### Read/Write Patterns

| Operation | What Happens |
|-----------|-------------|
| App startup | Read `config.json`, read/create current month file |
| Tab switch | `view.refresh()` called — re-reads relevant data |
| Savings tab open | Read `savings_planner.json` + single-pass scan of ALL month files (for spent cache) |
| User edits cell | In-memory update → `save_savings_planner()` writes full JSON |
| Add expense | Append to in-memory list → `save_month()` writes full JSON |
| Month navigation | Load different `YYYY-MM.json` |

### Caching Strategy

- `build_savings_spent_cache()`: Single-pass scan of all month files, returns `{cat_id: total_spent}`. Built once per `_rebuild_ui()` call, stored as `self._spent_cache`.
- Monthly data (`self.data`): Held in memory on `FlorinApp` controller, written on every change.
- Savings planner (`self.sp`): Held in memory on `SavingsView`, re-read from disk on `refresh()`.

---

## 4. Module/Component Architecture

### `data_manager.py` — Data Layer

| Function | Responsibility |
|----------|---------------|
| `init_env()` | Create data dir + default config if missing |
| `get_config()` / `save_config()` | Read/write `config.json` |
| `load_month(month_str)` | Load or create monthly JSON, apply migrations |
| `save_month(month_str, data)` | Write monthly JSON |
| `generate_default_month(month_str)` | Create new month with categories carried from previous |
| `migrate_month_data(data)` | Migrate old business format → income_items |
| `get_net_income(data)` | Sum additions - deductions |
| `get_allocated_amount(data, cat_id)` | Net income × category percent + targeted extras |
| `get_spent_amount(data, cat_id)` | Sum expenses for split bucket (excl. savings-funded) |
| `get_savings_spent(data, cat_id)` | Sum expenses funded from savings category (single month) |
| `get_remaining_amount(data, cat_id)` | Allocated - Spent |
| `add_expense()` / `edit_expense()` / `delete_expense()` | Expense CRUD |
| `get_expense_categories()` / `add_expense_category()` / etc. | Expense category CRUD |
| `get_default_income_items()` / `add_default_income_item()` / etc. | Config-level income item templates |
| `get_cashflow_targets()` / `add_cashflow_target()` / etc. | Cashflow target CRUD |
| `get_savings_planner()` / `save_savings_planner()` | Read/write savings planner JSON |
| `add_savings_category()` / `edit_savings_category()` / `delete_savings_category()` | Savings category CRUD |
| `add_savings_group()` / `edit_savings_group()` / `delete_savings_group()` | Savings group CRUD |
| `get_savings_actual(sp)` | Init actual tracking fields on planner dict |
| `get_cat_total_saved(sp, cat_id)` | Sum actual_grid for category (all months) |
| `get_cat_missing(sp, cat_id)` | max(0, target - saved) |
| `get_cat_progress(sp, cat_id)` | min(1.0, saved / target) |
| `get_cat_balance(sp, cat_id)` | Saved - Spent |
| `get_cat_rollover(sp, cat_id)` | Balance after deadline if next_year_target exists |
| `get_month_total_allocated(sp, mk)` | Sum all categories' planned amount for month |
| `get_month_remaining(sp, mk)` | Assumed - Allocated |
| `get_actual_month_total(sp, mk)` | Sum all categories' actual amount for month |
| `get_actual_month_remaining(sp, mk)` | Available - Actual total |
| `build_savings_spent_cache()` | Single-pass scan all month files → `{cat_id: total_spent}` |
| `get_cascade_adjustments(sp, cat_id, spent_cache)` | Surplus cascade algorithm |
| `_get_all_months_savings_spent(cat_id)` | Legacy per-category scan (fallback if no cache) |
| `load_xlsx()` | Import from Excel (stub/MVP) |

### `i18n.py` — Internationalization

| Function | Responsibility |
|----------|---------------|
| `t(key)` | Look up translated string by key, fallback to English then key itself |
| `set_language(lang)` | Switch active language (for future use) |

### `main.py` — UI Layer

| Class | Responsibility |
|-------|---------------|
| `FlorinApp` | Root window, sidebar nav, view switching, holds `self.data` |
| `DashboardView` | Overview: net income, category split summary |
| `IncomeView` | Income items list (additions/deductions), category split editor |
| `ExpensesView` | Expense list, add/edit dialog, category manager, month filter |
| `SavingsView` | Savings planner: actual table + planning grid, edit mode, groups |
| `SavingsActualView` | **Dead code** — unused standalone actual view |
| `CashFlowView` | Buffer targets, current balances, top-up calculator |
| `HistoryView` | Monthly archive (placeholder) |
| `SettingsView` | Default income items, cashflow targets config |
| `HelpView` | Renders HELP.md as formatted text with search filtering |

#### Key `SavingsView` Methods

| Method | Responsibility |
|--------|---------------|
| `refresh()` | Re-read data, rebuild UI |
| `_rebuild_ui()` | Destroy all widgets, build spent cache, render both tables |
| `build_actual_table()` | Render actual savings grid with summary columns |
| `build_grid()` | Pre-compute cascades, call `build_planner_table()` |
| `build_planner_table()` | Alias — calls `build_grid()` |
| `_render_actual_cat_row()` | Render one category row in actual table |
| `_render_planning_cat_row()` | Render one category row in planning table |
| `toggle_actual_group(gid)` | Expand/collapse actual table group (deferred build) |
| `toggle_planning_group(gid)` | Expand/collapse planning table group (deferred build) |
| `toggle_edit()` | Switch between view/edit mode, rebuild |
| `save_all()` | Persist all cell_vars to savings planner JSON |
| `update_summaries()` | Live-update allocated/remaining labels |
| `open_category_editor(cat)` | Dialog for add/edit savings category |

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│                    FlorinApp                          │
│  self.data (monthly)    self.config                  │
│         │                    │                       │
│    save_data()          save_config()                │
│         │                    │                       │
│         ▼                    ▼                       │
│   data/YYYY-MM.json    config.json                   │
└─────────────────────────────────────────────────────┘
         │
         │ controller.data passed to views
         ▼
┌─────────────────────────────────────────────────────┐
│              SavingsView                             │
│  self.sp ←── get_savings_planner()                  │
│         │                                           │
│  _rebuild_ui():                                     │
│    1. build_savings_spent_cache() → self._spent_cache│
│    2. build_actual_table()                          │
│    3. build_grid() → all_cascades dict              │
│         │                                           │
│  On edit: save_savings_planner(self.sp)             │
│         │                                           │
│         ▼                                           │
│   data/savings_planner.json                         │
└─────────────────────────────────────────────────────┘
```

---

## 5. Key Algorithms

### Surplus Cascade

**Purpose:** When a savings goal is fully funded AND spent (e.g., gift bought), the leftover surplus reduces future planned savings for that category's next-year target.

**Preconditions (all must be true):**
1. Category has `next_year_target` set
2. `deadline_month < 12`
3. Progress ≥ 100% (target fully met)
4. Total spent > 0 (goal event occurred)
5. Surplus > 0 (saved more than spent, up to deadline only)

**Algorithm:**
```
surplus = sum(actual_grid[cat][month] for month 1..deadline) - total_spent_across_all_months
remaining = surplus
for month in (deadline+1)..12:
    planned = grid[cat][month]
    if planned <= 0: skip
    if remaining >= planned:
        adjustments[month] = 0  (fully zeroed)
        remaining -= planned
    else:
        adjustments[month] = planned - remaining
        remaining = 0
        break
```

**Example:** Category "Dzień babci" — target 200, deadline Jan, next_year_target 200.
- Actual saved in Jan: 200. Spent: 150. Surplus = 200 - 150 = 50.
- Planning grid Feb-Dec: 18/month (for next year).
- Cascade: Feb → 18-18=0 (deduct 18, remaining=32), Mar → 18-18=0 (remaining=14), Apr → 18-14=4.
- Result: Feb=~~18~~→0, Mar=~~18~~→0, Apr=~~18~~→4, May-Dec unchanged.

**Key guard:** If surplus ≤ 0 (balance = 0 or overspent), cascade does NOT trigger.

### Planning Grid Calculations

| Metric | Formula |
|--------|---------|
| Total Allocated (month) | Sum of `grid[cat][month]` for all categories |
| Assumed Available (month) | User-entered expected savings budget |
| Remaining (month) | Assumed - Allocated |
| Category Progress | `row_total / target` (sum planned months up to deadline) |

### Actual Savings Summary (per category)

| Column | Formula |
|--------|---------|
| Saved | `sum(actual_grid[cat][all months])` |
| Missing | `max(0, target - saved)` |
| % | `min(100%, saved / target)` |
| Spent | Sum of expenses with `savings_category_id == cat_id` (current month) |
| Balance | Saved - Spent |

### Group Row Sums

Group header shows sum of all child categories per month:
```
group_total[month] = sum(actual_grid[child][month] for child in group.children)
```

For planning grid with cascade active:
```
group_total[month] = sum(cascade_adjusted_value OR raw_planned for child in group.children)
```

---

## 6. UI Architecture

### App Layout

```
┌──────────┬──────────────────────────────────────────┐
│ Sidebar  │           Main Container                  │
│          │  ┌────────────────────────────────────┐   │
│ 🏠 Dash  │  │         Active View                │   │
│ 💰 Income│  │    (stacked via tkraise())         │   │
│ 🧾 Expen │  │                                    │   │
│ 🎯 Savin │  │                                    │   │
│ 💧 Cash  │  │                                    │   │
│ 📅 Hist  │  │                                    │   │
│ ⚙️ Sett  │  └────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────┘
```

All views are pre-created and stacked. `show_view()` calls `tkraise()` + `refresh()`.

### Savings Tab Structure

```
SavingsView (CTkFrame)
├── Header (edit btn, add category/group btns)
└── _scroll_container (CTkFrame, grid layout)
    ├── _canvas (tk.Canvas) ← row 0, col 0
    ├── _v_scroll (CTkScrollbar) ← row 0, col 1
    └── _h_scroll (CTkScrollbar) ← row 1, col 0
        └── scroll (CTkFrame, canvas window)
            ├── "📊 Actual Savings" label
            ├── Actual Table (CTkFrame, grid layout)
            │   ├── Header row: Category | Jan..Dec | Saved | Missing | % | Spent | Balance
            │   ├── Ungrouped category rows
            │   ├── Group headers (collapsible)
            │   └── Grouped category rows (deferred if collapsed)
            ├── Separator
            ├── "📋 Planning Grid" label
            └── Planning Table (CTkFrame, grid layout)
                ├── Header row: Category | Jan..Dec | Progress
                ├── Ungrouped category rows
                ├── Group headers (collapsible) + monthly sums
                ├── Grouped category rows (deferred if collapsed)
                ├── Assumed Available row
                ├── Total Allocated row
                └── Remaining row
```

### Accordion Groups

- Groups default to **collapsed** on first load (unless user has toggled them)

### Display Ordering

All list-based UI elements are sorted alphabetically (case-insensitive) at render time:

- **Expense category dropdown:** sorted by name
- **Funding source dropdown:** sorted by name within each section (💰 split categories, 🎯 savings categories)
- **Savings groups:** sorted by group name
- **Savings categories within groups:** sorted by category name
- **Ungrouped savings categories:** sorted by name

Sorting is applied to display copies only — underlying data structures retain insertion order.
- `self._user_toggled` tracks which groups user has interacted with
- Collapsed groups use **deferred widget creation** — no widgets built until first expand
- On first expand: `_render_actual_cat_row()` / `_render_planning_cat_row()` builds widgets, stores in `*_group_children[gid]`
- Subsequent toggles: `grid()` / `grid_remove()` (instant, no rebuild)

### Edit Mode

1. `toggle_edit()` sets `self.editing = True`, shows add buttons, calls `_rebuild_ui()`
2. Rebuild creates `CTkEntry` widgets instead of `CTkLabel` for editable cells
3. Each entry bound to `<FocusOut>` / `<Return>` for live updates
4. "✓ Done" calls `save_all()` → persists all `cell_vars` to JSON → rebuilds as read-only

### Current Month Highlighting

- `current_m = datetime.now().month`
- Header labels for current month get `fg_color=COLOR_CURRENT_MONTH` (light tint)
- Cell labels in current month column get same background
- Deadline month cells get `fg_color=COLOR_ACCENT` (takes priority)

### Plan vs Actual Color Coding (Actual Table)

| Condition | Color |
|-----------|-------|
| actual > planned | `COLOR_OVER_PLAN` (blue) |
| actual == planned | `COLOR_MET_PLAN` (green) |
| actual < planned | `COLOR_UNDER_PLAN` (orange) |
| no actual value | `COLOR_TEXT_MUTED` |

---

## 7. Performance Decisions

### Optimization 1: Cached Month File Reads

**Problem:** `_get_all_months_savings_spent(cat_id)` opened and parsed ALL month files for EACH category. With 31 categories × N month files = O(31N) file reads per tab load.

**Solution:** `build_savings_spent_cache()` scans all month files once, returns `{cat_id: total_spent}`. Built once per `_rebuild_ui()`, passed to `get_cascade_adjustments()` via `spent_cache` parameter.

**Impact:** 62 file reads → 2 file reads (96% reduction).

### Optimization 2: Pre-computed Cascade Dict

**Problem:** `get_cascade_adjustments()` called per-category in `render_cat_row()` AND again per-grouped-category in `render_group_row()`. Grouped categories computed twice.

**Solution:** Compute `all_cascades = {cat_id: adjustments}` once at top of `build_grid()`. Both row renderers reference this dict.

**Impact:** ~42 cascade computations → 31 (no duplicates).

### Optimization 3: Deferred Widget Creation

**Problem:** All category rows created on initial load even for collapsed groups (then immediately `grid_remove()`'d). ~31 categories × 18 columns × 2 tables = ~1100 widgets, most hidden.

**Solution:** Collapsed groups reserve row indices but create zero widgets. On first expand, `toggle_*_group()` builds widgets via extracted methods (`_render_actual_cat_row`, `_render_planning_cat_row`), caches them for subsequent toggles.

**Impact:** ~1100 initial widgets → ~280 (75% reduction). Groups build on-demand.

---

## 8. Known Limitations & TODOs

### Known Limitations

- **Single file = single user.** No concurrent access handling.
- **Full JSON rewrite on every save.** No incremental updates. Fine for current data sizes (<30KB) but won't scale to thousands of expenses.
- **`SavingsActualView` is dead code.** Class defined but never instantiated. Should be removed.
- **No undo/redo.** Edits are immediately persisted.
- **Horizontal scroll on Savings tab** requires content wider than viewport. Uses `width=0` trick on canvas window which may behave differently across OS/tk versions.
- **`bind_all("<MouseWheel>")` in SavingsView** captures scroll events globally — may interfere with other views' scrolling.

### Incomplete Features

- **History tab:** Placeholder, no monthly snapshots implemented
- **xlsx import:** Stub only (`load_xlsx` returns mock response)
- **Charts/trends:** Not started
- **PDF export:** Not started
- **Dark mode:** Theme infrastructure exists but only light mode implemented

### Future Improvements to Consider

- **Incremental saves:** Only write changed fields instead of full JSON dump
- **Remove dead `SavingsActualView` class** (~200 lines of unused code)
- **Virtual scrolling:** For very large category lists, only render visible rows
- **Background file I/O:** Move `build_savings_spent_cache()` to a thread for large datasets
- **Data validation:** No schema validation on JSON load — corrupt files crash silently
- **Backup on save:** Write to `.bak` before overwriting, in case of crash during write
