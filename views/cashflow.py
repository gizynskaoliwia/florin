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
        mid = ctk.CTkFrame(month_box, fg_color="transparent")
        mid.pack(side="left", padx=6, pady=2)
        self.month_lbl = ctk.CTkLabel(mid, text="", font=FONT_LABEL, text_color=COLOR_TEXT)
        self.month_lbl.pack(anchor="center")
        self.month_sub_lbl = ctk.CTkLabel(mid, text="", font=FONT_MONO_SM, text_color=COLOR_TEXT_MUTED)
        self.month_sub_lbl.pack(anchor="center")
        ctk.CTkButton(month_box, text="›", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_SURFACE_2, command=lambda: self.controller.change_month(1)).pack(side="left", padx=(0, 4), pady=3)
        self.edit_btn = ctk.CTkButton(actions, text=ui_text("✎ Edit", "✎ Edytuj"), width=100, height=34, fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT, command=self.toggle_edit)
        self.edit_btn.pack(side="left", padx=(0, 8))
        self.add_target_btn = ctk.CTkButton(
            actions,
            text=ui_text("+ Add buffer", "+ Dodaj bufor"),
            width=120,
            height=34,
            fg_color=COLOR_PRIMARY,
            text_color=COLOR_SURFACE,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.add_target_dialog,
        )
        self.add_target_btn.pack(side="left")
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
            self.edit_btn.configure(text=ui_text("✎ Edit", "✎ Edytuj"), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_SOFT)
        else:
            self.editing = True
            self.edit_btn.configure(text=tx("✓ Done"), fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
        self.build()

    def build(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        data = self.controller.data
        targets = data.get("cashflow_targets")
        if targets is None:
            targets = dm.get_cashflow_targets(data)
            data["cashflow_targets"] = targets
        cf = dm.get_cashflow(data)
        self.month_lbl.configure(text=month_year_label(self.controller.current_month, upper=True))
        self.month_sub_lbl.configure(text=dm.get_budget_period_str(self.controller.current_month))

        self.balance_vars = {}
        self.target_vars = {}
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
            empty_box = ctk.CTkFrame(empty, fg_color="transparent")
            empty_box.pack(padx=24, pady=24, fill="x")
            ctk.CTkLabel(empty_box, text=ui_text("No buffer targets for this period yet.", "Brak celów przepływów w tym okresie."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkButton(empty_box, text=ui_text("+ Add buffer", "+ Dodaj bufor"), width=120, height=30, fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER, command=self.add_target_dialog).pack(side="right")

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

            if self.editing:
                ctk.CTkButton(head, text="×", width=24, height=24, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, font=(FONT_BODY_FAMILY, 14, "bold"), command=lambda t_id=tid: self.delete_target(t_id)).pack(side="right")
                ctk.CTkButton(head, text="✎", width=24, height=24, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, font=(FONT_BODY_FAMILY, 12), command=lambda t_id=tid: self.edit_target_dialog(t_id)).pack(side="right", padx=(0, 2))

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
            target_var = ctk.StringVar(value=f"{target_amount:.2f}")
            self.target_vars[tid] = target_var
            if self.editing:
                tgt_entry = ctk.CTkEntry(row_target, textvariable=target_var, font=FONT_MONO, width=118, height=30, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, justify="right")
                tgt_entry.pack(side="right")
                tgt_entry.bind("<KeyRelease>", self.calculate)
                tgt_entry.bind("<FocusOut>", lambda e, v=target_var, tid_=tid: self.on_target_blur(v, tid_))
            else:
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

    def on_target_blur(self, var, tid):
        val = var.get().replace(",", ".")
        try:
            var.set(f"{float(val):.2f}")
        except:
            pass
        self.calculate()

    def calculate(self, event=None):
        try:
            data = self.controller.data
            targets = data.get("cashflow_targets", [])
            cf = dm.get_cashflow(data)

            # Part 1: calculate top-ups
            total_topup = 0.0
            for t in targets:
                tid = t["id"]
                var = self.balance_vars.get(tid)
                acct = cf.setdefault("current_accounts", {}).setdefault(tid, {"balance": 0.0, "updated_at": ""})
                if var:
                    balance = parse_money(var.get())
                    acct["balance"] = balance
                else:
                    balance = acct.get("balance", 0.0)

                tgt_var = self.target_vars.get(tid)
                if tgt_var:
                    target_amount = parse_money(tgt_var.get())
                    t["target"] = target_amount
                else:
                    target_amount = t.get("target", 0.0)

                topup = max(0.0, target_amount - balance)
                total_topup += topup
                if tid in self.topup_lbls:
                    self.topup_lbls[tid].configure(
                        text=format_money(topup, suffix=False) if topup > 0 else ui_text("funded", "uzupełnione"),
                        text_color=COLOR_PRIMARY if topup > 0 else COLOR_SUCCESS,
                    )
                if tid in self.progress_bars:
                    ratio = min(balance / target_amount, 1.0) if target_amount > 0 else 1.0
                    self.progress_bars[tid].set(ratio)
                    self.progress_bars[tid].configure(progress_color=COLOR_PRIMARY if topup > 0 else COLOR_SUCCESS)
                if tid in self.timestamp_lbls:
                    ratio = min(balance / target_amount, 1.0) if target_amount > 0 else 1.0
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

    def add_target_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(ui_text("Add Buffer Target", "Dodaj cel przepływu"))
        dialog.geometry("380x320")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        period_str = dm.get_budget_period_str(self.controller.current_month)
        ctk.CTkLabel(dialog, text=f"{ui_text('Period', 'Okres')}: {month_year_label(self.controller.current_month)} ({period_str})", font=FONT_SMALL, text_color=COLOR_PRIMARY).pack(fill="x", padx=20, pady=(15, 8))

        ctk.CTkLabel(dialog, text=ui_text("Buffer Name:", "Nazwa bufora / konta:"), anchor="w").pack(fill="x", padx=20, pady=(4, 2))
        name_e = ctk.CTkEntry(dialog)
        name_e.pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=ui_text("Target Amount (PLN):", "Cel minimum (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        target_e = ctk.CTkEntry(dialog)
        target_e.pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=ui_text("Current Balance (optional):", "Aktualne saldo (opcjonalnie):"), anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        balance_e = ctk.CTkEntry(dialog)
        balance_e.pack(fill="x", padx=20)

        def save():
            name = name_e.get().strip()
            try:
                target_val = float(target_e.get().replace(",", "."))
            except:
                return
            if not name or target_val <= 0:
                return
            bal_val = 0.0
            if balance_e.get().strip():
                try:
                    bal_val = float(balance_e.get().replace(",", "."))
                except:
                    pass
            tid = str(uuid.uuid4())
            new_item = {"id": tid, "name": name, "target": target_val}
            self.controller.data.setdefault("cashflow_targets", []).append(new_item)
            cf = dm.get_cashflow(self.controller.data)
            cf.setdefault("current_accounts", {})[tid] = {
                "balance": bal_val,
                "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M") if bal_val else ""
            }
            self.controller.save_data()
            dialog.destroy()
            self.build()

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(20, 15))
        ctk.CTkButton(btns, text=tx("Cancel"), fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btns, text=tx("Save"), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=save).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def edit_target_dialog(self, tid):
        targets = self.controller.data.get("cashflow_targets", [])
        t_item = next((t for t in targets if t["id"] == tid), None)
        if not t_item:
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title(ui_text("Edit Buffer Target", "Edytuj cel przepływu"))
        dialog.geometry("380x280")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        period_str = dm.get_budget_period_str(self.controller.current_month)
        ctk.CTkLabel(dialog, text=f"{ui_text('Period', 'Okres')}: {month_year_label(self.controller.current_month)} ({period_str})", font=FONT_SMALL, text_color=COLOR_PRIMARY).pack(fill="x", padx=20, pady=(15, 8))

        ctk.CTkLabel(dialog, text=ui_text("Buffer Name:", "Nazwa bufora / konta:"), anchor="w").pack(fill="x", padx=20, pady=(4, 2))
        name_e = ctk.CTkEntry(dialog)
        name_e.insert(0, t_item["name"])
        name_e.pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text=ui_text("Target Amount (PLN):", "Cel minimum (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        target_e = ctk.CTkEntry(dialog)
        target_e.insert(0, f"{t_item['target']:.2f}")
        target_e.pack(fill="x", padx=20)

        def save():
            name = name_e.get().strip()
            try:
                target_val = float(target_e.get().replace(",", "."))
            except:
                return
            if not name or target_val <= 0:
                return
            t_item["name"] = name
            t_item["target"] = target_val
            self.controller.save_data()
            dialog.destroy()
            self.build()

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(20, 15))
        ctk.CTkButton(btns, text=tx("Cancel"), fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btns, text=tx("Save"), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=save).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def delete_target(self, tid):
        targets = self.controller.data.get("cashflow_targets", [])
        t_item = next((t for t in targets if t["id"] == tid), None)
        name = t_item["name"] if t_item else ""
        period_str = dm.get_budget_period_str(self.controller.current_month)
        if not messagebox.askyesno(
            ui_text("Delete target", "Usuń cel"),
            ui_text(f"Are you sure you want to delete buffer '{name}' for period {period_str}?", f"Czy na pewno chcesz usunąć cel '{name}' dla okresu {period_str}?")
        ):
            return
        self.controller.data["cashflow_targets"] = [t for t in targets if t["id"] != tid]
        cf = dm.get_cashflow(self.controller.data)
        if "current_accounts" in cf and tid in cf["current_accounts"]:
            del cf["current_accounts"][tid]
        self.controller.save_data()
        self.build()

    def refresh(self):
        self.build()

