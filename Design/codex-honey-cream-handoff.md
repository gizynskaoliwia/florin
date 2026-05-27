# Codex handoff — apply the “Honey Cream” direction to Florin

Paste the prompt at the bottom of this file into Codex. Run it from the Florin
repo root (`/Users/michalmystkowski/Documents/Florin`) — Codex needs that as
its working directory so it can edit `theme.py` and verify the app still runs.

The repo is a Python + `customtkinter` desktop app. All colors live in one
file: **`theme.py`**. Replacing the constants there re-skins the whole UI
because every view reads `from theme import *`.

---

## What “Honey Cream” means (source of truth)

OKLch tokens, copied verbatim from `florin-color-explorations.html`:

```css
[data-scheme="honey-cream"] {
  --bg:           oklch(96.5% 0.020 80);
  --surface:      oklch(100% 0 0);
  --surface-2:    oklch(94% 0.022 80);
  --border:       oklch(86% 0.030 75);
  --fg:           oklch(24% 0.025 60);
  --muted:        oklch(48% 0.030 65);
  --faint:        oklch(74% 0.025 70);
  --accent:       oklch(56% 0.13 50);
  --accent-hover: oklch(46% 0.15 45);
  --accent-soft:  oklch(56% 0.13 50 / 0.10);
  --income:       oklch(54% 0.10 130);
  --expense:      oklch(56% 0.14 40);
  --warning:      oklch(72% 0.14 80);
  --cat-1:        oklch(72% 0.13 75);
  --cat-2:        oklch(60% 0.10 230);
  --cat-3:        oklch(58% 0.11 140);
  --cat-4:        oklch(58% 0.13 35);
}
```

## Hex equivalents (already converted, ready for `theme.py`)

These are computed from the OKLch values above (sRGB, gamut-clipped). Drop
them in 1-for-1 — the existing constant names stay identical so nothing else
in the codebase changes.

| `theme.py` constant     | Old (Petal Rose) | New (Honey Cream) | Role                                  |
| ----------------------- | ---------------- | ----------------- | ------------------------------------- |
| `COLOR_BG`              | `#FFF5F8`        | `#FBF2E5`         | App background                        |
| `COLOR_SURFACE`         | `#FFFFFF`        | `#FFFFFF`         | Cards / sidebar                       |
| `COLOR_SURFACE_2`       | `#FFF0F4`        | `#F3EADB`         | Hover / sub-surface                   |
| `COLOR_BORDER`          | `#F0C8D8`        | `#DDCFBC`         | Hairline borders                      |
| `COLOR_PRIMARY`         | `#C96B98`        | `#AF5A21`         | Primary action / brand accent         |
| `COLOR_PRIMARY_HOVER`   | `#A84E7C`        | `#973200`         | Primary action hover                  |
| `COLOR_ACCENT`          | `#D4A8E8`        | `#D49838`         | Secondary accent (was lavender)       |
| `COLOR_TEXT`            | `#2D1B2E`        | `#281C13`         | Primary text                          |
| `COLOR_TEXT_MUTED`      | `#7C5E6A`        | `#6A5A4C`         | Secondary text                        |
| `COLOR_TEXT_FAINT`      | `#C4A8B4`        | `#B5A89A`         | Captions / placeholders               |
| `COLOR_SUCCESS`         | `#6BAD8A`        | `#558A49`         | Success state                         |
| `COLOR_WARNING`         | `#D4955A`        | `#D29922`         | Warning state                         |
| `COLOR_ERROR`           | `#C96B6B`        | `#B84F40`         | Error state                           |
| `COLOR_INCOME`          | `#5A9E8A`        | `#5B7A38`         | Income figures (olive-green)          |
| `COLOR_EXPENSE`         | `#C96B80`        | `#B6522D`         | Expense figures (terracotta)          |
| `COLOR_MET_PLAN`        | `#6BAD8A`        | `#558A49`         | Actual = planned                      |
| `COLOR_UNDER_PLAN`      | `#D4955A`        | `#D18E35`         | Actual < planned                      |
| `COLOR_OVER_PLAN`       | `#5A8EC9`        | `#328BB0`         | Actual > planned                      |
| `COLOR_CURRENT_MONTH`   | `#F5E6F0`        | `#F3EADB`         | Current-month column highlight        |
| `CATEGORY_COLORS["daily_life"]` | `#C9A86B`| `#D49838`         | Category — Daily life                 |
| `CATEGORY_COLORS["shared"]`     | `#6B98C9`| `#328BB0`         | Category — Shared                     |
| `CATEGORY_COLORS["saved"]`      | `#6BAD8A`| `#558A49`         | Category — Saved                      |
| `CATEGORY_COLORS["pleasure"]`   | `#C96B98`| `#BA5A42`         | Category — Pleasure (was rose)        |
| `CATEGORY_COLORS["business"]`   | `#9B6BC9`| `#AF5A21`         | Category — Business (kept on accent)  |

