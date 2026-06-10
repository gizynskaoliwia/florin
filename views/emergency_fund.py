import customtkinter as ctk
import data_manager as dm
from i18n import t, tr_text
import theme

class EmergencyFundView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.settings_data = {}
        self.section_refs = []
        self.editing = False
        
        self.setup_ui()
        self.refresh()
        
    def setup_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        title = ctk.CTkLabel(
            header_frame, 
            text=t("nav.emergency_fund"), 
            font=theme.FONT_DISPLAY, 
            text_color=theme.COLOR_TEXT
        )
        title.pack(side="left")

        self.btn_edit = ctk.CTkButton(
            header_frame, text=t("Edit"), width=100, height=36,
            fg_color=theme.COLOR_SURFACE, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_SURFACE_2,
            border_width=1, border_color=theme.COLOR_BORDER, corner_radius=theme.RADIUS_BUTTON,
            font=theme.FONT_LABEL, command=self.toggle_edit
        )
        self.btn_edit.pack(side="right")
        
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        self.sections_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.sections_container.pack(fill="both", expand=True)

    def _build_section(self, mode, title):
        data = self.settings_data.get(mode, {})
        section_frame = ctk.CTkFrame(self.sections_container, fg_color="transparent")
        section_frame.pack(fill="x", pady=(0, 40))
        
        ctk.CTkLabel(section_frame, text=title, font=theme.FONT_SECTION, text_color=theme.COLOR_PRIMARY).pack(anchor="w", pady=(0, 20))
        
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_columnconfigure(0, weight=1, uniform="ef_col")
        content_frame.grid_columnconfigure(1, weight=1, uniform="ef_col")
        
        stan_card = ctk.CTkFrame(content_frame, fg_color=theme.COLOR_SURFACE, corner_radius=16, border_width=1, border_color=theme.COLOR_BORDER)
        stan_card.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        ctk.CTkLabel(stan_card, text=tr_text("STAN"), font=theme.FONT_SECTION, text_color=theme.COLOR_TEXT).pack(pady=(20, 20))
        
        actual_frame = self.make_row(stan_card, "AKTUALNIE", "0.00")
        manage_btn = ctk.CTkButton(actual_frame["row"], text=tr_text("Zarządzaj"), width=80, height=24, font=theme.FONT_BODY,
                                   fg_color=theme.COLOR_SURFACE, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_SURFACE_2,
                                   border_width=1, border_color=theme.COLOR_BORDER, corner_radius=theme.RADIUS_BUTTON,
                                   command=lambda m=mode: self.open_manage_modal(m))
        manage_btn.pack(side="right", padx=(0, 10))
        
        missing_frame = self.make_row(stan_card, "BRAKUJE DO AKTUALNEGO CELU", "0.00", highlight=True)
        future_frame = self.make_row(stan_card, "CEL 2026", "0.00", magenta=True)
        
        asset_card = ctk.CTkFrame(content_frame, fg_color=theme.COLOR_SURFACE, corner_radius=16, border_width=1, border_color=theme.COLOR_BORDER)
        asset_card.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
        
        ctk.CTkLabel(asset_card, text=tr_text("PODZIAŁ KAPITAŁU"), font=theme.FONT_SECTION, text_color=theme.COLOR_TEXT).pack(pady=(20, 20))
        
        target_row = ctk.CTkFrame(asset_card, fg_color="transparent")
        target_row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(target_row, text=tr_text("CEL"), font=theme.FONT_BODY, text_color=theme.COLOR_TEXT).pack(side="left")
        
        manual = data.get("manual_target")
        if manual is not None:
            initial_target = f"{manual:.0f}"
        else:
            initial_target = f"{self.calculate_target(data):.0f}"
            
        target_var = ctk.StringVar(value=initial_target)
        target_entry = None
        target_label = None
        if self.editing:
            target_entry = ctk.CTkEntry(target_row, textvariable=target_var, width=120, font=theme.FONT_MONO, justify="right")
            target_entry.pack(side="right")
        else:
            target_label = ctk.CTkLabel(target_row, text=f"{float(initial_target):,.2f}", font=theme.FONT_MONO, text_color=theme.COLOR_TEXT)
            target_label.pack(side="right")
        
        cash_row = ctk.CTkFrame(asset_card, fg_color="transparent")
        cash_row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(cash_row, text=tr_text("Gotówka"), font=theme.FONT_BODY, text_color=theme.COLOR_TEXT).pack(side="left")
        
        cash_var = ctk.StringVar(value=f"{data.get('cash_allocated', 0.0):.0f}")
        cash_entry = None
        if self.editing:
            cash_entry = ctk.CTkEntry(cash_row, textvariable=cash_var, width=120, font=theme.FONT_MONO, justify="right")
            cash_entry.pack(side="right")
        else:
            ctk.CTkLabel(cash_row, text=f"{data.get('cash_allocated', 0.0):,.2f}", font=theme.FONT_MONO, text_color=theme.COLOR_TEXT).pack(side="right")
        
        target_no_cash_frame = self.make_row(asset_card, "CEL - GOTÓWKA", "0.00")
        
        allocs = data.get("allocations", {"80% CELU OBLIGACJE": 80.0, "20% CELU KONTO OSZCZ.": 20.0})
        alloc_frames = []
        for name, pct in allocs.items():
            alloc_frames.append(self.make_row(asset_card, name, "0.00"))

        goals_card = ctk.CTkFrame(section_frame, fg_color=theme.COLOR_SURFACE, corner_radius=16, border_width=1, border_color=theme.COLOR_BORDER)
        goals_card.pack(fill="x", pady=(20, 0))
        ctk.CTkLabel(goals_card, text=tr_text("CELE SZCZEGÓŁOWE"), font=theme.FONT_SECTION, text_color=theme.COLOR_TEXT).pack(anchor="w", padx=20, pady=(20, 10))
        goals_list_frame = ctk.CTkFrame(goals_card, fg_color="transparent")
        goals_list_frame.pack(fill="x", padx=20, pady=(0, 20))

        refs = {
            "mode": mode,
            "actual_frame": actual_frame,
            "missing_frame": missing_frame,
            "future_frame": future_frame,
            "target_var": target_var,
            "target_entry": target_entry,
            "target_label": target_label,
            "cash_var": cash_var,
            "cash_entry": cash_entry,
            "target_no_cash_frame": target_no_cash_frame,
            "alloc_frames": alloc_frames,
            "goals_list_frame": goals_list_frame,
            "goals_vars": []
        }
        
        self.section_refs.append(refs)

        def on_var_changed(*args):
            try:
                target_str = target_var.get().replace(",", ".").strip()
                t_val = float(target_str) if target_str else self.calculate_target(data)
            except ValueError:
                t_val = self.calculate_target(data)
                
            try:
                c_val = float(cash_var.get().replace(",", "."))
            except ValueError:
                c_val = 0.0
                
            t_no_cash = t_val - c_val
            target_no_cash_frame["label"].configure(text=f"{t_no_cash:,.2f}")
            
            allocs = data.get("allocations", {"80% CELU OBLIGACJE": 80.0, "20% CELU KONTO OSZCZ.": 20.0})
            for i, (name, pct) in enumerate(allocs.items()):
                if i < len(alloc_frames):
                    amt = t_no_cash * (pct / 100.0)
                    alloc_frames[i]["label"].configure(text=f"{amt:,.2f}")

        if self.editing:
            target_var.trace_add("write", on_var_changed)
            cash_var.trace_add("write", on_var_changed)

    def make_row(self, parent, label_text, value_text, highlight=False, magenta=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        color = theme.COLOR_TEXT
        if highlight:
            color = theme.COLOR_WARNING
        elif magenta:
            color = theme.COLOR_EXPENSE
        ctk.CTkLabel(row, text=tr_text(label_text), font=theme.FONT_BODY, text_color=theme.COLOR_TEXT).pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=value_text, font=theme.FONT_MONO, text_color=color)
        val_lbl.pack(side="right")
        return {"row": row, "label": val_lbl}

    def open_manage_modal(self, mode):
        modal = ctk.CTkToplevel(self)
        modal.title(tr_text("Historia operacji"))
        modal.geometry("500x600")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        form_frame = ctk.CTkFrame(modal, fg_color=theme.COLOR_SURFACE, corner_radius=16, border_width=1, border_color=theme.COLOR_BORDER)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text=tr_text("Nowa operacja"), font=theme.FONT_SECTION, text_color=theme.COLOR_TEXT).pack(anchor="w", padx=20, pady=(20, 10))
        
        from datetime import datetime
        
        date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row1, text=tr_text("Data"), width=100, anchor="w").pack(side="left")
        
        date_entry = ctk.CTkEntry(row1, textvariable=date_var)
        date_entry.pack(side="left", fill="x", expand=True)

        def open_calendar():
            from tkcalendar import Calendar
            cal_win = ctk.CTkToplevel(modal)
            cal_win.title("Kalendarz")
            cal_win.geometry("300x300")
            cal_win.transient(modal)
            cal_win.grab_set()
            try:
                d = datetime.strptime(date_var.get().strip(), "%Y-%m-%d")
            except:
                d = datetime.now()
            cal = Calendar(cal_win, selectmode="day", year=d.year, month=d.month, day=d.day, date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            def pick():
                date_var.set(cal.get_date())
                cal_win.destroy()
            ctk.CTkButton(cal_win, text="Wybierz", command=pick).pack(pady=(0, 10))

        ctk.CTkButton(row1, text="📅", width=36, height=28, fg_color=theme.COLOR_SURFACE_2, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_BORDER, command=open_calendar).pack(side="right", padx=(5, 0))
        
        type_var = ctk.StringVar(value="Aktualizacja salda")
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row2, text=tr_text("Typ"), width=100, anchor="w").pack(side="left")
        type_cb = ctk.CTkComboBox(row2, variable=type_var, values=["Aktualizacja salda", "Wpłata (notatka)", "Wypłata (notatka)"])
        type_cb.pack(side="right", fill="x", expand=True)
        
        amount_var = ctk.StringVar(value="0.00")
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row3, text=tr_text("Kwota"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(row3, textvariable=amount_var).pack(side="right", fill="x", expand=True)
        
        note_var = ctk.StringVar(value="")
        row3_note = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3_note.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row3_note, text=tr_text("Opis"), width=100, anchor="w").pack(side="left")
        ctk.CTkEntry(row3_note, textvariable=note_var, placeholder_text="Opcjonalnie").pack(side="right", fill="x", expand=True)
        
        error_lbl = ctk.CTkLabel(form_frame, text="", text_color=theme.COLOR_EXPENSE)
        error_lbl.pack(fill="x", padx=20, pady=(0, 5))
        
        list_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        
        def refresh_list():
            for w in list_frame.winfo_children():
                w.destroy()
            transactions = dm.get_emergency_fund_transactions(mode)
            for t in transactions:
                t_type = t.get("type", "note")
                is_snapshot = t_type == "snapshot"
                
                # Colors based on type
                if is_snapshot:
                    bg_color = theme.COLOR_PRIMARY_SOFT
                    border_c = theme.COLOR_PRIMARY
                    color = theme.COLOR_PRIMARY
                    lbl_text = "Migawka Salda"
                    sign = "="
                elif t_type == "deposit":
                    bg_color = theme.COLOR_SURFACE
                    border_c = theme.COLOR_BORDER
                    color = theme.COLOR_SUCCESS
                    lbl_text = "Wpłata"
                    sign = "+"
                elif t_type == "withdrawal":
                    bg_color = theme.COLOR_SURFACE
                    border_c = theme.COLOR_BORDER
                    color = theme.COLOR_EXPENSE
                    lbl_text = "Wypłata"
                    sign = "-"
                else:
                    bg_color = theme.COLOR_SURFACE
                    border_c = theme.COLOR_BORDER
                    color = theme.COLOR_TEXT_MUTED
                    lbl_text = "Notatka"
                    sign = ""
                
                t_row = ctk.CTkFrame(list_frame, fg_color=bg_color, corner_radius=8, border_width=1 if is_snapshot else 0, border_color=border_c)
                t_row.pack(fill="x", pady=4)
                
                info_frame = ctk.CTkFrame(t_row, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=6)
                
                top_lbl_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                top_lbl_frame.pack(fill="x")
                ctk.CTkLabel(top_lbl_frame, text=t["date"], font=theme.FONT_BODY, anchor="w", width=80).pack(side="left")
                ctk.CTkLabel(top_lbl_frame, text=f"{sign} {t['amount']:,.2f} PLN", font=theme.FONT_MONO, text_color=color).pack(side="left", padx=10)
                
                bot_lbl_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                bot_lbl_frame.pack(fill="x")
                ctk.CTkLabel(bot_lbl_frame, text=lbl_text, font=theme.FONT_MONO_SM_BOLD, text_color=color).pack(side="left")
                if t.get("note"):
                    ctk.CTkLabel(bot_lbl_frame, text=f" · {t['note']}", font=theme.FONT_BODY, text_color=theme.COLOR_TEXT_MUTED).pack(side="left")
                
                del_btn = ctk.CTkButton(t_row, text="X", width=30, fg_color=theme.COLOR_EXPENSE, hover_color=theme.COLOR_EXPENSE, command=lambda tid=t["id"]: delete_tx(tid))
                del_btn.pack(side="right", padx=10, pady=5)

        def add_tx():
            error_lbl.configure(text="")
            try:
                val = amount_var.get().replace(",", ".").replace(" ", "").replace("\u00a0", "")
                if not val:
                    error_lbl.configure(text="Podaj kwotę")
                    return
                amt = float(val)
                if amt < 0:
                    error_lbl.configure(text="Kwota musi być dodatnia")
                    return
            except ValueError:
                error_lbl.configure(text="Nieprawidłowa kwota")
                return
                
            # Verify date format
            date_val = date_var.get().strip()
            if not date_val:
                error_lbl.configure(text="Podaj datę")
                return
            try:
                from datetime import datetime
                datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError:
                error_lbl.configure(text="Nieprawidłowy format daty (YYYY-MM-DD)")
                return
                
            sel_type = type_var.get()
            if sel_type == "Aktualizacja salda":
                t_type = "snapshot"
            elif sel_type == "Wpłata (notatka)":
                t_type = "deposit"
            else:
                t_type = "withdrawal"
            
            try:
                dm.add_emergency_fund_transaction(mode, date_val, t_type, amt, note_var.get().strip())
                amount_var.set("0.00")
                note_var.set("")
                refresh_list()
                self.refresh()
            except Exception as e:
                error_lbl.configure(text=f"Błąd zapisu: {e}")
                print(f"Błąd zapisu: {e}")

        def delete_tx(tid):
            dm.delete_emergency_fund_transaction(tid, mode)
            refresh_list()
            self.refresh()
            
        row4 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row4.pack(fill="x", padx=20, pady=(15, 20))
        btn_add = ctk.CTkButton(row4, text=tr_text("Dodaj"), command=add_tx, fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS, text_color=theme.COLOR_SURFACE)
        btn_add.pack(side="right")
        
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        refresh_list()

    def toggle_edit(self):
        if self.editing:
            for refs in self.section_refs:
                try:
                    val = float(refs["cash_var"].get().replace(",", "."))
                    mode = refs["mode"]
                    data = self.settings_data.get(mode, {})
                    data["cash_allocated"] = val
                    
                    target_str = refs["target_var"].get().replace(",", ".").strip()
                    if target_str:
                        data["manual_target"] = float(target_str)
                    else:
                        data["manual_target"] = None
                        
                    for n_var, orig_idx in refs.get("goals_vars", []):
                        g_name = n_var.get().strip()
                        rev_goals = {v: k for k, v in dm.EMERGENCY_FUND_GOALS.items()}
                        g_key = rev_goals.get(g_name, g_name)
                        data["custom_goals"][orig_idx] = {"name": g_key, "amount": 0.0}
                    
                    data["custom_goals"] = [cg for cg in data["custom_goals"] if cg["name"]]
                        
                    dm.save_emergency_fund_settings(mode, data)
                except ValueError:
                    pass
            self.editing = False
            self.btn_edit.configure(text=t("Edit"), fg_color=theme.COLOR_SURFACE, text_color=theme.COLOR_TEXT, border_color=theme.COLOR_BORDER, hover_color=theme.COLOR_SURFACE_2, border_width=1)
            self.refresh()
        else:
            self.editing = True
            self.btn_edit.configure(text=t("Save"), fg_color=theme.COLOR_SUCCESS, text_color=theme.COLOR_SURFACE, hover_color=theme.COLOR_MET_PLAN, border_width=0)
            self.refresh()

    def calculate_target(self, mode_data, is_future=False):
        salary = mode_data.get("salary", 0.0)
        mortgage = mode_data.get("mortgage", 0.0)
        living = mode_data.get("living_expenses", 0.0)
        goal = mode_data.get("future_goal", "6msc_zycia") if is_future else mode_data.get("selected_goal", "3msc_zycia")
        
        if goal == "3msc_zycia": return 3 * living
        elif goal == "6msc_zycia": return 6 * living
        elif goal == "3msc_kredytu": return 3 * mortgage
        elif goal == "6msc_kredytu": return 6 * mortgage
        elif goal == "3msc_zycia_kredytu": return 3 * (living + mortgage)
        elif goal == "4msc_zycia_kredytu": return 4 * (living + mortgage)
        elif goal == "5msc_zycia_kredytu": return 5 * (living + mortgage)
        elif goal == "6msc_zycia_kredytu": return 6 * (living + mortgage)
        elif goal == "3msc_wyplaty": return 3 * salary
        elif goal == "6msc_wyplaty": return 6 * salary
        return 0.0

    def refresh_asset_allocation(self, data, refs):
        manual = data.get("manual_target")
        if manual is not None:
            target = manual
        else:
            target = self.calculate_target(data)
            
        cash = data.get("cash_allocated", 0.0)
        target_no_cash = target - cash
        
        if refs.get("target_label"):
            refs["target_label"].configure(text=f"{target:,.2f}")
        
        refs["target_no_cash_frame"]["label"].configure(text=f"{target_no_cash:,.2f}")
        
        allocs = data.get("allocations", {"80% CELU OBLIGACJE": 80.0, "20% CELU KONTO OSZCZ.": 20.0})
        for i, (name, pct) in enumerate(allocs.items()):
            if i < len(refs["alloc_frames"]):
                amt = target_no_cash * (pct / 100.0)
                refs["alloc_frames"][i]["label"].configure(text=f"{amt:,.2f}")

    def refresh(self):
        for w in self.sections_container.winfo_children():
            w.destroy()
        self.section_refs.clear()

        self.settings_data = dm.get_emergency_fund_settings()
        
        if self.controller.config.get("enable_ef_personal", "true") == "true":
            self._build_section("personal", tr_text("Poduszka Osobista (JA)"))
            
        if self.controller.config.get("enable_ef_shared", "false") == "true":
            self._build_section("shared", tr_text("Poduszka Wspólna (WSPÓLNE)"))
            
        for refs in self.section_refs:
            mode = refs["mode"]
            data = self.settings_data.get(mode, {})
            
            target = self.calculate_target(data)
            future_target = self.calculate_target(data, is_future=True)
            actual = data.get("actual_saved", 0.0)
            
            missing = target - actual if target > actual else 0.0
            missing_future = future_target - actual if future_target > actual else 0.0
            
            refs["actual_frame"]["label"].configure(text=f"{actual:,.2f}")
            refs["missing_frame"]["label"].configure(text=f"{missing:,.2f}")
            refs["future_frame"]["label"].configure(text=f"{missing_future:,.2f}")
            
            if self.focus_get() != refs.get("cash_entry"):
                refs["cash_var"].set(f"{data.get('cash_allocated', 0.0):.0f}")
                
            self.refresh_asset_allocation(data, refs)
            self.refresh_custom_goals(mode, data, refs)

    def refresh_custom_goals(self, mode, data, refs):
        container = refs["goals_list_frame"]
        for w in container.winfo_children():
            w.destroy()
            
        actual_saved = data.get("actual_saved", 0.0)
        
        combined_goals = []
        
        goal_labels = dm.EMERGENCY_FUND_GOALS
        
        system_goal_keys = list(goal_labels.keys())
        active_goal_key = data.get("selected_goal", "3msc_zycia")
        future_goal_key = data.get("future_goal", "6msc_zycia")
        
        # Evaluate all system goals
        for key in system_goal_keys:
            # Temporary mock data dict to calculate target for specific key
            temp_data = dict(data)
            temp_data["selected_goal"] = key
            target = self.calculate_target(temp_data, is_future=False)
            
            # Include if it's completed OR if it's the explicitly selected active/future goal
            is_active = (key == active_goal_key)
            is_future = (key == future_goal_key)
            
            if target > 0 and (actual_saved >= target or is_active or is_future):
                name_prefix = ""
                if is_active:
                    name_prefix = "Cel Aktywny: "
                elif is_future:
                    name_prefix = "Cel Przyszły: "
                    
                combined_goals.append({
                    "name": f"{name_prefix}{goal_labels.get(key, key)}", 
                    "target": target, 
                    "is_system": True,
                    "original_index": -1
                })
            
        custom_goals = data.get("custom_goals", [])
        for i, cg in enumerate(custom_goals):
            goal_key = cg.get("name", list(dm.EMERGENCY_FUND_GOALS.keys())[0])
            
            temp_data = dict(data)
            temp_data["selected_goal"] = goal_key
            target = self.calculate_target(temp_data, is_future=False)
            
            display_name = goal_labels.get(goal_key, goal_key)
            
            combined_goals.append({
                "key": goal_key,
                "name": display_name,
                "target": target,
                "is_system": False,
                "original_index": i
            })
            
        # Remove duplicates if any (e.g., if a custom goal matches a system goal exactly, though unlikely. Better to just deduplicate by name)
        seen_names = set()
        unique_goals = []
        for g in combined_goals:
            if g["name"] not in seen_names:
                unique_goals.append(g)
                seen_names.add(g["name"])
                
        unique_goals.sort(key=lambda x: x["target"])
        combined_goals = unique_goals
        
        refs["goals_vars"] = []
        previous_target = 0.0
        
        for goal in combined_goals:
            target = goal["target"]
            if actual_saved >= target:
                goal["status_text"] = "✓ spełnione"
                goal["status_color"] = theme.COLOR_SUCCESS
                goal["progress_str"] = " (100%)"
            elif actual_saved > previous_target:
                goal["status_text"] = "w trakcie"
                goal["status_color"] = theme.COLOR_WARNING
                goal["progress_str"] = f" (Brakuje: {target - actual_saved:,.2f} PLN)"
            else:
                goal["status_text"] = "niezaczęte"
                goal["status_color"] = theme.COLOR_TEXT_MUTED
                goal["progress_str"] = f" (Brakuje: {target - actual_saved:,.2f} PLN)"
            previous_target = target

        completed_goals = [g for g in combined_goals if g["status_text"] == "✓ spełnione"]
        active_goals = [g for g in combined_goals if g["status_text"] != "✓ spełnione"]

        def render_goal(goal, parent, dim=False):
            target = goal["target"]
            is_system = goal["is_system"]
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=4)
            
            if self.editing and not is_system:
                name_var = ctk.StringVar(value=dm.EMERGENCY_FUND_GOALS.get(goal.get("key", goal["name"]), goal["name"]))
                ctk.CTkOptionMenu(row, variable=name_var, values=list(dm.EMERGENCY_FUND_GOALS.values()), width=200).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(row, text=f"{target:,.2f} PLN", font=theme.FONT_MONO, text_color=theme.COLOR_TEXT).pack(side="left")
                
                def del_goal(idx=goal["original_index"], m=mode):
                    data["custom_goals"].pop(idx)
                    dm.save_emergency_fund_settings(m, data)
                    self.refresh()
                
                ctk.CTkButton(row, text="X", width=30, fg_color=theme.COLOR_EXPENSE, hover_color=theme.COLOR_EXPENSE, command=del_goal).pack(side="right", padx=(10, 0))
                refs["goals_vars"].append((name_var, goal["original_index"]))
            else:
                name_disp = goal["name"]
                if self.editing and is_system:
                    name_disp += " (Z ustawień)"
                
                text_color = theme.COLOR_TEXT_MUTED if dim else theme.COLOR_TEXT
                ctk.CTkLabel(row, text=name_disp, font=theme.FONT_BODY, text_color=text_color).pack(side="left")
                ctk.CTkLabel(row, text=f"{target:,.2f} PLN", font=theme.FONT_MONO, text_color=text_color).pack(side="right", padx=(10, 0))
                
                status_lbl = ctk.CTkLabel(row, text=f"{goal['status_text']}{goal['progress_str']}", font=theme.FONT_MONO_SM_BOLD, text_color=goal["status_color"])
                status_lbl.pack(side="right", padx=(20, 10))

        for goal in active_goals:
            render_goal(goal, container)
            
        if completed_goals:
            sep = ctk.CTkFrame(container, fg_color=theme.COLOR_BORDER, height=1)
            sep.pack(fill="x", pady=(15, 10))
            ctk.CTkLabel(container, text="ZREALIZOWANE", font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, 5))
            for goal in completed_goals:
                render_goal(goal, container, dim=True)
                
        if self.editing:
            add_row = ctk.CTkFrame(container, fg_color="transparent")
            add_row.pack(fill="x", pady=(10, 0))
            def add_new(m=mode):
                for n_var, orig_idx in refs.get("goals_vars", []):
                    g_name = n_var.get().strip()
                    rev_goals = {v: k for k, v in dm.EMERGENCY_FUND_GOALS.items()}
                    g_key = rev_goals.get(g_name, g_name)
                    data["custom_goals"][orig_idx] = {"name": g_key, "amount": 0.0}
                
                data.setdefault("custom_goals", []).append({"name": list(dm.EMERGENCY_FUND_GOALS.keys())[0], "amount": 0.0})
                dm.save_emergency_fund_settings(m, data)
                self.refresh()
            ctk.CTkButton(add_row, text="+ Dodaj cel", width=100, fg_color=theme.COLOR_SURFACE_2, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_BORDER, command=add_new).pack(side="left")
