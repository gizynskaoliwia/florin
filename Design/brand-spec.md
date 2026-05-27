# Florin — Brand Spec (codified for HTML build)

> *Lift above financial chaos. Stay grounded in clarity.*
> Source of truth: `BRAND_GUIDELINES.md` + `logo2.png` from the user's Florin repo.

## Visual posture (observed from logo + guidelines)

- **Logo:** delicate sage-green leaves cradling a peach/terracotta lily on a cream off-white circle. Organic, botanical, hand-painted feel — never geometric or sharp.
- **Canvas:** intentionally warm — *Petal White* (`#FFF5F8`) is the brand background, not an "AI default beige". The brand's whole point is replacing clinical-bank UI with something calm.
- **Numbers carry the work.** All financial figures are in `JetBrains Mono`, color-coded: teal-green for income, dusty rose for expenses, plum for neutral.
- **No harsh black borders, no shadows.** Soft rose-mist borders + whitespace separate everything.
- **Rounded everything.** 16px on cards, 10px on buttons, 8px on inputs, 24px on category pills.
- **Restraint:** one accent (Dusty Rose) used for primary actions and net-income hero only. Category colors are reserved for category-specific UI (pills, charts, allocation cards).

## Color tokens (light mode — the default)

OKLch values calibrated to match the source hex while staying P3-safe.

```css
:root {
  /* Surfaces */
  --bg:        oklch(97.5% 0.012 350);   /* #FFF5F8 Petal White */
  --surface:   oklch(100% 0 0);          /* #FFFFFF Soft Rose */
  --surface-2: oklch(96.5% 0.018 350);   /* #FFF0F4 Blush */
  --border:    oklch(85% 0.05 350);      /* #F0C8D8 Rose Mist */
  --border-strong: oklch(72% 0.06 350);  /* slightly stronger for inputs at focus */

  /* Text */
  --fg:        oklch(22% 0.04 340);      /* #2D1B2E Deep Plum */
  --muted:     oklch(48% 0.04 340);      /* #7C5E6A Mauve Gray */
  --faint:     oklch(75% 0.03 340);      /* #C4A8B4 Petal Gray */

  /* Brand action */
  --accent:        oklch(63% 0.13 348);  /* #C96B98 Dusty Rose */
  --accent-hover:  oklch(52% 0.14 348);  /* #A84E7C Deep Rose */
  --accent-soft:   oklch(63% 0.13 348 / 0.10);
  --lavender:      oklch(78% 0.10 320);  /* #D4A8E8 Lavender Blush, secondary accent */

  /* Semantic */
  --income:    oklch(60% 0.07 175);      /* #5A9E8A teal-green */
  --expense:   oklch(60% 0.13 6);        /* #C96B80 rose */
  --success:   oklch(67% 0.09 155);      /* #6BAD8A */
  --warning:   oklch(70% 0.12 60);       /* #D4955A peachy */
  --error:     oklch(60% 0.16 18);       /* #C96B6B */

  /* Category palette (charts + pills) */
  --cat-daily:    oklch(75% 0.10 80);    /* #C9A86B golden */
  --cat-shared:   oklch(64% 0.10 250);   /* #6B98C9 blue */
  --cat-saved:    oklch(67% 0.09 155);   /* #6BAD8A green */
  --cat-pleasure: oklch(63% 0.13 348);   /* #C96B98 rose */
  --cat-business: oklch(57% 0.15 295);   /* #9B6BC9 violet */
}
```

## Dark-mode tokens (override)

```css
[data-theme="dark"] {
  --bg:        oklch(20% 0.02 340);      /* #1E1520 */
  --surface:   oklch(26% 0.025 340);     /* #2A1D28 */
  --surface-2: oklch(29% 0.03 340);      /* #321F2F */
  --border:    oklch(38% 0.04 340);      /* #4D3347 */
  --fg:        oklch(94% 0.02 340);      /* #F2E6EF */
  --muted:     oklch(75% 0.03 340);      /* #B89AAA */
  --faint:     oklch(46% 0.03 340);      /* #6B4E5E */
  --accent:        oklch(72% 0.10 340);  /* #E08DB8 */
  --accent-hover:  oklch(64% 0.12 340);  /* #CC6FA0 */
}
```

## Typography

```css
--font-display: 'Playfair Display', 'Iowan Old Style', Georgia, serif;
--font-body:    'Nunito', -apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif;
--font-mono:    'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace;
```

| Use | Family | Size | Weight |
|---|---|---|---|
| Hero display | Playfair Display | clamp(40px, 5vw, 72px) | 600 |
| Section title | Playfair Display | 28–32px | 600 |
| Card title | Nunito | 16px | 700 |
| Body | Nunito | 14–15px | 400 |
| Small / label | Nunito | 11–12px | 700, uppercase, letter-spaced |
| Net income hero | JetBrains Mono | clamp(36px, 4vw, 56px) | 700 |
| Inline mono number | JetBrains Mono | 14–18px | 500–700 |

All financial figures use `font-variant-numeric: tabular-nums` and `--font-mono`.

## Spacing rhythm

```
--sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px;
--sp-6: 24px; --sp-8: 32px; --sp-12: 48px; --sp-16: 64px;
```

## Radii

```
--r-input: 8px;   --r-btn: 10px;   --r-card: 16px;   --r-pill: 24px;
```

## Posture rules (non-negotiable)

1. Background is always `--bg` (Petal White). **Never** white-on-white outside cards.
2. Borders are always `--border` (rose mist) at 1px. No solid grey rules. No box-shadows except for floating menus / modals where a soft 0 8px 24px `oklch(22% 0.04 340 / 0.08)` is allowed.
3. Numbers are always mono + tabular. Income green-teal, expense rose, neutral plum.
4. Only one Dusty-Rose surface per screen at a time (primary CTA *or* hero number, not both backgrounded).
5. Category pills always carry their category color at low opacity (10–14%) with the dark category color as text. Border same color at 30%.
6. Empty states get a one-line warm encouragement + a subtle emoji (🌸 ✨ 🌱 💧). Never "no data found".
7. Desktop app shell window is **1200 × 800** with a 220px sidebar.
8. Mobile/small reflow: stack sidebar to top sheet, single-column cards, never shrink desktop fixed widths.
