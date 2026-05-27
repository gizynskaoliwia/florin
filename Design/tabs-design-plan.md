# Florin — design plan for the remaining tabs

Status of `app.html` today:

| Tab | State |
|---|---|
| Dashboard | ✅ Designed |
| Expenses | ✅ Designed (list + detail) |
| Onboarding | ✅ Designed |
| Settings | ✅ Designed |
| **Income** | ⚠️ Stub only |
| **Savings** | ⚠️ Stub only |
| **Cash flow** | ⚠️ Stub only |
| **History** | ⚠️ Stub only (also a placeholder in Florin code per `ARCHITECTURE.md` §8) |

Florin already implements **Income, Expenses, Savings, Cash flow** as functional Python views (`main.py` IncomeView, ExpensesView, SavingsView, CashFlowView). History is the only one that's also incomplete in code. So the design work below is mostly about **codifying what these screens should look like in Honey Cream**, not inventing new behavior — except for History, where we're designing what the placeholder should become.

All screens share:
- Sidebar nav + window chrome from `app.html` (same `.app-window` shell, same sidebar, same topbar)
- Tokens from `assets/florin.css` after Honey Cream re-skin
- Mono numerics with `font-variant-numeric: tabular-nums`
- One accent (`--accent`) used at most twice per screen — typically eyebrow + primary CTA
- A **month switcher** in the topbar where the screen is month-scoped (Income, Expenses, Cash flow); no switcher on Savings (year-wide grid) or History (its own time axis)

I treat each tab below in the same shape:

1. **Purpose** — what the user actually does here
2. **Layout** — the visual structure on desktop ≥ 1100 px (and what changes on narrow)
3. **Modules** — the named blocks I'd build, with the data fields they bind to
4. **Interactions** — the actions that have to work
5. **States** — empty, error, edit-mode, transitional
6. **Open decisions** — things I want to lock with you before designing

Numbers in examples come from `docs/DATA_MODEL.md` and the existing Dashboard.

---

## 1. Income

### Purpose
The screen where the user logs a month's gross invoice, walks through deductions (VAT, income tax, ZUS), watches the net form, and adds any one-off "additional income". The Dashboard hero card is a **summary** of what lives here; this screen is where it's edited.

