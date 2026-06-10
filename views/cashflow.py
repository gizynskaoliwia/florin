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
        self.saved_actual_var = ctk.StringVar(value="0.00")
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
        saved_actual = cf.get("saved_actual", 0.0)
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
        self.saved_actual_var.set(f"{cf.get('saved_actual', 0.0):.2f}")

        rows = [
            (tx("Calculated"), format_money(shared_calc, suffix=False), format_money(saved_calc, suffix=False)),
            (tx("Assumed"), self.shared_assumed_var, self.saved_assumed_var),
            (tx("Actual"), self.shared_actual_var, self.saved_actual_var),
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
            elif self.editing and row_idx in (2, 3):
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

            saved_actual = parse_money(self.saved_actual_var.get())
            cf["saved_actual"] = saved_actual

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
                    text=f"{ui_text('Net', 'Netto')} {format_money(net_income, suffix=False)} − {ui_text('top-ups', 'uzupełn.')} {format_money(total_topup, suffix=False)} − {ui_text('shared', 'wspólne')} {format_money(shared_actual, suffix=False)}"
                )

            self.controller.save_data()
        except:
            pass

    def refresh(self):
        self.build()

