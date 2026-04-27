<div align="center">
  <img src="logo2.png" alt="Florin Logo" width="100"/>
  <h1>Florin</h1>
  <p><strong>A personal budget tracker for freelancers & self-employed professionals</strong></p>
  <p>Built with Python · customtkinter · JSON persistence</p>
</div>

---

## Overview

Florin is a desktop budget tracking app designed specifically for people with variable monthly income — like freelancers or sole proprietors. It helps you:

- Calculate your **net income** from a gross invoice after deductions (VAT, income tax, ZUS)
- **Split net income** across personal budget categories by percentage
- Track and categorise **expenses**
- Monitor your **cash flow buffer** and calculate top-up amounts
- Keep a monthly **history** with account balances

All data is stored locally in JSON files — no cloud, no subscriptions.

---

## Screenshots

> _Coming soon_

---

## Tech Stack

| Library | Purpose |
|---|---|
| `customtkinter` | Modern GUI framework (dark/light mode) |
| `openpyxl` | Read/write Excel files |
| `msoffcrypto-tool` | Decrypt password-protected `.xlsx` |
| `Pillow` | Icon/image handling |

Python 3.10+ required.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/florin.git
cd florin

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

> **Windows users:** You can also double-click `main.py` if Python is associated with `.py` files, or create a shortcut to `pythonw.exe main.py` for a clean launch without a terminal window.

---

## Project Structure

```
florin/
├── main.py              # App entry point + all UI views
├── data_manager.py      # JSON load/save, xlsx import, data helpers
├── theme.py             # Color constants and font definitions
├── requirements.txt     # Python dependencies
├── logo2.png            # App icon (circular floral logo)
└── data/                # Auto-created; stores monthly JSON files (gitignored)
```

---

## Data Storage

All data is saved in `./data/` as JSON files:

| File | Contents |
|---|---|
| `data/YYYY-MM.json` | Monthly income, expenses, categories, cashflow |
| `data/history.json` | Monthly snapshots and account balances |
| `config.json` | App config: last month, window size (gitignored) |

No data ever leaves your machine.

---

## Features

### 💰 Business Income
Enter your gross invoice amount and all deductions manually. Net income is calculated live:

```
Gross invoice:      13 000.00 PLN
− VAT:              − 2 430.89 PLN
− Income tax:       − 2 008.13 PLN
− ZUS:              − 1 600.00 PLN
─────────────────────────────────
Net income:         = 6 960.98 PLN
```

### 📊 Category Split
Distribute net income across custom categories by percentage. Default categories:

| Category | Default % |
|---|---|
| Daily Life | 40% |
| Shared | 20% |
| Saved | 20% |
| Pleasure | 20% |

Add or remove categories per month. Percentages must sum to 100%.

### ➕ Extra Income
Log one-off income (e.g. a freelance bonus) and assign it to:
- All categories proportionally, or
- One specific category

### 🧾 Expenses
- Log expenses with date, amount, description, subcategory and category
- See a per-category summary: allocated / spent / remaining
- Delete expenses with one click

### 💧 Cash Flow Buffer
Define minimum balances for key accounts and calculate exactly how much to top up after receiving your paycheck. Shows what's left for savings.

### 📅 History _(coming in a future phase)_
Monthly archive with auto-calculated remainders and manual account balance entries.

---

## Input Conventions

- **Currency:** PLN (Polish Złoty)
- **Dates:** DD/MM/YYYY
- **Decimal separator:** Use `.` or `,` — the app auto-converts commas to dots
- **Numbers:** Only digits and `.` are accepted in numeric fields

---

## Roadmap

- [x] Business income calculator
- [x] Category split with add/remove
- [x] Extra income dialog
- [x] Expense tracker
- [x] Cash flow buffer
- [ ] History tab with snapshots
- [ ] Settings tab (category names, buffer minimums)
- [ ] xlsx import from encrypted budget file
- [ ] Spending charts and trends
- [ ] PDF monthly report export

---

## License

MIT — do whatever you want with it.

---

<div align="center">
  <sub>Built with ❤️ for better financial clarity</sub>
</div>
