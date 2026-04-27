# GEMINI.md — Florin Budget Tracker

> Full project specification for AI-assisted code generation.
> Always reference `brandGuidelines.md` for all visual/design decisions.

---

## Project Overview

**App Name:** Florin
**Type:** Desktop budget tracking app
**Language:** Python 3.10+ ONLY — no JavaScript, no web frameworks
**GUI Framework:** `customtkinter` (pip install customtkinter)
**Platform:** Windows/macOS/Linux desktop
**Locale:** UI in English, currency in PLN (Polish Zloty), date format DD/MM/YYYY
**Data format:** JSON files for persistence (one file per month, stored in `./data/`)

---

## Technology Stack

| Library | Purpose | Install |
|---|---|---|
| `customtkinter` | GUI framework (modern tkinter) | `pip install customtkinter` |
| `openpyxl` | Read/write Excel files | `pip install openpyxl` |
| `msoffcrypto-tool` | Decrypt password-protected xlsx | `pip install msoffcrypto-tool` |
| `Pillow` | Image handling (icons, logos) | `pip install Pillow` |
| `json` | Data persistence (built-in) | — |
| `uuid` | Unique expense IDs (built-in) | — |
| `tkinter.filedialog` | File picker (built-in) | — |

**requirements.txt:**
```
customtkinter>=5.2.0
openpyxl>=3.1.0
msoffcrypto-tool>=5.4.0
Pillow>=10.0.0
```

---

## Phase 1 Scope

Phase 1 builds the core app. Features in order of priority:

1. **Import from xlsx** — open `budżet.xlsx` (password `02071999`), read sheet `kwiecień 2026`
2. **Business income section** — manually enter gross invoice + manual deductions → net income
3. **Category split** — distribute net income across 4 categories by percentage
4. **Additional income** — add one-off income to general pool or specific category
5. **Expense tracker** — log expenses, assign to category, add tags/notes
6. **Cash flow buffer** — minimum balance calculator with top-up amounts and savings remainder
7. **History tab** — monthly snapshots, manual account balances
8. **Settings** — edit category names, percentages, buffer minimums

---

## App Architecture

```
florin/
├── main.py              ← App entry point, CTk root window, navigation
├── theme.py             ← Color constants, font definitions (from brandGuidelines.md)
├── data_manager.py      ← Load/save JSON, import xlsx, data models
├── views/
│   ├── dashboard.py     ← Overview tab
│   ├── income.py        ← Business income + category management
│   ├── expenses.py      ← Expense list + add expense form
│   ├── cashflow.py      ← Cash flow buffer view
│   └── history.py       ← Monthly history and account balances
└── data/
    └── 2026-04.json     ← Monthly data file (auto-created)
```

> **Single-file alternative:** If simpler, all code can be in one `main.py` file using classes per view.

---

## Data Models

### Monthly Data File (`data/YYYY-MM.json`)

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
    { "id": "daily_life",  "name": "Daily Life",  "percent": 40, "color": "#C9A86B" },
    { "id": "shared",      "name": "Shared",       "percent": 20, "color": "#6B98C9" },
    { "id": "saved",       "name": "Saved",        "percent": 20, "color": "#6BAD8A" },
    { "id": "pleasure",    "name": "Pleasure",     "percent": 20, "color": "#C96B98" }
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

