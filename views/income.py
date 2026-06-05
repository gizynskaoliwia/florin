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
        
        # Performance pools
        self._item_rows_pool = []
        self._cat_rows_pool = []
        
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

    def _get_pooled_item_row(self, index, cols):
        if index < len(self._item_rows_pool):
            return self._item_rows_pool[index]
            
        row = ctk.CTkFrame(self.items_scroll, fg_color="transparent", height=64)
        row.pack_propagate(False)
        for idx, (_, weight, _) in enumerate(cols):
            row.grid_columnconfigure(idx, weight=weight)
            
        item_box = ctk.CTkFrame(row, fg_color="transparent")
        item_box.grid(row=0, column=0, sticky="ew", padx=(20, 10), pady=9)
        title_lbl = ctk.CTkLabel(item_box, text="", font=FONT_TITLE, text_color=COLOR_TEXT)
        title_lbl.pack(anchor="w")
        meta_lbl = ctk.CTkLabel(item_box, text="", font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED)
        meta_lbl.pack(anchor="w", pady=(3, 0))
        
        type_pill = ctk.CTkFrame(row, border_width=1, corner_radius=RADIUS_BUTTON)
        type_pill.grid(row=0, column=1, padx=10, pady=17)
        type_lbl = ctk.CTkLabel(type_pill, text="", font=FONT_SMALL, width=86, height=28)
        type_lbl.pack()
        
        amount_lbl = ctk.CTkLabel(row, text="", font=FONT_MONO, anchor="e")
        amount_lbl.grid(row=0, column=2, sticky="ew", padx=10, pady=18)
        
        badge = make_pill(row, " ", COLOR_PRIMARY, width=128, height=28)
        badge.grid(row=0, column=3, sticky="w", padx=10, pady=18)
        prop_lbl = ctk.CTkLabel(row, text="", font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED, anchor="w")
        prop_lbl.grid(row=0, column=3, sticky="w", padx=10, pady=18)
        
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.grid(row=0, column=4, sticky="e", padx=(8, 20), pady=14)
        edit_btn = ctk.CTkButton(action_frame, text="✎", width=30, height=30, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER)
        del_btn = ctk.CTkButton(action_frame, text="×", width=30, height=30, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_EXPENSE_SOFT)
        dot_lbl = ctk.CTkLabel(action_frame, text="", font=FONT_MONO_SM_BOLD, width=24)
        
        sep = ctk.CTkFrame(self.items_scroll, height=1, fg_color=COLOR_BORDER)
        
        widgets = {
            "row": row, "title_lbl": title_lbl, "meta_lbl": meta_lbl,
            "type_pill": type_pill, "type_lbl": type_lbl,
            "amount_lbl": amount_lbl, "badge": badge, "prop_lbl": prop_lbl,
            "edit_btn": edit_btn, "del_btn": del_btn, "dot_lbl": dot_lbl, "sep": sep,
            "action_frame": action_frame
        }
        self._item_rows_pool.append(widgets)
        return widgets

    def build_items_list(self):
        def display_type(t): return tx("Addition") if t == "addition" else tx("Deduction")

        for w in self._item_rows_pool:
            w["row"].pack_forget()
            w["sep"].pack_forget()
            
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

        cols = [
            (ui_text("Item", "Pozycja"), 4, "w"),
            (ui_text("Type", "Typ"), 2, "center"),
            (ui_text("Amount", "Kwota"), 2, "e"),
            (ui_text("Target", "Cel"), 2, "w"),
            ("", 1, "center"),
        ]

        if not hasattr(self, "_items_header"):
            self._items_header = ctk.CTkFrame(self.items_scroll, fg_color=COLOR_BG)
            self._items_header.pack(fill="x")
            for idx, (label, weight, anchor) in enumerate(cols):
                self._items_header.grid_columnconfigure(idx, weight=weight)
                ctk.CTkLabel(self._items_header, text=label.upper(), font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, anchor=anchor).grid(row=0, column=idx, sticky="ew", padx=(20 if idx == 0 else 10, 20 if idx == len(cols) - 1 else 10), pady=10)
        else:
            self._items_header.pack(fill="x")

        if hasattr(self, "_no_items_lbl"):
            self._no_items_lbl.pack_forget()

        if not items:
            if not hasattr(self, "_no_items_lbl"):
                self._no_items_lbl = ctk.CTkLabel(
                    self.items_scroll,
                    text=ui_text("No income items yet. Add an invoice or deduction to start.", "Brak pozycji przychodów. Dodaj fakturę albo odliczenie."),
                    font=FONT_BODY,
                    text_color=COLOR_TEXT_MUTED,
                )
            self._no_items_lbl.pack(anchor="w", padx=20, pady=18)
            return

        for i, item in enumerate(items):
            is_add = item["type"] == "addition"
            w = self._get_pooled_item_row(i, cols)
            w["row"].pack(fill="x")
            
            sign = "+" if is_add else "−"
            sign_color = COLOR_SUCCESS if is_add else COLOR_ERROR
            
            w["title_lbl"].configure(text=display_name(item["name"]))
            w["meta_lbl"].configure(text=ui_text("monthly income item", "pozycja miesięczna"))
            
            w["type_pill"].configure(fg_color=COLOR_INCOME_SOFT if is_add else COLOR_EXPENSE_SOFT, border_color=COLOR_SUCCESS if is_add else COLOR_ERROR)
            w["type_lbl"].configure(text=display_type(item["type"]), text_color=sign_color)
            
            w["amount_lbl"].configure(text=f"{sign} {format_money(item['amount'], suffix=False)}", text_color=sign_color)
            
            cat_id = item.get("category_id")
            if cat_id and cat_id in cats:
                cat = cats[cat_id]
                w["badge"].grid(row=0, column=3, sticky="w", padx=10, pady=18)
                w["badge"].configure(border_color=category_color(cat))
                w["badge"].winfo_children()[1].configure(text=display_category_name(cat))
                w["badge"].winfo_children()[0].configure(fg_color=category_color(cat))
                w["prop_lbl"].grid_forget()
            else:
                w["badge"].grid_forget()
                w["prop_lbl"].grid(row=0, column=3, sticky="w", padx=10, pady=18)
                w["prop_lbl"].configure(text=ui_text("proportional", "proporcjonalnie"))
                
            w["edit_btn"].configure(command=lambda iid=item["id"]: self.edit_item(iid))
            w["del_btn"].configure(command=lambda iid=item["id"]: self.delete_item(iid))
            
            if self.editing:
                w["edit_btn"].pack(side="left")
                w["del_btn"].pack(side="left")
                w["dot_lbl"].pack_forget()
            else:
                w["edit_btn"].pack_forget()
                w["del_btn"].pack_forget()
                w["dot_lbl"].pack(side="right")
                w["dot_lbl"].configure(text="●" if is_add else "○", text_color=sign_color)
                
            w["sep"].pack(fill="x")

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

