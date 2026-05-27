import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Nav items
nav_search = r'''        main_items = \[
            \("Dashboard", "🏠", "nav.dashboard"\),
            \("Income", "💰", "nav.income"\),
            \("Expenses", "🧾", "nav.expenses"\),
            \("Savings", "🎯", "nav.savings"\),
            \("Cash Flow", "💧", "nav.cashflow"\),
            \("History", "📅", "nav.history"\),
        \]'''

nav_replace = '''        main_items = [
            ("Dashboard", "🏠", "nav.dashboard"),
            ("Income", "💰", "nav.income"),
            ("Expenses", "🧾", "nav.expenses"),
            ("Savings", "🎯", "nav.savings"),
            ("Shared Goals", "🤝", "nav.shared_goals"),
            ("Cash Flow", "💧", "nav.cashflow"),
            ("History", "📅", "nav.history"),
        ]'''

content = re.sub(nav_search, nav_replace, content)

# 2. Add filtering out of shared goals if disabled
nav_loop_search = r'''        for name, icon, label_key in main_items:
            self\._sidebar_nav_item\(nav_frame, name, icon, t\(label_key\)\)'''

nav_loop_replace = '''        for name, icon, label_key in main_items:
            if name == "Shared Goals" and self.config.get("enable_shared_goals", "false") != "true":
                continue
            self._sidebar_nav_item(nav_frame, name, icon, t(label_key))'''

content = re.sub(nav_loop_search, nav_loop_replace, content)

# 3. Add toggle method to FlorinApp
app_methods_search = r'''    def refresh_sidebar\(self\):
        for widget in self\.sidebar\.winfo_children\(\):
            widget\.destroy\(\)
        self\._init_sidebar\(\)'''

app_methods_replace = '''    def toggle_shared_goals(self):
        val = "true" if self.config.get("enable_shared_goals", "false") != "true" else "false"
        self.config["enable_shared_goals"] = val
        dm.save_config(self.config)
        self.refresh_sidebar()
        if val == "false" and self.current_view_name == "Shared Goals":
            self.show_view("Dashboard")

    def refresh_sidebar(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self._init_sidebar()'''

content = re.sub(app_methods_search, app_methods_replace, content)

# 4. Settings View
settings_search = r'''        # === Data ===
        data_card = ctk\.CTkFrame\(self\.scroll, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER\)'''

settings_replace = '''        # === Features ===
        feat_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER)
        feat_card.pack(fill="x", pady=(0, 24))
        feat_hdr = ctk.CTkFrame(feat_card, fg_color="transparent")
        feat_hdr.pack(fill="x", padx=24, pady=(20, 16))
        ctk.CTkLabel(feat_hdr, text="Features", font=FONT_SECTION, text_color=COLOR_TEXT).pack(side="left")
        
        self.shared_goals_var = ctk.StringVar(value=self.controller.config.get("enable_shared_goals", "false"))
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
        sw.pack(anchor="w", padx=24, pady=(0, 24))

        # === Data ===
        data_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER)'''

content = re.sub(settings_search, settings_replace, content)

# 5. Settings toggle function
settings_func_search = r'''    def refresh\(self\):
        pass'''

settings_func_replace = '''    def toggle_shared_goals(self):
        val = self.shared_goals_var.get()
        self.controller.config["enable_shared_goals"] = val
        dm.save_config(self.controller.config)
        self.controller.refresh_sidebar()

    def refresh(self):
        pass'''

content = re.sub(settings_func_search, settings_func_replace, content)


# 6. SharedGoalsView class
shared_goals_class = '''

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

class HelpView(ctk.CTkFrame):'''

content = re.sub(r'class HelpView\(ctk\.CTkFrame\):', shared_goals_class, content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