### History Summary File (`data/history.json`)

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
        { "name": "Revolut", "balance": 500.00 }
      ],
      "business_account": 5500.00,
      "savings": [
        { "name": "Lokata 6M", "balance": 15000.00 },
        { "name": "Emergency Fund", "balance": 5000.00 }
      ]
    }
  ]
}
```

---

## Feature Specifications

### 1. Business Income Section

**Location:** Income tab — top section
**Purpose:** User manually enters all amounts from their invoice and deductions. No automatic tax calculations — the user knows her exact figures.

**Fields (all manually editable):**
- Gross invoice amount (PLN) — the number on the faktura (e.g. 13 000,00 PLN)
- VAT deducted (PLN) — amount of VAT paid, entered manually
- Income tax deducted (PLN) — income tax amount, entered manually
- ZUS deducted (PLN) — ZUS contribution, entered manually

**Net income calculation (simple subtraction, auto-updates live):**
```
net_income = gross_invoice - vat_deducted - income_tax_deducted - zus_deducted
```

**Display:**
- Show a clear breakdown column:
  ```
  Gross invoice:      13 000,00 PLN
  − VAT:              − 2 430,89 PLN
  − Income tax:       − 2 008,13 PLN
  − ZUS:              − 1 600,00 PLN
  ─────────────────────────────────
  Net income:         = 6 960,98 PLN  ← large, bold, teal-green
  ```
- Net income shown large, in mono font, teal-green color (`color-income`)
- Remember last used deduction values as defaults for next month (save to config.json)

---

### 2. Category Split Section

**Location:** Income tab — below business income section
**Default categories:**

| ID | Display Name | Default % | Color |
|---|---|---|---|
| `daily_life` | Daily Life | 40% | Gold |
| `shared` | Shared | 20% | Blue |
| `saved` | Saved | 20% | Green |
| `pleasure` | Pleasure | 20% | Rose |

**Features:**
- Percentage inputs per category — auto-calculate PLN amount from net income
- Validation: percentages must sum to 100% (show inline warning if not)
- Add / remove categories (minimum 2, maximum 8)
- Rename categories inline (double-click on name to edit)
- Total PLN amount shown per category with colored pill badge
- "Add extra income" button opens a small dialog:
  - Amount (PLN), description, date
  - Option: distribute across all categories proportionally, OR assign to one specific category only

---

### 3. Expense Tracker

**Location:** Expenses tab
**Two panels:** Left = expense list, Right = add/edit form

**Add/Edit Expense Form:**
- Date (default: today, DD/MM/YYYY, use DateEntry or manual input)
- Amount (PLN, positive number)
- Description (text, required)
- Subcategory (text, editable — e.g., "Beauty", "Food", "Transport", "Entertainment")
  - Show dropdown with previously used subcategories (build list from existing expenses)
- Assign to category (dropdown: Daily Life / Shared / Saved / Pleasure — colored pills)
- Tags (comma-separated, e.g., "beauty, personal")
- Notes (optional multiline text)
- Save / Cancel buttons

**Expense List:**
- Table with columns: Date | Description | Subcategory | Amount | Category | Tags
- Category column shows colored pill badge
- Amount in mono font, rose-pink color (`color-expense`)
- Row actions: Edit (pencil) | Delete (trash) — appear on row hover
- Filter bar above list: by category, date range, subcategory, tag search
- Search box for description text

**Per-category summary strip at top of Expenses tab:**
- For each category: Name | Allocated PLN | Spent PLN | Remaining PLN | Mini progress bar
- Progress bar: green → orange at 80% → red at 100%+

---

### 4. Cash Flow Buffer

**Location:** Cash Flow tab
**Purpose:** Calculate how much to top up each account from the paycheck, and see what's left for savings.

**Buffer minimums (editable in Settings, defaults below):**

| Category | Minimum Balance |
|---|---|
| Daily Life | 2 000,00 PLN |
| Pleasure | 1 100,00 PLN |
| Business Expenses | 2 760,00 PLN |

**Layout per buffer row:**
```
[Daily Life]   Minimum required: 2 000,00 PLN   I currently have: [____] PLN   → Top up: X PLN
```

**Summary block at the bottom:**
```
Total to top up:            X PLN
Net income this month:      Y PLN
─────────────────────────────────────────
Remaining for savings:     Y − X = Z PLN
```

- Remaining shown large, green if positive, red if negative with a warning
- "Currently have" fields are editable and saved to the monthly JSON

---

### 5. History Tab

**Purpose:** Monthly archive. Auto-calculated remainders + manual balance entries.

**Layout:**
- Left: list of saved months (clickable)
- Right: summary card for selected month

**A) Auto-calculated (read-only):**
- Remaining balance per category = (allocated from net income + additional income) − expenses

**B) Manual entry (editable per month):**
- Cash on hand (PLN)
- Bank accounts (add/remove/rename accounts):
  - e.g. "mBank Main", "Revolut" — balance per account (manual entry)
- Business account (PLN)
- Savings (add/remove/rename entries):
  - e.g. "Lokata 6M", "Emergency Fund" — balance per entry (manual entry)

**"Save snapshot" button** — locks current month data into history; prompts to start a new month.

> Future phase: balances will sync automatically. Phase 1 = all manual.

---

### 6. Dashboard

**Location:** First tab shown on startup.

**Cards:**
1. **Net Income** — this month's net income (large, teal-green)
2. **Category Breakdown** — 2×2 grid of cards: allocated / spent / remaining + mini progress bar
3. **Total Expenses** — count + total sum this month
4. **Cash Flow Buffer Status** — traffic light per buffer: 🟢 OK / 🟡 Low / 🔴 Below minimum
5. **Quick-Add Expense** — inline mini form: amount, description, category — for fast logging
6. **Last 5 Expenses** — compact table

---

### 7. Settings Tab

**Sections:**
- **Categories:** edit names and percentages, add/remove categories
- **Cash Flow Buffer minimums:** edit minimum per buffer category
- **Business income defaults:** pre-fill deduction fields (VAT, tax, ZUS) from last month
- **Import from Excel:** file picker, password input, sheet name selector
- **Data:** export current month to JSON, clear current month, open data folder

---

## xlsx Import Logic

```python
import msoffcrypto
import openpyxl
import io

