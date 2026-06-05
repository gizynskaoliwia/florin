# main.py
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import data_manager as dm
from db import get_db_path
import theme as theme_module
from theme import *
from datetime import datetime
from pathlib import Path
from i18n import (
    get_language,
    item_count,
    month_abbr,
    month_full,
    set_language,
    t,
    tr_text as tx,
    weekday_abbr,
)
from PIL import Image
import json
import os
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent


def resource_path(name):
    return BASE_DIR / name


THEME_EXPORTS = [
    "COLOR_BG",
    "COLOR_SURFACE",
    "COLOR_SURFACE_2",
    "COLOR_BORDER",
    "COLOR_PRIMARY",
    "COLOR_PRIMARY_HOVER",
    "COLOR_PRIMARY_SOFT",
    "COLOR_ACCENT",
    "COLOR_TEXT",
    "COLOR_TEXT_MUTED",
    "COLOR_TEXT_FAINT",
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_ERROR",
    "COLOR_INCOME",
    "COLOR_EXPENSE",
    "COLOR_INCOME_SOFT",
    "COLOR_EXPENSE_SOFT",
    "COLOR_WARNING_SOFT",
    "COLOR_MET_PLAN",
    "COLOR_UNDER_PLAN",
    "COLOR_OVER_PLAN",
    "COLOR_CURRENT_MONTH",
    "CATEGORY_COLORS",
]


def sync_theme_globals():
    for name in THEME_EXPORTS:
        globals()[name] = getattr(theme_module, name)
    dm.CATEGORY_COLORS = CATEGORY_COLORS
    dm.COLOR_TEXT_FAINT = COLOR_TEXT_FAINT


def format_money(value, suffix=True):
    text = f"{value:,.2f}".replace(",", " ")
    return f"{text} PLN" if suffix else text


def signed_money(value, suffix=True):
    sign = "+" if value >= 0 else "-"
    return f"{sign} {format_money(abs(value), suffix=suffix)}"


def ui_text(en, pl):
    return pl if get_language() == "pl" else en


def parse_money(value, default=0.0):
    try:
        return float(str(value).replace(",", ".").replace(" ", "") or default)
    except (TypeError, ValueError):
        return default


def category_color(cat):
    if isinstance(cat, dict):
        return CATEGORY_COLORS.get(cat.get("id"), cat.get("color", COLOR_PRIMARY))
    return CATEGORY_COLORS.get(cat, COLOR_PRIMARY)


def display_name(value):
    return tx(value or "")


def display_category_name(cat):
    if isinstance(cat, dict):
        if get_language() == "pl":
            default_budget_names = {
                "daily_life": "Życie codzienne",
                "shared": "Wspólne",
                "saved": "Oszczędności",
                "pleasure": "Przyjemności",
                "business": "Biznes",
            }
            if cat.get("id") in default_budget_names:
                return default_budget_names[cat["id"]]
        return display_name(cat.get("name", ""))
    return display_name(cat)


def display_type(kind):
    return tx("Addition" if kind == "addition" else "Deduction")


def month_year_label(month_str, upper=False):
    year, month = map(int, month_str.split("-"))
    label = f"{month_full(month)} {year}"
    return label.upper() if upper else label


