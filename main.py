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
    if width is not None:
        pill.configure(width=width)
        pill.pack_propagate(False)
    dot = ctk.CTkFrame(pill, width=8, height=8, fg_color=color, corner_radius=3)
    dot.pack(side="left", padx=(10, 6))
    dot.pack_propagate(False)
    ctk.CTkLabel(pill, text=display_name(text), font=FONT_SMALL, text_color=COLOR_TEXT, height=height).pack(side="left", padx=(0, 10))
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

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.dashboard"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=22)

        ctk.CTkButton(
            self.topbar, text=f"+ {t('common.add_expense')}", height=32, width=132,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            corner_radius=RADIUS_BUTTON, command=lambda: self.controller.show_view("Expenses")
        ).pack(side="right", padx=(8, 22))
        self.snapshot_status = ctk.StringVar(value="")
        ctk.CTkButton(
            self.topbar, text=t("common.save_snapshot"), height=32, width=130,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
            command=self.save_snapshot,
        ).pack(side="right", padx=8)
        ctk.CTkLabel(self.topbar, textvariable=self.snapshot_status, font=FONT_SMALL, text_color=COLOR_SUCCESS).pack(side="right", padx=4)
        month_box = ctk.CTkFrame(self.topbar, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        month_box.pack(side="right", padx=8)
        ctk.CTkButton(month_box, text="‹", width=28, height=28, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(-1)).pack(side="left", padx=(4, 0), pady=3)
        self.month_lbl = ctk.CTkLabel(month_box, text="", font=FONT_MONO, text_color=COLOR_TEXT, width=112)
        self.month_lbl.pack(side="left")
        ctk.CTkButton(month_box, text="›", width=28, height=28, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(1)).pack(side="left", padx=(0, 4), pady=3)

        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=22, pady=22)
        
    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        data = self.controller.data
        net = dm.get_net_income(data)
        cats = data.get("categories", [])
        total_exp = dm.get_total_expenses(data)
        remaining = sum(dm.get_remaining_amount(data, cat["id"]) for cat in cats)
        self.month_lbl.configure(text=month_year_label(self.controller.current_month, upper=True))

        hero_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        hero_grid.pack(fill="x")
        hero_grid.grid_columnconfigure(0, weight=12, uniform="hero")
        hero_grid.grid_columnconfigure(1, weight=10, uniform="hero")

        hero = make_card(hero_grid, height=238)
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        hero.grid_propagate(False)
        hero.grid_columnconfigure(0, weight=1)
        hero_head = ctk.CTkFrame(hero, fg_color="transparent")
        hero_head.pack(fill="x", padx=24, pady=(24, 0))
        ctk.CTkButton(
            hero_head,
            text=t("common.edit_income"),
            height=30,
            width=118,
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_SOFT,
            corner_radius=RADIUS_BUTTON,
            command=lambda: self.controller.show_view("Income"),
        ).pack(side="right", anchor="n")
        hero_copy = ctk.CTkFrame(hero_head, fg_color="transparent")
        hero_copy.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(hero_copy, text=f"●  {t('dashboard.net_income')}", font=FONT_LABEL, text_color=COLOR_PRIMARY).pack(anchor="w")
        amount_row = ctk.CTkFrame(hero_copy, fg_color="transparent")
        amount_row.pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(amount_row, text=format_money(net, suffix=False), font=FONT_HERO, text_color=COLOR_INCOME).pack(side="left")
        ctk.CTkLabel(amount_row, text="PLN", font=FONT_TITLE, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(8, 0), pady=(22, 0))
        ctk.CTkLabel(
            hero_copy,
            text=t("dashboard.net_income_desc"),
            font=FONT_BODY, text_color=COLOR_TEXT_MUTED, wraplength=360, width=390, anchor="w", justify="left"
        ).pack(anchor="w")

        ctk.CTkFrame(hero, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=24, pady=16)
        breakdown = ctk.CTkFrame(hero, fg_color="transparent")
        breakdown.pack(fill="x", padx=24, pady=(0, 18))
        income_items = data.get("income_items", [])
        breakdown_items = income_items[:4] or [
            {"name": "Gross", "amount": 0.0, "type": "addition"},
            {"name": "VAT", "amount": 0.0, "type": "deduction"},
            {"name": "Income tax", "amount": 0.0, "type": "deduction"},
            {"name": "ZUS", "amount": 0.0, "type": "deduction"},
        ]
        for idx, item in enumerate(breakdown_items):
            breakdown.grid_columnconfigure(idx, weight=1)
            cell = ctk.CTkFrame(breakdown, fg_color="transparent")
            cell.grid(row=0, column=idx, sticky="ew")
            ctk.CTkLabel(cell, text=display_name(item["name"]).upper(), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            sign = "" if item["type"] == "addition" else "- "
            color = COLOR_TEXT if item["type"] == "addition" else COLOR_EXPENSE
            ctk.CTkLabel(cell, text=f"{sign}{format_money(item['amount'], suffix=False)}", font=FONT_MONO, text_color=color).pack(anchor="w")

        donut_card = make_card(hero_grid, height=238)
        donut_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        donut_card.grid_propagate(False)
        donut_card.grid_columnconfigure(1, weight=1)
        canvas = tk.Canvas(donut_card, width=160, height=160, bg=COLOR_SURFACE, highlightthickness=0)
        canvas.grid(row=0, column=0, padx=(22, 16), pady=36)
        self._draw_donut(canvas, cats)
        legend = ctk.CTkFrame(donut_card, fg_color="transparent")
        legend.grid(row=0, column=1, sticky="nsew", padx=(0, 22), pady=32)
        for cat in cats:
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(fill="x", pady=4)
            swatch = ctk.CTkFrame(row, width=9, height=9, fg_color=category_color(cat), corner_radius=3)
            swatch.pack(side="left", padx=(0, 8))
            swatch.pack_propagate(False)
            ctk.CTkLabel(row, text=display_category_name(cat), font=FONT_BODY, text_color=COLOR_TEXT, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{cat['percent']:.0f}%", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=44, anchor="e").pack(side="right")

        stats = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 16))
        stats.grid_columnconfigure((0, 1, 2), weight=1, uniform="stats")
        self._stat_card(stats, 0, t("dashboard.spent"), total_exp, COLOR_EXPENSE, t("dashboard.spent_desc"))
        self._stat_card(stats, 1, t("dashboard.remaining"), remaining, COLOR_SUCCESS if remaining >= 0 else COLOR_ERROR, t("dashboard.remaining_desc"))
        self._stat_card(stats, 2, t("dashboard.free_savings"), max(0, remaining), COLOR_TEXT, t("dashboard.free_savings_desc"))

        lower = ctk.CTkFrame(self.scroll, fg_color="transparent")
        lower.pack(fill="x", pady=(0, 16))
        lower.grid_columnconfigure(0, weight=16, uniform="lower")
        lower.grid_columnconfigure(1, weight=10, uniform="lower")

        alloc = make_card(lower)
        alloc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(alloc, text=t("dashboard.spending_by_category"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(alloc, text=t("dashboard.allocated_spent_remaining"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 8))
        for cat in cats:
            self._category_row(alloc, cat)

        buffer = make_card(lower)
        buffer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        buffer_head = ctk.CTkFrame(buffer, fg_color="transparent")
        buffer_head.pack(fill="x", padx=24, pady=(22, 4))
        ctk.CTkLabel(buffer_head, text=t("dashboard.cashflow_buffer"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(
            buffer_head,
            text=f"{t('common.adjust')} →",
            width=72,
            height=24,
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_SOFT,
            font=FONT_SMALL,
            command=lambda: self.controller.show_view("Settings"),
        ).pack(side="right")
        total_box = ctk.CTkFrame(buffer, fg_color=COLOR_INCOME_SOFT, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        total_box.pack(fill="x", padx=24, pady=(12, 12))
        ctk.CTkLabel(total_box, text=t("dashboard.free_savings"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(total_box, text=format_money(max(0, remaining), suffix=False), font=(FONT_MONO_FAMILY, 22, "bold"), text_color=COLOR_INCOME).pack(anchor="e", padx=16, pady=(0, 12))
        for target in dm.get_cashflow_targets()[:4]:
            row = ctk.CTkFrame(buffer, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=8)
            ctk.CTkLabel(row, text=target["name"], font=FONT_BODY, text_color=COLOR_TEXT, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=signed_money(target["target"]), font=FONT_MONO, text_color=COLOR_WARNING).pack(side="right")
            progress = ctk.CTkProgressBar(buffer, height=6, progress_color=COLOR_WARNING, fg_color=COLOR_SURFACE_2)
            progress.pack(fill="x", padx=24, pady=(0, 4))
            progress.set(0.78)

        self._recent_list(total_exp)

    def save_snapshot(self):
        self.controller.save_data()
        meta = dm.save_snapshot(self.controller.current_month, self.controller.data)
        created = meta["created_at"].split(" ")[-1][:5]
        self.snapshot_status.set(t("status.snapshot_saved").format(time=created))

    def _draw_donut(self, canvas, cats):
        start = 90
        total = sum(max(cat.get("percent", 0), 0) for cat in cats) or 1
        for cat in cats:
            extent = -360 * (max(cat.get("percent", 0), 0) / total)
            canvas.create_arc(12, 12, 148, 148, start=start, extent=extent, fill=category_color(cat), outline="")
            start += extent
        canvas.create_oval(46, 46, 114, 114, fill=COLOR_SURFACE, outline=COLOR_SURFACE)
        canvas.create_text(80, 76, text="100%", fill=COLOR_TEXT, font=(FONT_MONO_FAMILY, 16, "bold"))
        canvas.create_text(80, 96, text=t("dashboard.donut_label"), fill=COLOR_TEXT_MUTED, font=(FONT_MONO_FAMILY, 7, "bold"))

    def _stat_card(self, parent, column, label, value, color, subtext):
        card = make_card(parent)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0 if column == 2 else 8))
        ctk.CTkLabel(card, text=label, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 3))
        ctk.CTkLabel(card, text=format_money(value, suffix=False), font=FONT_MONO_LG, text_color=color).pack(anchor="w", padx=16)
        ctk.CTkLabel(card, text=subtext, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, wraplength=230, justify="left").pack(anchor="w", padx=16, pady=(3, 14))

    def _category_row(self, parent, cat):
        allocated = dm.get_allocated_amount(self.controller.data, cat["id"])
        spent = dm.get_spent_amount(self.controller.data, cat["id"])
        rem = allocated - spent
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=8)
        pill = make_pill(row, display_category_name(cat), category_color(cat), width=148)
        pill.pack(side="left")
        mid = ctk.CTkFrame(row, fg_color="transparent")
        mid.pack(side="left", fill="x", expand=True, padx=12)
        meta = ctk.CTkFrame(mid, fg_color="transparent")
        meta.pack(fill="x")
        spent_label = "wydano" if get_language() == "pl" else "spent"
        of_label = "z" if get_language() == "pl" else "of"
        ctk.CTkLabel(meta, text=f"{format_money(spent, suffix=False)} {spent_label}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(meta, text=f"{of_label} {format_money(allocated, suffix=False)}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right")
        progress = ctk.CTkProgressBar(mid, height=6, progress_color=category_color(cat), fg_color=COLOR_SURFACE_2)
        progress.pack(fill="x", pady=(4, 0))
        progress.set(min(spent / allocated, 1.0) if allocated > 0 else 0)
        ctk.CTkLabel(row, text=signed_money(rem, suffix=False), font=FONT_MONO, text_color=COLOR_SUCCESS if rem >= 0 else COLOR_ERROR, width=100).pack(side="right")

    def _recent_list(self, total_exp):
        card = make_card(self.scroll)
        card.pack(fill="x")
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(18, 12))
        current_month = datetime.strptime(self.controller.current_month, "%Y-%m")
        recent_title = f"{tx('Recent expenses')} · {month_full(current_month.month)}"
        ctk.CTkLabel(head, text=recent_title, font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(
            head,
            text=f"{tx('View all')} {len(self.controller.data.get('expenses', []))} →",
            height=24,
            width=92,
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_SOFT,
            font=FONT_SMALL,
            command=lambda: self.controller.show_view("Expenses"),
        ).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        expenses = sorted(self.controller.data.get("expenses", []), key=lambda exp: self._date_key(exp), reverse=True)[:5]
        if not expenses:
            ctk.CTkLabel(card, text=t("dashboard.no_expenses"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(padx=24, pady=18, anchor="w")
        for exp in expenses:
            self._recent_row(card, exp)
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        ctk.CTkButton(
            card,
            text=f"{t('dashboard.view_all_expenses')} →",
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_SOFT,
            height=38,
            command=lambda: self.controller.show_view("Expenses"),
        ).pack(fill="x", padx=24, pady=8)

    def _recent_row(self, parent, exp):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=10)
        ctk.CTkLabel(row, text=self._date_key(exp).strftime("%d %b"), font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=70, anchor="w").pack(side="left")
        desc = ctk.CTkFrame(row, fg_color="transparent")
        desc.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(desc, text=exp.get("description") or tx("Expense"), font=FONT_BODY, text_color=COLOR_TEXT).pack(anchor="w")
        exp_cats = {c["id"]: c["name"] for c in self.controller.data.get("expense_categories", [])}
        ctk.CTkLabel(desc, text=display_name(exp_cats.get(exp.get("expense_category_id"), "Uncategorized")), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
        cat = next((c for c in self.controller.data.get("categories", []) if c["id"] == exp.get("category_id")), None)
        if cat:
            pill = make_pill(row, display_category_name(cat), category_color(cat), width=132, height=26)
            pill.pack(side="left", padx=12)
        ctk.CTkLabel(row, text=f"- {format_money(exp['amount'], suffix=False)}", font=FONT_MONO, text_color=COLOR_EXPENSE, width=100).pack(side="right")

    def _date_key(self, exp):
        try:
            return datetime.strptime(exp.get("date", ""), "%d/%m/%Y")
        except Exception:
            return datetime.min

class IncomeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.editing = False

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.income"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)

        self.actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        self.actions.pack(side="right", padx=24)
        month_box = ctk.CTkFrame(self.actions, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        month_box.pack(side="left", padx=(0, 10))
        ctk.CTkButton(month_box, text="‹", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(-1)).pack(side="left", padx=(4, 0), pady=3)
        self.month_lbl = ctk.CTkLabel(month_box, text="", font=FONT_MONO, text_color=COLOR_TEXT, width=118)
        self.month_lbl.pack(side="left")
        ctk.CTkButton(month_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(1)).pack(side="left", padx=(0, 4), pady=3)
        self.edit_btn = ctk.CTkButton(self.actions, text=tx("✎ Edit"), width=86, height=34, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=self.toggle_edit)
        self.edit_btn.pack(side="left", padx=(0, 8))
        self.add_deduction_btn = ctk.CTkButton(self.actions, text=tx("− Deduction"), width=112, height=34, fg_color=COLOR_SURFACE, text_color=COLOR_ERROR, hover_color=COLOR_EXPENSE_SOFT, border_width=1, border_color=COLOR_BORDER, command=lambda: self.add_item("deduction"))
        self.add_addition_btn = ctk.CTkButton(self.actions, text=ui_text("+ Log invoice", "+ Dodaj przychód"), width=128, height=34, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=lambda: self.add_item("addition"))
        self.add_addition_btn.pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)

        self.hero_card = make_card(self.scroll, height=178)
        self.hero_card.pack(fill="x", pady=(0, 22))
        self.hero_card.pack_propagate(False)
        self.hero_card.grid_columnconfigure(0, weight=1)
        self.hero_card.grid_columnconfigure(1, weight=0)

        hero_left = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        hero_left.grid(row=0, column=0, sticky="nsew", padx=32, pady=26)
        self.hero_kicker = ctk.CTkLabel(hero_left, text="", font=FONT_MONO_SM_BOLD, text_color=COLOR_PRIMARY)
        self.hero_kicker.pack(anchor="w")
        amount_row = ctk.CTkFrame(hero_left, fg_color="transparent")
        amount_row.pack(anchor="w", pady=(8, 2))
        self.net_lbl = ctk.CTkLabel(amount_row, text="0.00", font=FONT_HERO, text_color=COLOR_INCOME)
        self.net_lbl.pack(side="left")
        ctk.CTkLabel(amount_row, text="PLN", font=FONT_TITLE, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(10, 0), pady=(26, 0))
        self.net_breakdown_lbl = ctk.CTkLabel(hero_left, text="", font=FONT_MONO, text_color=COLOR_TEXT_MUTED)
        self.net_breakdown_lbl.pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(
            hero_left,
            text=ui_text(
                "Change any invoice, bonus or deduction below. The monthly split recalculates immediately.",
                "Zmień fakturę, bonus albo odliczenie poniżej. Podział miesiąca przelicza się od razu.",
            ),
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            wraplength=520,
            justify="left",
        ).pack(anchor="w")

        hero_right = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        hero_right.grid(row=0, column=1, sticky="e", padx=32, pady=26)
        self.last_edited_lbl = ctk.CTkLabel(hero_right, text="", font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_FAINT)
        self.last_edited_lbl.pack(anchor="e", pady=(40, 8))
        ctk.CTkButton(
            hero_right,
            text=ui_text("Recalculate split", "Przelicz podział"),
            width=154,
            height=32,
            fg_color=COLOR_SURFACE_2,
            text_color=COLOR_TEXT,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.calculate_split,
        ).pack(anchor="e")

        self.items_card = make_card(self.scroll)
        self.items_card.pack(fill="both", expand=True, pady=(0, 22))
        items_hdr = ctk.CTkFrame(self.items_card, fg_color="transparent")
        items_hdr.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(items_hdr, text=ui_text("Income items", "Pozycje przychodów"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.items_count_lbl = ctk.CTkLabel(items_hdr, text="", font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED)
        self.items_count_lbl.pack(side="right")
        ctk.CTkFrame(self.items_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        self.items_scroll = ctk.CTkFrame(self.items_card, fg_color="transparent")
        self.items_scroll.pack(fill="both", expand=True)

        self.split_card = make_card(self.scroll)
        self.split_card.pack(fill="x", pady=(0, 6))
        header_row = ctk.CTkFrame(self.split_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(header_row, text=tx("Category Split"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.sum_warning = ctk.CTkLabel(header_row, text="", font=FONT_BODY, text_color=COLOR_WARNING)
        self.sum_warning.pack(side="right")
        ctk.CTkFrame(self.split_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        self.cat_rows_frame = ctk.CTkFrame(self.split_card, fg_color="transparent")
        self.cat_rows_frame.pack(fill="x", padx=20, pady=18)
        
        self.cat_vars = {}
        self.cat_lbls = {}
        self.cat_pct_lbls = {}
        self.cat_bar_widgets = {}
        self.cat_built = False

    def toggle_edit(self):
        self.editing = not self.editing
        if self.editing:
            self.edit_btn.configure(text=tx("✓ Done"), fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
            self.add_deduction_btn.pack(side="left", padx=(0, 8), before=self.add_addition_btn)
        else:
            self.edit_btn.configure(text=tx("✎ Edit"), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT)
            self.add_deduction_btn.pack_forget()
        self.build_items_list()
        self.build_cat_rows()
        self.calculate_split()

    def add_item(self, item_type):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Add Addition" if item_type == "addition" else "Add Deduction"))
        dialog.geometry("420x450" if item_type == "addition" else "420x320")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text=tx("Amount (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        
        alloc_mode_var = ctk.StringVar(value=ui_text("Proportional", "Proporcjonalnie"))
        cat_var = ctk.StringVar()
        
        if item_type == "addition":
            ctk.CTkLabel(dialog, text=ui_text("Allocation:", "Alokacja:"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
            
            alloc_options = [ui_text("Proportional", "Proporcjonalnie"), ui_text("Direct to Category", "Przypisz do jednej kategorii")]
            alloc_menu = ctk.CTkOptionMenu(dialog, values=alloc_options, variable=alloc_mode_var)
            alloc_menu.pack(fill="x", padx=20)
            
            cat_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            
            ctk.CTkLabel(cat_frame, text=tx("Target Category:"), anchor="w").pack(fill="x", pady=(10, 5))
            cats = self.controller.data.get("categories", [])
            cat_names = [display_category_name(c) for c in cats]
            if cat_names:
                cat_var.set(cat_names[0])
            cat_menu = ctk.CTkOptionMenu(cat_frame, values=cat_names, variable=cat_var)
            cat_menu.pack(fill="x")
            
            def on_alloc_change(val):
                if val == ui_text("Direct to Category", "Przypisz do jednej kategorii"):
                    cat_frame.pack(fill="x", padx=20)
                else:
                    cat_frame.pack_forget()
                    
            alloc_menu.configure(command=on_alloc_change)
            on_alloc_change(alloc_mode_var.get())
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                cat_id = None
                if item_type == "addition" and alloc_mode_var.get() == ui_text("Direct to Category", "Przypisz do jednej kategorii"):
                    matched = next((c for c in self.controller.data.get("categories", []) if display_category_name(c) == cat_var.get()), None)
                    if matched:
                        cat_id = matched["id"]
                        
                item = {"id": dm.generate_id(), "name": name, "amount": amt, "type": item_type, "category_id": cat_id}
                self.controller.data.setdefault("income_items", []).append(item)
                self.controller.save_data()
                dialog.destroy()
                self.refresh()
            except:
                pass
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)

    def edit_item(self, item_id):
        item = next((i for i in self.controller.data.get("income_items", []) if i["id"] == item_id), None)
        if not item:
            return
        item_type = item.get("type", "addition")
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit Item"))
        dialog.geometry("420x450" if item_type == "addition" else "420x320")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.insert(0, item["name"])
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text=tx("Amount (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.insert(0, str(item["amount"]))
        amt_entry.pack(fill="x", padx=20)
        
        alloc_mode_var = ctk.StringVar(value=ui_text("Proportional", "Proporcjonalnie"))
        cat_var = ctk.StringVar()
        
        if item_type == "addition":
            ctk.CTkLabel(dialog, text=ui_text("Allocation:", "Alokacja:"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
            
            alloc_options = [ui_text("Proportional", "Proporcjonalnie"), ui_text("Direct to Category", "Przypisz do jednej kategorii")]
            
            # Default state
            if item.get("category_id"):
                alloc_mode_var.set(ui_text("Direct to Category", "Przypisz do jednej kategorii"))
            
            alloc_menu = ctk.CTkOptionMenu(dialog, values=alloc_options, variable=alloc_mode_var)
            alloc_menu.pack(fill="x", padx=20)
            
            cat_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            
            ctk.CTkLabel(cat_frame, text=tx("Target Category:"), anchor="w").pack(fill="x", pady=(10, 5))
            cats = self.controller.data.get("categories", [])
            cat_names = [display_category_name(c) for c in cats]
            if cat_names:
                cat_var.set(cat_names[0])
                
            # Pre-select actual category if exists
            if item.get("category_id"):
                matched = next((c for c in cats if c["id"] == item["category_id"]), None)
                if matched:
                    cat_var.set(display_category_name(matched))
            
            cat_menu = ctk.CTkOptionMenu(cat_frame, values=cat_names, variable=cat_var)
            cat_menu.pack(fill="x")
            
            def on_alloc_change(val):
                if val == ui_text("Direct to Category", "Przypisz do jednej kategorii"):
                    cat_frame.pack(fill="x", padx=20)
                else:
                    cat_frame.pack_forget()
                    
            alloc_menu.configure(command=on_alloc_change)
            on_alloc_change(alloc_mode_var.get())
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                cat_id = None
                if item_type == "addition" and alloc_mode_var.get() == ui_text("Direct to Category", "Przypisz do jednej kategorii"):
                    matched = next((c for c in self.controller.data.get("categories", []) if display_category_name(c) == cat_var.get()), None)
                    if matched:
                        cat_id = matched["id"]
                        
                item["name"] = name
                item["amount"] = amt
                item["category_id"] = cat_id
                self.controller.save_data()
                dialog.destroy()
                self.refresh()
            except:
                pass
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)

    def delete_item(self, item_id):
        self.controller.data["income_items"] = [i for i in self.controller.data.get("income_items", []) if i["id"] != item_id]
        self.controller.save_data()
        self.refresh()

    def build_items_list(self):
        for w in self.items_scroll.winfo_children():
            w.destroy()
        
        items = self.controller.data.get("income_items", [])
        cats = {c["id"]: c for c in self.controller.data.get("categories", [])}
        additions = sum(1 for item in items if item.get("type") == "addition")
        deductions = len(items) - additions
        self.items_count_lbl.configure(
            text=ui_text(
                f"{len(items)} entries · {additions} additions · {deductions} deductions",
                f"{len(items)} pozycji · {additions} przych. · {deductions} odlicz.",
            )
        )

        header = ctk.CTkFrame(self.items_scroll, fg_color=COLOR_BG)
        header.pack(fill="x")
        cols = [
            (ui_text("Item", "Pozycja"), 4, "w"),
            (ui_text("Type", "Typ"), 2, "center"),
            (ui_text("Amount", "Kwota"), 2, "e"),
            (ui_text("Target", "Cel"), 2, "w"),
            ("", 1, "center"),
        ]
        for idx, (label, weight, anchor) in enumerate(cols):
            header.grid_columnconfigure(idx, weight=weight)
            ctk.CTkLabel(header, text=label.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, anchor=anchor).grid(row=0, column=idx, sticky="ew", padx=(20 if idx == 0 else 10, 20 if idx == len(cols) - 1 else 10), pady=10)

        if not items:
            ctk.CTkLabel(
                self.items_scroll,
                text=ui_text("No income items yet. Add an invoice or deduction to start.", "Brak pozycji przychodów. Dodaj fakturę albo odliczenie."),
                font=FONT_BODY,
                text_color=COLOR_TEXT_MUTED,
            ).pack(anchor="w", padx=20, pady=18)
            return

        for item in items:
            is_add = item["type"] == "addition"
            row = ctk.CTkFrame(self.items_scroll, fg_color="transparent", height=64)
            row.pack(fill="x")
            row.pack_propagate(False)
            for idx, (_, weight, _) in enumerate(cols):
                row.grid_columnconfigure(idx, weight=weight)

            item_box = ctk.CTkFrame(row, fg_color="transparent")
            item_box.grid(row=0, column=0, sticky="ew", padx=(20, 10), pady=9)
            sign = "+" if is_add else "−"
            sign_color = COLOR_SUCCESS if is_add else COLOR_ERROR
            ctk.CTkLabel(item_box, text=display_name(item["name"]), font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
            meta = ui_text("monthly income item", "pozycja miesięczna")
            ctk.CTkLabel(item_box, text=meta, font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(3, 0))

            type_pill = ctk.CTkFrame(row, fg_color=COLOR_INCOME_SOFT if is_add else COLOR_EXPENSE_SOFT, border_width=1, border_color=COLOR_SUCCESS if is_add else COLOR_ERROR, corner_radius=RADIUS_BUTTON)
            type_pill.grid(row=0, column=1, padx=10, pady=17)
            ctk.CTkLabel(type_pill, text=display_type(item["type"]), font=FONT_SMALL, text_color=sign_color, width=86, height=28).pack()

            amount_text = f"{sign} {format_money(item['amount'], suffix=False)}"
            ctk.CTkLabel(row, text=amount_text, font=FONT_MONO, text_color=sign_color, anchor="e").grid(row=0, column=2, sticky="ew", padx=10, pady=18)

            cat_id = item.get("category_id")
            if cat_id and cat_id in cats:
                badge = make_pill(row, display_category_name(cats[cat_id]), category_color(cats[cat_id]), width=128, height=28)
                badge.grid(row=0, column=3, sticky="w", padx=10, pady=18)
            else:
                ctk.CTkLabel(row, text=ui_text("proportional", "proporcjonalnie"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED, anchor="w").grid(row=0, column=3, sticky="w", padx=10, pady=18)

            action_frame = ctk.CTkFrame(row, fg_color="transparent")
            action_frame.grid(row=0, column=4, sticky="e", padx=(8, 20), pady=14)
            if self.editing:
                ctk.CTkButton(action_frame, text="✎", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.edit_item(iid)).pack(side="left")
                ctk.CTkButton(action_frame, text="×", width=30, height=30, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_EXPENSE_SOFT, command=lambda iid=item["id"]: self.delete_item(iid)).pack(side="left")
            else:
                ctk.CTkLabel(action_frame, text="●" if is_add else "○", font=FONT_MONO_SM_BOLD, text_color=sign_color, width=24).pack(side="right")
            ctk.CTkFrame(self.items_scroll, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        
    def build_cat_rows(self):
        for widget in self.cat_rows_frame.winfo_children():
            widget.destroy()
        self.cat_vars = {}
        self.cat_lbls = {}
        self.cat_pct_lbls = {}
        self.cat_bar_widgets = {}
            
        data = self.controller.data
        cats = data.get("categories", [])

        grid = ctk.CTkFrame(self.cat_rows_frame, fg_color="transparent")
        grid.pack(fill="x")
        for idx in range(3):
            grid.grid_columnconfigure(idx, weight=1, uniform="income_split")

        for idx, cat in enumerate(cats):
            row = make_card(grid, fg_color=COLOR_SURFACE_2)
            row.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=(0 if idx % 3 == 0 else 6, 0 if idx % 3 == 2 else 6), pady=6)

            head = ctk.CTkFrame(row, fg_color="transparent")
            head.pack(fill="x", padx=14, pady=(12, 8))
            dot = ctk.CTkFrame(head, width=10, height=10, fg_color=category_color(cat), corner_radius=4)
            dot.pack(side="left", padx=(0, 8))
            dot.pack_propagate(False)
            ctk.CTkLabel(head, text=display_category_name(cat), font=FONT_TITLE, text_color=COLOR_TEXT, anchor="w").pack(side="left", fill="x", expand=True)
            
            var = ctk.StringVar(value=str(cat["percent"]))
            self.cat_vars[cat["id"]] = var
            
            if self.editing:
                entry = ctk.CTkEntry(head, textvariable=var, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, width=58, justify="center")
                entry.pack(side="right")
                entry.bind("<KeyRelease>", self.calculate_split)
                entry.bind("<FocusOut>", lambda e, v=var: self.format_on_blur_pct(e, v))
                ctk.CTkLabel(head, text="%", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=(4, 8))
            else:
                pct_lbl = ctk.CTkLabel(head, text=f"{cat['percent']:.1f}%", font=FONT_MONO, text_color=COLOR_TEXT_MUTED)
                pct_lbl.pack(side="right")
                self.cat_pct_lbls[cat["id"]] = pct_lbl

            lbl = ctk.CTkLabel(row, text="0.00 PLN", font=FONT_MONO_LG, text_color=category_color(cat), anchor="w")
            lbl.pack(anchor="w", padx=14)
            self.cat_lbls[cat["id"]] = lbl
            progress = ctk.CTkProgressBar(row, height=6, progress_color=category_color(cat), fg_color=COLOR_SURFACE)
            progress.pack(fill="x", padx=14, pady=(10, 14))
            progress.set(min(max(cat.get("percent", 0) / 100.0, 0.0), 1.0))
            self.cat_bar_widgets[cat["id"]] = progress

            if self.editing:
                ctk.CTkButton(
                    row,
                    text=tx("Delete"),
                    height=26,
                    fg_color="transparent",
                    text_color=COLOR_ERROR,
                    hover_color=COLOR_EXPENSE_SOFT,
                    command=lambda cid=cat["id"]: self.delete_category(cid),
                ).pack(anchor="w", padx=10, pady=(0, 10))
        
        if self.editing:
            add_btn = ctk.CTkButton(self.cat_rows_frame, text=tx("+ Add Category"), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=self.add_category)
            add_btn.pack(anchor="w", pady=(10, 0))
        self.cat_built = True

    def format_on_blur_pct(self, event, var):
        val = var.get()
        if val:
            try:
                var.set(f"{float(val):.1f}")
                self.calculate_split()
            except:
                pass

    def delete_category(self, cat_id):
        cats = self.controller.data.get("categories", [])
        if len(cats) <= 2:
            return
        self.controller.data["categories"] = [c for c in cats if c["id"] != cat_id]
        self.build_cat_rows()
        self.calculate_split()
        self.controller.save_data()
        
    def add_category(self):
        dialog = ctk.CTkInputDialog(text=tx("Enter new category name:"), title=tx("Add Category"))
        name = dialog.get_input()
        if name:
            new_cat = {"id": dm.generate_id(), "name": name, "percent": 0.0, "color": COLOR_PRIMARY}
            self.controller.data.setdefault("categories", []).append(new_cat)
            self.build_cat_rows()
            self.calculate_split()
            self.controller.save_data()

    def calculate_split(self, event=None):
        try:
            total_pct = 0.0
            parsed_pcts = {}
            for cat_id, v in self.cat_vars.items():
                val_str = v.get().replace(",", ".")
                clean_str = "".join(c for c in val_str if c.isdigit() or c == ".")
                pct = float(clean_str) if clean_str else 0.0
                parsed_pcts[cat_id] = pct
                total_pct += pct
                
            if abs(total_pct - 100.0) > 0.01:
                self.sum_warning.configure(text=t("income.percent_warning").format(percent=f"{total_pct:.1f}"))
            else:
                self.sum_warning.configure(text="")
                
            net = dm.get_net_income(self.controller.data)
            # General net excludes category-targeted additions
            cat_targeted = sum(i["amount"] for i in self.controller.data.get("income_items", []) if i.get("category_id") and i["type"] == "addition")
            general_net = net - cat_targeted
            
            for cat in self.controller.data.get("categories", []):
                if cat["id"] in parsed_pcts:
                    new_pct = parsed_pcts[cat["id"]]
                    cat["percent"] = new_pct
                    amt = general_net * (new_pct / 100.0)
                    # Add category-specific extras
                    amt += sum(i["amount"] for i in self.controller.data.get("income_items", []) if i.get("category_id") == cat["id"] and i["type"] == "addition")
                    if cat["id"] in self.cat_lbls:
                        self.cat_lbls[cat["id"]].configure(text=format_money(amt))
                    if cat["id"] in self.cat_pct_lbls:
                        self.cat_pct_lbls[cat["id"]].configure(text=f"{new_pct:.1f}%")
                    if cat["id"] in self.cat_bar_widgets:
                        self.cat_bar_widgets[cat["id"]].set(min(max(new_pct / 100.0, 0.0), 1.0))
                    
            if abs(total_pct - 100.0) <= 0.01:
                self.controller.save_data()
        except:
            pass

    def refresh(self):
        self.month_lbl.configure(text=month_year_label(self.controller.current_month, upper=True))
        self.hero_kicker.configure(text=f"● {ui_text('NET', 'NETTO')} · {month_year_label(self.controller.current_month, upper=True)}")
        if not self.cat_built:
            self.build_cat_rows()
        self.build_items_list()
        items = self.controller.data.get("income_items", [])
        gross = sum(item["amount"] for item in items if item.get("type") == "addition")
        deductions = sum(item["amount"] for item in items if item.get("type") == "deduction")
        net = dm.get_net_income(self.controller.data)
        self.net_lbl.configure(text=format_money(net, suffix=False))
        self.net_breakdown_lbl.configure(
            text=ui_text(
                f"Gross {format_money(gross, suffix=False)} - deductions {format_money(deductions, suffix=False)}",
                f"Brutto {format_money(gross, suffix=False)} - odliczenia {format_money(deductions, suffix=False)}",
            )
        )
        self.last_edited_lbl.configure(text=ui_text("AUTO-SAVED LOCALLY", "ZAPIS LOKALNY"))
        self.calculate_split()

class ExpensesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller

        # Month filter state
        self.filter_month = None
        self.filter_year = None
        self.active_tag = None
        self.active_source_id = None
        self.group_mode = "date"
        self.selected_expense_id = None
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.expenses"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)
        ctk.CTkButton(self.topbar, text=f"+ {t('common.add_expense')}", width=136, height=34, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, corner_radius=RADIUS_BUTTON, command=self.open_add_expense).pack(side="right", padx=(8, 24))
        ctk.CTkButton(self.topbar, text=t("expenses.manage_categories"), width=154, height=34, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON, command=self.open_category_manager).pack(side="right", padx=8)
        month_box = ctk.CTkFrame(self.topbar, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        month_box.pack(side="right", padx=8)
        ctk.CTkButton(month_box, text="‹", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(-1)).pack(side="left", padx=(4, 0), pady=3)
        self._month_label = ctk.CTkLabel(month_box, text="", font=FONT_MONO, text_color=COLOR_TEXT, width=116)
        self._month_label.pack(side="left")
        ctk.CTkButton(month_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(1)).pack(side="left", padx=(0, 4), pady=3)
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.filter_bar = make_card(self)
        self.filter_bar.pack(fill="x", padx=24, pady=(24, 16))
        self.search_entry = ctk.CTkEntry(self.filter_bar, textvariable=self.search_var, placeholder_text=tx("Search description, tag, or amount..."), width=240, height=38, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER)
        self.search_entry.pack(side="left", padx=(14, 8), pady=14)
        self.tag_bar = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        self.tag_bar.pack(side="left", fill="x", expand=True, padx=4, pady=14)
        segmented = ctk.CTkFrame(self.filter_bar, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON)
        segmented.pack(side="right", padx=(8, 14), pady=14)
        self.by_date_btn = ctk.CTkButton(segmented, text=tx("By date"), height=30, width=86, corner_radius=7, font=FONT_SMALL, command=lambda: self.set_group_mode("date"))
        self.by_date_btn.pack(side="left", padx=(3, 0), pady=3)
        self.by_category_btn = ctk.CTkButton(segmented, text=tx("By category"), height=30, width=112, corner_radius=7, font=FONT_SMALL, command=lambda: self.set_group_mode("category"))
        self.by_category_btn.pack(side="left", padx=(0, 3), pady=3)

        self.content_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.content_grid.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.content_grid.grid_columnconfigure(0, weight=3)
        self.content_grid.grid_columnconfigure(1, weight=2)
        self.content_grid.grid_rowconfigure(0, weight=1)

        self.list_card = make_card(self.content_grid)
        self.list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.summary_frame = ctk.CTkFrame(self.list_card, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkFrame(self.list_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        self.scroll = ctk.CTkScrollableFrame(self.list_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self.detail_card = make_card(self.content_grid)
        self.detail_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    # --- Add Expense Dialog ---
    def open_add_expense(self, edit_exp=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit Expense") if edit_exp else tx("Add Expense"))
        dialog.geometry("480x580")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        data = self.controller.data

        # Date field with calendar toggle
        ctk.CTkLabel(dialog, text=tx("Date (DD/MM/YYYY):"), anchor="w").pack(fill="x", padx=20, pady=(15, 3))
        date_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        date_frame.pack(fill="x", padx=20)
        date_entry = ctk.CTkEntry(date_frame, font=FONT_BODY)
        date_entry.pack(side="left", fill="x", expand=True)
        date_entry.insert(0, edit_exp["date"] if edit_exp else datetime.now().strftime("%d/%m/%Y"))
        date_error_lbl = ctk.CTkLabel(dialog, text="", font=FONT_SMALL, text_color=COLOR_ERROR, anchor="w")
        date_error_lbl.pack(fill="x", padx=20)

        def open_calendar():
            from tkcalendar import Calendar
            cal_win = ctk.CTkToplevel(dialog)
            cal_win.title(tx("Select Date"))
            cal_win.geometry("300x300")
            cal_win.transient(dialog)
            cal_win.grab_set()
            try:
                d = datetime.strptime(date_entry.get().strip(), "%d/%m/%Y")
            except:
                d = datetime.now()
            cal = Calendar(cal_win, selectmode="day", year=d.year, month=d.month, day=d.day, date_pattern="dd/mm/yyyy")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            def pick():
                date_entry.delete(0, "end")
                date_entry.insert(0, cal.get_date())
                date_error_lbl.configure(text="")
                cal_win.destroy()
            ctk.CTkButton(cal_win, text=tx("Select"), command=pick).pack(pady=(0, 10))

        ctk.CTkButton(date_frame, text=tx("Cal"), width=46, height=36, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=open_calendar).pack(side="right", padx=(5, 0))

        ctk.CTkLabel(dialog, text=tx("Amount (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        if edit_exp:
            amt_entry.insert(0, f"{edit_exp['amount']:.2f}")

        # Expense Category with inline creation
        ctk.CTkLabel(dialog, text=tx("Expense Category:"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        exp_cats = dm.get_expense_categories(data)
        create_marker = tx("+ Create new category...")
        exp_cat_options = {display_name(c["name"]): c["id"] for c in exp_cats}
        exp_cat_names = sorted(exp_cat_options.keys(), key=str.casefold) + [create_marker]
        if not exp_cats:
            exp_cat_names = [tx("(none)"), create_marker]
        exp_cat_var = ctk.StringVar(value=exp_cat_names[0])
        if edit_exp:
            cur = next((display_name(c["name"]) for c in exp_cats if c["id"] == edit_exp.get("expense_category_id")), exp_cat_names[0])
            exp_cat_var.set(cur)

        exp_cat_menu = ctk.CTkOptionMenu(dialog, values=exp_cat_names, variable=exp_cat_var, command=lambda val: self._on_exp_cat_select(val, exp_cat_var, exp_cat_menu, dialog, data))
        exp_cat_menu.pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Funding Source:"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        split_cats = data.get("categories", [])
        sp = dm.get_savings_planner()
        sav_cats = sp.get("categories", [])
        source_options = {}
        for c in split_cats:
            source_options[f"{tx('Budget')}: {display_category_name(c)}"] = ("budget", c["id"])
        for c in sav_cats:
            source_options[f"{tx('Goal')}: {display_name(c['name'])}"] = ("goal", c["id"])
        source_names = sorted(source_options.keys(), key=str.casefold)
        if not source_names:
            source_names = [tx("(none)")]
        default_source = source_names[0] if source_names else tx("(none)")
        if edit_exp:
            if edit_exp.get("savings_category_id"):
                default_source = next((f"{tx('Goal')}: {display_name(c['name'])}" for c in sav_cats if c["id"] == edit_exp["savings_category_id"]), default_source)
            else:
                default_source = next((f"{tx('Budget')}: {display_category_name(c)}" for c in split_cats if c["id"] == edit_exp.get("category_id")), default_source)
        elif self.active_source_id:
            found = next((f"{tx('Budget')}: {display_category_name(c)}" for c in split_cats if c["id"] == self.active_source_id), None)
            if found:
                default_source = found

        source_var = ctk.StringVar(value=default_source)
        ctk.CTkOptionMenu(dialog, values=source_names, variable=source_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Description (optional):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        desc_entry = ctk.CTkEntry(dialog)
        desc_entry.pack(fill="x", padx=20)
        if edit_exp:
            desc_entry.insert(0, edit_exp.get("description", ""))

        ctk.CTkLabel(dialog, text=tx("Tags (comma-separated, optional):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        tags_entry = ctk.CTkEntry(dialog)
        tags_entry.pack(fill="x", padx=20)
        if edit_exp:
            tags_entry.insert(0, ", ".join(edit_exp.get("tags", [])))

        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                if amt <= 0:
                    return
            except:
                return
            date_val = date_entry.get().strip()
            try:
                datetime.strptime(date_val, "%d/%m/%Y")
                date_error_lbl.configure(text="")
            except ValueError:
                date_error_lbl.configure(text=tx("Invalid date. Use DD/MM/YYYY format."))
                return
            exp_cats_current = dm.get_expense_categories(data)
            exp_cat_id = next((c["id"] for c in exp_cats_current if display_name(c["name"]) == exp_cat_var.get()), None)
            desc = desc_entry.get().strip()
            tags = [t.strip() for t in tags_entry.get().split(",") if t.strip()]

            # Parse funding source
            split_id = None
            savings_cat_id = None
            source_kind, source_id = source_options.get(source_var.get(), (None, None))
            if source_kind == "budget":
                split_id = source_id
            elif source_kind == "goal":
                savings_cat_id = source_id

            # Check if moving to a different month
            new_date = datetime.strptime(date_val, "%d/%m/%Y")
            new_month_str = f"{new_date.year}-{new_date.month:02d}"

            if new_month_str != self.controller.current_month:
                if edit_exp:
                    dm.delete_expense(data, edit_exp["id"])
                self.controller.save_data()
                
                other_data = dm.load_month(new_month_str)
                exp = dm.add_expense(other_data, date_val, amt, split_id, expense_category_id=exp_cat_id, description=desc, tags=tags)
                exp["savings_category_id"] = savings_cat_id
                if edit_exp:
                    exp["id"] = edit_exp["id"]
                dm.save_month(new_month_str, other_data)
                
                self.controller.current_month = new_month_str
                self.controller.config["last_month"] = new_month_str
                dm.save_config(self.controller.config)
                self.controller.data = other_data
                dialog.destroy()
                self.controller.show_view("Expenses")
                return

            if edit_exp:
                dm.edit_expense(data, edit_exp["id"], date=date_val, amount=amt, expense_category_id=exp_cat_id, category_id=split_id, savings_category_id=savings_cat_id, description=desc, tags=tags)
            else:
                exp = dm.add_expense(data, date_val, amt, split_id, expense_category_id=exp_cat_id, description=desc, tags=tags)
                exp["savings_category_id"] = savings_cat_id
            self.controller.save_data()
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(fill="x", padx=20, pady=15)

    def _on_exp_cat_select(self, val, exp_cat_var, exp_cat_menu, parent_dialog, data):
        create_marker = tx("+ Create new category...")
        if val != create_marker:
            return
        d = ctk.CTkInputDialog(text=tx("New category name:"), title=tx("Create Category"))
        name = d.get_input()
        if name and name.strip():
            dm.add_expense_category(data, name.strip())
            self.controller.save_data()
            exp_cats = dm.get_expense_categories(data)
            new_names = [display_name(c["name"]) for c in exp_cats] + [create_marker]
            exp_cat_menu.configure(values=new_names)
            exp_cat_var.set(display_name(name.strip()))
        else:
            exp_cat_var.set(exp_cat_menu.cget("values")[0] if exp_cat_menu.cget("values") else tx("(none)"))

    # --- Category Manager Dialog ---
    def open_category_manager(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Expense Categories"))
        dialog.geometry("440x500")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        data = self.controller.data

        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def rebuild():
            for w in list_frame.winfo_children():
                w.destroy()
            for cat in dm.get_expense_categories(data):
                row = ctk.CTkFrame(list_frame, fg_color=COLOR_SURFACE_2, corner_radius=8)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=display_name(cat["name"]), font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=8)
                ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda cid=cat["id"]: do_delete(cid)).pack(side="right", padx=5, pady=5)
                ctk.CTkButton(row, text="✎", width=28, height=28, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda cid=cat["id"], cn=cat["name"]: do_edit(cid, cn)).pack(side="right", padx=2, pady=5)

        def do_delete(cid):
            dm.delete_expense_category(data, cid)
            self.controller.save_data()
            rebuild()

        def do_edit(cid, current_name):
            d = ctk.CTkInputDialog(text=tx("New name:"), title=tx("Rename Category"))
            new_name = d.get_input()
            if new_name and new_name.strip():
                dm.edit_expense_category(data, cid, new_name.strip())
                self.controller.save_data()
                rebuild()

        rebuild()

        # Add new category
        add_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=10)
        new_entry = ctk.CTkEntry(add_frame, placeholder_text=tx("New category name"))
        new_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def do_add():
            name = new_entry.get().strip()
            if name:
                dm.add_expense_category(data, name)
                self.controller.save_data()
                new_entry.delete(0, "end")
                rebuild()

        ctk.CTkButton(add_frame, text=tx("Add"), width=70, command=do_add).pack(side="right")

    # --- Accordion toggle ---
    def toggle_category(self, cat_id):
        self.expanded_cats[cat_id] = not self.expanded_cats.get(cat_id, False)
        self.refresh()

    # --- Tag filter ---
    def set_tag_filter(self, tag):
        if self.active_tag == tag:
            self.active_tag = None
        else:
            self.active_tag = tag
        self.refresh()

    def set_source_filter(self, source_id):
        self.active_source_id = source_id
        self.refresh()

    def set_group_mode(self, mode):
        self.group_mode = mode
        self.refresh()

    # --- Delete expense ---
    def delete_expense(self, exp_id):
        dm.delete_expense(self.controller.data, exp_id)
        self.controller.save_data()
        self.refresh()

    # --- Refresh / Build List + Detail ---
    def refresh(self):
        data = self.controller.data
        if "expense_categories" not in data:
            data["expense_categories"] = list(dm.DEFAULT_EXPENSE_CATEGORIES)

        year_str, month_str = self.controller.current_month.split("-")
        self.filter_year = int(year_str)
        self.filter_month = int(month_str)

        self._month_label.configure(text=f"{month_full(self.filter_month).upper()} {self.filter_year}")
        filtered_expenses = self._visible_expenses()

        if self.selected_expense_id not in {e["id"] for e in filtered_expenses}:
            self.selected_expense_id = filtered_expenses[0]["id"] if filtered_expenses else None

        self._build_filters(filtered_expenses)
        self._build_summary(filtered_expenses)
        self._sync_segmented()
        self._build_expense_list(filtered_expenses)
        selected = next((e for e in filtered_expenses if e["id"] == self.selected_expense_id), None)
        self._build_detail(selected)

    def _visible_expenses(self):
        query = self.search_var.get().strip().lower()

        def in_month(exp):
            try:
                d = datetime.strptime(exp["date"], "%d/%m/%Y")
                return d.month == self.filter_month and d.year == self.filter_year
            except Exception:
                return False

        expenses = [e for e in self.controller.data.get("expenses", []) if in_month(e)]
        if self.active_tag:
            expenses = [e for e in expenses if self.active_tag in e.get("tags", [])]
        if self.active_source_id:
            expenses = [e for e in expenses if e.get("category_id") == self.active_source_id]
        if query:
            expenses = [
                e for e in expenses
                if query in e.get("description", "").lower()
                or query in f"{e.get('amount', 0):.2f}"
                or any(query in tag.lower() for tag in e.get("tags", []))
                or query in self._expense_category_name(e).lower()
                or query in self._source_name(e).lower()
            ]
        return sorted(expenses, key=lambda e: self._date_key(e), reverse=True)

    def _date_key(self, exp):
        try:
            return datetime.strptime(exp.get("date", ""), "%d/%m/%Y")
        except Exception:
            return datetime.min

    def _build_filters(self, expenses):
        for w in self.tag_bar.winfo_children():
            w.destroy()
        month_expenses = [
            e for e in self.controller.data.get("expenses", [])
            if self._date_key(e).month == self.filter_month and self._date_key(e).year == self.filter_year
        ]
        self._filter_button(tx("All"), len(month_expenses), self.active_source_id is None, lambda: self.set_source_filter(None))
        for cat in self.controller.data.get("categories", []):
            count = sum(1 for exp in month_expenses if exp.get("category_id") == cat["id"])
            self._filter_button(display_category_name(cat), count, self.active_source_id == cat["id"], lambda cid=cat["id"]: self.set_source_filter(cid), category_color(cat))

    def _filter_button(self, label, count, active, command, color=None):
        text = f"{label} · {count}"
        ctk.CTkButton(
            self.tag_bar, text=text, height=32, width=max(72, len(text) * 8),
            fg_color=COLOR_PRIMARY_SOFT if active else COLOR_SURFACE_2,
            text_color=(color or COLOR_PRIMARY) if active else COLOR_TEXT,
            hover_color=COLOR_PRIMARY_SOFT if active else COLOR_BORDER,
            border_width=1, border_color=(color or COLOR_PRIMARY) if active else COLOR_BORDER,
            corner_radius=RADIUS_BUTTON, font=FONT_SMALL, command=command
        ).pack(side="left", padx=4)

    def _build_summary(self, expenses):
        for w in self.summary_frame.winfo_children():
            w.destroy()
        total = sum(e["amount"] for e in expenses)
        allocated = dm.get_net_income(self.controller.data)
        remaining = allocated - total
        stats = [
            (t("expenses.spent_month"), total, COLOR_EXPENSE),
            (tx("Allocated").upper(), allocated, COLOR_TEXT),
            (tx("Remaining").upper(), remaining, COLOR_SUCCESS if remaining >= 0 else COLOR_ERROR),
        ]
        for label, amount, color in stats:
            cell = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
            cell.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(cell, text=label, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(cell, text=format_money(amount, suffix=False), font=FONT_MONO_LG, text_color=color).pack(anchor="w", pady=(2, 0))

    def _build_expense_list(self, expenses):
        for w in self.scroll.winfo_children():
            w.destroy()
        if not expenses:
            ctk.CTkLabel(self.scroll, text=tx("No expenses for this month."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=42)
            return

        if self.group_mode == "category":
            self._build_expense_list_by_category(expenses)
            return

        current_day = None
        for exp in expenses:
            day = exp.get("date", "")
            if day != current_day:
                current_day = day
                total = sum(e["amount"] for e in expenses if e.get("date", "") == day)
                hdr = ctk.CTkFrame(self.scroll, fg_color=COLOR_BG, corner_radius=0)
                hdr.pack(fill="x", padx=0, pady=(10, 0))
                d = self._date_key(exp)
                label_day = f"{weekday_abbr(d.weekday())} · {d.day:02d} {month_full(d.month)}"
                day_count = sum(1 for e in expenses if e.get("date", "") == day)
                ctk.CTkLabel(hdr, text=label_day.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=20, pady=8)
                ctk.CTkLabel(hdr, text=f"{item_count(day_count)} · - {format_money(total)}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=20)

            selected = exp["id"] == self.selected_expense_id
            row = ctk.CTkFrame(
                self.scroll,
                fg_color=COLOR_PRIMARY_SOFT if selected else COLOR_SURFACE,
                corner_radius=0,
                border_width=0,
            )
            row.pack(fill="x")
            row.bind("<Button-1>", lambda _e, exp_id=exp["id"]: self._select_expense(exp_id))
            accent = ctk.CTkFrame(row, fg_color=COLOR_PRIMARY if selected else COLOR_BORDER, width=3)
            accent.pack(side="left", fill="y")
            source_cat = self._source_category(exp)
            icon = self._source_icon(source_cat)
            icon_box = ctk.CTkFrame(row, width=28, height=28, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=8)
            icon_box.pack(side="left", padx=(17, 0), pady=12)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text=icon, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(expand=True)
            body = ctk.CTkFrame(row, fg_color="transparent")
            body.pack(side="left", fill="x", expand=True, padx=14, pady=12)
            title = exp.get("description") or self._expense_category_name(exp)
            ctk.CTkLabel(body, text=title, font=FONT_TITLE, text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
            meta = f"{self._expense_category_name(exp)} · {self._source_name(exp)}"
            ctk.CTkLabel(body, text=meta, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
            if exp.get("tags"):
                tag_row = ctk.CTkFrame(body, fg_color="transparent")
                tag_row.pack(anchor="w", pady=(4, 0))
                for tag in exp.get("tags", [])[:3]:
                    ctk.CTkLabel(tag_row, text=tag, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, fg_color=COLOR_SURFACE_2, corner_radius=6).pack(side="left", padx=(0, 4), ipadx=6, ipady=2)
            amount_col = ctk.CTkFrame(row, fg_color="transparent")
            amount_col.pack(side="right", padx=(12, 20))
            ctk.CTkLabel(amount_col, text=f"- {format_money(exp['amount'], suffix=False)}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(anchor="e")
            if source_cat:
                pill = make_pill(row, display_category_name(source_cat), category_color(source_cat), width=120, height=26)
                pill.pack(side="right")
            for child in row.winfo_children() + body.winfo_children() + amount_col.winfo_children():
                child.bind("<Button-1>", lambda _e, exp_id=exp["id"]: self._select_expense(exp_id))

    def _build_expense_list_by_category(self, expenses):
        source_order = self.controller.data.get("categories", [])
        savings_bucket = {"id": "savings", "name": tx("Savings goals"), "color": COLOR_SUCCESS}
        buckets = []
        for cat in source_order:
            cat_expenses = [e for e in expenses if e.get("category_id") == cat["id"] and not e.get("savings_category_id")]
            if cat_expenses:
                buckets.append((cat, cat_expenses))
        savings_expenses = [e for e in expenses if e.get("savings_category_id")]
        if savings_expenses:
            buckets.append((savings_bucket, savings_expenses))

        for cat, cat_expenses in buckets:
            total = sum(e["amount"] for e in cat_expenses)
            hdr = ctk.CTkFrame(self.scroll, fg_color=COLOR_BG, corner_radius=0)
            hdr.pack(fill="x", padx=0, pady=(10, 0))
            ctk.CTkLabel(hdr, text=display_category_name(cat).upper(), font=FONT_LABEL, text_color=category_color(cat)).pack(side="left", padx=20, pady=8)
            ctk.CTkLabel(hdr, text=f"{item_count(len(cat_expenses))} · - {format_money(total)}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=20)
            for exp in sorted(cat_expenses, key=lambda e: self._date_key(e), reverse=True):
                self._expense_row(exp)

    def _expense_row(self, exp):
        selected = exp["id"] == self.selected_expense_id
        row = ctk.CTkFrame(
            self.scroll,
            fg_color=COLOR_PRIMARY_SOFT if selected else COLOR_SURFACE,
            corner_radius=0,
            border_width=0,
        )
        row.pack(fill="x")
        row.bind("<Button-1>", lambda _e, exp_id=exp["id"]: self._select_expense(exp_id))
        accent = ctk.CTkFrame(row, fg_color=COLOR_PRIMARY if selected else COLOR_BORDER, width=3)
        accent.pack(side="left", fill="y")
        source_cat = self._source_category(exp)
        icon = self._source_icon(source_cat)
        icon_box = ctk.CTkFrame(row, width=28, height=28, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=8)
        icon_box.pack(side="left", padx=(17, 0), pady=12)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(expand=True)
        body = ctk.CTkFrame(row, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        title = exp.get("description") or self._expense_category_name(exp)
        ctk.CTkLabel(body, text=title, font=FONT_TITLE, text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
        meta = f"{self._expense_category_name(exp)} · {self._source_name(exp)}"
        ctk.CTkLabel(body, text=meta, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
        if exp.get("tags"):
            tag_row = ctk.CTkFrame(body, fg_color="transparent")
            tag_row.pack(anchor="w", pady=(4, 0))
            for tag in exp.get("tags", [])[:3]:
                ctk.CTkLabel(tag_row, text=tag, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, fg_color=COLOR_SURFACE_2, corner_radius=6).pack(side="left", padx=(0, 4), ipadx=6, ipady=2)
        amount_col = ctk.CTkFrame(row, fg_color="transparent")
        amount_col.pack(side="right", padx=(12, 20))
        ctk.CTkLabel(amount_col, text=f"- {format_money(exp['amount'], suffix=False)}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(anchor="e")
        if source_cat:
            pill = make_pill(row, display_category_name(source_cat), category_color(source_cat), width=120, height=26)
            pill.pack(side="right")
        for child in row.winfo_children() + body.winfo_children() + amount_col.winfo_children():
            child.bind("<Button-1>", lambda _e, exp_id=exp["id"]: self._select_expense(exp_id))

    def _sync_segmented(self):
        self.by_date_btn.configure(
            fg_color=COLOR_SURFACE if self.group_mode == "date" else "transparent",
            text_color=COLOR_TEXT if self.group_mode == "date" else COLOR_TEXT_MUTED,
            hover_color=COLOR_SURFACE,
        )
        self.by_category_btn.configure(
            fg_color=COLOR_SURFACE if self.group_mode == "category" else "transparent",
            text_color=COLOR_TEXT if self.group_mode == "category" else COLOR_TEXT_MUTED,
            hover_color=COLOR_SURFACE,
        )

    def _build_detail(self, exp):
        for w in self.detail_card.winfo_children():
            w.destroy()
        if not exp:
            ctk.CTkLabel(self.detail_card, text=tx("Expense detail"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", padx=24, pady=(24, 6))
            ctk.CTkLabel(self.detail_card, text=tx("Select an expense to inspect it."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=24)
            return

        source_cat = self._source_category(exp)
        source_color = category_color(source_cat) if source_cat else COLOR_PRIMARY
        head = ctk.CTkFrame(self.detail_card, fg_color=COLOR_PRIMARY_SOFT, corner_radius=0)
        head.pack(fill="x")
        top = ctk.CTkFrame(head, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(top, text=f"●  {tx('EXPENSE DETAIL')}", font=FONT_LABEL, text_color=COLOR_PRIMARY).pack(side="left")
        
        ctk.CTkButton(top, text=f"✎ {tx('Edit')}", width=60, height=24, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, font=FONT_SMALL, corner_radius=4, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=(10, 0))
        
        d = self._date_key(exp)
        ctk.CTkLabel(top, text=f"{tx('Edited')} · {d.day:02d} {month_abbr(d.month)}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkLabel(head, text=exp.get("description") or self._expense_category_name(exp), font=FONT_DETAIL_TITLE, text_color=COLOR_TEXT).pack(anchor="w", padx=24, pady=(8, 0))
        amount_row = ctk.CTkFrame(head, fg_color="transparent")
        amount_row.pack(anchor="w", padx=24, pady=(6, 8))
        ctk.CTkLabel(amount_row, text=f"- {format_money(exp['amount'], suffix=False)}", font=FONT_DETAIL_AMOUNT, text_color=COLOR_EXPENSE).pack(side="left")
        ctk.CTkLabel(amount_row, text="PLN", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(6, 0), pady=(20, 0))
        meta_row = ctk.CTkFrame(head, fg_color="transparent")
        meta_row.pack(fill="x", padx=24, pady=(0, 16))
        if source_cat:
            pill = make_pill(meta_row, display_category_name(source_cat), source_color, height=26)
            pill.pack(side="left")
        ctk.CTkLabel(meta_row, text=f"{self._expense_category_name(exp)} {tx('subcategory')}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10)

        foot = ctk.CTkFrame(self.detail_card, fg_color=COLOR_SURFACE_2, corner_radius=0)
        foot.pack(side="bottom", fill="x")
        ctk.CTkButton(foot, text=tx("Delete"), fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_EXPENSE_SOFT, command=lambda eid=exp["id"]: self.delete_expense(eid)).pack(side="left", padx=24, pady=16)
        ctk.CTkButton(foot, text=tx("Edit"), height=32, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=(6, 24), pady=16)
        ctk.CTkButton(foot, text=tx("Cancel"), height=32, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, border_width=1, border_color=COLOR_BORDER, command=self.refresh).pack(side="right", padx=6, pady=16)

        body = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)
        self._detail_field(body, tx("Date"), exp.get("date", ""), mono=True)
        self._detail_field(body, tx("Amount"), format_money(exp["amount"], suffix=False), mono=True)
        self._detail_field(body, tx("Description"), exp.get("description") or "")
        self._detail_field(body, tx("Subcategory"), self._expense_category_name(exp))
        self._detail_field(body, tx("Funding"), self._source_name(exp))
        if exp.get("tags"):
            self._detail_field(body, tx("Tags"), ", ".join(exp["tags"]))
        self._budget_breakdown(body, exp, source_cat)

    def _detail_field(self, parent, label, value, mono=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(row, text=label.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=128, anchor="w").pack(side="left")
        ctk.CTkLabel(
            row,
            text=value or "—",
            font=FONT_MONO if mono else FONT_BODY,
            text_color=COLOR_TEXT,
            fg_color="transparent",
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(12, 0))
        ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    def _budget_breakdown(self, parent, exp, source_cat):
        if not source_cat:
            return
        allocated = dm.get_allocated_amount(self.controller.data, source_cat["id"])
        spent = dm.get_spent_amount(self.controller.data, source_cat["id"])
        remaining = allocated - spent
        box = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        box.pack(fill="x", pady=(12, 0))
        impact = tx("IMPACT ON {name} BUDGET").format(name=display_category_name(source_cat).upper())
        ctk.CTkLabel(box, text=impact, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 8))
        for label, amount, color in [
            (tx("Allocated"), allocated, COLOR_TEXT),
            (tx("Spent so far"), -spent, COLOR_EXPENSE),
            (tx("Remaining"), remaining, COLOR_WARNING if remaining >= 0 else COLOR_ERROR),
        ]:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=label, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
            text = signed_money(amount) if label != tx("Allocated") else format_money(amount)
            ctk.CTkLabel(row, text=text, font=FONT_MONO, text_color=color).pack(side="right")
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()

    def _select_expense(self, exp_id):
        self.selected_expense_id = exp_id
        self.refresh()

    def _expense_category_name(self, exp):
        exp_cats = {c["id"]: c["name"] for c in dm.get_expense_categories(self.controller.data)}
        return display_name(exp_cats.get(exp.get("expense_category_id"), "Uncategorized"))

    def _source_name(self, exp):
        if exp.get("savings_category_id"):
            sp = dm.get_savings_planner()
            return next((display_name(c["name"]) for c in sp.get("categories", []) if c["id"] == exp["savings_category_id"]), tx("Savings"))
        split_cats = {c["id"]: c["name"] for c in self.controller.data.get("categories", [])}
        return display_name(split_cats.get(exp.get("category_id"), "Unknown"))

    def _source_category(self, exp):
        if exp.get("savings_category_id"):
            return None
        return next((c for c in self.controller.data.get("categories", []) if c["id"] == exp.get("category_id")), None)

    def _source_icon(self, cat):
        if not cat:
            return "✦"
        return {
            "daily_life": "DL",
            "shared": "SH",
            "saved": "SV",
            "pleasure": "PL",
            "business": "BU",
        }.get(cat.get("id"), "✦")


class SavingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.sp = dm.get_savings_planner()
        self.editing = False
        self.cell_vars = {}
        self.assumed_vars = {}
        self.actual_collapsed = set()
        self.planning_collapsed = set()
        self._user_toggled = set()
        self._planning_deferred = {}
        self._actual_deferred = {}

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.savings"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)
        actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        actions.pack(side="right", padx=24)
        year_box = ctk.CTkFrame(actions, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        year_box.pack(side="left", padx=(0, 10))
        ctk.CTkButton(year_box, text="‹", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(-12)).pack(side="left", padx=(4, 0), pady=3)
        self.year_lbl = ctk.CTkLabel(year_box, text="", font=FONT_MONO, text_color=COLOR_PRIMARY, width=76, fg_color=COLOR_SURFACE_2, corner_radius=7)
        self.year_lbl.pack(side="left", pady=4)
        ctk.CTkButton(year_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(12)).pack(side="left", padx=(0, 4), pady=3)
        self.edit_btn = ctk.CTkButton(actions, text=tx("✎ Edit"), width=86, height=34, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=self.toggle_edit)
        self.edit_btn.pack(side="left", padx=(0, 8))
        self.add_grp_btn = ctk.CTkButton(actions, text=tx("+ Group"), width=92, height=34, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, command=self.add_group_dialog)
        self.add_cat_btn = ctk.CTkButton(actions, text=ui_text("+ Goal", "+ Cel"), width=92, height=34, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_category_dialog)
        self.add_grp_btn.pack(side="left", padx=(0, 8))
        self.add_cat_btn.pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        # Dual-scroll container (vertical + horizontal)
        self._scroll_container = ctk.CTkFrame(self, fg_color="transparent")
        self._scroll_container.pack(fill="both", expand=True, padx=24, pady=24)
        self._scroll_container.grid_rowconfigure(0, weight=1)
        self._scroll_container.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(self._scroll_container, highlightthickness=0, bg=COLOR_BG)
        self._v_scroll = ctk.CTkScrollbar(self._scroll_container, command=self._canvas.yview)
        self._h_scroll = ctk.CTkScrollbar(self._scroll_container, orientation="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=self._v_scroll.set, xscrollcommand=self._h_scroll.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._v_scroll.grid(row=0, column=1, sticky="ns")
        self._h_scroll.grid(row=1, column=0, sticky="ew")

        self.scroll = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._canvas_window = self._canvas.create_window((0, 0), window=self.scroll, anchor="nw")

        def _update_scroll_width():
            req = self.scroll.winfo_reqwidth()
            canvas_w = self._canvas.winfo_width()
            if req <= canvas_w:
                self._canvas.itemconfig(self._canvas_window, width=canvas_w)
            else:
                self._canvas.itemconfig(self._canvas_window, width=0)

        def _on_configure(e):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            _update_scroll_width()
        self.scroll.bind("<Configure>", _on_configure)

        def _on_canvas_configure(e):
            _update_scroll_width()
        self._canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self._canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def toggle_edit(self):
        if self.editing:
            self.save_all()
            self.editing = False
            self.edit_btn.configure(text=tx("✎ Edit"), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT)
        else:
            self.editing = True
            self.edit_btn.configure(text=tx("✓ Done"), fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
        self._rebuild_ui()

    def open_category_editor(self, cat=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit Category") if cat else tx("Add Savings Category"))
        dialog.geometry("440x520")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(15, 3))
        name_e = ctk.CTkEntry(dialog)
        name_e.pack(fill="x", padx=20)
        if cat:
            name_e.insert(0, cat["name"])

        ctk.CTkLabel(dialog, text=tx("Target Amount (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        target_e = ctk.CTkEntry(dialog)
        target_e.pack(fill="x", padx=20)
        if cat:
            target_e.insert(0, f"{cat['target']:.2f}")

        ctk.CTkLabel(dialog, text=tx("Deadline Month:"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        deadline_values = [month_full(m) for m in range(1, 13)]
        deadline_var = ctk.StringVar(value=deadline_values[(cat["deadline_month"] - 1) if cat else 11])
        ctk.CTkOptionMenu(dialog, values=deadline_values, variable=deadline_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Group (optional):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        groups = self.sp.get("groups", [])
        none_label = tx("None")
        group_names = [none_label] + [g["name"] for g in groups]
        group_var = ctk.StringVar(value=none_label)
        if cat and cat.get("group_id"):
            cur_g = next((g["name"] for g in groups if g["id"] == cat["group_id"]), none_label)
            group_var.set(cur_g)
        ctk.CTkOptionMenu(dialog, values=group_names, variable=group_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Next Year Target (optional):"), anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        nyt_e = ctk.CTkEntry(dialog)
        nyt_e.pack(fill="x", padx=20)
        if cat and cat.get("next_year_target"):
            nyt_e.insert(0, f"{cat['next_year_target']:.2f}")

        def save():
            name = name_e.get().strip()
            try:
                target = float(target_e.get().replace(",", "."))
                deadline = deadline_values.index(deadline_var.get()) + 1
            except:
                return
            if not name or target <= 0:
                return
            gid = next((g["id"] for g in groups if g["name"] == group_var.get()), None)
            nyt = None
            if nyt_e.get().strip():
                try:
                    nyt = float(nyt_e.get().replace(",", "."))
                except:
                    pass
            if cat:
                dm.edit_savings_category(self.sp, cat["id"], name=name, target=target, deadline_month=deadline, group_id=gid, next_year_target=nyt)
                # Redistribute if deadline changed and next_year_target set
                if nyt and deadline < 12:
                    grid_row = self.sp.get("grid", {}).get(cat["id"], {})
                    monthly_nyt = round(nyt / (12 - deadline), 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            else:
                dm.add_savings_category(self.sp, name, target, deadline, gid, nyt)
                # If next_year_target, fill months after deadline
                if nyt and deadline < 12:
                    new_cat = self.sp["categories"][-1]
                    grid_row = self.sp["grid"][new_cat["id"]]
                    monthly_nyt = round(nyt / (12 - deadline), 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            dm.save_savings_planner(self.sp)
            dialog.destroy()
            self._rebuild_ui()

        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(fill="x", padx=20, pady=15)

    def add_category_dialog(self):
        self.open_category_editor(cat=None)

    def add_group_dialog(self):
        d = ctk.CTkInputDialog(text=tx("Group name:"), title=tx("Add Group"))
        name = d.get_input()
        if name and name.strip():
            dm.add_savings_group(self.sp, name.strip())
            dm.save_savings_planner(self.sp)
            self._rebuild_ui()

    def delete_category(self, cat_id):
        dm.delete_savings_category(self.sp, cat_id)
        dm.save_savings_planner(self.sp)
        self._rebuild_ui()

    def on_cell_change(self, cat_id, month_key, var):
        try:
            val = float(var.get().replace(",", ".")) if var.get() else 0.0
            self.sp.setdefault("grid", {}).setdefault(cat_id, {})[month_key] = val
        except:
            pass
        self.update_summaries()

    def on_assumed_change(self, month_key, var):
        try:
            val = float(var.get().replace(",", ".")) if var.get() else 0.0
            self.sp.setdefault("assumed", {})[month_key] = val
        except:
            pass
        self.update_summaries()

    def save_all(self):
        for key, var in self.cell_vars.items():
            try:
                val = float(var.get().replace(",", ".") or "0")
                if key[0] == "actual":
                    _, cat_id, mk = key
                    self.sp.setdefault("actual_grid", {}).setdefault(cat_id, {})[mk] = val
                elif key[0] == "avail":
                    _, mk = key
                    self.sp.setdefault("actual_available", {})[mk] = val
                else:
                    cat_id, mk = key
                    self.sp.setdefault("grid", {}).setdefault(cat_id, {})[mk] = val
            except:
                pass
        for mk, var in self.assumed_vars.items():
            try:
                self.sp.setdefault("assumed", {})[mk] = float(var.get().replace(",", ".") or "0")
            except:
                pass
        dm.save_savings_planner(self.sp)

    def update_summaries(self):
        for m in range(1, 13):
            mk = f"{m:02d}"
            allocated = dm.get_month_total_allocated(self.sp, mk)
            assumed = self.sp.get("assumed", {}).get(mk, 0.0)
            remaining = assumed - allocated
            if hasattr(self, 'alloc_lbls') and mk in self.alloc_lbls:
                self.alloc_lbls[mk].configure(text=f"{allocated:,.0f}")
            if hasattr(self, 'remain_lbls') and mk in self.remain_lbls:
                color = COLOR_SUCCESS if remaining >= 0 else COLOR_ERROR
                self.remain_lbls[mk].configure(text=f"{remaining:,.0f}", text_color=color)
        if hasattr(self, 'group_lbls'):
            _grouped = {}
            for c in self.sp["categories"]:
                gid = c.get("group_id")
                if gid:
                    _grouped.setdefault(gid, []).append(c)
            for (gid, mk), lbl in self.group_lbls.items():
                children = _grouped.get(gid, [])
                total = sum(self.sp.get("grid", {}).get(c["id"], {}).get(mk, 0.0) for c in children)
                lbl.configure(text=f"{total:,.0f}")
        if hasattr(self, 'cat_total_lbls'):
            for cat_id, lbl in self.cat_total_lbls.items():
                cat = next((c for c in self.sp["categories"] if c["id"] == cat_id), None)
                deadline = cat.get("deadline_month", 12) if cat else 12
                row_total = sum(self.sp.get("grid", {}).get(cat_id, {}).get(f"{m:02d}", 0.0) for m in range(1, deadline + 1))
                target = cat["target"] if cat else 0
                lbl.configure(text=f"{row_total:,.0f} / {target:,.0f}")

    def _render_planning_cat_row(self, table, cat, r, grid, all_cascades, current_m):
        COL_W = 60
        NAME_W = 150
        name_frame = ctk.CTkFrame(table, fg_color="transparent")
        name_frame.grid(row=r, column=0, padx=2, pady=1, sticky="w")
        ctk.CTkLabel(name_frame, text=display_name(cat["name"]), font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W-50, anchor="w").pack(side="left")
        if self.editing:
            ctk.CTkButton(name_frame, text="✎", width=20, height=20, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda c=cat: self.open_category_editor(c)).pack(side="right", padx=1)
            ctk.CTkButton(name_frame, text="×", width=20, height=20, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda cid=cat["id"]: self.delete_category(cid)).pack(side="right")

        cat_grid = grid.get(cat["id"], {})
        deadline = cat.get("deadline_month", 12)
        cascade = all_cascades.get(cat["id"], {})
        for m in range(12):
            mk = f"{m+1:02d}"
            val = cat_grid.get(mk, 0.0)
            is_deadline = (m + 1 == deadline)
            cell_bg = COLOR_ACCENT if is_deadline else COLOR_SURFACE_2
            if self.editing:
                var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                self.cell_vars[(cat["id"], mk)] = var
                e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=cell_bg, border_color=COLOR_PRIMARY if is_deadline else COLOR_BORDER, justify="center")
                e.grid(row=r, column=m+1, padx=1, pady=1)
                e.bind("<FocusOut>", lambda ev, cid=cat["id"], mk_=mk, v=var: self.on_cell_change(cid, mk_, v))
                e.bind("<Return>", lambda ev, cid=cat["id"], mk_=mk, v=var: self.on_cell_change(cid, mk_, v))
            else:
                if mk in cascade:
                    adjusted = cascade[mk]
                    cell_frame = ctk.CTkFrame(table, fg_color=COLOR_WARNING_SOFT, corner_radius=4, width=COL_W, height=26)
                    cell_frame.grid(row=r, column=m+1, padx=1, pady=1)
                    cell_frame.grid_propagate(False)
                    cell_frame.grid_columnconfigure(0, weight=1)
                    cell_frame.grid_rowconfigure((0, 1), weight=1)
                    ctk.CTkLabel(cell_frame, text=f"{val:,.0f}", font=FONT_MONO_SM, text_color=COLOR_TEXT_MUTED, height=12).grid(row=0, column=0)
                    ctk.CTkLabel(cell_frame, text=f"{adjusted:,.0f}", font=FONT_MONO_SM_BOLD, text_color=COLOR_WARNING, height=12).grid(row=1, column=0)
                else:
                    txt = f"{val:,.0f}" if val else "–"
                    is_current = (m + 1 == current_m)
                    if is_deadline:
                        bg = COLOR_ACCENT
                    elif is_current:
                        bg = COLOR_CURRENT_MONTH
                    else:
                        bg = "transparent"
                    ctk.CTkLabel(table, text=txt, font=FONT_SMALL, text_color=COLOR_TEXT, width=COL_W, anchor="center", fg_color=bg, corner_radius=4).grid(row=r, column=m+1, padx=1, pady=1)

        row_total = sum(cat_grid.get(f"{m+1:02d}", 0.0) for m in range(deadline))
        lbl = ctk.CTkLabel(table, text=f"{row_total:,.0f} / {cat['target']:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=100, anchor="center")
        lbl.grid(row=r, column=13, padx=2, pady=1)
        self.cat_total_lbls[cat["id"]] = lbl

    def build_grid(self):
        sp = self.sp
        categories = sp.get("categories", [])
        groups = sp.get("groups", [])
        grid = sp.get("grid", {})
        assumed = sp.get("assumed", {})

        # Pre-compute all cascade adjustments once
        all_cascades = {cat["id"]: dm.get_cascade_adjustments(sp, cat["id"], self._spent_cache) for cat in categories}

        card = make_card(self.scroll)
        card.pack(anchor="nw", fill="x", pady=(0, 22))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(head, text=tx("Planning Grid"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(head, text=ui_text("what's intended each month", "plan na każdy miesiąc"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        table = ctk.CTkFrame(card, fg_color="transparent")
        table.pack(anchor="nw", padx=14, pady=14)

        COL_W = 60
        NAME_W = 150

        # Header row
        ctk.CTkLabel(table, text=tx("Category"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        current_m = datetime.now().month
        for m in range(12):
            is_current = (m + 1 == current_m)
            hdr_bg = COLOR_CURRENT_MONTH if is_current else "transparent"
            hdr_color = COLOR_PRIMARY if is_current else COLOR_TEXT_MUTED
            ctk.CTkLabel(table, text=month_abbr(m + 1), font=FONT_LABEL, text_color=hdr_color, width=COL_W, anchor="center", fg_color=hdr_bg, corner_radius=4).grid(row=0, column=m+1, padx=1, pady=2)
        ctk.CTkLabel(table, text=tx("Progress"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=100, anchor="center").grid(row=0, column=13, padx=2, pady=2)

        row_idx = 1

        grouped_cats = {}
        ungrouped = []
        for cat in categories:
            gid = cat.get("group_id")
            if gid:
                grouped_cats.setdefault(gid, []).append(cat)
            else:
                ungrouped.append(cat)
        ungrouped.sort(key=lambda c: c["name"].casefold())
        for gid in grouped_cats:
            grouped_cats[gid].sort(key=lambda c: c["name"].casefold())

        def render_cat_row(cat, r):
            self._render_planning_cat_row(table, cat, r, grid, all_cascades, current_m)

        def render_group_row(group, r):
            collapsed = group["id"] in self.planning_collapsed
            chevron = "▶" if collapsed else "▼"
            lbl = ctk.CTkLabel(table, text=f"{chevron} {group['name']}", font=FONT_LABEL, text_color=COLOR_PRIMARY, width=NAME_W, anchor="w", cursor="hand2")
            lbl.grid(row=r, column=0, padx=2, pady=(6, 1), sticky="w")
            lbl.bind("<Button-1>", lambda e, gid=group["id"]: self.toggle_planning_group(gid))
            self.planning_group_labels[group["id"]] = lbl
            children = grouped_cats.get(group["id"], [])
            # Use pre-computed cascade adjustments for each child
            child_cascades = {c["id"]: all_cascades.get(c["id"], {}) for c in children}
            for m in range(12):
                mk = f"{m+1:02d}"
                total = 0.0
                for c in children:
                    raw = grid.get(c["id"], {}).get(mk, 0.0)
                    total += child_cascades[c["id"]].get(mk, raw)
                lbl = ctk.CTkLabel(table, text=f"{total:,.0f}", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=COL_W, anchor="center")
                lbl.grid(row=r, column=m+1, padx=1, pady=(6, 1))
                self.group_lbls[(group["id"], mk)] = lbl

        for cat in ungrouped:
            render_cat_row(cat, row_idx)
            row_idx += 1

        for group in sorted(groups, key=lambda g: g["name"].casefold()):
            render_group_row(group, row_idx)
            row_idx += 1
            cats_in_group = grouped_cats.get(group["id"], [])
            if group["id"] in self.planning_collapsed:
                # Defer: reserve rows but don't create widgets
                start_row = row_idx
                row_idx += len(cats_in_group)
                self.planning_group_children[group["id"]] = []
                self._planning_deferred[group["id"]] = (table, cats_in_group, start_row, all_cascades)
            else:
                child_widgets = []
                for cat in cats_in_group:
                    render_cat_row(cat, row_idx)
                    row_widgets = [w for w in table.grid_slaves(row=row_idx)]
                    child_widgets.extend(row_widgets)
                    row_idx += 1
                self.planning_group_children[group["id"]] = child_widgets

        row_idx += 1

        # Assumed Available
        ctk.CTkLabel(table, text=tx("Assumed Available"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(10, 1), sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            val = assumed.get(mk, 0.0)
            if self.editing:
                var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                self.assumed_vars[mk] = var
                e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=COLOR_SURFACE, border_color=COLOR_PRIMARY, justify="center")
                e.grid(row=row_idx, column=m+1, padx=1, pady=(10, 1))
                e.bind("<FocusOut>", lambda ev, mk_=mk, v=var: self.on_assumed_change(mk_, v))
                e.bind("<Return>", lambda ev, mk_=mk, v=var: self.on_assumed_change(mk_, v))
            else:
                txt = f"{val:,.0f}" if val else "–"
                ctk.CTkLabel(table, text=txt, font=FONT_SMALL, text_color=COLOR_TEXT, width=COL_W, anchor="center").grid(row=row_idx, column=m+1, padx=1, pady=(10, 1))
        row_idx += 1

        # Total Allocated (always read-only)
        ctk.CTkLabel(table, text=tx("Total Allocated"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            allocated = dm.get_month_total_allocated(sp, mk)
            lbl = ctk.CTkLabel(table, text=f"{allocated:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.alloc_lbls[mk] = lbl
        row_idx += 1

        # Remaining (always read-only)
        ctk.CTkLabel(table, text=tx("Remaining"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            remaining = dm.get_month_remaining(sp, mk)
            color = COLOR_SUCCESS if remaining >= 0 else COLOR_ERROR
            lbl = ctk.CTkLabel(table, text=f"{remaining:,.0f}", font=FONT_SMALL, text_color=color, width=COL_W, anchor="center")
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.remain_lbls[mk] = lbl

    def toggle_actual_group(self, group_id):
        self._user_toggled.add(group_id)
        self.actual_collapsed.discard(group_id) if group_id in self.actual_collapsed else self.actual_collapsed.add(group_id)
        collapsed = group_id in self.actual_collapsed
        # Build deferred widgets on first expand
        if not collapsed and group_id in self._actual_deferred:
            table, children, start_row = self._actual_deferred.pop(group_id)
            sp = self.sp
            data = self.controller.data
            actual_grid = sp.get("actual_grid", {})
            plan_grid = sp.get("grid", {})
            current_m = datetime.now().month
            child_widgets = []
            for i, cat in enumerate(children):
                r = start_row + i
                self._render_actual_cat_row(table, cat, r, actual_grid, plan_grid, sp, data, current_m)
                row_widgets = [w for w in table.grid_slaves(row=r)]
                child_widgets.extend(row_widgets)
            self.actual_group_children[group_id] = child_widgets
        # Toggle visibility of child row widgets
        for widget in self.actual_group_children.get(group_id, []):
            if collapsed:
                widget.grid_remove()
            else:
                widget.grid()
        # Update chevron label
        if group_id in self.actual_group_labels:
            self.actual_group_labels[group_id].configure(text=f"{'▶' if collapsed else '▼'} {self._get_group_name(group_id)}")

    def toggle_planning_group(self, group_id):
        self._user_toggled.add(group_id)
        self.planning_collapsed.discard(group_id) if group_id in self.planning_collapsed else self.planning_collapsed.add(group_id)
        collapsed = group_id in self.planning_collapsed
        # Build deferred widgets on first expand
        if not collapsed and group_id in self._planning_deferred:
            table, cats, start_row, all_cascades = self._planning_deferred.pop(group_id)
            child_widgets = []
            sp = self.sp
            grid = sp.get("grid", {})
            current_m = datetime.now().month
            for i, cat in enumerate(cats):
                r = start_row + i
                self._render_planning_cat_row(table, cat, r, grid, all_cascades, current_m)
                row_widgets = [w for w in table.grid_slaves(row=r)]
                child_widgets.extend(row_widgets)
            self.planning_group_children[group_id] = child_widgets
        # Toggle visibility of child row widgets
        for widget in self.planning_group_children.get(group_id, []):
            if collapsed:
                widget.grid_remove()
            else:
                widget.grid()
        # Update chevron label
        if group_id in self.planning_group_labels:
            self.planning_group_labels[group_id].configure(text=f"{'▶' if collapsed else '▼'} {self._get_group_name(group_id)}")

    def _get_group_name(self, group_id):
        return next((g["name"] for g in self.sp.get("groups", []) if g["id"] == group_id), "")

    def _render_actual_cat_row(self, table, cat, r, actual_grid, plan_grid, sp, data, current_m):
        COL_W = 60
        NAME_W = 150
        ctk.CTkLabel(table, text=display_name(cat["name"]), font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=r, column=0, padx=2, pady=1, sticky="w")
        cat_actual = actual_grid.get(cat["id"], {})
        cat_plan = plan_grid.get(cat["id"], {})
        deadline = cat.get("deadline_month", 12)
        for m in range(12):
            mk = f"{m+1:02d}"
            val = cat_actual.get(mk, 0.0)
            planned = cat_plan.get(mk, 0.0)
            is_deadline = (m + 1 == deadline)
            cell_bg = COLOR_ACCENT if is_deadline else COLOR_SURFACE_2
            if self.editing:
                var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                self.cell_vars[("actual", cat["id"], mk)] = var
                e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=cell_bg, border_color=COLOR_PRIMARY if is_deadline else COLOR_BORDER, justify="center")
                e.grid(row=r, column=m+1, padx=1, pady=1)
                e.bind("<KeyRelease>", lambda ev, cid=cat["id"], mk_=mk, v=var: self._on_actual_cell(cid, mk_, v))
                e.bind("<FocusOut>", lambda ev, cid=cat["id"], mk_=mk, v=var: self._on_actual_cell_save(cid, mk_, v))
            else:
                if val and planned:
                    if val > planned:
                        color = COLOR_OVER_PLAN
                    elif val >= planned:
                        color = COLOR_MET_PLAN
                    else:
                        color = COLOR_UNDER_PLAN
                elif val:
                    color = COLOR_TEXT
                else:
                    color = COLOR_TEXT_MUTED
                txt = f"{val:,.0f}" if val else "–"
                is_current = (m + 1 == current_m)
                if is_deadline:
                    bg = COLOR_ACCENT
                elif is_current:
                    bg = COLOR_CURRENT_MONTH
                else:
                    bg = "transparent"
                ctk.CTkLabel(table, text=txt, font=FONT_SMALL, text_color=color, width=COL_W, anchor="center", fg_color=bg, corner_radius=4).grid(row=r, column=m+1, padx=1, pady=1)

        saved = dm.get_cat_total_saved(sp, cat["id"])
        missing = dm.get_cat_missing(sp, cat["id"])
        progress = dm.get_cat_progress(sp, cat["id"])
        spent = dm.get_savings_spent(data, cat["id"])
        balance = saved - spent

        s_lbl = ctk.CTkLabel(table, text=f"{saved:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT, width=55, anchor="center")
        s_lbl.grid(row=r, column=13, padx=1, pady=1)
        m_lbl = ctk.CTkLabel(table, text=f"{missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if missing > 0 else COLOR_SUCCESS, width=55, anchor="center")
        m_lbl.grid(row=r, column=14, padx=1, pady=1)
        p_lbl = ctk.CTkLabel(table, text=f"{progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT, width=55, anchor="center")
        p_lbl.grid(row=r, column=15, padx=1, pady=1)
        sp_lbl = ctk.CTkLabel(table, text=f"{spent:,.0f}" if spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center")
        sp_lbl.grid(row=r, column=16, padx=1, pady=1)
        b_lbl = ctk.CTkLabel(table, text=f"{balance:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if balance >= 0 else COLOR_ERROR, width=55, anchor="center")
        b_lbl.grid(row=r, column=17, padx=1, pady=1)
        self.actual_summary_lbls[cat["id"]] = {"saved": s_lbl, "missing": m_lbl, "progress": p_lbl, "balance": b_lbl}

    def build_actual_table(self):
        """Render actual savings tracker table (top section)."""
        sp = self.sp
        data = self.controller.data
        categories = sp.get("categories", [])
        groups = sp.get("groups", [])
        actual_grid = sp.get("actual_grid", {})
        plan_grid = sp.get("grid", {})
        actual_available = sp.get("actual_available", {})

        card = make_card(self.scroll)
        card.pack(anchor="nw", fill="x", pady=(0, 22))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(head, text=tx("Actual Savings"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(head, text=ui_text("what's already in each pot", "ile realnie jest w każdym celu"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkLabel(head, text=ui_text("months · saved · missing · % · spent · balance", "miesiące · odłożono · brakuje · % · wydano · saldo"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        table = ctk.CTkFrame(card, fg_color="transparent")
        table.pack(anchor="nw", padx=14, pady=14)

        COL_W = 60
        NAME_W = 150

        ctk.CTkLabel(table, text=tx("Category"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        current_m = datetime.now().month
        for m in range(12):
            is_current = (m + 1 == current_m)
            hdr_bg = COLOR_CURRENT_MONTH if is_current else "transparent"
            hdr_color = COLOR_PRIMARY if is_current else COLOR_TEXT_MUTED
            ctk.CTkLabel(table, text=month_abbr(m + 1), font=FONT_LABEL, text_color=hdr_color, width=COL_W, anchor="center", fg_color=hdr_bg, corner_radius=4).grid(row=0, column=m+1, padx=1, pady=2)
        for i, h in enumerate([tx("Saved"), tx("Missing"), "%", tx("Spent"), tx("Balance")]):
            ctk.CTkLabel(table, text=h, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=55, anchor="center").grid(row=0, column=13+i, padx=1, pady=2)

        row_idx = 1
        grouped_cats = {}
        ungrouped = []
        for cat in categories:
            if cat.get("group_id"):
                grouped_cats.setdefault(cat["group_id"], []).append(cat)
            else:
                ungrouped.append(cat)
        ungrouped.sort(key=lambda c: c["name"].casefold())
        for gid in grouped_cats:
            grouped_cats[gid].sort(key=lambda c: c["name"].casefold())

        def render_actual_row(cat, r):
            self._render_actual_cat_row(table, cat, r, actual_grid, plan_grid, sp, data, current_m)

        def render_group_header(group, children, r):
            collapsed = group["id"] in self.actual_collapsed
            chevron = "▶" if collapsed else "▼"
            lbl = ctk.CTkLabel(table, text=f"{chevron} {group['name']}", font=FONT_LABEL, text_color=COLOR_PRIMARY, width=NAME_W, anchor="w", cursor="hand2")
            lbl.grid(row=r, column=0, padx=2, pady=(6, 1), sticky="w")
            lbl.bind("<Button-1>", lambda e, gid=group["id"]: self.toggle_actual_group(gid))
            self.actual_group_labels[group["id"]] = lbl
            # Monthly sums for group
            for m in range(12):
                mk = f"{m+1:02d}"
                total = sum(actual_grid.get(c["id"], {}).get(mk, 0.0) for c in children)
                ctk.CTkLabel(table, text=f"{total:,.0f}" if total else "", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=COL_W, anchor="center").grid(row=r, column=m+1, padx=1, pady=(6, 1))
            # Summary sums for group
            g_saved = sum(dm.get_cat_total_saved(sp, c["id"]) for c in children)
            g_missing = sum(dm.get_cat_missing(sp, c["id"]) for c in children)
            g_target_sum = sum(c.get("target", 0) for c in children)
            g_progress = g_saved / g_target_sum if g_target_sum > 0 else 0.0
            g_spent = sum(dm.get_savings_spent(data, c["id"]) for c in children)
            g_balance = g_saved - g_spent
            ctk.CTkLabel(table, text=f"{g_saved:,.0f}", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=13, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if g_missing > 0 else COLOR_SUCCESS, width=55, anchor="center").grid(row=r, column=14, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_progress >= 1.0 else COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=15, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_spent:,.0f}" if g_spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center").grid(row=r, column=16, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_balance:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_balance >= 0 else COLOR_ERROR, width=55, anchor="center").grid(row=r, column=17, padx=1, pady=(6, 1))

        for cat in ungrouped:
            render_actual_row(cat, row_idx)
            row_idx += 1
        for group in sorted(groups, key=lambda g: g["name"].casefold()):
            children = grouped_cats.get(group["id"], [])
            render_group_header(group, children, row_idx)
            row_idx += 1
            if group["id"] in self.actual_collapsed:
                # Defer: reserve rows but don't create widgets
                start_row = row_idx
                row_idx += len(children)
                self.actual_group_children[group["id"]] = []
                self._actual_deferred[group["id"]] = (table, children, start_row)
            else:
                child_widgets = []
                for cat in children:
                    render_actual_row(cat, row_idx)
                    row_widgets = [w for w in table.grid_slaves(row=row_idx)]
                    child_widgets.extend(row_widgets)
                    row_idx += 1
                self.actual_group_children[group["id"]] = child_widgets

        row_idx += 1
        # Actual Available
        ctk.CTkLabel(table, text=tx("Actual Available"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(8, 1), sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            val = actual_available.get(mk, 0.0)
            if self.editing:
                var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                self.cell_vars[("avail", mk)] = var
                e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=COLOR_SURFACE, border_color=COLOR_PRIMARY, justify="center")
                e.grid(row=row_idx, column=m+1, padx=1, pady=(8, 1))
                e.bind("<KeyRelease>", lambda ev, mk_=mk, v=var: self._on_avail(mk_, v))
                e.bind("<FocusOut>", lambda ev, mk_=mk, v=var: self._on_avail_save(mk_, v))
            else:
                ctk.CTkLabel(table, text=f"{val:,.0f}" if val else "–", font=FONT_SMALL, text_color=COLOR_TEXT, width=COL_W, anchor="center").grid(row=row_idx, column=m+1, padx=1, pady=(8, 1))
        row_idx += 1
        # Actual Allocated + Remaining
        ctk.CTkLabel(table, text=tx("Allocated"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            lbl = ctk.CTkLabel(table, text=f"{dm.get_actual_month_total(sp, mk):,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.actual_alloc_lbls[mk] = lbl
        row_idx += 1
        ctk.CTkLabel(table, text=tx("Remaining"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            rem = dm.get_actual_month_remaining(sp, mk)
            lbl = ctk.CTkLabel(table, text=f"{rem:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if rem >= 0 else COLOR_ERROR, width=COL_W, anchor="center")
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.actual_remain_lbls[mk] = lbl

    def build_planner_table(self):
        self.build_grid()

    def _on_actual_cell(self, cat_id, mk, var):
        try:
            self.sp.setdefault("actual_grid", {}).setdefault(cat_id, {})[mk] = float(var.get().replace(",", ".") or "0")
        except:
            pass
        self._update_actual_summaries()

    def _on_actual_cell_save(self, cat_id, mk, var):
        self._on_actual_cell(cat_id, mk, var)
        dm.save_savings_planner(self.sp)

    def _on_avail(self, mk, var):
        try:
            self.sp.setdefault("actual_available", {})[mk] = float(var.get().replace(",", ".") or "0")
        except:
            pass
        self._update_actual_summaries()

    def _on_avail_save(self, mk, var):
        self._on_avail(mk, var)
        dm.save_savings_planner(self.sp)

    def _update_actual_summaries(self):
        sp = self.sp
        data = self.controller.data
        for mk in [f"{m:02d}" for m in range(1, 13)]:
            if mk in self.actual_alloc_lbls:
                self.actual_alloc_lbls[mk].configure(text=f"{dm.get_actual_month_total(sp, mk):,.0f}")
            if mk in self.actual_remain_lbls:
                rem = dm.get_actual_month_remaining(sp, mk)
                self.actual_remain_lbls[mk].configure(text=f"{rem:,.0f}", text_color=COLOR_SUCCESS if rem >= 0 else COLOR_ERROR)
        for cat_id, lbls in self.actual_summary_lbls.items():
            saved = dm.get_cat_total_saved(sp, cat_id)
            missing = dm.get_cat_missing(sp, cat_id)
            progress = dm.get_cat_progress(sp, cat_id)
            spent = dm.get_savings_spent(data, cat_id)
            balance = saved - spent
            lbls["saved"].configure(text=f"{saved:,.0f}")
            lbls["missing"].configure(text=f"{missing:,.0f}", text_color=COLOR_WARNING if missing > 0 else COLOR_SUCCESS)
            lbls["progress"].configure(text=f"{progress*100:.0f}%", text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT)
            lbls["balance"].configure(text=f"{balance:,.0f}", text_color=COLOR_SUCCESS if balance >= 0 else COLOR_ERROR)

    def _rebuild_ui(self):
        """Rebuild widgets from cached self.sp without re-fetching data."""
        for w in self.scroll.winfo_children():
            w.destroy()
        self.cell_vars = {}
        self.assumed_vars = {}
        self.alloc_lbls = {}
        self.remain_lbls = {}
        self.group_lbls = {}
        self.cat_total_lbls = {}
        self.actual_summary_lbls = {}
        self.actual_alloc_lbls = {}
        self.actual_remain_lbls = {}
        self.actual_group_children = {}
        self.actual_group_labels = {}
        self.planning_group_children = {}
        self.planning_group_labels = {}
        self._planning_deferred = {}
        self._actual_deferred = {}
        # Single-pass cache: scan all month files once for savings spent
        self._spent_cache = dm.build_savings_spent_cache()
        year = self.controller.current_month.split("-")[0]
        self.year_lbl.configure(text=year)
        self._build_year_summary()
        self.build_actual_table()
        self.build_planner_table()

    def _build_year_summary(self):
        summary_width = max(820, self.winfo_width() - 80)
        card = make_card(self.scroll, width=summary_width, height=116)
        card.pack(anchor="nw", pady=(0, 22))
        card.pack_propagate(False)
        card.grid_columnconfigure((0, 1, 2), weight=1, uniform="saving_summary")
        current_month = int(self.controller.current_month.split("-")[1])
        planned_to_date = sum(dm.get_month_total_allocated(self.sp, f"{m:02d}") for m in range(1, current_month + 1))
        actual_to_date = sum(dm.get_actual_month_total(self.sp, f"{m:02d}") for m in range(1, current_month + 1))
        plan_ratio = (actual_to_date / planned_to_date) if planned_to_date > 0 else 0.0
        categories = self.sp.get("categories", [])
        met = sum(1 for cat in categories if dm.get_cat_progress(self.sp, cat["id"]) >= 1.0)
        stats = [
            (ui_text("Saved this year", "Odłożono w tym roku"), format_money(actual_to_date, suffix=False), ui_text(f"Across {len(categories)} active goals", f"{len(categories)} aktywnych celów"), COLOR_INCOME),
            (ui_text("On plan", "Zgodnie z planem"), f"{plan_ratio * 100:.0f}%", ui_text("Saved vs. planned to date", "Odłożone względem planu do dziś"), COLOR_TEXT),
            (ui_text("Goals met", "Cele zrealizowane"), f"{met} / {len(categories)}", ui_text("Completed savings goals", "Ukończone cele oszczędnościowe"), COLOR_TEXT),
        ]
        for idx, (label, value, sub, color) in enumerate(stats):
            cell = ctk.CTkFrame(card, fg_color="transparent")
            cell.grid(row=0, column=idx, sticky="nsew", padx=20, pady=18)
            if idx > 0:
                ctk.CTkFrame(cell, width=1, fg_color=COLOR_BORDER).pack(side="left", fill="y", padx=(0, 20))
            body = ctk.CTkFrame(cell, fg_color="transparent")
            body.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(body, text=label.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(body, text=value, font=FONT_MONO_LG, text_color=color).pack(anchor="w", pady=(6, 2))
            ctk.CTkLabel(body, text=sub, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")

    def refresh(self):
        self.sp = dm.get_savings_planner()
        dm.get_savings_actual(self.sp)
        # Default all groups to collapsed on first load
        all_group_ids = {g["id"] for g in self.sp.get("groups", [])}
        # Only set defaults for groups not yet interacted with
        for gid in all_group_ids:
            if gid not in self._user_toggled:
                self.actual_collapsed.add(gid)
                self.planning_collapsed.add(gid)
        self._rebuild_ui()


class SavingsActualView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.sp = dm.get_savings_planner()
        self.editing = False
        self.cell_vars = {}
        self.avail_vars = {}
        self.spent_vars = {}

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(hdr, text=tx("Actual Savings"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.edit_btn = ctk.CTkButton(hdr, text=tx("✎ Edit"), width=92, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.toggle_edit)
        self.edit_btn.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", orientation="horizontal")
        self.scroll.pack(fill="both", expand=True)

    def toggle_edit(self):
        if self.editing:
            self.save_all()
            self.editing = False
            self.edit_btn.configure(text=tx("✎ Edit"), fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER)
        else:
            self.editing = True
            self.edit_btn.configure(text=tx("✓ Done"), fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
        self.build_grid()

    def save_all(self):
        sp = self.sp
        for (cat_id, mk), var in self.cell_vars.items():
            try:
                sp.setdefault("actual_grid", {}).setdefault(cat_id, {})[mk] = float(var.get().replace(",", ".") or "0")
            except:
                pass
        for mk, var in self.avail_vars.items():
            try:
                sp.setdefault("actual_available", {})[mk] = float(var.get().replace(",", ".") or "0")
            except:
                pass
        for cat_id, var in self.spent_vars.items():
            try:
                sp.setdefault("spent", {})[cat_id] = float(var.get().replace(",", ".") or "0")
            except:
                pass
        dm.save_savings_planner(sp)

    def on_cell_change(self, cat_id, mk, var):
        try:
            self.sp.setdefault("actual_grid", {}).setdefault(cat_id, {})[mk] = float(var.get().replace(",", ".") or "0")
        except:
            pass
        dm.save_savings_planner(self.sp)
        self.update_summaries()

    def on_avail_change(self, mk, var):
        try:
            self.sp.setdefault("actual_available", {})[mk] = float(var.get().replace(",", ".") or "0")
        except:
            pass
        dm.save_savings_planner(self.sp)
        self.update_summaries()

    def on_spent_change(self, cat_id, var):
        try:
            self.sp.setdefault("spent", {})[cat_id] = float(var.get().replace(",", ".") or "0")
        except:
            pass
        dm.save_savings_planner(self.sp)
        self.update_summaries()

    def update_summaries(self):
        sp = self.sp
        for mk in [f"{m:02d}" for m in range(1, 13)]:
            if hasattr(self, 'alloc_lbls') and mk in self.alloc_lbls:
                self.alloc_lbls[mk].configure(text=f"{dm.get_actual_month_total(sp, mk):,.0f}")
            if hasattr(self, 'remain_lbls') and mk in self.remain_lbls:
                rem = dm.get_actual_month_remaining(sp, mk)
                self.remain_lbls[mk].configure(text=f"{rem:,.0f}", text_color=COLOR_SUCCESS if rem >= 0 else COLOR_ERROR)
        if hasattr(self, 'summary_lbls'):
            for cat_id, lbls in self.summary_lbls.items():
                saved = dm.get_cat_total_saved(sp, cat_id)
                missing = dm.get_cat_missing(sp, cat_id)
                progress = dm.get_cat_progress(sp, cat_id)
                balance = dm.get_cat_balance(sp, cat_id)
                rollover = dm.get_cat_rollover(sp, cat_id)
                lbls["saved"].configure(text=f"{saved:,.0f}")
                lbls["missing"].configure(text=f"{missing:,.0f}")
                lbls["progress"].configure(text=f"{progress*100:.0f}%", text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT)
                lbls["balance"].configure(text=f"{balance:,.0f}", text_color=COLOR_SUCCESS if balance >= 0 else COLOR_ERROR)
                if "rollover" in lbls:
                    if rollover > 0:
                        lbls["rollover"].configure(text=f"↻ {rollover:,.0f}", text_color=COLOR_SUCCESS)
                    else:
                        lbls["rollover"].configure(text="")

    def build_grid(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        self.cell_vars = {}
        self.avail_vars = {}
        self.spent_vars = {}
        self.alloc_lbls = {}
        self.remain_lbls = {}
        self.summary_lbls = {}

        sp = self.sp
        dm.get_savings_actual(sp)
        categories = sp.get("categories", [])
        groups = sp.get("groups", [])
        actual_grid = sp.get("actual_grid", {})
        plan_grid = sp.get("grid", {})
        actual_available = sp.get("actual_available", {})

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(fill="both", expand=True)

        COL_W = 60
        NAME_W = 150

        # Header
        ctk.CTkLabel(table, text=tx("Category"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        for m in range(12):
            ctk.CTkLabel(table, text=month_abbr(m + 1), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center").grid(row=0, column=m+1, padx=1, pady=2)
        # Summary column headers
        sum_cols = [tx("Saved"), tx("Missing"), "%", tx("Spent"), tx("Balance"), ""]
        for i, h in enumerate(sum_cols):
            ctk.CTkLabel(table, text=h, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=55, anchor="center").grid(row=0, column=13+i, padx=1, pady=2)

        row_idx = 1
        grouped_cats = {}
        ungrouped = []
        for cat in categories:
            gid = cat.get("group_id")
            if gid:
                grouped_cats.setdefault(gid, []).append(cat)
            else:
                ungrouped.append(cat)
        ungrouped.sort(key=lambda c: c["name"].casefold())
        for gid in grouped_cats:
            grouped_cats[gid].sort(key=lambda c: c["name"].casefold())

        def render_cat_row(cat, r):
            ctk.CTkLabel(table, text=display_name(cat["name"]), font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=r, column=0, padx=2, pady=1, sticky="w")

            cat_actual = actual_grid.get(cat["id"], {})
            cat_plan = plan_grid.get(cat["id"], {})

            for m in range(12):
                mk = f"{m+1:02d}"
                val = cat_actual.get(mk, 0.0)
                planned = cat_plan.get(mk, 0.0)

                if self.editing:
                    var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                    self.cell_vars[(cat["id"], mk)] = var
                    e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, justify="center")
                    e.grid(row=r, column=m+1, padx=1, pady=1)
                    e.bind("<KeyRelease>", lambda ev, cid=cat["id"], mk_=mk, v=var: self.on_cell_change(cid, mk_, v))
                    e.bind("<FocusOut>", lambda ev, cid=cat["id"], mk_=mk, v=var: self.on_cell_change(cid, mk_, v))
                else:
                    # Color: green if met plan, red if under
                    if val and planned:
                        color = COLOR_SUCCESS if val >= planned else COLOR_ERROR
                    elif val:
                        color = COLOR_TEXT
                    else:
                        color = COLOR_TEXT_MUTED
                    txt = f"{val:,.0f}" if val else "–"
                    ctk.CTkLabel(table, text=txt, font=FONT_SMALL, text_color=color, width=COL_W, anchor="center").grid(row=r, column=m+1, padx=1, pady=1)

            # Summary cells
            saved = dm.get_cat_total_saved(sp, cat["id"])
            missing = dm.get_cat_missing(sp, cat["id"])
            progress = dm.get_cat_progress(sp, cat["id"])
            balance = dm.get_cat_balance(sp, cat["id"])
            rollover = dm.get_cat_rollover(sp, cat["id"])

            s_lbl = ctk.CTkLabel(table, text=f"{saved:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT, width=55, anchor="center")
            s_lbl.grid(row=r, column=13, padx=1, pady=1)
            m_lbl = ctk.CTkLabel(table, text=f"{missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if missing > 0 else COLOR_SUCCESS, width=55, anchor="center")
            m_lbl.grid(row=r, column=14, padx=1, pady=1)
            p_lbl = ctk.CTkLabel(table, text=f"{progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT, width=55, anchor="center")
            p_lbl.grid(row=r, column=15, padx=1, pady=1)

            # Spent - editable in edit mode
            spent_val = sp.get("spent", {}).get(cat["id"], 0.0)
            if self.editing:
                sp_var = ctk.StringVar(value=f"{spent_val:.0f}" if spent_val else "")
                self.spent_vars[cat["id"]] = sp_var
                sp_e = ctk.CTkEntry(table, textvariable=sp_var, font=FONT_SMALL, width=55, height=26, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, justify="center")
                sp_e.grid(row=r, column=16, padx=1, pady=1)
                sp_e.bind("<KeyRelease>", lambda ev, cid=cat["id"], v=sp_var: self.on_spent_change(cid, v))
                sp_e.bind("<FocusOut>", lambda ev, cid=cat["id"], v=sp_var: self.on_spent_change(cid, v))
            else:
                sp_lbl = ctk.CTkLabel(table, text=f"{spent_val:,.0f}" if spent_val else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center")
                sp_lbl.grid(row=r, column=16, padx=1, pady=1)

            bal_color = COLOR_SUCCESS if balance >= 0 else COLOR_ERROR
            b_lbl = ctk.CTkLabel(table, text=f"{balance:,.0f}", font=FONT_SMALL, text_color=bal_color, width=55, anchor="center")
            b_lbl.grid(row=r, column=17, padx=1, pady=1)

            # Rollover badge
            r_lbl = ctk.CTkLabel(table, text=f"↻ {rollover:,.0f}" if rollover > 0 else "", font=FONT_SMALL, text_color=COLOR_SUCCESS, width=55, anchor="center")
            r_lbl.grid(row=r, column=18, padx=1, pady=1)

            self.summary_lbls[cat["id"]] = {"saved": s_lbl, "missing": m_lbl, "progress": p_lbl, "balance": b_lbl, "rollover": r_lbl}

        def render_group_row(group, r):
            ctk.CTkLabel(table, text=f"▸ {group['name']}", font=FONT_LABEL, text_color=COLOR_PRIMARY, width=NAME_W, anchor="w").grid(row=r, column=0, padx=2, pady=(6, 1), sticky="w")
            children = grouped_cats.get(group["id"], [])
            for m in range(12):
                mk = f"{m+1:02d}"
                total = sum(actual_grid.get(c["id"], {}).get(mk, 0.0) for c in children)
                ctk.CTkLabel(table, text=f"{total:,.0f}" if total else "", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=COL_W, anchor="center").grid(row=r, column=m+1, padx=1, pady=(6, 1))

        for cat in ungrouped:
            render_cat_row(cat, row_idx)
            row_idx += 1
        for group in sorted(groups, key=lambda g: g["name"].casefold()):
            render_group_row(group, row_idx)
            row_idx += 1
            for cat in grouped_cats.get(group["id"], []):
                render_cat_row(cat, row_idx)
                row_idx += 1

        row_idx += 1

        # Actual Available (manual)
        ctk.CTkLabel(table, text=tx("Actual Available"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(10, 1), sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            val = actual_available.get(mk, 0.0)
            if self.editing:
                var = ctk.StringVar(value=f"{val:.0f}" if val else "")
                self.avail_vars[mk] = var
                e = ctk.CTkEntry(table, textvariable=var, font=FONT_SMALL, width=COL_W, height=26, fg_color=COLOR_SURFACE, border_color=COLOR_PRIMARY, justify="center")
                e.grid(row=row_idx, column=m+1, padx=1, pady=(10, 1))
                e.bind("<KeyRelease>", lambda ev, mk_=mk, v=var: self.on_avail_change(mk_, v))
                e.bind("<FocusOut>", lambda ev, mk_=mk, v=var: self.on_avail_change(mk_, v))
            else:
                txt = f"{val:,.0f}" if val else "–"
                ctk.CTkLabel(table, text=txt, font=FONT_SMALL, text_color=COLOR_TEXT, width=COL_W, anchor="center").grid(row=row_idx, column=m+1, padx=1, pady=(10, 1))
        row_idx += 1

        # Actual Allocated (auto)
        ctk.CTkLabel(table, text=tx("Actual Allocated"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            allocated = dm.get_actual_month_total(sp, mk)
            lbl = ctk.CTkLabel(table, text=f"{allocated:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.alloc_lbls[mk] = lbl
        row_idx += 1

        # Remaining (auto)
        ctk.CTkLabel(table, text=tx("Remaining"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            rem = dm.get_actual_month_remaining(sp, mk)
            color = COLOR_SUCCESS if rem >= 0 else COLOR_ERROR
            lbl = ctk.CTkLabel(table, text=f"{rem:,.0f}", font=FONT_SMALL, text_color=color, width=COL_W, anchor="center")
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.remain_lbls[mk] = lbl

    def refresh(self):
        self.sp = dm.get_savings_planner()
        self.build_grid()



class CashFlowView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.editing = False

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.cashflow"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)
        actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        actions.pack(side="right", padx=24)
        month_box = ctk.CTkFrame(actions, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        month_box.pack(side="left", padx=(0, 10))
        ctk.CTkButton(month_box, text="‹", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(-1)).pack(side="left", padx=(4, 0), pady=3)
        self.month_lbl = ctk.CTkLabel(month_box, text="", font=FONT_MONO, text_color=COLOR_TEXT, width=118)
        self.month_lbl.pack(side="left")
        ctk.CTkButton(month_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(1)).pack(side="left", padx=(0, 4), pady=3)
        self.edit_btn = ctk.CTkButton(actions, text=ui_text("✎ Edit balances", "✎ Edytuj salda"), width=122, height=34, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=self.toggle_edit)
        self.edit_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text=ui_text("Adjust targets ↗", "Cele w ustawieniach ↗"),
            width=136,
            height=34,
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            hover_color=COLOR_SURFACE_2,
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.controller.show_view("Settings"),
        ).pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)

        self.built = False
        self.balance_vars = {}
        self.topup_lbls = {}
        self.progress_bars = {}
        self.timestamp_lbls = {}
        self.shared_assumed_var = ctk.StringVar(value="0.00")
        self.saved_assumed_var = ctk.StringVar(value="0.00")
        self.shared_actual_var = ctk.StringVar(value="0.00")
        self.saved_actual_lbl = None
        self.total_topup_lbl = None
        self.net_income_lbl = None
        self.cashflow_formula_lbl = None

    def toggle_edit(self):
        if self.editing:
            self.calculate()
            self.editing = False
            self.edit_btn.configure(text=ui_text("✎ Edit balances", "✎ Edytuj salda"), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT)
        else:
            self.editing = True
            self.edit_btn.configure(text="✓ Done", fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
        self.build()

    def build(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        data = self.controller.data
        targets = dm.get_cashflow_targets(self.controller.config)
        cf = dm.get_cashflow(data)
        self.month_lbl.configure(text=month_year_label(self.controller.current_month, upper=True))

        self.balance_vars = {}
        self.topup_lbls = {}
        self.progress_bars = {}
        self.timestamp_lbls = {}

        net_income = dm.get_net_income(data)
        total_topup = sum(max(0.0, target["target"] - cf.get("current_accounts", {}).get(target["id"], {}).get("balance", 0.0)) for target in targets)
        shared_actual = cf.get("shared_actual", 0.0)
        actual_saved = net_income - total_topup - shared_actual

        result = make_card(self.scroll, height=198)
        result.pack(fill="x", pady=(0, 22))
        result.pack_propagate(False)
        result.grid_columnconfigure(0, weight=7)
        result.grid_columnconfigure(1, weight=5)

        left = ctk.CTkFrame(result, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=32, pady=28)
        ctk.CTkLabel(left, text=f"● {ui_text('TOP-UP NEEDED THIS MONTH', 'DO UZUPEŁNIENIA W TYM MIESIĄCU')}", font=FONT_MONO_SM_BOLD, text_color=COLOR_PRIMARY).pack(anchor="w")
        amount_row = ctk.CTkFrame(left, fg_color="transparent")
        amount_row.pack(anchor="w", pady=(8, 6))
        self.total_topup_lbl = ctk.CTkLabel(amount_row, text=format_money(total_topup, suffix=False), font=FONT_HERO, text_color=COLOR_PRIMARY)
        self.total_topup_lbl.pack(side="left")
        ctk.CTkLabel(amount_row, text="PLN", font=FONT_TITLE, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(10, 0), pady=(26, 0))
        ctk.CTkLabel(
            left,
            text=ui_text(
                "Move this from the business account to bring every buffer back to its minimum.",
                "Przenieś tę kwotę z konta firmowego, żeby każdy bufor wrócił do minimum.",
            ),
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            wraplength=470,
            justify="left",
        ).pack(anchor="w")

        right = ctk.CTkFrame(result, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=32, pady=34)
        ctk.CTkLabel(right, text=ui_text("Free for savings after top-ups", "Wolne na oszczędności po uzupełnieniach"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
        saved_row = ctk.CTkFrame(right, fg_color="transparent")
        saved_row.pack(anchor="w", pady=(10, 4))
        self.saved_actual_lbl = ctk.CTkLabel(saved_row, text=format_money(actual_saved, suffix=False), font=(FONT_MONO_FAMILY, 28, "bold"), text_color=COLOR_INCOME if actual_saved >= 0 else COLOR_ERROR)
        self.saved_actual_lbl.pack(side="left")
        ctk.CTkLabel(saved_row, text="PLN", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(8, 0), pady=(14, 0))
        self.cashflow_formula_lbl = ctk.CTkLabel(right, text="", font=FONT_MONO, text_color=COLOR_TEXT)
        self.cashflow_formula_lbl.pack(anchor="w")
        ctk.CTkButton(
            right,
            text=ui_text("Allocate to goals →", "Przejdź do celów →"),
            height=34,
            width=142,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=lambda: self.controller.show_view("Savings"),
        ).pack(anchor="w", pady=(14, 0))

        cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 22))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="buffer_cards")

        if not targets:
            empty = make_card(cards)
            empty.grid(row=0, column=0, columnspan=3, sticky="ew")
            ctk.CTkLabel(empty, text=ui_text("No cash-flow targets yet.", "Brak celów przepływów."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=20)

        cats = data.get("categories", [])
        shared_cat = next((c for c in cats if c["id"] == "shared"), None)
        saved_cat = next((c for c in cats if c["id"] == "saved"), None)
        shared_calc = dm.get_allocated_amount(data, "shared") if shared_cat else 0.0
        saved_calc = dm.get_allocated_amount(data, "saved") if saved_cat else 0.0

        for idx, t_item in enumerate(targets):
            tid = t_item["id"]
            acct = cf.get("current_accounts", {}).get(tid, {"balance": 0.0, "updated_at": ""})
            balance = acct.get("balance", 0.0)
            target_amount = t_item.get("target", 0.0)
            topup = max(0.0, target_amount - balance)
            funded_ratio = min(balance / target_amount, 1.0) if target_amount > 0 else 1.0
            card = make_card(cards, border_color=COLOR_SUCCESS if topup <= 0 else COLOR_BORDER, fg_color=COLOR_SURFACE if topup > 0 else COLOR_SURFACE_2)
            card.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=(0 if idx % 3 == 0 else 6, 0 if idx % 3 == 2 else 6), pady=6)
            head = ctk.CTkFrame(card, fg_color="transparent")
            head.pack(fill="x", padx=18, pady=(18, 10))
            icon = "✓" if topup <= 0 else str(idx + 1)
            ctk.CTkLabel(head, text=icon, width=32, height=32, fg_color=COLOR_INCOME_SOFT if topup <= 0 else COLOR_PRIMARY_SOFT, corner_radius=9, font=FONT_MONO, text_color=COLOR_SUCCESS if topup <= 0 else COLOR_PRIMARY).pack(side="left", padx=(0, 10))
            title_box = ctk.CTkFrame(head, fg_color="transparent")
            title_box.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(title_box, text=display_name(t_item["name"]), font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
            ctk.CTkLabel(title_box, text=ui_text("minimum buffer", "minimalny bufor"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(2, 0))

            row_now = ctk.CTkFrame(card, fg_color="transparent")
            row_now.pack(fill="x", padx=18, pady=(2, 2))
            ctk.CTkLabel(row_now, text=ui_text("Now", "Teraz"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            var = ctk.StringVar(value=f"{balance:.2f}")
            self.balance_vars[tid] = var
            if self.editing:
                entry = ctk.CTkEntry(row_now, textvariable=var, font=FONT_MONO, width=118, height=30, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, justify="right")
                entry.pack(side="right")
                entry.bind("<KeyRelease>", self.calculate)
                entry.bind("<FocusOut>", lambda e, v=var, tid_=tid: self.on_balance_blur(v, tid_))
            else:
                ctk.CTkLabel(row_now, text=format_money(balance, suffix=False), font=FONT_MONO, text_color=COLOR_TEXT).pack(side="right")
            row_target = ctk.CTkFrame(card, fg_color="transparent")
            row_target.pack(fill="x", padx=18, pady=(2, 8))
            ctk.CTkLabel(row_target, text=ui_text("Minimum target", "Cel minimum"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row_target, text=format_money(target_amount, suffix=False), font=FONT_MONO, text_color=COLOR_TEXT).pack(side="right")
            ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=18, pady=(0, 10))
            topup_row = ctk.CTkFrame(card, fg_color="transparent")
            topup_row.pack(fill="x", padx=18)
            ctk.CTkLabel(topup_row, text=ui_text("TOP UP", "UZUPEŁNIJ"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            topup_lbl = ctk.CTkLabel(topup_row, text=format_money(topup, suffix=False) if topup > 0 else ui_text("funded", "uzupełnione"), font=FONT_MONO_LG, text_color=COLOR_PRIMARY if topup > 0 else COLOR_SUCCESS)
            topup_lbl.pack(side="right")
            self.topup_lbls[tid] = topup_lbl
            progress = ctk.CTkProgressBar(card, height=6, progress_color=COLOR_PRIMARY if topup > 0 else COLOR_SUCCESS, fg_color=COLOR_SURFACE_2)
            progress.pack(fill="x", padx=18, pady=(10, 8))
            progress.set(funded_ratio)
            self.progress_bars[tid] = progress
            ts_text = acct.get("updated_at", "")
            ts_lbl = ctk.CTkLabel(card, text=f"{int(funded_ratio * 100)}% {ui_text('funded', 'sfinansowane')} · {ts_text or ui_text('not updated yet', 'jeszcze bez aktualizacji')}", font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED)
            ts_lbl.pack(anchor="w", padx=18, pady=(0, 16))
            self.timestamp_lbls[tid] = ts_lbl

        goals = make_card(self.scroll)
        goals.pack(fill="x", pady=(0, 22))
        goals_head = ctk.CTkFrame(goals, fg_color="transparent")
        goals_head.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(goals_head, text=tx("Savings & Shared Goals"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(goals_head, text=ui_text("calculated vs assumed", "wyliczone vs założone"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkFrame(goals, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        goals_grid = ctk.CTkFrame(goals, fg_color="transparent")
        goals_grid.pack(fill="x", padx=18, pady=16)
        for idx in range(3):
            goals_grid.grid_columnconfigure(idx, weight=1, uniform="goals")
        self.shared_assumed_var.set(f"{cf.get('shared_assumed', 0.0):.2f}")
        self.saved_assumed_var.set(f"{cf.get('saved_assumed', 0.0):.2f}")
        self.shared_actual_var.set(f"{cf.get('shared_actual', 0.0):.2f}")

        rows = [
            (tx("Calculated"), format_money(shared_calc, suffix=False), format_money(saved_calc, suffix=False)),
            (tx("Assumed"), self.shared_assumed_var, self.saved_assumed_var),
            (tx("Actual"), self.shared_actual_var, None),
        ]
        ctk.CTkLabel(goals_grid, text="", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ctk.CTkLabel(goals_grid, text=tx("Shared"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(goals_grid, text=tx("Saved"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).grid(row=0, column=2, sticky="ew", padx=4, pady=4)
        for row_idx, (label, shared_val, saved_val) in enumerate(rows, start=1):
            ctk.CTkLabel(goals_grid, text=label, font=FONT_LABEL, text_color=COLOR_TEXT, anchor="w").grid(row=row_idx, column=0, sticky="w", padx=4, pady=5)
            if self.editing and row_idx in (2, 3):
                shared_entry = ctk.CTkEntry(goals_grid, textvariable=shared_val, font=FONT_MONO, height=30, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, justify="center")
                shared_entry.grid(row=row_idx, column=1, sticky="ew", padx=8, pady=5)
                shared_entry.bind("<KeyRelease>", self.calculate)
                shared_entry.bind("<FocusOut>", lambda e: self.calculate())
            else:
                text = shared_val.get() if hasattr(shared_val, "get") else shared_val
                ctk.CTkLabel(goals_grid, text=text, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, corner_radius=7, height=30).grid(row=row_idx, column=1, sticky="ew", padx=8, pady=5)
            if saved_val is None:
                self.net_income_lbl = ctk.CTkLabel(goals_grid, text=format_money(net_income, suffix=False), font=FONT_MONO, text_color=COLOR_INCOME, fg_color=COLOR_SURFACE_2, corner_radius=7, height=30)
                self.net_income_lbl.grid(row=row_idx, column=2, sticky="ew", padx=8, pady=5)
            elif self.editing and row_idx == 2:
                saved_entry = ctk.CTkEntry(goals_grid, textvariable=saved_val, font=FONT_MONO, height=30, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, justify="center")
                saved_entry.grid(row=row_idx, column=2, sticky="ew", padx=8, pady=5)
                saved_entry.bind("<KeyRelease>", self.calculate)
                saved_entry.bind("<FocusOut>", lambda e: self.calculate())
            else:
                text = saved_val.get() if hasattr(saved_val, "get") else saved_val
                ctk.CTkLabel(goals_grid, text=text, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, corner_radius=7, height=30).grid(row=row_idx, column=2, sticky="ew", padx=8, pady=5)

        recent = make_card(self.scroll)
        recent.pack(fill="x")
        r_head = ctk.CTkFrame(recent, fg_color="transparent")
        r_head.pack(fill="x", padx=20, pady=(16, 12))
        ctk.CTkLabel(r_head, text=ui_text("Recent edits", "Ostatnie zmiany"), font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(r_head, text=ui_text("latest balance updates", "ostatnie aktualizacje sald"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkFrame(recent, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        updates = []
        for t_item in targets:
            acct = cf.get("current_accounts", {}).get(t_item["id"], {})
            if acct.get("updated_at"):
                updates.append((acct["updated_at"], display_name(t_item["name"]), acct.get("balance", 0.0)))
        if not updates:
            ctk.CTkLabel(recent, text=ui_text("No balance updates yet.", "Brak aktualizacji sald."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=18)
        for ts_text, name, balance in sorted(updates, reverse=True)[:5]:
            row = ctk.CTkFrame(recent, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=f"{name} {ui_text('balance updated', 'saldo zaktualizowane')}", font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(row, text=format_money(balance, suffix=False), font=FONT_MONO, text_color=COLOR_TEXT).pack(side="left", padx=12)
            ctk.CTkLabel(row, text=ts_text, font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_FAINT).pack(side="right")

        self.built = True
        self.calculate()

    def on_balance_blur(self, var, tid):
        val = var.get().replace(",", ".")
        try:
            var.set(f"{float(val):.2f}")
        except:
            pass
        # Update timestamp
        cf = dm.get_cashflow(self.controller.data)
        acct = cf.setdefault("current_accounts", {}).setdefault(tid, {"balance": 0.0, "updated_at": ""})
        acct["updated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        if tid in self.timestamp_lbls:
            self.timestamp_lbls[tid].configure(text=f"{tx('Updated:')} {acct['updated_at']}")
        self.calculate()

    def calculate(self, event=None):
        try:
            data = self.controller.data
            config = self.controller.config
            targets = dm.get_cashflow_targets(config)
            cf = dm.get_cashflow(data)

            # Part 1: calculate top-ups
            total_topup = 0.0
            for t in targets:
                tid = t["id"]
                var = self.balance_vars.get(tid)
                if not var:
                    continue
                balance = parse_money(var.get())
                acct = cf.setdefault("current_accounts", {}).setdefault(tid, {"balance": 0.0, "updated_at": ""})
                acct["balance"] = balance
                topup = max(0.0, t["target"] - balance)
                total_topup += topup
                if tid in self.topup_lbls:
                    self.topup_lbls[tid].configure(
                        text=format_money(topup, suffix=False) if topup > 0 else ui_text("funded", "uzupełnione"),
                        text_color=COLOR_PRIMARY if topup > 0 else COLOR_SUCCESS,
                    )
                if tid in self.progress_bars:
                    ratio = min(balance / t["target"], 1.0) if t["target"] > 0 else 1.0
                    self.progress_bars[tid].set(ratio)
                if tid in self.timestamp_lbls:
                    ratio = min(balance / t["target"], 1.0) if t["target"] > 0 else 1.0
                    ts_text = acct.get("updated_at", "")
                    self.timestamp_lbls[tid].configure(text=f"{int(ratio * 100)}% {ui_text('funded', 'sfinansowane')} · {ts_text or ui_text('not updated yet', 'jeszcze bez aktualizacji')}")

            if self.total_topup_lbl:
                self.total_topup_lbl.configure(text=format_money(total_topup, suffix=False))

            # Part 2: save all manual values
            net_income = dm.get_net_income(data)
            if self.net_income_lbl:
                self.net_income_lbl.configure(text=format_money(net_income, suffix=False))

            shared_actual = parse_money(self.shared_actual_var.get())
            cf["shared_actual"] = shared_actual

            shared_assumed = parse_money(self.shared_assumed_var.get())
            cf["shared_assumed"] = shared_assumed

            saved_assumed = parse_money(self.saved_assumed_var.get())
            cf["saved_assumed"] = saved_assumed

            # Actual Saved = Net Income - Total Top-ups - Shared Actual
            actual_saved = net_income - total_topup - shared_actual
            color = COLOR_SUCCESS if actual_saved >= 0 else COLOR_ERROR
            if self.saved_actual_lbl:
                self.saved_actual_lbl.configure(text=format_money(actual_saved, suffix=False), text_color=color)
            if self.cashflow_formula_lbl:
                self.cashflow_formula_lbl.configure(
                    text=f"{ui_text('Net', 'Netto')} {format_money(net_income, suffix=False)} − {ui_text('top-up', 'uzupełn.') } {format_money(total_topup, suffix=False)}"
                )

            self.controller.save_data()
        except:
            pass

    def refresh(self):
        self.build()

class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.year = int(controller.current_month.split("-")[0])
        self.expanded_month = None
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self.topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        ctk.CTkLabel(self.topbar, text=t("screen.history"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)

        actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        actions.pack(side="right", padx=24)
        self.search_entry = ctk.CTkEntry(actions, textvariable=self.search_var, placeholder_text=ui_text("Search a month or expense...", "Szukaj miesiąca albo wydatku..."), width=260, height=38, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER)
        self.search_entry.pack(side="left", padx=(0, 12))
        year_box = ctk.CTkFrame(actions, fg_color=COLOR_SURFACE, corner_radius=RADIUS_BUTTON, border_width=1, border_color=COLOR_BORDER)
        year_box.pack(side="left", padx=(0, 12))
        ctk.CTkButton(year_box, text="‹", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.change_year(-1)).pack(side="left", padx=(4, 0), pady=3)
        self.year_lbl = ctk.CTkLabel(year_box, text=str(self.year), font=FONT_MONO, text_color=COLOR_PRIMARY, width=76, fg_color=COLOR_SURFACE_2, corner_radius=7)
        self.year_lbl.pack(side="left", pady=4)
        ctk.CTkButton(year_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.change_year(1)).pack(side="left", padx=(0, 4), pady=3)
        ctk.CTkButton(actions, text=ui_text("Export year ↗", "Eksport roku ↗"), width=118, height=34, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, command=self.export_year).pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)

    def change_year(self, delta):
        self.year += delta
        self.refresh()

    def _history_months(self):
        months = [self.controller.current_month] + dm.get_past_months(self.controller.current_month)
        return sorted({m for m in months if int(m[:4]) == self.year}, reverse=True)

    def export_year(self):
        months = self._filtered_months()
        if not months:
            return
        path = filedialog.asksaveasfilename(
            title=ui_text("Export year", "Eksport roku"),
            defaultextension=".json",
            initialfile=f"florin-{self.year}-history.json",
            filetypes=[(tx("JSON files"), "*.json"), (tx("All files"), "*.*")],
        )
        if not path:
            return
        payload = {month: dm.load_month(month) for month in months}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        messagebox.showinfo(ui_text("Export complete", "Eksport zakończony"), ui_text("Year history exported.", "Historia roku została wyeksportowana."))

    def _filtered_months(self):
        needle = self.search_var.get().strip().casefold()
        months = self._history_months()
        if not needle:
            return months
        filtered = []
        for month_str in months:
            data = dm.load_month(month_str)
            label = month_year_label(month_str).casefold()
            expenses = " ".join(
                " ".join([exp.get("description", ""), str(exp.get("amount", "")), " ".join(exp.get("tags", []))])
                for exp in data.get("expenses", [])
            ).casefold()
            if needle in label or needle in expenses:
                filtered.append(month_str)
        return filtered

    def toggle_month(self, month_str):
        self.expanded_month = None if self.expanded_month == month_str else month_str
        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        self.year_lbl.configure(text=str(self.year))
        months = self._filtered_months()
        if not months:
            ctk.CTkLabel(self.scroll, text=tx("No past months found."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=40)
            return

        if self.expanded_month not in months:
            self.expanded_month = months[0]

        self._render_year_summary(months)
        for month_str in months:
            self._render_month(month_str, expanded=month_str == self.expanded_month)

    def _render_year_summary(self, months):
        data_by_month = [dm.load_month(month) for month in months]
        net = sum(dm.get_net_income(data) for data in data_by_month)
        spent = sum(dm.get_total_expenses(data) for data in data_by_month)
        saved = sum(dm.get_allocated_amount(data, "saved") for data in data_by_month)
        card = make_card(self.scroll)
        card.pack(fill="x", pady=(0, 24))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="history_summary")
        stats = [
            (str(self.year), ui_text(f"{len(months)} months tracked", f"{len(months)} mies. śledzone"), COLOR_TEXT),
            (ui_text("Net income", "Dochód netto"), format_money(net, suffix=False), COLOR_INCOME),
            (ui_text("Spent", "Wydano"), format_money(spent, suffix=False), COLOR_EXPENSE),
            (ui_text("Saved", "Odłożono"), format_money(saved, suffix=False), COLOR_TEXT),
        ]
        for idx, (label, value, color) in enumerate(stats):
            cell = ctk.CTkFrame(card, fg_color="transparent")
            cell.grid(row=0, column=idx, sticky="nsew", padx=24, pady=20)
            if idx > 0:
                ctk.CTkFrame(cell, width=1, fg_color=COLOR_BORDER).pack(side="left", fill="y", padx=(0, 20))
            body = ctk.CTkFrame(cell, fg_color="transparent")
            body.pack(side="left", fill="both", expand=True)
            if idx == 0:
                ctk.CTkLabel(body, text=label, font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
                ctk.CTkLabel(body, text=value, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            else:
                ctk.CTkLabel(body, text=label.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
                ctk.CTkLabel(body, text=value, font=FONT_MONO_LG, text_color=color).pack(anchor="w", pady=(6, 0))

    def _render_month(self, month_str, expanded=False):
        data = dm.load_month(month_str)
        net = dm.get_net_income(data)
        total_exp = dm.get_total_expenses(data)
        saved = dm.get_allocated_amount(data, "saved")
        expenses = data.get("expenses", [])

        card = make_card(self.scroll)
        card.pack(fill="x", pady=(0, 16))
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 16))
        month_dt = datetime.strptime(month_str, "%Y-%m")
        title = f"{month_full(month_dt.month)} {month_dt.year}"
        ctk.CTkButton(
            hdr,
            text=("⌄ " if expanded else "› ") + title,
            width=170,
            height=32,
            fg_color="transparent",
            text_color=COLOR_TEXT,
            hover_color=COLOR_PRIMARY_SOFT,
            anchor="w",
            font=FONT_TITLE,
            command=lambda m=month_str: self.toggle_month(m),
        ).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{ui_text('Spent', 'Wydano')} {format_money(total_exp, suffix=False)} · {item_count(len(expenses))}  |  {ui_text('Saved', 'Odłożono')} {format_money(saved, suffix=False)}", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=12)
        ctk.CTkLabel(hdr, text=f"{ui_text('NET', 'NETTO')}\n{format_money(net, suffix=False)}", font=FONT_MONO, text_color=COLOR_INCOME, justify="right").pack(side="right")

        if not expanded:
            return
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        detail = ctk.CTkFrame(card, fg_color="transparent")
        detail.pack(fill="x", padx=24, pady=18)
        detail.grid_columnconfigure((0, 1, 2), weight=1, uniform="history_detail")
        self._history_allocation_card(detail, data, 0)
        self._history_expense_card(detail, data, 1)
        self._history_balance_card(detail, data, 2, month_dt)

    def _history_allocation_card(self, parent, data, column):
        card = make_card(parent)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(card, text=ui_text("Allocation snapshot", "Migawka podziału").upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 10))
        canvas = tk.Canvas(card, width=116, height=116, bg=COLOR_SURFACE, highlightthickness=0)
        canvas.pack(anchor="center", pady=(0, 8))
        self._draw_history_donut(canvas, data.get("categories", []))
        for cat in data.get("categories", [])[:5]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=5)
            pill = make_pill(row, display_category_name(cat), category_color(cat), width=126, height=26)
            pill.pack(side="left")
            ctk.CTkLabel(row, text=format_money(dm.get_allocated_amount(data, cat["id"]), suffix=False), font=FONT_MONO, text_color=COLOR_TEXT).pack(side="right")

    def _history_expense_card(self, parent, data, column):
        card = make_card(parent)
        card.grid(row=0, column=column, sticky="nsew", padx=8)
        ctk.CTkLabel(card, text=ui_text("Top expense categories", "Top kategorie wydatków").upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 12))
        grouped = dm.get_expenses_by_expense_category(data)
        exp_cats = {c["id"]: display_name(c["name"]) for c in dm.get_expense_categories(data)}
        rows = []
        for cat_id, items in grouped.items():
            rows.append((sum(exp["amount"] for exp in items), exp_cats.get(cat_id, tx("Uncategorized")), len(items)))
        for amount, name, count in sorted(rows, reverse=True)[:6]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=8)
            ctk.CTkLabel(row, text=f"{name}  {count}", font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(row, text=f"- {format_money(amount, suffix=False)}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right")
        if not rows:
            ctk.CTkLabel(card, text=tx("No expenses for this month."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=10)

    def _history_balance_card(self, parent, data, column, month_dt):
        card = make_card(parent)
        card.grid(row=0, column=column, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(card, text=ui_text(f"Account balances · end of {month_full(month_dt.month)}", f"Salda kont · koniec: {month_full(month_dt.month)}").upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 12))
        cf = dm.get_cashflow(data)
        targets = {target["id"]: target["name"] for target in dm.get_cashflow_targets(self.controller.config)}
        total_assets = 0.0
        rows = []
        for tid, acct in cf.get("current_accounts", {}).items():
            balance = acct.get("balance", 0.0)
            total_assets += balance
            rows.append((targets.get(tid, tid), balance))
        for name, balance in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=8)
            ctk.CTkLabel(row, text=display_name(name), font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(row, text=format_money(balance, suffix=False), font=FONT_MONO, text_color=COLOR_TEXT).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=18, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkLabel(row, text=ui_text("Total assets", "Aktywa razem"), font=FONT_LABEL, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(row, text=format_money(total_assets, suffix=False), font=FONT_MONO, text_color=COLOR_INCOME).pack(side="right")

    def _draw_history_donut(self, canvas, cats):
        start = 90
        total = sum(max(cat.get("percent", 0), 0) for cat in cats) or 1
        for cat in cats:
            extent = -360 * (max(cat.get("percent", 0), 0) / total)
            canvas.create_arc(8, 8, 108, 108, start=start, extent=extent, fill=category_color(cat), outline="")
            start += extent
        canvas.create_oval(36, 36, 80, 80, fill=COLOR_SURFACE, outline=COLOR_SURFACE)

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller

        topbar = ctk.CTkFrame(self, fg_color=COLOR_BG, height=60, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text=t("screen.settings"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left", padx=24)
        ctk.CTkLabel(topbar, text=t("status.auto_save"), font=FONT_MONO, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=24)
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=24)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.section_widgets = {}
        self.settings_nav_buttons = {}
        nav = ctk.CTkFrame(body, fg_color="transparent", width=200)
        nav.grid(row=0, column=0, sticky="nsw", padx=(0, 24))
        nav.grid_propagate(False)
        sections = [
            ("Default income", "settings.nav.default_income"),
            ("Cash-flow targets", "settings.nav.cashflow"),
            ("Categories", "settings.nav.categories"),
            ("Appearance", "settings.nav.appearance"),
            ("Language", "settings.nav.language"),
            ("Features", "settings.nav.features"),
            ("Emergency Fund Settings", "settings.nav.emergency_fund"),
            ("Data & backup", "settings.nav.data"),
        ]
        for i, (section_key, label_key) in enumerate(sections):
            button = ctk.CTkButton(
                nav, text=t(label_key), height=40, anchor="w",
                fg_color="transparent",
                text_color=COLOR_TEXT_MUTED,
                hover_color=COLOR_SURFACE_2,
                border_width=0,
                border_color=COLOR_BORDER,
                corner_radius=RADIUS_BUTTON,
                font=FONT_BODY,
                command=lambda key=section_key: self.scroll_to_section(key),
            )
            button.pack(fill="x", pady=4)
            self.settings_nav_buttons[section_key] = button
        self._set_active_settings_section(sections[0][0])

        self.scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.scroll.grid(row=0, column=1, sticky="nsew")

        # === Default Income Items ===
        inc_card = make_card(self.scroll)
        inc_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Default income"] = inc_card

        inc_hdr = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(inc_hdr, text=t("settings.default_income.title"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(inc_hdr, text=t("settings.default_income.desc"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(inc_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.inc_items_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        self.inc_items_frame.pack(fill="x", padx=24, pady=(16, 10))

        inc_add_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_add_frame.pack(fill="x", padx=24, pady=(0, 24))
        self.inc_new_name = ctk.CTkEntry(inc_add_frame, placeholder_text=t("settings.default_income.item_name"), width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.inc_new_name.pack(side="left", padx=(0, 5))
        self.inc_type_var = ctk.StringVar(value=tx("Addition"))
        self.inc_type_options = {tx("Addition"): "addition", tx("Deduction"): "deduction"}
        ctk.CTkOptionMenu(inc_add_frame, values=list(self.inc_type_options.keys()), variable=self.inc_type_var, width=130).pack(side="left", padx=(0, 5))
        ctk.CTkButton(inc_add_frame, text=f"+ {t('common.add')}", width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_income_item).pack(side="left")

        # === Cash Flow Targets ===
        card = make_card(self.scroll)
        card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Cash-flow targets"] = card

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(hdr, text=t("settings.cashflow.title"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(hdr, text=t("settings.cashflow.desc"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")

        self.targets_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.targets_frame.pack(fill="x", padx=24, pady=(16, 10))

        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=24, pady=(0, 24))
        self.new_name = ctk.CTkEntry(add_frame, placeholder_text=t("settings.cashflow.account_name"), width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.new_name.pack(side="left", padx=(0, 5))
        self.new_target = ctk.CTkEntry(add_frame, placeholder_text=t("settings.cashflow.target"), width=130, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.new_target.pack(side="left", padx=(0, 5))
        ctk.CTkButton(add_frame, text=f"+ {t('common.add')}", width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_target).pack(side="left")

        # === Categories ===
        cat_card = make_card(self.scroll)
        cat_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Categories"] = cat_card
        cat_hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(cat_hdr, text=t("settings.categories.title"), font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(cat_hdr, text=t("settings.categories.desc"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(cat_card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        self.settings_categories_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
        self.settings_categories_frame.pack(fill="x", padx=24, pady=16)

        # === Appearance ===
        appearance = make_card(self.scroll)
        appearance.pack(fill="x", pady=(0, 24))
        self.section_widgets["Appearance"] = appearance
        active_theme = theme_module.normalize_theme_name(self.controller.config.get("theme", "Petal Rose"))
        self._settings_section_header(appearance, t("settings.appearance.title"), t("settings.appearance.desc").format(theme=active_theme))
        theme_grid = ctk.CTkFrame(appearance, fg_color="transparent")
        theme_grid.pack(fill="x", padx=24, pady=(16, 24))
        for idx, name in enumerate(theme_module.THEME_NAMES):
            palette = theme_module.get_theme_palette(name)
            active = name == active_theme
            bg = palette["COLOR_BG"]
            accent = palette["COLOR_PRIMARY"]
            surface = palette["COLOR_SURFACE"]
            border = palette["COLOR_BORDER"]
            preview = ctk.CTkFrame(theme_grid, fg_color=COLOR_SURFACE, border_width=2 if active else 1, border_color=COLOR_PRIMARY if active else COLOR_BORDER, corner_radius=RADIUS_CARD)
            preview.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=(0 if idx % 2 == 0 else 6, 0 if idx % 2 == 1 else 6), pady=(0, 12))
            theme_grid.grid_columnconfigure(idx % 2, weight=1)
            mock = ctk.CTkFrame(preview, fg_color=bg, border_width=1, border_color=border, corner_radius=10, height=92)
            mock.pack(fill="x", padx=14, pady=(14, 10))
            mock.pack_propagate(False)
            ctk.CTkFrame(mock, fg_color=accent, height=8, corner_radius=4).pack(fill="x", padx=12, pady=(18, 8))
            ctk.CTkFrame(mock, fg_color=surface, height=8, corner_radius=4).pack(fill="x", padx=12, pady=4)
            ctk.CTkFrame(mock, fg_color=surface, height=8, corner_radius=4).pack(fill="x", padx=12, pady=4)
            row = ctk.CTkFrame(preview, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(0, 14))
            ctk.CTkLabel(row, text=name, font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(row, text=t("common.active") if active else t("common.preview"), font=FONT_SMALL, text_color=COLOR_PRIMARY if active else COLOR_TEXT_MUTED).pack(side="right")
            ctk.CTkButton(
                preview,
                text=t("common.active") if active else t("common.use_theme"),
                height=28,
                fg_color=COLOR_PRIMARY if not active else COLOR_SURFACE_2,
                text_color=COLOR_SURFACE if not active else COLOR_TEXT,
                hover_color=COLOR_PRIMARY_HOVER if not active else COLOR_BORDER,
                command=lambda n=name: self.set_theme_pref(n),
            ).pack(fill="x", padx=14, pady=(0, 14))

        # === Language ===
        language = make_card(self.scroll)
        language.pack(fill="x", pady=(0, 24))
        self.section_widgets["Language"] = language
        self._settings_section_header(language, t("settings.language.title"), t("settings.language.desc"))
        lang_row = ctk.CTkFrame(language, fg_color="transparent")
        lang_row.pack(fill="x", padx=24, pady=(16, 24))
        current_lang = self.controller.config.get("language", "en")
        self.language_cards = {}
        for idx, (code, flag, name, subtitle) in enumerate([
            ("en", "EN", "English", t("settings.language.english_desc")),
            ("pl", "PL", "Polski", t("settings.language.polish_desc")),
        ]):
            card = ctk.CTkFrame(lang_row, fg_color=COLOR_SURFACE, border_width=2 if current_lang == code else 1, border_color=COLOR_PRIMARY if current_lang == code else COLOR_BORDER, corner_radius=RADIUS_CARD)
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0 if idx == 1 else 6))
            lang_row.grid_columnconfigure(idx, weight=1)
            badge = ctk.CTkLabel(card, text=flag, font=FONT_MONO, text_color=COLOR_PRIMARY, fg_color=COLOR_SURFACE_2, corner_radius=16, width=34, height=34)
            badge.pack(side="left", padx=16, pady=16)
            copy = ctk.CTkFrame(card, fg_color="transparent")
            copy.pack(side="left", fill="x", expand=True, pady=16)
            ctk.CTkLabel(copy, text=name, font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
            ctk.CTkLabel(copy, text=subtitle, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            ctk.CTkButton(card, text=t("common.active") if current_lang == code else t("common.use"), width=74, height=30, fg_color=COLOR_PRIMARY if current_lang == code else COLOR_SURFACE_2, text_color=COLOR_SURFACE if current_lang == code else COLOR_TEXT, hover_color=COLOR_PRIMARY_SOFT, command=lambda lang=code: self.set_language_pref(lang)).pack(side="right", padx=16, pady=16)
            self.language_cards[code] = card

        # === Features ===
        feat_card = make_card(self.scroll)
        feat_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Features"] = feat_card
        self._settings_section_header(feat_card, "Features", "Enable experimental or extra features.")
        
        self.shared_goals_var = ctk.StringVar(value=self.controller.config.get("enable_shared_goals", "true"))
        sw = ctk.CTkSwitch(
            feat_card,
            text=t("settings.enable_shared_goals"),
            variable=self.shared_goals_var,
            onvalue="true",
            offvalue="false",
            command=self.toggle_shared_goals,
            font=FONT_BODY,
            fg_color=COLOR_BORDER,
            progress_color=COLOR_PRIMARY
        )
        sw.pack(anchor="w", padx=24, pady=(16, 24))


        # === Emergency Fund Settings ===
        ef_card = make_card(self.scroll)
        ef_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Emergency Fund Settings"] = ef_card
        self._settings_section_header(ef_card, t("Emergency Fund Settings"), "")
        
        self.emergency_fund_var = ctk.StringVar(value=self.controller.config.get("enable_emergency_fund", "false"))
        self.ef_personal_var = ctk.StringVar(value=self.controller.config.get("enable_ef_personal", "true"))
        self.ef_shared_var = ctk.StringVar(value=self.controller.config.get("enable_ef_shared", "false"))

        self.editing_ef = False
        self.p_allocations = []
        self.s_allocations = []

        # Personal Vars
        self.ef_p_salary_var = ctk.StringVar(value="0.0")
        self.ef_p_mortgage_var = ctk.StringVar(value="0.0")
        self.ef_p_living_var = ctk.StringVar(value="0.0")
        self.ef_p_actual_var = ctk.StringVar(value="0.0")
        self.ef_p_goal_var = ctk.StringVar(value="3msc_zycia_kredytu")
        self.ef_p_future_goal_var = ctk.StringVar(value="6msc_kredytu")

        # Shared Vars
        self.ef_s_salary_var = ctk.StringVar(value="0.0")
        self.ef_s_mortgage_var = ctk.StringVar(value="0.0")
        self.ef_s_living_var = ctk.StringVar(value="0.0")
        self.ef_s_actual_var = ctk.StringVar(value="0.0")
        self.ef_s_goal_var = ctk.StringVar(value="3msc_zycia_kredytu")
        self.ef_s_future_goal_var = ctk.StringVar(value="6msc_kredytu")

        self.ef_body = ctk.CTkFrame(ef_card, fg_color="transparent")
        self.ef_body.pack(fill="x", padx=24, pady=(0, 24))

        # Toggles
        toggles_frame = ctk.CTkFrame(self.ef_body, fg_color="transparent")
        toggles_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkSwitch(
            toggles_frame, text=t("Enable Emergency Fund Globally"), variable=self.emergency_fund_var,
            onvalue="true", offvalue="false", command=self.toggle_emergency_fund, font=FONT_TITLE,
            fg_color=COLOR_BORDER, progress_color=COLOR_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        sub_frame = ctk.CTkFrame(toggles_frame, fg_color="transparent")
        sub_frame.pack(fill="x")
        ctk.CTkCheckBox(sub_frame, text=t("Enable Personal Fund (JA)"), variable=self.ef_personal_var, onvalue="true", offvalue="false", command=self.toggle_ef_sub, fg_color=COLOR_PRIMARY).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(sub_frame, text=t("Enable Shared Fund (WSPÓLNE)"), variable=self.ef_shared_var, onvalue="true", offvalue="false", command=self.toggle_ef_sub, fg_color=COLOR_PRIMARY).pack(side="left")

        self.ef_forms_container = ctk.CTkFrame(self.ef_body, fg_color="transparent")
        self.ef_forms_container.pack(fill="x")

        self.load_ef_settings()
        self.render_ef_forms()


        # === Data & backup ===
        data_card = make_card(self.scroll)
        data_card.pack(fill="x", pady=(0, 24))
        self.section_widgets["Data & backup"] = data_card
        self._settings_section_header(data_card, t("settings.data.title"), t("settings.data.desc"))
        data_body = ctk.CTkFrame(data_card, fg_color="transparent")
        data_body.pack(fill="x", padx=24, pady=(16, 24))
        self._data_row(data_body, t("settings.data.database"), t("settings.data.database_desc"), t("common.local"), t("settings.data.open_folder"), self.open_database_folder)
        self._data_row(data_body, t("settings.data.exports"), t("settings.data.exports_desc"), t("common.manual"), t("settings.data.export_json"), self.export_current_month)

    def _settings_section_header(self, parent, title, body):
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(head, text=title, font=FONT_SECTION, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(head, text=body, font=FONT_BODY, text_color=COLOR_TEXT_MUTED, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))
        ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    def _data_row(self, parent, title, body, badge, action_label=None, action_command=None):
        row = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        row.pack(fill="x", pady=6)
        copy = ctk.CTkFrame(row, fg_color="transparent")
        copy.pack(side="left", fill="x", expand=True, padx=16, pady=14)
        ctk.CTkLabel(copy, text=title, font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(copy, text=body, font=FONT_BODY, text_color=COLOR_TEXT_MUTED, wraplength=520, justify="left").pack(anchor="w", pady=(2, 0))
        if action_label and action_command:
            ctk.CTkButton(row, text=action_label, width=112, height=32, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, border_width=1, border_color=COLOR_BORDER, command=action_command).pack(side="right", padx=(4, 16), pady=14)
        ctk.CTkLabel(row, text=badge.upper(), font=FONT_SMALL, text_color=COLOR_PRIMARY, fg_color=COLOR_SURFACE, corner_radius=6).pack(side="right", padx=16, pady=14, ipadx=8, ipady=3)

    def scroll_to_section(self, key):
        section = self.section_widgets.get(key)
        canvas = getattr(self.scroll, "_parent_canvas", None)
        if not section or not canvas:
            return
        self.update_idletasks()
        bbox = canvas.bbox("all") or (0, 0, 1, 1)
        content_height = max(bbox[3] - bbox[1], 1)
        viewport_height = max(canvas.winfo_height(), 1)
        max_scroll = max(content_height - viewport_height, 1)
        target_y = max(0, min(section.winfo_y() - 8, max_scroll))
        canvas.yview_moveto(max(0, min(target_y / content_height, 1)))
        self._set_active_settings_section(key)

    def _set_active_settings_section(self, active_key):
        for key, button in self.settings_nav_buttons.items():
            active = key == active_key
            button.configure(
                fg_color=COLOR_SURFACE if active else "transparent",
                text_color=COLOR_PRIMARY if active else COLOR_TEXT_MUTED,
                border_width=1 if active else 0,
                border_color=COLOR_BORDER,
            )

    def set_theme_pref(self, name):
        self.controller.config["theme"] = theme_module.set_theme(name)
        sync_theme_globals()
        dm.save_config(self.controller.config)
        self.controller.rebuild_shell("Settings")

    def set_language_pref(self, lang):
        self.controller.config["language"] = lang
        dm.save_config(self.controller.config)
        set_language(lang)
        self.controller.rebuild_shell("Settings")

    def open_database_folder(self):
        open_in_file_manager(get_db_path().parent)

    def export_current_month(self):
        default_name = f"florin-{self.controller.current_month}.json"
        path = filedialog.asksaveasfilename(
            title=tx("Export current month"),
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[(tx("JSON files"), "*.json"), (tx("All files"), "*.*")]
        )
        if not path:
            return
        self.controller.save_data()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.controller.data, f, ensure_ascii=False, indent=2, sort_keys=True)
        messagebox.showinfo(tx("Export complete"), t("settings.export_saved").format(name=Path(path).name))

    def build_settings_categories(self):
        for widget in self.settings_categories_frame.winfo_children():
            widget.destroy()
        cats = self.controller.data.get("categories", [])
        expenses = self.controller.data.get("expenses", [])
        for cat in cats:
            row = ctk.CTkFrame(self.settings_categories_frame, fg_color="transparent")
            row.pack(fill="x", pady=6)
            swatch = ctk.CTkFrame(row, width=24, height=24, fg_color=category_color(cat), corner_radius=6)
            swatch.pack(side="left", padx=(0, 12))
            swatch.pack_propagate(False)
            ctk.CTkLabel(row, text=display_category_name(cat), font=FONT_TITLE, text_color=COLOR_TEXT, width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{cat['percent']:.0f} %", font=FONT_MONO, text_color=COLOR_TEXT, width=70).pack(side="left", padx=8)
            cat_expenses = [e for e in expenses if e.get("category_id") == cat["id"]]
            total = sum(e["amount"] for e in cat_expenses)
            ctk.CTkLabel(row, text=f"{item_count(len(cat_expenses))} · {format_money(total)}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text=tx("Edit"), width=68, height=30, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=lambda c=cat: self.open_budget_category_editor(c)).pack(side="right")
            ctk.CTkFrame(self.settings_categories_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    def open_budget_category_editor(self, cat):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit budget category"))
        dialog.geometry("380x260")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(20, 4))
        name_var = ctk.StringVar(value=cat["name"])
        ctk.CTkEntry(dialog, textvariable=name_var, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=tx("Monthly split (%):"), anchor="w").pack(fill="x", padx=20, pady=(12, 4))
        percent_var = ctk.StringVar(value=f"{cat.get('percent', 0):.1f}")
        ctk.CTkEntry(dialog, textvariable=percent_var, font=FONT_MONO, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(fill="x", padx=20)
        error = ctk.CTkLabel(dialog, text="", font=FONT_SMALL, text_color=COLOR_ERROR)
        error.pack(fill="x", padx=20, pady=(4, 0))

        def save():
            name = name_var.get().strip()
            try:
                percent = float(percent_var.get().replace(",", "."))
            except ValueError:
                error.configure(text=tx("Enter a valid percentage."))
                return
            if not name or percent < 0:
                error.configure(text=tx("Name is required and percent cannot be negative."))
                return
            cat["name"] = name
            cat["percent"] = percent
            self.controller.save_data()
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text=tx("Save"), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=save).pack(fill="x", padx=20, pady=(12, 20))

    # --- Default Income Items ---
    def add_income_item(self):
        name = self.inc_new_name.get().strip()
        if not name:
            return
        dm.add_default_income_item(name, self.inc_type_options.get(self.inc_type_var.get(), "addition"))
        self.inc_new_name.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_income_item(self, item_id):
        dm.delete_default_income_item(item_id)
        self.controller.config = dm.get_config()
        self.refresh()

    def build_income_items(self):
        for w in self.inc_items_frame.winfo_children():
            w.destroy()
        items = dm.get_default_income_items(self.controller.config)
        for item in items:
            row = ctk.CTkFrame(self.inc_items_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            sign = "+" if item["type"] == "addition" else "−"
            color = COLOR_SUCCESS if item["type"] == "addition" else COLOR_ERROR
            ctk.CTkLabel(row, text=sign, font=FONT_MONO, text_color=color, width=28, fg_color=COLOR_INCOME_SOFT if item["type"] == "addition" else COLOR_EXPENSE_SOFT, corner_radius=8).pack(side="left", padx=(0, 10), pady=8)
            ctk.CTkLabel(row, text=display_name(item["name"]), font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=display_type(item["type"]), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.delete_income_item(iid)).pack(side="right", padx=5, pady=5)
            ctk.CTkFrame(self.inc_items_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")

    # --- Cash Flow Targets ---
    def add_target(self):
        name = self.new_name.get().strip()
        try:
            amt = float(self.new_target.get().replace(",", "."))
        except:
            return
        if not name or amt <= 0:
            return
        dm.add_cashflow_target(name, amt)
        self.new_name.delete(0, "end")
        self.new_target.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_target(self, tid):
        dm.delete_cashflow_target(tid)
        self.controller.config = dm.get_config()
        self.refresh()

    def save_edit(self, tid, name_var, amt_var):
        name = name_var.get().strip()
        try:
            amt = float(amt_var.get().replace(",", "."))
        except:
            return
        if name and amt > 0:
            dm.edit_cashflow_target(tid, name=name, target_amount=amt)
            self.controller.config = dm.get_config()

    def toggle_shared_goals(self):
        val = self.shared_goals_var.get()
        self.controller.config["enable_shared_goals"] = val
        dm.save_config(self.controller.config)
        self.controller.refresh_sidebar()

    def toggle_emergency_fund(self):
        val = self.emergency_fund_var.get()
        self.controller.config["enable_emergency_fund"] = val
        dm.save_config(self.controller.config)
        self.controller.refresh_sidebar()
        
    def _ef_input(self, parent, label_text, var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=label_text, font=FONT_TITLE, width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, font=FONT_MONO, width=150).pack(side="left")

    def _ef_label(self, parent, label_text, val_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=label_text, font=FONT_TITLE, width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=val_text, font=FONT_MONO).pack(side="left")

    def toggle_ef_sub(self):
        self.controller.config["enable_ef_personal"] = self.ef_personal_var.get()
        self.controller.config["enable_ef_shared"] = self.ef_shared_var.get()
        dm.save_config(self.controller.config)
        self.render_ef_forms()
        self.controller.refresh_sidebar()

    def toggle_edit_ef(self):
        self.editing_ef = True
        self.render_ef_forms()

    def save_and_toggle_ef(self):
        self.save_ef_settings()
        self.editing_ef = False
        self.render_ef_forms()

    def add_allocation(self, alloc_list):
        alloc_list.append({"name": ctk.StringVar(value="Nowa kategoria"), "pct": ctk.StringVar(value="0")})
        self.render_ef_forms()

    def remove_allocation(self, alloc_list, item):
        alloc_list.remove(item)
        self.render_ef_forms()

    def render_ef_forms(self):
        for w in self.ef_forms_container.winfo_children():
            w.destroy()

        if self.emergency_fund_var.get() != "true":
            return

        goal_options = [
            "3msc_kredytu", "3msc_zycia", "6msc_kredytu",
            "3msc_zycia_kredytu", "4msc_zycia_kredytu", "5msc_zycia_kredytu", "6msc_zycia_kredytu",
            "3msc_wyplaty", "6msc_wyplaty"
        ]

        def _build_form(parent, title, s_var, m_var, l_var, a_var, g_var, f_var, alloc_list):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=(10, 20))
            
            hdr = ctk.CTkFrame(f, fg_color="transparent")
            hdr.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(hdr, text=title, font=FONT_SECTION, text_color=COLOR_PRIMARY).pack(side="left")
            
            if not self.editing_ef:
                ctk.CTkButton(hdr, text=t("Edit"), width=60, height=28, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, border_width=1, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_2, command=self.toggle_edit_ef).pack(side="right")
                
                self._ef_label(f, t("Salary (Wypłata)"), f"{float(s_var.get()):,.2f} PLN")
                self._ef_label(f, t("Mortgage/Loan (Kredyt)"), f"{float(m_var.get()):,.2f} PLN")
                self._ef_label(f, t("Living Expenses (Do życia)"), f"{float(l_var.get()):,.2f} PLN")
                self._ef_label(f, t("Actual Saved:"), f"{float(a_var.get()):,.2f} PLN")
                self._ef_label(f, t("Active Goal:"), g_var.get())
                self._ef_label(f, t("Future Goal:"), f_var.get())
                
                ctk.CTkLabel(f, text=t("Asset Allocations"), font=FONT_TITLE, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(15, 5))
                for al in alloc_list:
                    r = ctk.CTkFrame(f, fg_color="transparent")
                    r.pack(fill="x", pady=2)
                    ctk.CTkLabel(r, text=f"• {al['name'].get()}:", font=FONT_BODY, width=150, anchor="w").pack(side="left")
                    ctk.CTkLabel(r, text=f"{al['pct'].get()}%", font=FONT_MONO).pack(side="left")
            else:
                ctk.CTkButton(hdr, text=t("Save"), width=60, height=28, fg_color=COLOR_SUCCESS, text_color=COLOR_SURFACE, hover_color=COLOR_MET_PLAN, command=self.save_and_toggle_ef).pack(side="right")
                
                self._ef_input(f, t("Salary (Wypłata)"), s_var)
                self._ef_input(f, t("Mortgage/Loan (Kredyt)"), m_var)
                self._ef_input(f, t("Living Expenses (Do życia)"), l_var)
                self._ef_input(f, t("Actual Saved:"), a_var)
                
                gf = ctk.CTkFrame(f, fg_color="transparent")
                gf.pack(fill="x", pady=5)
                ctk.CTkLabel(gf, text=t("Active Goal:"), font=FONT_TITLE, width=150, anchor="w").pack(side="left")
                ctk.CTkOptionMenu(gf, variable=g_var, values=goal_options).pack(side="left")
                
                ff = ctk.CTkFrame(f, fg_color="transparent")
                ff.pack(fill="x", pady=5)
                ctk.CTkLabel(ff, text=t("Future Goal:"), font=FONT_TITLE, width=150, anchor="w").pack(side="left")
                ctk.CTkOptionMenu(ff, variable=f_var, values=goal_options).pack(side="left")
                
                ctk.CTkLabel(f, text=t("Asset Allocations (%)"), font=FONT_TITLE, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(15, 5))
                for al in alloc_list:
                    r = ctk.CTkFrame(f, fg_color="transparent")
                    r.pack(fill="x", pady=2)
                    ctk.CTkEntry(r, textvariable=al["name"], width=200).pack(side="left", padx=5)
                    ctk.CTkEntry(r, textvariable=al["pct"], width=60).pack(side="left")
                    ctk.CTkLabel(r, text="%").pack(side="left", padx=5)
                    ctk.CTkButton(r, text="×", width=28, fg_color="transparent", text_color=COLOR_ERROR, command=lambda a=al, lst=alloc_list: self.remove_allocation(lst, a)).pack(side="left")
                
                ctk.CTkButton(f, text="+ Add Allocation", width=120, height=28, fg_color="transparent", text_color=COLOR_PRIMARY, border_width=1, border_color=COLOR_PRIMARY, command=lambda lst=alloc_list: self.add_allocation(lst)).pack(anchor="w", pady=(5, 10), padx=5)

        if self.ef_personal_var.get() == "true":
            _build_form(self.ef_forms_container, t("Personal Settings (JA)"), self.ef_p_salary_var, self.ef_p_mortgage_var, self.ef_p_living_var, self.ef_p_actual_var, self.ef_p_goal_var, self.ef_p_future_goal_var, self.p_allocations)
            
        if self.ef_shared_var.get() == "true":
            _build_form(self.ef_forms_container, t("Shared Settings (WSPÓLNE)"), self.ef_s_salary_var, self.ef_s_mortgage_var, self.ef_s_living_var, self.ef_s_actual_var, self.ef_s_goal_var, self.ef_s_future_goal_var, self.s_allocations)

    def load_ef_settings(self):
        settings = dm.get_emergency_fund_settings()
        
        p_data = settings.get("personal", {})
        self.ef_p_salary_var.set(str(p_data.get("salary", 0.0)))
        self.ef_p_mortgage_var.set(str(p_data.get("mortgage", 0.0)))
        self.ef_p_living_var.set(str(p_data.get("living_expenses", 0.0)))
        self.ef_p_actual_var.set(str(p_data.get("actual_saved", 0.0)))
        self.ef_p_goal_var.set(p_data.get("selected_goal", "3msc_zycia_kredytu"))
        self.ef_p_future_goal_var.set(p_data.get("future_goal", "6msc_zycia"))
        self.p_allocations = [{"name": ctk.StringVar(value=k), "pct": ctk.StringVar(value=str(v))} for k, v in p_data.get("allocations", {}).items()]

        s_data = settings.get("shared", {})
        self.ef_s_salary_var.set(str(s_data.get("salary", 0.0)))
        self.ef_s_mortgage_var.set(str(s_data.get("mortgage", 0.0)))
        self.ef_s_living_var.set(str(s_data.get("living_expenses", 0.0)))
        self.ef_s_actual_var.set(str(s_data.get("actual_saved", 0.0)))
        self.ef_s_goal_var.set(s_data.get("selected_goal", "3msc_zycia_kredytu"))
        self.ef_s_future_goal_var.set(s_data.get("future_goal", "6msc_zycia"))
        self.s_allocations = [{"name": ctk.StringVar(value=k), "pct": ctk.StringVar(value=str(v))} for k, v in s_data.get("allocations", {}).items()]

    def save_ef_settings(self):
        try:
            p_old = dm.get_emergency_fund_settings().get("personal", {})
            p_allocs = {}
            for a in self.p_allocations:
                try:
                    p_allocs[a["name"].get()] = float(a["pct"].get().replace(",", "."))
                except: pass

            p_data = {
                "salary": float(self.ef_p_salary_var.get().replace(",", ".")),
                "mortgage": float(self.ef_p_mortgage_var.get().replace(",", ".")),
                "living_expenses": float(self.ef_p_living_var.get().replace(",", ".")),
                "actual_saved": float(self.ef_p_actual_var.get().replace(",", ".")),
                "selected_goal": self.ef_p_goal_var.get(),
                "future_goal": self.ef_p_future_goal_var.get(),
                "cash_allocated": p_old.get("cash_allocated", 0.0),
                "allocations": p_allocs
            }
            dm.save_emergency_fund_settings("personal", p_data)

            s_old = dm.get_emergency_fund_settings().get("shared", {})
            s_allocs = {}
            for a in self.s_allocations:
                try:
                    s_allocs[a["name"].get()] = float(a["pct"].get().replace(",", "."))
                except: pass

            s_data = {
                "salary": float(self.ef_s_salary_var.get().replace(",", ".")),
                "mortgage": float(self.ef_s_mortgage_var.get().replace(",", ".")),
                "living_expenses": float(self.ef_s_living_var.get().replace(",", ".")),
                "actual_saved": float(self.ef_s_actual_var.get().replace(",", ".")),
                "selected_goal": self.ef_s_goal_var.get(),
                "future_goal": self.ef_s_future_goal_var.get(),
                "cash_allocated": s_old.get("cash_allocated", 0.0),
                "allocations": s_allocs
            }
            dm.save_emergency_fund_settings("shared", s_data)

            if "Emergency Fund" in self.controller.views:
                self.controller.views["Emergency Fund"].refresh()
        except ValueError:
            pass

    def refresh(self):
        self.build_income_items()
        self.build_settings_categories()
        for w in self.targets_frame.winfo_children():
            w.destroy()
        targets = dm.get_cashflow_targets(self.controller.config)
        for t in targets:
            row = ctk.CTkFrame(self.targets_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            name_var = ctk.StringVar(value=t["name"])
            amt_var = ctk.StringVar(value=f"{t['target']:.2f}")
            ctk.CTkEntry(row, textvariable=name_var, font=FONT_BODY, width=220, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=(0, 5), pady=8)
            ctk.CTkEntry(row, textvariable=amt_var, font=FONT_MONO, width=110, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text="PLN", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkButton(row, text="OK", width=34, height=28, fg_color="transparent", text_color=COLOR_SUCCESS, hover_color=COLOR_BORDER, command=lambda tid=t["id"], n=name_var, a=amt_var: self.save_edit(tid, n, a)).pack(side="right", padx=2, pady=5)
            ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda tid=t["id"]: self.delete_target(tid)).pack(side="right", padx=5, pady=5)
            ctk.CTkFrame(self.targets_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x")



class SharedGoalsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 24))
        ctk.CTkLabel(hdr, text=t("nav.shared_goals"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        
        self.btn_edit = ctk.CTkButton(
            hdr, text=t("Edit"), width=100, height=36,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
            font=FONT_LABEL, command=self.toggle_edit
        )
        self.btn_edit.pack(side="right")
        
        self.editing = False
        
        # Scrollable area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.cell_vars = {}
        
        self.refresh()
        
    def toggle_edit(self):
        if self.editing:
            # Save data
            for (goal_id, mk, pid, fld), var in self.cell_vars.items():
                try:
                    val = float(var.get().replace(",", "."))
                except:
                    val = 0.0
                
                # find goal
                for g in self.goals:
                    if g["id"] == goal_id:
                        g["data"][mk][pid][fld] = val
                        break
            
            dm.save_shared_goals(self.goals)
            self.editing = False
            self.btn_edit.configure(text=t("Edit"), fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_2)
            self.refresh()
        else:
            self.editing = True
            self.btn_edit.configure(text=t("Save"), fg_color=COLOR_SUCCESS, text_color=COLOR_SURFACE, hover_color=COLOR_MET_PLAN, border_width=0)
            self.refresh()
            
    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.cell_vars = {}
        self.goals = dm.get_shared_goals()
        
        for goal in self.goals:
            card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER)
            card.pack(fill="x", pady=(0, 24))
            
            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=24, pady=(20, 10))
            ctk.CTkLabel(hdr, text=goal["name"], font=FONT_SECTION, text_color=COLOR_TEXT).pack(side="left")
            
            # Table container
            grid = ctk.CTkFrame(card, fg_color="transparent")
            grid.pack(fill="x", padx=24, pady=(0, 24))
            
            persons = goal["persons"]
            if not persons:
                continue
                
            # Headers
            ctk.CTkLabel(grid, text="Month", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=80, anchor="w").grid(row=0, column=0, padx=5, pady=5)
            col_idx = 1
            for p in persons:
                ctk.CTkLabel(grid, text=p["name"], font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=160).grid(row=0, column=col_idx, columnspan=2, padx=5, pady=5)
                ctk.CTkLabel(grid, text=t("shared.planned"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=1, column=col_idx, padx=2, pady=2)
                ctk.CTkLabel(grid, text=t("shared.actual"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=1, column=col_idx+1, padx=2, pady=2)
                col_idx += 2
            ctk.CTkLabel(grid, text="Combined", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=160).grid(row=0, column=col_idx, columnspan=2, padx=5, pady=5)
            ctk.CTkLabel(grid, text=t("shared.planned"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=1, column=col_idx, padx=2, pady=2)
            ctk.CTkLabel(grid, text=t("shared.actual"), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=1, column=col_idx+1, padx=2, pady=2)
            col_idx += 2
            ctk.CTkLabel(grid, text=t("shared.status"), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=0, column=col_idx, rowspan=2, padx=5, pady=5)
            
            months = sorted(goal["data"].keys())
            row_idx = 2
            
            tot_planned = {p["id"]: 0.0 for p in persons}
            tot_actual = {p["id"]: 0.0 for p in persons}
            
            for mk in months:
                try:
                    d = datetime.strptime(mk, "%Y-%m")
                    months_pl = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
                    mk_display = f"{months_pl[d.month-1]}.{str(d.year)[-2:]}"
                except:
                    mk_display = mk
                    
                ctk.CTkLabel(grid, text=mk_display, font=FONT_BODY, text_color=COLOR_TEXT, width=80, anchor="w").grid(row=row_idx, column=0, padx=5, pady=5)
                
                col_idx = 1
                month_planned_sum = 0
                month_actual_sum = 0
                
                for p in persons:
                    pid = p["id"]
                    pdata = goal["data"][mk].get(pid, {"planned": 0.0, "actual": 0.0})
                    
                    tot_planned[pid] += pdata["planned"]
                    tot_actual[pid] += pdata["actual"]
                    month_planned_sum += pdata["planned"]
                    month_actual_sum += pdata["actual"]
                    
                    if self.editing:
                        v_plan = ctk.StringVar(value=f"{pdata['planned']:.0f}")
                        v_act = ctk.StringVar(value=f"{pdata['actual']:.0f}")
                        self.cell_vars[(goal["id"], mk, pid, "planned")] = v_plan
                        self.cell_vars[(goal["id"], mk, pid, "actual")] = v_act
                        
                        ctk.CTkEntry(grid, textvariable=v_plan, font=FONT_MONO, width=70, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).grid(row=row_idx, column=col_idx, padx=2, pady=5)
                        ctk.CTkEntry(grid, textvariable=v_act, font=FONT_MONO, width=70, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).grid(row=row_idx, column=col_idx+1, padx=2, pady=5)
                    else:
                        ctk.CTkLabel(grid, text=f"{pdata['planned']:,.0f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=80).grid(row=row_idx, column=col_idx, padx=2, pady=5)
                        act_color = COLOR_SUCCESS if pdata["actual"] >= pdata["planned"] else COLOR_WARNING if pdata["actual"] > 0 else COLOR_TEXT
                        ctk.CTkLabel(grid, text=f"{pdata['actual']:,.0f}", font=FONT_MONO, text_color=act_color, width=80).grid(row=row_idx, column=col_idx+1, padx=2, pady=5)
                    col_idx += 2
                
                # Combined column
                ctk.CTkLabel(grid, text=f"{month_planned_sum:,.0f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=80).grid(row=row_idx, column=col_idx, padx=2, pady=5)
                comb_color = COLOR_SUCCESS if month_actual_sum >= month_planned_sum and month_planned_sum > 0 else COLOR_WARNING if month_actual_sum > 0 else COLOR_TEXT
                ctk.CTkLabel(grid, text=f"{month_actual_sum:,.0f}", font=FONT_MONO, text_color=comb_color, width=80).grid(row=row_idx, column=col_idx+1, padx=2, pady=5)
                col_idx += 2

                # Status indicator
                status_color = COLOR_SUCCESS if month_actual_sum >= month_planned_sum and month_planned_sum > 0 else COLOR_ERROR if month_actual_sum > 0 else COLOR_BORDER
                indicator = ctk.CTkFrame(grid, width=16, height=16, corner_radius=8, fg_color=status_color)
                indicator.grid(row=row_idx, column=col_idx, padx=5, pady=5)
                
                row_idx += 1
                
            # Totals Row
            # Draw separator
            sep = ctk.CTkFrame(grid, height=1, fg_color=COLOR_BORDER)
            sep.grid(row=row_idx, column=0, columnspan=col_idx+1, sticky="ew", pady=(10, 5))
            row_idx += 1
            
            ctk.CTkLabel(grid, text=t("shared.totals"), font=FONT_TITLE, text_color=COLOR_TEXT, width=80, anchor="w").grid(row=row_idx, column=0, padx=5, pady=5)
            col_idx = 1
            total_planned_all = sum(tot_planned.values())
            total_actual_all = sum(tot_actual.values())
            for p in persons:
                pid = p["id"]
                ctk.CTkLabel(grid, text=f"{tot_planned[pid]:,.0f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=80).grid(row=row_idx, column=col_idx, padx=2, pady=5)
                act_color = COLOR_SUCCESS if tot_actual[pid] >= tot_planned[pid] and tot_planned[pid] > 0 else COLOR_TEXT
                ctk.CTkLabel(grid, text=f"{tot_actual[pid]:,.0f}", font=FONT_MONO, text_color=act_color, width=80).grid(row=row_idx, column=col_idx+1, padx=2, pady=5)
                col_idx += 2
            
            # Combined Totals
            ctk.CTkLabel(grid, text=f"{total_planned_all:,.0f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=80).grid(row=row_idx, column=col_idx, padx=2, pady=5)
            comb_tot_color = COLOR_SUCCESS if total_actual_all >= total_planned_all and total_planned_all > 0 else COLOR_TEXT
            ctk.CTkLabel(grid, text=f"{total_actual_all:,.0f}", font=FONT_MONO, text_color=comb_tot_color, width=80).grid(row=row_idx, column=col_idx+1, padx=2, pady=5)

class HelpView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self._sections = []  # [(heading, content_text, frame_widget)]

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(hdr, text=t("help.title"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")

        # Search box
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        search = ctk.CTkEntry(hdr, textvariable=self._search_var, placeholder_text=t("help.search_placeholder"), width=220)
        search.pack(side="right")

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self._render_markdown()

    def _load_help_text(self):
        filename = "HELP.pl.md" if get_language() == "pl" else "HELP.md"
        help_path = Path(__file__).parent / filename
        try:
            return help_path.read_text(encoding="utf-8")
        except:
            return f"# {t('help.title')}\n\n{t('help.file_not_found')}"

    def _render_markdown(self):
        text = self._load_help_text()
        lines = text.split("\n")
        current_heading = ""
        current_lines = []
        sections = []

        def flush():
            if current_heading or current_lines:
                sections.append((current_heading, "\n".join(current_lines)))

        for line in lines:
            if line.startswith("# "):
                flush()
                current_heading = line[2:].strip()
                current_lines = []
            elif line.startswith("## "):
                flush()
                current_heading = line[3:].strip()
                current_lines = []
            elif line.startswith("### "):
                flush()
                current_heading = line[4:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        flush()

        for heading, body in sections:
            frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
            frame.pack(fill="x", pady=(8, 0), anchor="w")

            if heading:
                ctk.CTkLabel(frame, text=heading, font=FONT_TITLE, text_color=COLOR_PRIMARY, anchor="w").pack(fill="x")

            if body.strip():
                rendered = self._format_body(body.strip())
                lbl = ctk.CTkLabel(frame, text=rendered, font=FONT_BODY, text_color=COLOR_TEXT, anchor="w", justify="left", wraplength=700)
                lbl.pack(fill="x", padx=(10, 0), pady=(2, 0))

            self._sections.append((heading.lower(), body.lower(), frame))

    def _format_body(self, text):
        """Light formatting: strip markdown bold/table syntax for display."""
        lines = []
        for line in text.split("\n"):
            line = line.replace("**", "")
            if line.startswith("- "):
                line = "  • " + line[2:]
            elif line.startswith("| ") and "---" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                line = "  " + "  |  ".join(cells)
            elif line.startswith("|") and "---" in line:
                continue
            elif line.startswith("---"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _filter(self):
        query = self._search_var.get().lower().strip()
        any_visible = False
        for heading, body, frame in self._sections:
            if not query or query in heading or query in body:
                frame.pack(fill="x", pady=(8, 0), anchor="w")
                any_visible = True
            else:
                frame.pack_forget()
        # Show "no results" if nothing matches
        if hasattr(self, "_no_results_lbl"):
            self._no_results_lbl.destroy()
        if not any_visible and query:
            self._no_results_lbl = ctk.CTkLabel(self._scroll, text=t("help.no_results"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED)
            self._no_results_lbl.pack(pady=20)


    def refresh(self):
        pass  # Static content, no refresh needed


if __name__ == "__main__":
    app = FlorinApp()
    app.mainloop()
