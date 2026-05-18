# theme.py
import customtkinter as ctk

# Colors (Light Mode Defaults based on Brand Guidelines)
COLOR_BG = "#FFF5F8"
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_2 = "#FFF0F4"
COLOR_BORDER = "#F0C8D8"
COLOR_PRIMARY = "#C96B98"
COLOR_PRIMARY_HOVER = "#A84E7C"
COLOR_ACCENT = "#D4A8E8"
COLOR_TEXT = "#2D1B2E"
COLOR_TEXT_MUTED = "#7C5E6A"
COLOR_TEXT_FAINT = "#C4A8B4"

COLOR_SUCCESS = "#6BAD8A"
COLOR_WARNING = "#D4955A"
COLOR_ERROR = "#C96B6B"
COLOR_INCOME = "#5A9E8A"
COLOR_EXPENSE = "#C96B80"

# Subtle comparison tints (text colors)
COLOR_MET_PLAN = "#6BAD8A"       # subtle green - actual == planned
COLOR_UNDER_PLAN = "#D4955A"     # subtle orange - actual < planned
COLOR_OVER_PLAN = "#5A8EC9"      # subtle blue/teal - actual > planned

# Current month column highlight
COLOR_CURRENT_MONTH = "#F5E6F0"  # very light primary tint

# Category Colors
CATEGORY_COLORS = {
    "daily_life": "#C9A86B",
    "shared": "#6B98C9",
    "saved": "#6BAD8A",
    "pleasure": "#C96B98",
    "business": "#9B6BC9"
}

# Fonts
FONT_DISPLAY = ("Playfair Display", 22, "bold")
FONT_TITLE = ("Nunito", 16, "bold")
FONT_BODY = ("Nunito", 13)
FONT_SMALL = ("Nunito", 11)
FONT_LABEL = ("Nunito", 11, "bold")
FONT_MONO = ("JetBrains Mono", 13)
FONT_MONO_LG = ("JetBrains Mono", 16, "bold")

def apply_theme():
    ctk.set_appearance_mode("light")  # For Phase 1 we stick to light theme
    ctk.set_default_color_theme("green") # Base theme, will be overridden by custom colors