def make_pill(parent, text, color, width=None, height=28):
    pill = ctk.CTkFrame(
        parent,
        fg_color=COLOR_SURFACE_2,
        corner_radius=RADIUS_BUTTON,
        border_width=1,
        border_color=color,
        height=height,
    )
    # Never set pack_propagate(False) — let the pill auto-size to its content.
    # The width parameter is kept for API compatibility but only used as a
    # minimum width hint; the pill will still grow if the text needs more space.
    dot = ctk.CTkFrame(pill, width=8, height=8, fg_color=color, corner_radius=3)
    dot.pack(side="left", padx=(10, 6), pady=max(1, (height - 8) // 2))
    dot.pack_propagate(False)
    ctk.CTkLabel(pill, text=display_name(text), font=FONT_SMALL, text_color=COLOR_TEXT, height=height).pack(side="left", padx=(0, 12))
    return pill



def make_card(parent, **kwargs):
    options = {
        "fg_color": COLOR_SURFACE,
        "corner_radius": RADIUS_CARD,
        "border_width": 1,
        "border_color": COLOR_BORDER,
    }
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)


def open_in_file_manager(path):
    target = Path(path)
    if sys.platform == "win32":
        os.startfile(str(target))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
    else:
        subprocess.run(["xdg-open", str(target)], check=False)

class FlorinApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        apply_theme()
        self.config = dm.get_config()
        self.config["theme"] = theme_module.set_theme(self.config.get("theme", "Petal Rose"))
        sync_theme_globals()
        set_language(self.config.get("language", "en"))
        self.current_month = datetime.now().strftime("%Y-%m")
        self.config["last_month"] = self.current_month
        dm.save_config(self.config)
        self.data = dm.load_month(self.current_month)
        
        self.title("Florin")
        self.apply_window_chrome()
        try:
            self._window_icon = tk.PhotoImage(file=str(resource_path("logo2.png")))
            self.iconphoto(True, self._window_icon)
        except Exception:
            pass
        self.geometry("1200x800")
        self.minsize(1100, 720)
        self.configure(fg_color=COLOR_BG)
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1200) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1200x800+{x}+{y}")
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.views = {}
        self.setup_views()
        self.show_view("Dashboard")

    def apply_window_chrome(self):
        if sys.platform != "darwin":
            return
        try:
            appearance = "darkaqua" if self.config.get("theme") == "Dark Rose" else "aqua"
            self.wm_attributes("-appearance", appearance)
        except tk.TclError:
            pass
        
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=208, fg_color=COLOR_SURFACE, corner_radius=0, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=58)
        brand.pack(fill="x", padx=16, pady=(0, 0))
        brand.pack_propagate(False)
        try:
            self.logo_image = ctk.CTkImage(Image.open(resource_path("logo2.png")), size=(28, 28))
            ctk.CTkLabel(brand, image=self.logo_image, text="", width=28).pack(side="left", pady=15)
        except Exception:
            ctk.CTkLabel(brand, text="✦", font=(FONT_DISPLAY_FAMILY, 18, "bold"), text_color=COLOR_PRIMARY, width=28).pack(side="left", pady=15)
        ctk.CTkLabel(brand, text="Florin", font=(FONT_DISPLAY_FAMILY, 21, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=(10, 0), pady=15)

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        
        self.nav_buttons = {}
        main_items = [
            ("Dashboard", "✦", "nav.dashboard"),
            ("Income", "💰", "nav.income"),
            ("Expenses", "🧾", "nav.expenses"),
            ("Savings", "🌱", "nav.savings"),
            ("Cash Flow", "💧", "nav.cashflow"),
            ("History", "📅", "nav.history"),
            ("Shared Goals", "🎯", "nav.shared_goals"),
            ("Emergency Fund", "☂️", "nav.emergency_fund"),
        ]

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=10, pady=(14, 8))
        self._sidebar_section_label(nav_frame, t("nav.section.main"))
        
        for name, icon, label_key in main_items:
            if name == "Shared Goals" and self.config.get("enable_shared_goals", "true") != "true":
                continue
            if name == "Emergency Fund" and self.config.get("enable_emergency_fund", "false") != "true":
                continue
            self._sidebar_nav_item(nav_frame, name, icon, t(label_key))

        bottom_nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_nav.pack(fill="x", padx=10, pady=(0, 10))
        self._sidebar_section_label(bottom_nav, t("nav.section.more"))
        self._sidebar_nav_item(bottom_nav, "Settings", "⚙️", t("nav.settings"))

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=16, pady=(0, 12))
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLOR_BORDER).pack(fill="x", side="bottom")
        ctk.CTkLabel(footer, text=f"●  {t('status.local')}", font=FONT_SMALL, text_color=COLOR_SUCCESS).pack(side="left")
        ctk.CTkButton(
            footer,
            text=f"{t('nav.help')} ↗",
            width=74,
            height=22,
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_SOFT,
            font=FONT_SMALL,
            command=lambda: self.show_view("Help"),
        ).pack(side="right")

    def _sidebar_section_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text.upper(),
            font=FONT_MONO_SM_BOLD,
            text_color=COLOR_TEXT_FAINT,
            anchor="w",
            height=18,
        ).pack(fill="x", padx=6, pady=(0, 6))

    def _sidebar_nav_item(self, parent, name, icon, label):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=38, corner_radius=RADIUS_BUTTON, border_width=0)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        indicator = ctk.CTkFrame(row, width=3, fg_color="transparent", corner_radius=2)
        indicator.pack(side="left", fill="y", padx=(0, 7), pady=9)
        indicator.pack_propagate(False)

        icon_badge = ctk.CTkLabel(
            row,
            text=icon,
            width=30,
            height=24,
            corner_radius=7,
            fg_color="transparent",
            text_color=COLOR_TEXT_MUTED,
            font=self._sidebar_icon_font(icon),
        )
        icon_badge.pack(side="left", pady=7)

        text_label = ctk.CTkLabel(row, text=label, font=FONT_NAV, text_color=COLOR_TEXT_MUTED, anchor="w")
        text_label.pack(side="left", fill="x", expand=True, padx=(9, 8))

        for widget in (row, indicator, icon_badge, text_label):
            widget.bind("<Button-1>", lambda event, n=name: self.show_view(n))
            widget.bind("<Enter>", lambda event, n=name: self._sidebar_nav_hover(n, True))
            widget.bind("<Leave>", lambda event, n=name: self._sidebar_nav_hover(n, False))
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass

        self.nav_buttons[name] = {
            "row": row,
            "indicator": indicator,
            "icon": icon_badge,
            "label": text_label,
        }

    def _sidebar_icon_font(self, icon):
        if icon == "✦":
            return (FONT_DISPLAY_FAMILY, 18, "bold")
        if sys.platform == "darwin":
            return ("Apple Color Emoji", 17)
        if sys.platform == "win32":
            return ("Segoe UI Emoji", 17)
        return (FONT_BODY_FAMILY, 17)

    def _sidebar_nav_hover(self, name, hovered):
        if getattr(self, "current_view_name", None) == name or name not in self.nav_buttons:
            return
        self._style_sidebar_item(name, active=False, hovered=hovered)

    def _style_sidebar_item(self, name, active=False, hovered=False):
        item = self.nav_buttons[name]
        row = item["row"]
        indicator = item["indicator"]
        icon = item["icon"]
        label = item["label"]

        if active:
            row.configure(fg_color=COLOR_PRIMARY_SOFT, border_width=0)
            indicator.configure(fg_color=COLOR_PRIMARY)
            icon.configure(fg_color="transparent", text_color=COLOR_PRIMARY)
            label.configure(text_color=COLOR_PRIMARY)
        elif hovered:
            row.configure(fg_color=COLOR_SURFACE_2, border_width=0)
            indicator.configure(fg_color="transparent")
            icon.configure(fg_color="transparent", text_color=COLOR_TEXT)
            label.configure(text_color=COLOR_TEXT)
        else:
            row.configure(fg_color="transparent", border_width=0)
            indicator.configure(fg_color="transparent")
            icon.configure(fg_color="transparent", text_color=COLOR_TEXT_MUTED)
            label.configure(text_color=COLOR_TEXT_MUTED)
            
    def setup_views(self):
        from views.dashboard import DashboardView
        from views.savings import SavingsView, SavingsActualView
        from views.settings import SettingsView
        from views.shared_goals import SharedGoalsView
        from views.help import HelpView
        from views.income import IncomeView
        from views.expenses import ExpensesView
        from views.cashflow import CashFlowView
        from views.history import HistoryView
        
        self.views["Dashboard"] = DashboardView(self.main_container, self)
        self.views["Income"] = IncomeView(self.main_container, self)
        self.views["Expenses"] = ExpensesView(self.main_container, self)
        self.views["Savings"] = SavingsView(self.main_container, self)
        self.views["Cash Flow"] = CashFlowView(self.main_container, self)
        self.views["History"] = HistoryView(self.main_container, self)
        self.views["Shared Goals"] = SharedGoalsView(self.main_container, self)
        from views.emergency_fund import EmergencyFundView
        self.views["Emergency Fund"] = EmergencyFundView(self.main_container, self)
        self.views["Settings"] = SettingsView(self.main_container, self)
        self.views["Help"] = HelpView(self.main_container, self)
        
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")
            
    def show_view(self, name):
        self.current_view_name = name
        for btn_name in self.nav_buttons:
            self._style_sidebar_item(btn_name, active=btn_name == name)
                
        self.views[name].tkraise()
        self.views[name].refresh()

    def rebuild_shell(self, view_name=None):
        view_name = view_name or getattr(self, "current_view_name", "Dashboard")
        for child in self.winfo_children():
            child.destroy()

        self.configure(fg_color=COLOR_BG)
        self.apply_window_chrome()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.views = {}
        self.setup_views()
        self.show_view(view_name if view_name in self.views else "Dashboard")
        
    def refresh_sidebar(self):
        if hasattr(self, "sidebar"):
            self.sidebar.destroy()
        self.setup_sidebar()
        
    def save_data(self):
        dm.save_month(self.current_month, self.data)

    def change_month(self, delta):
        self.save_data()
        year, month = map(int, self.current_month.split("-"))
        month += delta
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self.current_month = f"{year:04d}-{month:02d}"
        self.config["last_month"] = self.current_month
        dm.save_config(self.config)
        self.data = dm.load_month(self.current_month)
        self.views.get(getattr(self, "current_view_name", "Dashboard"), self.views["Dashboard"]).refresh()

if __name__ == "__main__":
    app = FlorinApp()
    app.mainloop()