def load_xlsx(filepath: str, password: str = None, sheet_name: str = "kwiecień 2026") -> dict:
    """
    Opens an Excel file (optionally password-protected).
    
    1. If password provided, decrypt with msoffcrypto
    2. Open with openpyxl
    3. Find sheet by name (case-insensitive, strip whitespace)
    4. Parse: category names, percentages, expenses, business income fields
    5. Return structured dict matching data model
    
    Error handling:
    - Wrong password    → error dialog, offer retry
    - Sheet not found   → list available sheets, let user pick
    - Unrecognized data → import what is parseable, warn about skipped rows
    """
    with open(filepath, 'rb') as f:
        if password:
            office_file = msoffcrypto.OfficeFile(f)
            office_file.load_key(password=password)
            decrypted = io.BytesIO()
            office_file.decrypt(decrypted)
            wb = openpyxl.load_workbook(decrypted)
        else:
            wb = openpyxl.load_workbook(f)

    sheet = None
    for name in wb.sheetnames:
        if name.strip().lower() == sheet_name.strip().lower():
            sheet = wb[name]
            break

    if not sheet:
        return {"error": "sheet_not_found", "available_sheets": wb.sheetnames}

    # Parse sheet and return data dict
    return parsed_data
```

---

## UI Layout Specification

```
┌──────────────────────────────────────────────────────────────┐
│  ✦ FLORIN                [Month: April 2026 ▼]    [🌙] [×]  │
├───────────────┬──────────────────────────────────────────────┤
│ NAVIGATION    │                                              │
│               │                                              │
│ 🏠 Dashboard  │          MAIN CONTENT AREA                  │
│ 💰 Income     │          (changes with selected nav item)    │
│ 🧾 Expenses   │                                              │
│ 💧 Cash Flow  │                                              │
│ 📅 History    │                                              │
│ ⚙️  Settings  │                                              │
│               │                                              │
│ ─────────────│                                              │
│ Net income    │                                              │
│ 6 960,98 PLN  │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

### Styling rules (from brandGuidelines.md):
- Sidebar: `color-surface`, 220px, active item has 3px left bar in `color-primary`
- Cards: `color-surface`, `corner_radius=16`, `border=1px color-border`
- All PLN amounts: `FONT_MONO`, income = `color-income` (teal), expenses = `color-expense` (rose)
- Category pills: category color at 20% opacity background, full-opacity text

---

## Error Handling & Edge Cases

- Percentages ≠ 100% → yellow inline warning, disable save until fixed
- Overspent category → remaining shown in red, warning badge on category label
- Wrong xlsx password → dialog to retry with different password
- Sheet not found → dropdown showing available sheet names
- Delete expense → always confirm before deleting
- Polish characters in file paths → use `pathlib.Path` everywhere
- No data file yet → auto-create empty month on first launch with default values

---

## Code Quality Guidelines

- Class per view (e.g. `class DashboardView(ctk.CTkFrame)`)
- `data_manager.py` handles all file I/O — views never touch files directly
- Format currency: `f"{amount:,.2f} PLN"` (thousands separator = comma)
- Auto-save on every field change (debounce 500ms) — no manual Save button needed
- Use `ctk.StringVar`, `ctk.DoubleVar` for all reactive form fields
- App config (last used month, window size, theme) stored in `config.json`

---

## Phase 2 Preview (do NOT implement in Phase 1)

- Bank balance auto-sync via API
- Recurring expenses
- Spending charts and trends
- PDF monthly report export
- Budget goals and projections

---

*End of GEMINI.md — Reference brandGuidelines.md for all design tokens, colors, fonts, and component styles.*
