# theme.py
import customtkinter as ctk

# Colors (Light Mode Defaults based on Brand Guidelines)
THEME_NAMES = ("Petal Rose", "Honey Cream", "Dark Rose")

THEMES = {
    "Petal Rose": {
        "COLOR_BG": "#FFF5F8",
        "COLOR_SURFACE": "#FFFFFF",
        "COLOR_SURFACE_2": "#FFF0F4",
        "COLOR_BORDER": "#F0C8D8",
        "COLOR_PRIMARY": "#C96B98",
        "COLOR_PRIMARY_HOVER": "#A84E7C",
        "COLOR_PRIMARY_SOFT": "#F7E7F0",
        "COLOR_ACCENT": "#D4A8E8",
        "COLOR_TEXT": "#2D1B2E",
        "COLOR_TEXT_MUTED": "#7C5E6A",
        "COLOR_TEXT_FAINT": "#C4A8B4",
        "COLOR_SUCCESS": "#6BAD8A",
        "COLOR_WARNING": "#D4955A",
        "COLOR_ERROR": "#C96B6B",
        "COLOR_INCOME": "#5A9E8A",
        "COLOR_EXPENSE": "#C96B80",
        "COLOR_INCOME_SOFT": "#E9F5EF",
        "COLOR_EXPENSE_SOFT": "#F8E6EB",
        "COLOR_WARNING_SOFT": "#F7EBDD",
        "COLOR_MET_PLAN": "#6BAD8A",
        "COLOR_UNDER_PLAN": "#D4955A",
        "COLOR_OVER_PLAN": "#5A8EC9",
        "COLOR_CURRENT_MONTH": "#F5E6F0",
        "CATEGORY_COLORS": {
            "daily_life": "#C9A86B",
            "shared": "#6B98C9",
            "saved": "#6BAD8A",
            "pleasure": "#C96B98",
            "business": "#9B6BC9",
        },
    },
    "Honey Cream": {
        "COLOR_BG": "#FBF2E5",
        "COLOR_SURFACE": "#FFFFFF",
        "COLOR_SURFACE_2": "#F3EADB",
        "COLOR_BORDER": "#DDCFBC",
        "COLOR_PRIMARY": "#AF5A21",
        "COLOR_PRIMARY_HOVER": "#973200",
        "COLOR_PRIMARY_SOFT": "#F4E2D5",
        "COLOR_ACCENT": "#D49838",
        "COLOR_TEXT": "#281C13",
        "COLOR_TEXT_MUTED": "#6A5A4C",
        "COLOR_TEXT_FAINT": "#B5A89A",
        "COLOR_SUCCESS": "#558A49",
        "COLOR_WARNING": "#D29922",
        "COLOR_ERROR": "#B84F40",
        "COLOR_INCOME": "#5B7A38",
        "COLOR_EXPENSE": "#B6522D",
        "COLOR_INCOME_SOFT": "#E8F0E3",
        "COLOR_EXPENSE_SOFT": "#F5E1D9",
        "COLOR_WARNING_SOFT": "#F5EAD5",
        "COLOR_MET_PLAN": "#558A49",
        "COLOR_UNDER_PLAN": "#D18E35",
        "COLOR_OVER_PLAN": "#328BB0",
        "COLOR_CURRENT_MONTH": "#F3EADB",
        "CATEGORY_COLORS": {
            "daily_life": "#D49838",
            "shared": "#328BB0",
            "saved": "#558A49",
            "pleasure": "#BA5A42",
            "business": "#AF5A21",
        },
    },
    "Dark Rose": {
        "COLOR_BG": "#241A22",
        "COLOR_SURFACE": "#2F2430",
        "COLOR_SURFACE_2": "#3A2B39",
        "COLOR_BORDER": "#5B4354",
        "COLOR_PRIMARY": "#E18AB4",
        "COLOR_PRIMARY_HOVER": "#F0A4C8",
        "COLOR_PRIMARY_SOFT": "#4B3445",
        "COLOR_ACCENT": "#C89BE8",
        "COLOR_TEXT": "#FFF5F8",
        "COLOR_TEXT_MUTED": "#D8C5CF",
        "COLOR_TEXT_FAINT": "#9B8491",
        "COLOR_SUCCESS": "#8AC9A6",
        "COLOR_WARNING": "#E0B168",
        "COLOR_ERROR": "#E17C7C",
        "COLOR_INCOME": "#8AC9A6",
        "COLOR_EXPENSE": "#E08AA0",
        "COLOR_INCOME_SOFT": "#2E493D",
        "COLOR_EXPENSE_SOFT": "#4D303B",
        "COLOR_WARNING_SOFT": "#4D402C",
        "COLOR_MET_PLAN": "#8AC9A6",
        "COLOR_UNDER_PLAN": "#E0B168",
        "COLOR_OVER_PLAN": "#86B5E6",
        "COLOR_CURRENT_MONTH": "#3A2B39",
        "CATEGORY_COLORS": {
            "daily_life": "#D9BE79",
            "shared": "#86B5E6",
            "saved": "#8AC9A6",
            "pleasure": "#E18AB4",
            "business": "#B794E6",
        },
    },
}

