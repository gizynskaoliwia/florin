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
        
        self.show_all_months = False
        
        def toggle_show_all():
            self.show_all_months = not self.show_all_months
            self.btn_show_all.configure(text="Ukryj stare" if self.show_all_months else "Pokaż wszystkie")
            self.refresh()
            
        self.btn_show_all = ctk.CTkButton(
            hdr, text="Pokaż wszystkie", width=120, height=36,
            fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE,
            border_width=1, border_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
            font=FONT_LABEL, command=toggle_show_all
        )
        self.btn_show_all.pack(side="right", padx=(0, 10))
        
        self.editing = False
        
        # Scrollable area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.cell_vars = {}
        
        self.refresh()
        
    def toggle_edit(self):
        if self.editing:
            self._save_current_edits()
            dm.save_shared_goals(self.goals)
            self.editing = False
            self.btn_edit.configure(text=t("Edit"), fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_2)
            self.refresh()
        else:
            self.editing = True
            self.btn_edit.configure(text=t("Save"), fg_color=COLOR_SUCCESS, text_color=COLOR_SURFACE, hover_color=COLOR_MET_PLAN, border_width=0)
            self.refresh()

    def _save_current_edits(self):
        for (goal_id, mk, pid, fld), var in self.cell_vars.items():
            try:
                val = float(var.get().replace(",", "."))
            except:
                val = 0.0
            
            for g in self.goals:
                if g["id"] == goal_id and mk in g["data"]:
                    g["data"][mk][pid][fld] = val
                    break

    def delete_month(self, goal, month_key):
        self._save_current_edits()
        if month_key in goal["data"]:
            del goal["data"][month_key]
            dm.save_shared_goals(self.goals)
        self.refresh()

    def add_month(self, goal):
        self._save_current_edits()
        dialog = ctk.CTkToplevel(self)
        dialog.title("Dodaj miesiąc")
        dialog.geometry("300x200")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Miesiąc (YYYY-MM):", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        
        next_m = ""
        if goal.get("data"):
            last_m = sorted(goal["data"].keys())[-1]
            try:
                y, m = map(int, last_m.split("-"))
                m += 1
                if m > 12:
                    m = 1
                    y += 1
                next_m = f"{y}-{m:02d}"
            except:
                pass
                
        m_var = ctk.StringVar(value=next_m)
        ctk.CTkEntry(dialog, textvariable=m_var).pack(fill="x", padx=20)
        
        err_lbl = ctk.CTkLabel(dialog, text="", text_color=COLOR_ERROR, font=FONT_SMALL)
        err_lbl.pack(pady=5)
        
        def save():
            mk = m_var.get().strip()
            import re
            if not re.match(r"^\d{4}-\d{2}$", mk):
                err_lbl.configure(text="Format musi być YYYY-MM")
                return
            if mk in goal["data"]:
                err_lbl.configure(text="Taki miesiąc już istnieje")
                return
            
            goal["data"][mk] = {p["id"]: {"planned": 0.0, "actual": 0.0} for p in goal["persons"]}
            dm.save_shared_goals(self.goals)
            dialog.destroy()
            self.refresh()
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Anuluj", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE, command=dialog.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Dodaj", fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, command=save).pack(side="right", expand=True, padx=5)

            
    def refresh(self):
        canvas = getattr(self.scroll, "_parent_canvas", None)
        scroll_pos = canvas.yview()[0] if canvas else 0.0

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
            
            actions = ctk.CTkFrame(hdr, fg_color="transparent")
            actions.pack(side="right")
            
            ctk.CTkButton(actions, text="Wypłać / Wydatek", width=120, height=28, fg_color=COLOR_WARNING, text_color=COLOR_SURFACE, font=FONT_LABEL, command=lambda g=goal: self.open_withdraw_modal(g)).pack(side="right", padx=(10, 0))
            ctk.CTkButton(actions, text="Historia wypłat", width=120, height=28, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER, font=FONT_LABEL, command=lambda g=goal: self.open_history_modal(g)).pack(side="right")
            
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
            status_header_text = "Akcje" if self.editing else t("shared.status")
            ctk.CTkLabel(grid, text=status_header_text, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=80).grid(row=0, column=col_idx, rowspan=2, padx=5, pady=5)
            
            all_months = sorted(goal["data"].keys())
            if getattr(self, "show_all_months", False):
                months = all_months
            else:
                base_m = self.controller.current_month
                visible_set = set()
                for offset in range(-2, 3):
                    y, m = map(int, base_m.split('-'))
                    m += offset
                    while m > 12: m -= 12; y += 1
                    while m < 1: m += 12; y -= 1
                    visible_set.add(f"{y}-{m:02d}")
                months = [m for m in all_months if m in visible_set]
                # If there are no intersecting months, just show everything
                if not months:
                    months = all_months

            tot_planned = {p["id"]: 0.0 for p in persons}
            tot_actual = {p["id"]: 0.0 for p in persons}
            
            # Pre-calculate totals using ALL months
            for mk in all_months:
                for p in persons:
                    pdata = goal["data"][mk].get(p["id"], {"planned": 0.0, "actual": 0.0})
                    tot_planned[p["id"]] += pdata["planned"]
                    tot_actual[p["id"]] += pdata["actual"]
            
            row_idx = 2
            
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

                if self.editing:
                    del_btn = ctk.CTkButton(grid, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda g=goal, m=mk: self.delete_month(g, m))
                    del_btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)
                else:
                    # Status indicator
                    status_color = COLOR_SUCCESS if month_actual_sum >= month_planned_sum and month_planned_sum > 0 else COLOR_ERROR if month_actual_sum > 0 else COLOR_BORDER
                    indicator = ctk.CTkFrame(grid, width=16, height=16, corner_radius=8, fg_color=status_color)
                    indicator.grid(row=row_idx, column=col_idx, padx=5, pady=5)
                
                row_idx += 1
                
            if self.editing:
                btn_add = ctk.CTkButton(grid, text="+ Dodaj miesiąc", fg_color="transparent", text_color=COLOR_PRIMARY, border_width=1, border_color=COLOR_PRIMARY, command=lambda g=goal: self.add_month(g))
                btn_add.grid(row=row_idx, column=0, columnspan=col_idx+1, pady=(10, 5))
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

            total_withdrawn = sum(w["amount"] for w in goal.get("withdrawals", []))
            available = total_actual_all - total_withdrawn
            
            summary_frame = ctk.CTkFrame(card, fg_color=COLOR_SURFACE_2, corner_radius=RADIUS_BUTTON)
            summary_frame.pack(fill="x", padx=24, pady=(0, 24))
            
            ctk.CTkLabel(summary_frame, text=f"Zgromadzono: {total_actual_all:,.2f} PLN", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=16, pady=12)
            ctk.CTkLabel(summary_frame, text=f"Wypłacono: {total_withdrawn:,.2f} PLN", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=16, pady=12)
            
            avail_color = COLOR_SUCCESS if available >= 0 else COLOR_ERROR
            ctk.CTkLabel(summary_frame, text=f"Dostępne: {available:,.2f} PLN", font=FONT_TITLE, text_color=avail_color).pack(side="right", padx=16, pady=12)

        if canvas:
            self.update_idletasks()
            canvas.yview_moveto(scroll_pos)

    def open_withdraw_modal(self, goal):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Wypłata: {goal['name']}")
        dialog.geometry("400x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"Dodaj wydatek / wypłatę", font=FONT_TITLE, text_color=COLOR_TEXT).pack(pady=(20, 10))
        
        ctk.CTkLabel(dialog, text="Kwota (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        amount_var = ctk.StringVar()
        ctk.CTkEntry(dialog, textvariable=amount_var, font=FONT_BODY).pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Data (DD/MM/YYYY):", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        date_var = ctk.StringVar(value=datetime.today().strftime("%d/%m/%Y"))
        ctk.CTkEntry(dialog, textvariable=date_var, font=FONT_BODY).pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Opis:", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        desc_var = ctk.StringVar()
        ctk.CTkEntry(dialog, textvariable=desc_var, font=FONT_BODY).pack(fill="x", padx=20)
        
        error_lbl = ctk.CTkLabel(dialog, text="", text_color=COLOR_ERROR, font=FONT_SMALL)
        error_lbl.pack(pady=5)
        
        def save():
            try:
                amt = float(amount_var.get().replace(",", "."))
                if amt <= 0: raise ValueError
            except:
                error_lbl.configure(text="Nieprawidłowa kwota.")
                return
                
            d_str = date_var.get().strip()
            try:
                dt = datetime.strptime(d_str, "%d/%m/%Y")
                iso_date = dt.strftime("%Y-%m-%d")
            except:
                error_lbl.configure(text="Nieprawidłowy format daty.")
                return
                
            desc = desc_var.get().strip()
            if not desc:
                error_lbl.configure(text="Opis jest wymagany.")
                return
                
            dm.add_shared_goal_transaction(goal["id"], iso_date, amt, desc)
            dialog.destroy()
            self.refresh()
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Anuluj", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_SURFACE, command=dialog.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Zapisz", fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, command=save).pack(side="right", expand=True, padx=5)

    def open_history_modal(self, goal):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Historia wypłat: {goal['name']}")
        dialog.geometry("500x500")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Historia wypłat", font=FONT_TITLE, text_color=COLOR_TEXT).pack(pady=20)
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        withdrawals = goal.get("withdrawals", [])
        if not withdrawals:
            ctk.CTkLabel(scroll, text="Brak wypłat.", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=20)
            return
            
        def delete_w(w_id):
            dm.delete_shared_goal_transaction(w_id)
            dialog.destroy()
            self.refresh()
            self.open_history_modal(next(g for g in self.goals if g["id"] == goal["id"]))
            
        for w in withdrawals:
            row = ctk.CTkFrame(scroll, fg_color=COLOR_SURFACE_2, corner_radius=8)
            row.pack(fill="x", pady=5)
            
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            
            ctk.CTkLabel(info, text=w["date"], font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(info, text=w["description"], font=FONT_BODY, text_color=COLOR_TEXT).pack(anchor="w")
            
            ctk.CTkLabel(row, text=f"-{w['amount']:,.2f} PLN", font=FONT_MONO, text_color=COLOR_ERROR).pack(side="left", padx=10)
            
            ctk.CTkButton(row, text="Usuń", width=60, fg_color=COLOR_ERROR, text_color=COLOR_SURFACE, command=lambda wid=w["id"]: delete_w(wid)).pack(side="right", padx=10)

