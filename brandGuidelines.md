# Florin — Brand Guidelines

> *Lift above financial chaos. Stay grounded in clarity.*

---

## Brand Identity

**App Name:** Florin  
**Tagline:** *Rise above your finances.*  
**Personality:** Soft, feminine, calm, organized, empowering  
**Audience:** Young professional woman, detail-oriented, aesthetic-driven  
**Tone:** Warm, clear, encouraging — never clinical or corporate

---

## Color System

All colors are defined as hex values for use in customtkinter themes and CTk widget configuration.

### Primary Palette

| Token | Name | Hex (Light) | Hex (Dark) | Usage |
|---|---|---|---|---|
| `color-bg` | Petal White | `#FFF5F8` | `#1E1520` | App background |
| `color-surface` | Soft Rose | `#FFFFFF` | `#2A1D28` | Cards, panels |
| `color-surface-2` | Blush | `#FFF0F4` | `#321F2F` | Nested cards, inputs |
| `color-border` | Rose Mist | `#F0C8D8` | `#4D3347` | Borders, dividers |
| `color-primary` | Dusty Rose | `#C96B98` | `#E08DB8` | Primary buttons, accents |
| `color-primary-hover` | Deep Rose | `#A84E7C` | `#CC6FA0` | Hover states |
| `color-accent` | Lavender Blush | `#D4A8E8` | `#B885D4` | Secondary accents, badges |
| `color-text` | Deep Plum | `#2D1B2E` | `#F2E6EF` | Primary text |
| `color-text-muted` | Mauve Gray | `#7C5E6A` | `#B89AAA` | Secondary text, labels |
| `color-text-faint` | Petal Gray | `#C4A8B4` | `#6B4E5E` | Placeholder text, hints |

### Semantic Colors

| Token | Hex (Light) | Hex (Dark) | Usage |
|---|---|---|---|
| `color-success` | `#6BAD8A` | `#7DC99F` | Positive balance, income |
| `color-warning` | `#D4955A` | `#E8A86A` | Low balance warnings |
| `color-error` | `#C96B6B` | `#E08D8D` | Overspent, errors |
| `color-income` | `#5A9E8A` | `#7DC9B2` | Income amounts (green-teal) |
| `color-expense` | `#C96B80` | `#E08D9E` | Expense amounts (rose) |

### Category Colors (for charts & badges)

| Category | Light Hex | Dark Hex |
|---|---|---|
| Daily Life | `#C9A86B` | `#E8C880` |
| Shared | `#6B98C9` | `#88B5E0` |
| Saved | `#6BAD8A` | `#85C9A4` |
| Pleasure | `#C96B98` | `#E08DB8` |
| Business | `#9B6BC9` | `#B888E0` |

---

## Typography

**Primary Font (UI):** `Nunito` — Rounded, friendly, highly legible  
**Secondary Font (Display/Headers):** `Playfair Display` — Elegant serif for section titles  
**Mono Font:** `JetBrains Mono` — For numbers and financial data

```
customtkinter font setup:
  FONT_DISPLAY  = ("Playfair Display", 22, "bold")
  FONT_TITLE    = ("Nunito", 16, "bold")
  FONT_BODY     = ("Nunito", 13)
  FONT_SMALL    = ("Nunito", 11)
  FONT_LABEL    = ("Nunito", 11, "bold")
  FONT_MONO     = ("JetBrains Mono", 13)
  FONT_MONO_LG  = ("JetBrains Mono", 16, "bold")
```

**Fallback stack:** `Nunito` → `Segoe UI` (Windows) → `Helvetica Neue` → `sans-serif`

---

## UI Components

### Window & Layout
- **Minimum window size:** 1100 × 720px
- **Sidebar width:** 220px
- **Content padding:** 24px
- **Card padding:** 20px inner, 12px gap between cards
- **Corner radius:** 16px for cards, 10px for buttons, 8px for inputs, 24px for category pills

### Cards
```
Background: color-surface
Border: 1px color-border
Border-radius: 16px
Shadow: subtle (use CTkFrame with fg_color)
Hover: slightly elevated (simulate with border color change)
```

