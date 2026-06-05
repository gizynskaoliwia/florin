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
                    monthly_nyt = round(nyt / 12, 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            else:
                dm.add_savings_category(self.sp, name, target, deadline, gid, nyt)
                # If next_year_target, fill months after deadline
                if nyt and deadline < 12:
                    new_cat = self.sp["categories"][-1]
                    grid_row = self.sp["grid"][new_cat["id"]]
                    monthly_nyt = round(nyt / 12, 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            dm.save_savings_planner(self.sp)
            dialog.destroy()
            self._rebuild_ui()

        def delete_cat():
            if not messagebox.askyesno(tx("Confirm Delete"), ui_text(f"Are you sure you want to delete category '{cat['name']}'?", f"Czy na pewno chcesz usunąć kategorię '{cat['name']}'?")):
                return
            try:
                dm.delete_savings_category(self.sp, cat["id"])
                dm.save_savings_planner(self.sp)
                dialog.destroy()
                self._rebuild_ui()
            except ValueError as e:
                messagebox.showerror(ui_text("Cannot delete", "Nie można usunąć"), str(e))

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=15)
        
        save_btn = ctk.CTkButton(btns, text=tx("Save"), command=save)
        save_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        if cat:
            del_btn = ctk.CTkButton(btns, text=tx("Delete"), fg_color=COLOR_EXPENSE, hover_color="#A94442", command=delete_cat)
            del_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

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
        cat = next((c for c in self.sp["categories"] if c["id"] == cat_id), None)
        if not cat: return
        if not messagebox.askyesno(tx("Confirm Delete"), ui_text(f"Are you sure you want to delete category '{cat['name']}'?", f"Czy na pewno chcesz usunąć kategorię '{cat['name']}'?")):
            return
        try:
            dm.delete_savings_category(self.sp, cat_id)
            dm.save_savings_planner(self.sp)
            self._rebuild_ui()
        except ValueError as e:
            messagebox.showerror(ui_text("Cannot delete", "Nie można usunąć"), str(e))

    def delete_group(self, group_id):
        group = next((g for g in self.sp.get("groups", []) if g["id"] == group_id), None)
        if not group: return
        
        children = [c for c in self.sp.get("categories", []) if c.get("group_id") == group_id]
        if children:
            if not messagebox.askyesno(tx("Confirm Delete"), ui_text(
                f"Group '{group['name']}' contains {len(children)} categories. They will be detached and moved to Ungrouped. Continue?",
                f"Grupa '{group['name']}' zawiera kategorie ({len(children)}). Zostaną one odpięte i przeniesione do Niezgrupowanych. Kontynuować?"
            )):
                return
        else:
            if not messagebox.askyesno(tx("Confirm Delete"), ui_text(f"Are you sure you want to delete group '{group['name']}'?", f"Czy na pewno chcesz usunąć grupę '{group['name']}'?")):
                return
                
        dm.delete_savings_group(self.sp, group_id)
        dm.save_savings_planner(self.sp)
        self._rebuild_ui()

    def edit_group_dialog(self, group):
        d = ctk.CTkInputDialog(text=tx("Enter new group name:"), title=tx("Edit Group"))
        name = d.get_input()
        if name and name.strip() and name.strip() != group["name"]:
            dm.edit_savings_group(self.sp, group["id"], name.strip())
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
        spent_cache = getattr(self, '_spent_cache', None)
        for m in range(1, 13):
            mk = f"{m:02d}"
            allocated = dm.get_month_total_allocated(self.sp, mk, spent_cache)
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
                total = 0.0
                for c in children:
                    raw = self.sp.get("grid", {}).get(c["id"], {}).get(mk, 0.0)
                    adj = dm.get_cascade_adjustments(self.sp, c["id"], spent_cache)
                    total += adj.get(mk, raw)
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
            
            name_frame = ctk.CTkFrame(table, fg_color="transparent")
            name_frame.grid(row=r, column=0, padx=2, pady=(6, 1), sticky="w")
            
            lbl = ctk.CTkLabel(name_frame, text=f"{chevron} {group['name']}", font=FONT_LABEL, text_color=COLOR_PRIMARY, width=NAME_W-40, anchor="w", cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, gid=group["id"]: self.toggle_planning_group(gid))
            
            if self.editing:
                ctk.CTkButton(name_frame, text="✎", width=20, height=20, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda g=group: self.edit_group_dialog(g)).pack(side="right", padx=1)
                ctk.CTkButton(name_frame, text="×", width=20, height=20, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda gid=group["id"]: self.delete_group(gid)).pack(side="right")

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
            allocated = dm.get_month_total_allocated(sp, mk, self._spent_cache)
            lbl = ctk.CTkLabel(table, text=f"{allocated:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.alloc_lbls[mk] = lbl
        row_idx += 1

        # Remaining (always read-only)
        ctk.CTkLabel(table, text=tx("Remaining"), font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            remaining = dm.get_month_remaining(sp, mk, self._spent_cache)
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

        saved = dm.get_cat_saved_until_deadline(sp, cat["id"])
        missing = dm.get_cat_missing(sp, cat["id"])
        progress = dm.get_cat_progress(sp, cat["id"])
        spent = self._spent_cache.get(cat["id"], {}).get("total", 0.0)
        spent_until_deadline = self._spent_cache.get(cat["id"], {}).get("until_deadline", 0.0)
        balance_deadline = saved - spent_until_deadline
        post_deadline = dm.get_cat_saved_after_deadline(sp, cat["id"])

        s_lbl = ctk.CTkLabel(table, text=f"{saved:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT, width=55, anchor="center")
        s_lbl.grid(row=r, column=13, padx=1, pady=1)
        m_lbl = ctk.CTkLabel(table, text=f"{missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if missing > 0 else COLOR_SUCCESS, width=55, anchor="center")
        m_lbl.grid(row=r, column=14, padx=1, pady=1)
        p_lbl = ctk.CTkLabel(table, text=f"{progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT, width=55, anchor="center")
        p_lbl.grid(row=r, column=15, padx=1, pady=1)
        sp_lbl = ctk.CTkLabel(table, text=f"{spent:,.0f}" if spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center")
        sp_lbl.grid(row=r, column=16, padx=1, pady=1)
        bd_lbl = ctk.CTkLabel(table, text=f"{balance_deadline:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if balance_deadline >= 0 else COLOR_ERROR, width=55, anchor="center")
        bd_lbl.grid(row=r, column=17, padx=1, pady=1)
        pd_lbl = ctk.CTkLabel(table, text=f"{post_deadline:,.0f}" if post_deadline else "–", font=FONT_SMALL, text_color=COLOR_TEXT, width=55, anchor="center")
        pd_lbl.grid(row=r, column=18, padx=1, pady=1)
        
        self.actual_summary_lbls[cat["id"]] = {"saved": s_lbl, "missing": m_lbl, "progress": p_lbl, "balance": bd_lbl}

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
        ctk.CTkLabel(head, text=ui_text("months · saved · missing · % · spent · balance deadline · post deadline", "miesiące · odłożono · brakuje · % · wydano · saldo do deadline · po deadline"), font=FONT_MONO_SM_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
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
        for i, h in enumerate([ui_text("Saved", "Odłożono"), ui_text("Missing", "Brakuje"), "%", ui_text("Spent", "Wydano"), ui_text("Bal. Deadline", "Saldo dl."), ui_text("Post Deadl.", "Po terminie")]):
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
            g_saved = sum(dm.get_cat_saved_until_deadline(sp, c["id"]) for c in children)
            g_missing = sum(dm.get_cat_missing(sp, c["id"], spent_cache=self._spent_cache) for c in children)
            g_target_sum = sum(c.get("target", 0) for c in children)
            g_progress = g_saved / g_target_sum if g_target_sum > 0 else 0.0
            g_spent = sum(self._spent_cache.get(c["id"], {}).get("total", 0.0) for c in children)
            g_spent_deadline = sum(self._spent_cache.get(c["id"], {}).get("until_deadline", 0.0) for c in children)
            g_balance_deadline = g_saved - g_spent_deadline
            g_post_deadline = sum(dm.get_cat_saved_after_deadline(sp, c["id"]) for c in children)
            
            ctk.CTkLabel(table, text=f"{g_saved:,.0f}", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=13, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if g_missing > 0 else COLOR_SUCCESS, width=55, anchor="center").grid(row=r, column=14, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_progress >= 1.0 else COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=15, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_spent:,.0f}" if g_spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center").grid(row=r, column=16, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_balance_deadline:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_balance_deadline >= 0 else COLOR_ERROR, width=55, anchor="center").grid(row=r, column=17, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_post_deadline:,.0f}" if g_post_deadline else "–", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=18, padx=1, pady=(6, 1))

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
            raw_spent = self._spent_cache.get(cat_id, 0.0)
            spent = raw_spent.get("total", 0.0) if isinstance(raw_spent, dict) else raw_spent
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
        planned_to_date = sum(dm.get_month_total_allocated(self.sp, f"{m:02d}", getattr(self, '_spent_cache', None)) for m in range(1, current_month + 1))
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

            # Spent
            raw_spent = self._spent_cache.get(cat["id"], 0.0)
            spent_val = raw_spent.get("total", 0.0) if isinstance(raw_spent, dict) else raw_spent
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



