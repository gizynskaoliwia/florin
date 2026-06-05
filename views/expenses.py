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
from main import ui_text, format_money, signed_money, make_pill, make_card, display_name, display_category_name, category_color, parse_money, month_year_label, item_count, weekday_abbr, month_abbr

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
        self.render_limit = 50
        self.search_var = ctk.StringVar()
        self._search_job = None
        self._expense_rows = []
        self._header_rows = []
        self.search_var.trace_add("write", lambda *_: self._schedule_refresh())

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

    def _schedule_refresh(self):
        if self._search_job is not None:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self.refresh)

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
        exp_cats = dm.get_global_expense_categories()
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
        split_cats = dm.get_global_categories()
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

        save_btn = ctk.CTkButton(dialog, text=tx("Save"))
        
        def save():
            save_btn.configure(state="disabled")
            try:
                amt = float(amt_entry.get().replace(",", "."))
                if amt <= 0:
                    save_btn.configure(state="normal")
                    return
            except:
                save_btn.configure(state="normal")
                return
            date_val = date_entry.get().strip()
            try:
                datetime.strptime(date_val, "%d/%m/%Y")
                date_error_lbl.configure(text="")
            except ValueError:
                date_error_lbl.configure(text=tx("Invalid date. Use DD/MM/YYYY format."))
                save_btn.configure(state="normal")
                return
            exp_cats_current = dm.get_global_expense_categories()
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
            self._schedule_refresh()

        save_btn.configure(command=save)
        save_btn.pack(fill="x", padx=20, pady=15)

    def _on_exp_cat_select(self, val, exp_cat_var, exp_cat_menu, parent_dialog, data):
        create_marker = tx("+ Create new category...")
        if val != create_marker:
            return
        d = ctk.CTkInputDialog(text=tx("New category name:"), title=tx("Create Category"))
        name = d.get_input()
        if name and name.strip():
            dm.add_expense_category(data, name.strip())
            self.controller.save_data()
            exp_cats = dm.get_global_expense_categories()
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
            for cat in dm.get_global_expense_categories():
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
    def refresh(self, reset_limit=True):
        if reset_limit:
            self.render_limit = 50
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
        for cat in dm.get_global_categories():
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

    def _get_pooled_row(self, index):
        if index < len(self._expense_rows):
            return self._expense_rows[index]
        
        row = ctk.CTkFrame(self.scroll, corner_radius=0, border_width=0)
        accent = ctk.CTkFrame(row, width=3)
        accent.pack(side="left", fill="y")
        icon_box = ctk.CTkFrame(row, width=28, height=28, fg_color=COLOR_SURFACE_2, border_width=1, border_color=COLOR_BORDER, corner_radius=8)
        icon_box.pack(side="left", padx=(17, 0), pady=12)
        icon_box.pack_propagate(False)
        icon_lbl = ctk.CTkLabel(icon_box, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED)
        icon_lbl.pack(expand=True)
        
        body = ctk.CTkFrame(row, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        title_lbl = ctk.CTkLabel(body, text="", font=FONT_TITLE, text_color=COLOR_TEXT, anchor="w")
        title_lbl.pack(anchor="w")
        meta_lbl = ctk.CTkLabel(body, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w")
        meta_lbl.pack(anchor="w")
        
        tag_row = ctk.CTkFrame(body, fg_color="transparent")
        tag_row.pack(anchor="w", pady=(4, 0))
        tag_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(tag_row, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, fg_color=COLOR_SURFACE_2, corner_radius=6)
            lbl.pack(side="left", padx=(0, 4), ipadx=6, ipady=2)
            tag_labels.append(lbl)
            
        amount_col = ctk.CTkFrame(row, fg_color="transparent")
        amount_col.pack(side="right", padx=(12, 20))
        amount_lbl = ctk.CTkLabel(amount_col, text="", font=FONT_MONO, text_color=COLOR_EXPENSE)
        amount_lbl.pack(anchor="e")
        
        pill = make_pill(row, " ", COLOR_PRIMARY, width=120, height=26)
        pill.pack(side="right")
        pill_lbl = pill.winfo_children()[1]
        pill_dot = pill.winfo_children()[0]
        
        widgets = {
            "row": row, "accent": accent, "icon_lbl": icon_lbl,
            "title_lbl": title_lbl, "meta_lbl": meta_lbl,
            "tag_row": tag_row, "tag_labels": tag_labels,
            "amount_lbl": amount_lbl, "pill": pill, "pill_lbl": pill_lbl, "pill_dot": pill_dot,
            "body": body, "amount_col": amount_col
        }
        self._expense_rows.append(widgets)
        return widgets

    def _get_pooled_header(self, index):
        if index < len(self._header_rows):
            return self._header_rows[index]
            
        hdr = ctk.CTkFrame(self.scroll, fg_color=COLOR_BG, corner_radius=0)
        lbl_left = ctk.CTkLabel(hdr, text="", font=FONT_LABEL)
        lbl_left.pack(side="left", padx=20, pady=8)
        lbl_right = ctk.CTkLabel(hdr, text="", font=FONT_MONO, text_color=COLOR_TEXT_MUTED)
        lbl_right.pack(side="right", padx=20)
        
        widgets = {"hdr": hdr, "lbl_left": lbl_left, "lbl_right": lbl_right}
        self._header_rows.append(widgets)
        return widgets

    def _build_expense_list(self, expenses):
        # Hide all existing rows instead of destroying
        for w in self._expense_rows: w["row"].pack_forget()
        for w in self._header_rows: w["hdr"].pack_forget()
        for w in self.scroll.winfo_children():
            if w not in [r["row"] for r in self._expense_rows] and w not in [h["hdr"] for h in self._header_rows]:
                w.destroy()
                
        if not expenses:
            ctk.CTkLabel(self.scroll, text=tx("No expenses for this month."), font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=42)
            return

        if self.group_mode == "category":
            self._build_expense_list_by_category(expenses)
            return

        limited_expenses = expenses[:self.render_limit]
        current_day = None
        row_idx = 0
        hdr_idx = 0
        
        for exp in limited_expenses:
            day = exp.get("date", "")
            if day != current_day:
                current_day = day
                total = sum(e["amount"] for e in expenses if e.get("date", "") == day)
                d = self._date_key(exp)
                label_day = f"{weekday_abbr(d.weekday())} · {d.day:02d} {month_full(d.month)}"
                day_count = sum(1 for e in expenses if e.get("date", "") == day)
                
                h_widgets = self._get_pooled_header(hdr_idx)
                hdr_idx += 1
                h_widgets["hdr"].pack(fill="x", padx=0, pady=(10, 0))
                h_widgets["lbl_left"].configure(text=label_day.upper(), text_color=COLOR_TEXT_MUTED)
                h_widgets["lbl_right"].configure(text=f"{item_count(day_count)} · - {format_money(total)}")

            self._configure_expense_row(exp, row_idx)
            row_idx += 1

        if len(expenses) > self.render_limit:
            btn = ctk.CTkButton(self.scroll, text=tx("Load more..."), fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._load_more)
            btn.pack(pady=20)

    def _load_more(self):
        self.render_limit += 50
        self.refresh(reset_limit=False)

    def _build_expense_list_by_category(self, expenses):
        source_order = dm.get_global_categories()
        savings_bucket = {"id": "savings", "name": tx("Savings goals"), "color": COLOR_SUCCESS}
        buckets = []
        for cat in source_order:
            cat_expenses = [e for e in expenses if e.get("category_id") == cat["id"] and not e.get("savings_category_id")]
            if cat_expenses:
                buckets.append((cat, cat_expenses))
        savings_expenses = [e for e in expenses if e.get("savings_category_id")]
        if savings_expenses:
            buckets.append((savings_bucket, savings_expenses))

        row_idx = 0
        hdr_idx = 0

        for cat, cat_expenses in buckets:
            total = sum(e["amount"] for e in cat_expenses)
            h_widgets = self._get_pooled_header(hdr_idx)
            hdr_idx += 1
            h_widgets["hdr"].pack(fill="x", padx=0, pady=(10, 0))
            h_widgets["lbl_left"].configure(text=display_category_name(cat).upper(), text_color=category_color(cat))
            h_widgets["lbl_right"].configure(text=f"{item_count(len(cat_expenses))} · - {format_money(total)}")
            
            for exp in sorted(cat_expenses, key=lambda e: self._date_key(e), reverse=True)[:self.render_limit]:
                self._configure_expense_row(exp, row_idx)
                row_idx += 1

        if len(expenses) > self.render_limit:
            btn = ctk.CTkButton(self.scroll, text=tx("Load more..."), fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._load_more)
            btn.pack(pady=20)

    def _configure_expense_row(self, exp, row_idx):
        w = self._get_pooled_row(row_idx)
        w["row"].pack(fill="x")
        
        selected = exp["id"] == self.selected_expense_id
        w["row"].configure(fg_color=COLOR_PRIMARY_SOFT if selected else COLOR_SURFACE)
        w["accent"].configure(fg_color=COLOR_PRIMARY if selected else COLOR_BORDER)
        
        source_cat = self._source_category(exp)
        icon = self._source_icon(source_cat)
        w["icon_lbl"].configure(text=icon)
        
        title = exp.get("description") or self._expense_category_name(exp)
        w["title_lbl"].configure(text=title)
        
        meta = f"{self._expense_category_name(exp)} · {self._source_name(exp)}"
        w["meta_lbl"].configure(text=meta)
        
        tags = exp.get("tags", [])[:3]
        if tags:
            w["tag_row"].pack(anchor="w", pady=(4, 0))
            for i, lbl in enumerate(w["tag_labels"]):
                if i < len(tags):
                    lbl.configure(text=tags[i])
                    lbl.pack(side="left", padx=(0, 4), ipadx=6, ipady=2)
                else:
                    lbl.pack_forget()
        else:
            w["tag_row"].pack_forget()
            
        w["amount_lbl"].configure(text=f"- {format_money(exp['amount'], suffix=False)}")
        
        if source_cat:
            w["pill"].pack(side="right")
            w["pill"].configure(border_color=category_color(source_cat))
            w["pill_lbl"].configure(text=display_category_name(source_cat))
            w["pill_dot"].configure(fg_color=category_color(source_cat))
        else:
            w["pill"].pack_forget()
            
        def bind_click(widget):
            widget.bind("<Button-1>", lambda _e, exp_id=exp["id"]: self._select_expense(exp_id))
            
        bind_click(w["row"])
        bind_click(w["body"])
        bind_click(w["amount_col"])
        bind_click(w["title_lbl"])
        bind_click(w["meta_lbl"])
        bind_click(w["amount_lbl"])

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
        exp_cats = {c["id"]: c["name"] for c in dm.get_global_expense_categories()}
        return display_name(exp_cats.get(exp.get("expense_category_id"), "Uncategorized"))

    def _source_name(self, exp):
        if exp.get("savings_category_id"):
            sp = dm.get_savings_planner()
            return next((display_name(c["name"]) for c in sp.get("categories", []) if c["id"] == exp["savings_category_id"]), tx("Savings"))
        split_cats = {c["id"]: c["name"] for c in dm.get_global_categories()}
        return display_name(split_cats.get(exp.get("category_id"), "Unknown"))

    def _source_category(self, exp):
        if exp.get("savings_category_id"):
            return None
        return next((c for c in dm.get_global_categories() if c["id"] == exp.get("category_id")), None)

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