THEME_ALIASES = {
    "light": "Petal Rose",
    "rose": "Petal Rose",
    "petal": "Petal Rose",
    "petal rose": "Petal Rose",
    "honey": "Honey Cream",
    "cream": "Honey Cream",
    "honey cream": "Honey Cream",
    "dark": "Dark Rose",
    "dark rose": "Dark Rose",
}


def normalize_theme_name(name):
    if name in THEMES:
        return name
    return THEME_ALIASES.get(str(name or "").strip().lower(), "Petal Rose")


def get_theme_palette(name):
    return THEMES[normalize_theme_name(name)]


def set_theme(name):
    theme_name = normalize_theme_name(name)
    palette = THEMES[theme_name]
    for key, value in palette.items():
        if key == "CATEGORY_COLORS":
            continue
        globals()[key] = value
    CATEGORY_COLORS.clear()
    CATEGORY_COLORS.update(palette["CATEGORY_COLORS"])
    return theme_name


# Defaults are populated through set_theme() so runtime theme switching and
# first import use the same path.
CATEGORY_COLORS = {}
set_theme("Petal Rose")

# Fonts
# Use families that ship on both macOS and Windows so layout measurements stay
# close across platforms. Trebuchet keeps the rounded brand feel without the
# heavy spacing Verdana introduced in dense budget screens.
FONT_DISPLAY_FAMILY = "Georgia"
FONT_BODY_FAMILY = "Trebuchet MS"
FONT_MONO_FAMILY = "Courier New"

FONT_DISPLAY = (FONT_DISPLAY_FAMILY, 21, "bold")
FONT_SECTION = (FONT_DISPLAY_FAMILY, 23, "bold")
FONT_DETAIL_TITLE = (FONT_DISPLAY_FAMILY, 22, "bold")
FONT_HERO = (FONT_MONO_FAMILY, 48, "bold")
FONT_DETAIL_AMOUNT = (FONT_MONO_FAMILY, 34, "bold")
FONT_TITLE = (FONT_BODY_FAMILY, 15, "bold")
FONT_BODY = (FONT_BODY_FAMILY, 13)
FONT_NAV = (FONT_BODY_FAMILY, 13, "bold")
FONT_SMALL = (FONT_BODY_FAMILY, 11)
FONT_LABEL = (FONT_BODY_FAMILY, 11, "bold")
FONT_MONO = (FONT_MONO_FAMILY, 13)
FONT_MONO_LG = (FONT_MONO_FAMILY, 15, "bold")
FONT_MONO_SM = (FONT_MONO_FAMILY, 8)
FONT_MONO_SM_BOLD = (FONT_MONO_FAMILY, 9, "bold")

RADIUS_INPUT = 8
RADIUS_BUTTON = 8
RADIUS_CARD = 12

def apply_theme():
    ctk.set_appearance_mode("light")  # For Phase 1 we stick to light theme
    ctk.set_default_color_theme("green") # Base theme, will be overridden by custom colors
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