### Buttons
```
Primary:    bg=color-primary, text=white, radius=10px, height=40px
Secondary:  bg=color-surface-2, text=color-text, border=color-border
Ghost:      bg=transparent, text=color-primary
Danger:     bg=color-error, text=white
Pill:       radius=24px (for category badges/chips)
```

### Inputs
```
Background: color-surface-2
Border: 1px color-border
Border-radius: 8px
Height: 40px
Focus: border → color-primary
Placeholder: color-text-faint
```

### Navigation Sidebar
```
Background: color-surface
Width: 220px
Logo area: 64px height
Nav items: 44px height, 12px padding, radius=10px
Active item: bg=color-primary (10% opacity), text=color-primary, left bar=color-primary 3px
Icons: 18px, line-style (use emoji or unicode symbols as fallbacks)
```

---

## Logo & Icon

**Logo:** Stylized "A" with an upward arrow integrated — representing "antigravity" (lifting up finances)  
**Icon character for fallback:** ✦ (four-pointed star) or 🌸 for app icon  
**CTk window icon:** Use a `.ico` or `.png` file if generated, otherwise use default

---

## Spacing System

```
SPACE_1  = 4px   # Tight gaps (icon to label)
SPACE_2  = 8px   # Input internal padding
SPACE_3  = 12px  # Between list items
SPACE_4  = 16px  # Standard component gap
SPACE_6  = 24px  # Section padding
SPACE_8  = 32px  # Between sections
SPACE_12 = 48px  # Page-level gaps
```

---

## customtkinter Theme Configuration

```python
# theme.py — Florin custom theme values
THEME = {
    "light": {
        "CTk": {"fg_color": "#FFF5F8"},
        "CTkFrame": {"fg_color": "#FFFFFF", "border_color": "#F0C8D8", "border_width": 1, "corner_radius": 16},
        "CTkButton": {"fg_color": "#C96B98", "hover_color": "#A84E7C", "text_color": "#FFFFFF", "corner_radius": 10},
        "CTkEntry": {"fg_color": "#FFF0F4", "border_color": "#F0C8D8", "text_color": "#2D1B2E"},
        "CTkLabel": {"text_color": "#2D1B2E"},
        "CTkScrollbar": {"fg_color": "#F0C8D8", "button_color": "#C96B98"},
        "CTkSegmentedButton": {"fg_color": "#FFF0F4", "selected_color": "#C96B98"},
        "CTkTabview": {"fg_color": "#FFF5F8", "segmented_button_fg_color": "#FFF0F4"},
    },
    "dark": {
        "CTk": {"fg_color": "#1E1520"},
        "CTkFrame": {"fg_color": "#2A1D28", "border_color": "#4D3347", "border_width": 1, "corner_radius": 16},
        "CTkButton": {"fg_color": "#E08DB8", "hover_color": "#CC6FA0", "text_color": "#1E1520", "corner_radius": 10},
        "CTkEntry": {"fg_color": "#321F2F", "border_color": "#4D3347", "text_color": "#F2E6EF"},
        "CTkLabel": {"text_color": "#F2E6EF"},
    }
}
```

---

## Visual Style Rules

1. **No harsh black borders** — use soft rose/pink borders at low opacity
2. **Rounded everything** — minimum 8px radius on any interactive element
3. **Numbers in mono font** — all financial figures use `JetBrains Mono`
4. **Color-coded amounts** — income = teal-green, expenses = rose-pink
5. **Soft separators** — `color-border` divider lines, never solid gray
6. **Category pills** — color-coded pill badges for category assignment
7. **Progress bars** — thin (8px height), rounded, showing % of budget used
8. **Empty states** — warm message + soft illustration emoji (🌸, ✨, 💸)
9. **Success animations** — subtle (avoid heavy motion; a color flash on save is enough)
10. **Consistent icon set** — use `lucide` icons if available, otherwise Unicode symbols

---

## Emoji Icon Map (fallback icons)

```
Dashboard  → 🏠 or ✦
Income     → 💰
Expenses   → 🧾
Cash Flow  → 💧
History    → 📅
Settings   → ⚙️
Add        → ＋
Edit       → ✏️
Delete     → 🗑
Save       → 💾
Business   → 💼
Daily Life → 🌸
Shared     → 🤝
Saved      → 🌱
Pleasure   → ✨
```

