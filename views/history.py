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

class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.year = int(controller.current_month.split("-")[0])
        self.expanded_month = None
        self.search_var = ctk.StringVar()
        self._search_job = None
        self.search_var.trace_add("write", lambda *_: self._schedule_refresh())
        self._init_ui()

    def _schedule_refresh(self):
        if self._search_job is not None:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self.refresh)

    def _init_ui(self):
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
        exp_cats = {c["id"]: display_name(c["name"]) for c in dm.get_global_expense_categories()}
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