Fonts and `apply_theme()` stay as they are — Honey Cream is a palette swap,
not a typography change.

---

## Reference material Codex should read (read-only)

- `BRAND_GUIDELINES.md` (this repo) — for posture rules.
- The exploration UIs that prove the palette works on real screens:
  - `/Users/michalmystkowski/Library/Application Support/Open Design/namespaces/release-stable/data/projects/ce16141b-915d-4723-8bb1-6cd9d88a88a6/florin-color-explorations.html`
  - `…/color-explorations.html`
  - `…/app.html` — full multi-screen prototype (currently rendered in Petal Rose; the layout is the target)
  - `…/landing.html` — marketing page (won’t be re-skinned by Codex unless asked)
- `…/brand-spec.md` — codified version of the brand.

---

## Prompt to paste into Codex

```text
You are working in the Florin repo at /Users/michalmystkowski/Documents/Florin.
Florin is a Python + customtkinter desktop budget app. All UI colors live in
theme.py and every view does `from theme import *`, so changing the constants
there re-skins the whole app.

I want you to switch the visual direction from “Petal Rose” (current) to
“Honey Cream”. The new palette is already computed for you below. Do not
invent new tokens, do not add a theme switcher, do not refactor view files —
just replace the constants in theme.py with the values in the table.

Replace these constants in theme.py (keep names, comments, and order intact):

  COLOR_BG          = "#FBF2E5"
  COLOR_SURFACE     = "#FFFFFF"
  COLOR_SURFACE_2   = "#F3EADB"
  COLOR_BORDER      = "#DDCFBC"
  COLOR_PRIMARY     = "#AF5A21"
  COLOR_PRIMARY_HOVER = "#973200"
  COLOR_ACCENT      = "#D49838"
  COLOR_TEXT        = "#281C13"
  COLOR_TEXT_MUTED  = "#6A5A4C"
  COLOR_TEXT_FAINT  = "#B5A89A"
  COLOR_SUCCESS     = "#558A49"
  COLOR_WARNING     = "#D29922"
  COLOR_ERROR       = "#B84F40"
  COLOR_INCOME      = "#5B7A38"
  COLOR_EXPENSE     = "#B6522D"
  COLOR_MET_PLAN    = "#558A49"
  COLOR_UNDER_PLAN  = "#D18E35"
  COLOR_OVER_PLAN   = "#328BB0"
  COLOR_CURRENT_MONTH = "#F3EADB"

  CATEGORY_COLORS = {
      "daily_life": "#D49838",
      "shared":     "#328BB0",
      "saved":      "#558A49",
      "pleasure":   "#BA5A42",
      "business":   "#AF5A21",
  }

Then:

1. Grep the codebase for any hard-coded hex literals matching the OLD palette
   (#FFF5F8, #FFFFFF (only inside theme contexts), #FFF0F4, #F0C8D8, #C96B98,
   #A84E7C, #D4A8E8, #2D1B2E, #7C5E6A, #C4A8B4, #6BAD8A, #D4955A, #C96B6B,
   #5A9E8A, #C96B80, #5A8EC9, #F5E6F0, #C9A86B, #6B98C9, #9B6BC9). Anything
   outside theme.py should be replaced with the matching `COLOR_*` /
   `CATEGORY_COLORS[...]` constant — not with the new hex literal.

2. Run `python3 -c "import theme; print('ok')"` to make sure the module still
   imports.

3. If the project has a quick smoke-launch (e.g. `python3 main.py`), DO NOT
   actually launch a window in this session. Just confirm the Python compiles
   with `python3 -m py_compile main.py theme.py`.

4. Show me the diff before committing. Do not commit unless I say so.

The brand posture (rounded cards, mono numerics for figures, single-accent
budget per screen, no harsh shadows) must stay unchanged — you are only
swapping the palette.
```

---

## Why these constants and not a CSS/JSON file

`theme.py` already centralises every color the app uses; the views (`main.py`)
read those constants by name. Keeping the swap inside that one file is the
smallest, most reversible change — `git checkout theme.py` undoes the whole
re-skin if you change your mind.

If later you want a runtime theme switcher, that’s a separate task —
turn `theme.py` into a function that returns a dict keyed by theme name and
have the views read `theme.current()` instead of module-level constants. Not
needed for this handoff.