### Layout (desktop)
```
┌───────────────────────────────────────────────────────────────┐
│ Topbar:   < April 2026 >        [✎ Edit]  [＋ Log invoice]    │
├───────────────────────────────────────────────────────────────┤
│ ┌─ Net income hero card ──────────────────────────────────┐   │
│ │ NET · APRIL                                             │   │
│ │ 6 960,98 PLN     ←—— 48px mono, accent-strong            │   │
│ │ Gross 13 000,00 − VAT 2 430,89 − Tax 2 008,13 − ZUS …    │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                                │
│ ┌─ Income items table (read mode) ───────────────────────┐    │
│ │ ITEM             TYPE       AMOUNT     TARGET           │    │
│ │ Gross invoice    Addition   13 000,00  —                │    │
│ │ VAT              Deduction  − 2 430,89 —                │    │
│ │ Income tax       Deduction  − 2 008,13 —                │    │
│ │ ZUS              Deduction  − 1 600,00 —                │    │
│ │ Freelance bonus  Addition       500,00 Pleasure         │    │
│ │                                                         │    │
│ │ [＋ Addition] [＋ Deduction]                            │    │
│ └────────────────────────────────────────────────────────┘    │
│                                                                │
│ ┌─ Allocation preview (live) ─────────────────────────────┐   │
│ │ How net 6 960,98 splits — same donut+legend as Dashboard │   │
│ │ but read-only here; "Edit split" jumps to Settings.      │   │
│ └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

Narrow (< 920 px): hero card stays full width; allocation preview drops below the items table; columns collapse to two (`Item · Amount`) with type/target as a sub-line.

### Modules
- **Net income hero** — `business.gross_invoice`, `business.vat_deducted`, `business.income_tax_deducted`, `business.zus_deducted`, `business.net_income`
- **Items table** — combines `business.*` rows + `additional_income[]` into one list. Type column shows `Addition` / `Deduction`. "Target" column is the per-item `target_category` (or `—` if proportional).
- **Allocation preview** — same donut as Dashboard, fed by `categories[]` × net. Read-only — its job here is reassurance, not editing.

### Interactions
- **Edit mode toggle** (`✎ Edit` → `✓ Done`) — turns amount cells into inputs (mirrors `IncomeView.toggle_edit()` in code). On Done: validate, recalculate net, refresh allocation donut.
- **＋ Addition / ＋ Deduction** — append a blank row in edit mode with a focus on the description input.
- **＋ Log invoice** (primary CTA) — only visible when there is no `business.gross_invoice` yet for the month. Opens a small inline form that fills all four `business.*` fields at once.
- **Per-row delete** — only visible in edit mode, only on `additional_income[]` rows (the four `business.*` rows are always present).

### States
- **Empty (no invoice yet)** — hero shows `—,—`, "Log this month's invoice to see your net" with a single CTA.
- **Edit mode** — entries replace labels, primary CTA changes to `✓ Done`, sidebar dims slightly.
- **Validation error** — inline red microcopy under the offending row; net updates only on blur if the row parses.

### Open decisions
- Do we keep the **allocation preview on this screen**, or push the user to Dashboard? My take: keep it small (one row, no chart), so you don't have to switch tabs to feel the impact of an edit.
- Should "Log invoice" be a **modal** or an **inline expand**? Inline matches the screen's "everything-in-one-table" feel and avoids a dialog.
- Currency symbol: `PLN` after the number, or no symbol in the table (only in the hero)? Less noise = no symbol in table.

---

## 2. Expenses (already designed — proposed refinements only)

The list-+-detail layout you already approved stays. Three refinements I'd make once we're in Honey Cream:

1. **Group filter strip** — Florin supports per-month `expense_categories[]` and per-expense `subcategory`. The pill row in the current design only shows the four split categories (`Daily life · Shared · Saved · Pleasure`). Add a second, lighter filter strip below it for **expense subcategories** (e.g. "Beauty · Groceries · Transport") that updates from `expense_categories[]`.
2. **Funding source pill on each row** — When an expense is funded from a **savings category** (`savings_category_id` set, per `data_manager.get_savings_spent`), tag the row with a small `🌱 Lokata 6M` chip in the accent. Today the design treats every expense as drawing from a split bucket, which hides the savings-funded ones.
3. **Detail card: edit history** — A subtle "Last edited 2 days ago" line under the date field. Florin's `db.py` already records `updated_at` on cashflow rows; if it doesn't on expenses yet, that's a one-line schema add — flag it for Codex.

No new layout work; this becomes a small `app.html` patch + a Codex prompt for the schema field if needed.

---

## 3. Savings

This is the **most complex** screen in Florin (~700 lines in `SavingsView`). The HTML can simplify the view-mode rendering but must respect the same domain shape: groups, categories, planning grid vs. actual grid, deadline highlighting, surplus cascade.

### Purpose
Plan and track multi-month savings goals. Two stacked tables:
- **Actual savings** — what's already in each savings pot (months 1-12 columns + summary).
- **Planning grid** — what's *intended* per month, with progress vs. target.

### Layout (desktop, designed for ≥ 1280 px because the 12-column grid is wide)
```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar:  Savings · 2026                  [✎ Edit] [＋ Group] [＋ Goal]│
├──────────────────────────────────────────────────────────────────────┤
│ ┌─ Year summary strip ────────────────────────────────────────────┐  │
│ │ Saved 18 240,00   ·  On plan 78%  ·  4 of 11 goals met          │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│ ▾ ACTUAL SAVINGS  (frosted section header, sticky on scroll)         │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Category   J F M A M J J A S O N D   Saved Missing %  Spent Bal ││
│ │ Lokata 6M  · · · 200 · · · · · · · ·   200    300 40%   150 +50 ││
│ │ ▸ Travel (group, collapsed)                                       ││
│ │ ▾ Gifts (group, expanded)                                         ││
│ │   Mum's bday  · · · · · 50 · · · · · ·   50    50 50%    0 +50  ││
│ │   Christmas   · · · · · · · · · · 100 ·  100    0 100% 100  0   ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ▾ PLANNING GRID                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Category   J F M A M J J A S O N D   Progress                    ││
│ │ Lokata 6M  50 50 50 50 50 50 50 50 50 50 50 50  ▓▓▓▓░ 60%       ││
│ │ … cascade-adjusted cells render with strikethrough + new value …  ││
│ │                                                                   ││
│ │ Assumed available 2 000 2 000 2 000 …                            ││
│ │ Total allocated  1 850 1 850 1 850 …                             ││
│ │ Remaining          150   150   150 …  ← green if ≥ 0, red if < 0 ││
│ └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

