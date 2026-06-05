import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import data_manager as dm
from datetime import datetime, date
import uuid
import json
import os
import sys
from i18n import t, tr_text as tx, month_full, get_language
from theme import *
from main import ui_text, format_money, signed_money, make_pill, make_card, display_name, display_category_name, category_color, parse_money, month_year_label, item_count, weekday_abbr

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