Cell colour rules (mirror Florin code in `ARCHITECTURE.md` §6):
- Current month column header gets `--current-month` tint
- Deadline-month cell gets `--accent` background (takes priority over current month)
- Actual table cell colours: `actual > planned` → `--over-plan`, `==` → `--met-plan`, `<` → `--under-plan`, missing → muted

### Modules
- **Year summary strip** — derived from `savings_planner.json`: total saved across all `actual_grid` months; on-plan % = `total_saved / total_planned_so_far`; goals met = count where `progress ≥ 1.0`.
- **Actual savings table** — `savings_actual_grid` × `savings_actual_available` per month. Right summary columns: Saved, Missing, %, Spent (single-month, from `expenses.savings_category_id`), Balance (saved − spent).
- **Planning grid table** — `savings_grid` × `savings_assumed`. Progress bar in the right column = sum-to-deadline / target.
- **Group accordions** — collapsed by default (matches Florin's deferred-widget rule). Group header row shows monthly **sums** of children. Same render pattern in actual + planning tables.
- **Edit-mode footer (sticky)** — `Reset · Cancel · Save` only visible in edit mode.

### Interactions
- **Edit toggle** swaps every cell label for a number input. On Save: validate (numbers only), persist, re-render with cascades recomputed.
- **Group expand/collapse** — instant after first expand (cached per Florin's `_user_toggled` rule).
- **Cascade highlight** — when a planned cell is reduced by the surplus cascade, render `~~50~~ 32` with the strikethrough in `--text-faint` and the new value in `--accent`. A small "Why?" tooltip explains the surplus.
- **＋ Group** opens a small dialog (name only). **＋ Goal** opens the full category editor (name, target, deadline month, group, next-year target).
- **Horizontal scroll** when the table overflows — show a soft fade gradient on the right edge and keep the first column (category name) sticky.

### States
- **No goals yet** — empty illustration + "Add your first goal" CTA, no tables rendered.
- **All groups collapsed** — only group header rows visible; "Expand all" / "Collapse all" links above the table.
- **Edit mode** — entries everywhere; the year-summary strip shows `Pending changes` instead of stats.

### Open decisions
- **Two tables stacked, or tabs?** I prefer stacked (matches today's Python implementation; one mental model). Tabs would force the user to switch contexts when comparing planned vs. actual — that's the whole point of the screen.
- **Mobile fallback** — at < 920 px the 12-column grid is unreadable. My proposal: render a **per-category card view** with one sparkline per goal + the summary numbers, and a "View grid on desktop" prompt. Don't try to shrink the grid.
- **Surplus cascade tooltip copy** — needs a one-line explanation. Suggested: "Goal fully funded and spent — surplus reduces next year's plan."
- **What sits in the topbar besides the year label?** No month switcher (year-wide screen). I'd add a year picker `‹ 2026 ›` for browsing past plans.

---

## 4. Cash flow

### Purpose
The "do I have enough to top up?" screen. For each tracked account/buffer (Daily life, Pleasure, Business…), the user enters the **current balance**, sees the **minimum target**, and Florin tells them the **exact top-up** to do after this month's invoice — and the **surplus** that's free for savings.

### Layout (desktop)
```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar:   < April 2026 >                  [✎ Edit] [Adjust targets ↗]│
├──────────────────────────────────────────────────────────────────────┤
│ ┌─ Big result card ────────────────────────────────────────────┐    │
│ │ TOP-UP NEEDED THIS MONTH                                      │    │
│ │ 4 220,00 PLN     ← from net 6 960,98                          │    │
│ │ Free for savings: 1 740,98 PLN                                │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│ ┌─ Per-buffer cards (3-up row) ────────────────────────────────┐    │
│ │ DAILY LIFE          PLEASURE           BUSINESS               │    │
│ │ Now    1 380,00     Now      950,00    Now    2 100,00        │    │
│ │ Min    2 000,00     Min    1 100,00    Min    2 760,00        │    │
│ │ ──────────────      ──────────────     ──────────────         │    │
│ │ Top up   620,00     Top up   150,00    Top up   660,00        │    │
│ │ ▓▓▓▓▓░░ 69%         ▓▓▓▓▓▓░ 86%        ▓▓▓▓▓▓░ 76%            │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│ ┌─ Recent edits log (small) ───────────────────────────────────┐    │
│ │ Daily life balance · 1 380,00 · updated 2 days ago            │    │
│ │ Pleasure target · 1 100,00 → 1 200,00 · last month            │    │
│ └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

Narrow (< 920 px): per-buffer cards stack vertically; the "big result" card stays prominent at the top.

### Modules
- **Big result card** — sums all `cashflow_buffer` top-ups; subtracts from `business.net_income` to compute `Free for savings`. The most important number on the screen, biggest type.
- **Per-buffer card** (one per `cashflow_targets` row in DB) — name, current balance input, minimum target (read-only here, edited via "Adjust targets ↗"), top-up = `max(0, min - current)`, fill bar = `current / min`.
- **Recent edits log** — uses `cashflow.updated_at` from DB. Shows last 5 edits across all buffers.

### Interactions
- **Edit mode** — current-balance fields become inputs; on Done: persist + recompute top-ups + refresh big result.
- **Adjust targets ↗** routes to Settings § cashflow targets (we already designed that section).
- **＋ Add buffer** appears only in edit mode, only on the per-buffer row (last card slot becomes a `+` placeholder).

### States
- **No buffers configured** — empty state with CTA "Set up buffers in Settings".
- **All buffers above target** — big result card shows `0,00 PLN top-up needed` in `--success`, and `Free for savings` becomes the dominant number.
- **One buffer below target by a small amount** — top-up fill bar is mostly green; only the small delta is rendered.

### Open decisions
- **Should the per-buffer card show a 7-day sparkline of balance history?** Nice but adds schema (we don't store balance history per day today). Mark as v2.
- **Top-up rounding** — do we round to nearest 10 PLN? Most banking apps do. I'd default to no rounding here (cash flow is exact) and add it as a Settings toggle later.
- **What if `current > min`?** Top-up = 0. Card still shown, just with no top-up row. I'd grey out the bar to signal "fully funded".

---

## 5. History

This is the only one that's both a stub in design **and** a placeholder in Florin code. So this is the most invention-heavy of the five — but the data shape is already written for us in `docs/DATA_MODEL.md` (`history.json` with `months[]` snapshots).

### Purpose
A calm month-by-month archive. For each past month: net income, what was allocated, what was spent, end-of-month balances. Click any row to expand it into a snapshot card showing exactly what the Dashboard looked like that month.

### Layout (desktop)
```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar:   2026 ▾    [Search]                       [Export year ↗]  │
├──────────────────────────────────────────────────────────────────────┤
│ ┌─ Year strip ─────────────────────────────────────────────────┐    │
│ │ 2026 · 4 months tracked                                       │    │
│ │ Net 27 843,92  ·  Spent 18 220,40  ·  Saved 4 100,00          │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│ ┌─ Month rows (one per past month, newest first) ──────────────┐    │
│ │ APRIL 2026                          Net  6 960,98 ›           │    │
│ │ Spent 2 184,50 (47 items) · Daily 40 · Shared 20 · Saved 20…  │    │
│ │ ──────────────────────────────────────────────────            │    │
│ │ MARCH 2026                          Net  7 102,30 ›           │    │
│ │ Spent 3 010,12 (62 items) · Daily 40 · Shared 20 · Saved 20…  │    │
│ │ ──────────────────────────────────────────────────            │    │
│ │ FEBRUARY 2026                       Net  6 802,15 ›           │    │
│ │ …                                                             │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│ Click a row → expands inline to:                                     │
│ ┌─ April 2026 snapshot ────────────────────────────────────────┐    │
│ │ Allocation pie · Top expense categories · Account balances    │    │
│ │ Cash 300,00 · mBank 3 200,00 · Revolut 500,00 · Lokata 15 000│    │
│ └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

Narrow: rows reflow but stay one-per-line; expansion takes full width.

### Modules
- **Year strip** — aggregates over `history.json/months[]` filtered by year. Pure read.
- **Month row** — bound to one entry. Shows month label, net, spent, expense count, category mix as inline mini-pills.
- **Expanded snapshot card** — when a row is expanded:
  - Allocation donut for that month (`category_remainders` against allocated)
  - Top 5 expense subcategories (computed from that month's expenses on demand — would need a small `data_manager.get_top_subcategories(month)` helper, flag for Codex)
  - Account balance list from `bank_accounts[]`, `cash`, `business_account`, `savings[]`
- **Save snapshot CTA** — only on the **current** month, sitting in the Dashboard topbar (not here). Pressing it appends to `history.json/months[]`.

### Interactions
- **Year picker** in topbar — `2026 ▾` opens a small list of years that have entries.
- **Search** — filters by month label or by description match in expenses (live, debounced 200 ms).
- **Row click** — expand/collapse the snapshot card inline (one expanded at a time; opening a new one collapses the previous).
- **Export year ↗** — generates a single PDF or printable HTML view summarising every month in the year. v2 if this is too much for v1.

### States
- **Empty (no past months)** — illustration + "Save your first snapshot from the Dashboard". Block all controls.
- **Current month is incomplete** — never appears here; History is past-only.
- **One month, no balances** — the snapshot card just shows "No account balances captured for this month".

### Open decisions
- **Auto-snapshot vs. manual?** Today's `data/history.json` is manual (user clicks "Save snapshot"). I'd keep it manual for v1 — auto creates surprise data that doesn't match what the user remembers. Add an auto-prompt at month rollover later.
- **What goes in the row vs. the expansion?** I'd keep the row to **one line** (month, net, headline) so 12 months fit in a tall window. Everything else in the expansion. The current placeholder code already shows a multi-line card per month — that's denser than I'd want.
- **Export format** — PDF needs an extra dependency (`reportlab`). HTML print stylesheet is free and already half-present. Default to print-ready HTML.

---

## Suggested order to design these next

| # | Tab | Why this order |
|---|---|---|
| 1 | **Cash flow** | Smallest screen, sharpest payoff; the "big result" card is one of Florin's most-used moments. Ships fast. |
| 2 | **Income** | Direct cousin of Dashboard hero; reuses the donut module already designed. Almost no new components. |
| 3 | **Savings** | Largest screen, but the table pattern is reusable (would also tighten the Settings categories section). Saves it for when momentum is high. |
| 4 | **History** | Last because Florin code itself is a placeholder — designing it forces a small data-model conversation (top subcategories helper, schema for `updated_at` if missing). |
| — | Expenses refinements | Slot in alongside any of the above as small `app.html` patches. |

## After each tab is designed

The handoff to Codex follows the same shape as `codex-prompt.md` for Honey Cream:

1. Design the screen in `app.html` (or split out `app/<tab>.html` if it gets big).
2. Diff against the Florin Python view (`IncomeView` / `CashFlowView` / `SavingsView` / `HistoryView`) to identify the exact widget changes.
3. Write a Codex prompt that says: "in `main.py`, in `<View>`, replace the current widget tree with the structure shown in `app.html` `data-screen-content="<tab>"`. Use existing `theme.py` constants. Don't change `data_manager.py` behavior. Show me the diff."

Each tab handoff should fit in one Codex session and one round of review.
