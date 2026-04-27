# main.py
import customtkinter as ctk
import data_manager as dm
from theme import *
from datetime import datetime

class FlorinApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        apply_theme()
        self.config = dm.get_config()
        self.current_month = self.config.get("last_month", datetime.now().strftime("%Y-%m"))
        self.data = dm.load_month(self.current_month)
        
        self.title("Florin")
        try:
            self.iconbitmap("logo2.ico")
        except:
            pass
        self.geometry("1100x720")
        self.configure(fg_color=COLOR_BG)
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.views = {}
        self.setup_views()
        self.show_view("Dashboard")
        
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=COLOR_SURFACE, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        logo = ctk.CTkLabel(self.sidebar, text="✦ FLORIN", font=FONT_DISPLAY, text_color=COLOR_PRIMARY)
        logo.pack(pady=(24, 32), padx=20, anchor="w")
        
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "🏠"), ("Income", "💰"), 
            ("Expenses", "🧾"), ("Cash Flow", "💧"), 
            ("History", "📅"), ("Settings", "⚙️")
        ]
        
        for name, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"{icon}  {name}", 
                fg_color="transparent", text_color=COLOR_TEXT, 
                font=FONT_BODY, anchor="w",
                hover_color=COLOR_SURFACE_2,
                command=lambda n=name: self.show_view(n)
            )
            btn.pack(pady=4, padx=12, fill="x")
            self.nav_buttons[name] = btn
            
    def setup_views(self):
        self.views["Dashboard"] = DashboardView(self.main_container, self)
        self.views["Income"] = IncomeView(self.main_container, self)
        self.views["Expenses"] = ExpensesView(self.main_container, self)
        self.views["Cash Flow"] = CashFlowView(self.main_container, self)
        self.views["History"] = HistoryView(self.main_container, self)
        self.views["Settings"] = SettingsView(self.main_container, self)
        
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")
            
    def show_view(self, name):
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color=COLOR_PRIMARY, text_color=COLOR_SURFACE, hover_color=COLOR_PRIMARY_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_2)
                
        self.views[name].tkraise()
        self.views[name].refresh()
        
    def save_data(self):
        dm.save_month(self.current_month, self.data)

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="Dashboard", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.month_lbl = ctk.CTkLabel(header, text=f"Month: {self.controller.current_month}", font=FONT_TITLE, text_color=COLOR_TEXT_MUTED)
        self.month_lbl.pack(side="right")
        
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(card, text="Net Income This Month", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=(20, 0))
        self.net_income_lbl = ctk.CTkLabel(card, text="0.00 PLN", font=FONT_MONO_LG, text_color=COLOR_INCOME)
        self.net_income_lbl.pack(anchor="w", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(self, text="Category Breakdown", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", pady=(10, 5))
        self.cat_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.cat_grid.pack(fill="x", pady=5)
        self.cat_grid.grid_columnconfigure((0, 1), weight=1)
        
        self.exp_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        self.exp_card.pack(fill="x", pady=10)
        self.total_exp_lbl = ctk.CTkLabel(self.exp_card, text="Total Expenses: 0.00 PLN (0 items)", font=FONT_BODY, text_color=COLOR_TEXT)
        self.total_exp_lbl.pack(padx=20, pady=20, anchor="w")
        
    def refresh(self):
        self.month_lbl.configure(text=f"Month: {self.controller.current_month}")
        data = self.controller.data
        net = data["business"].get("net_income", 0.0)
        self.net_income_lbl.configure(text=f"{net:,.2f} PLN".replace(",", " "))
        
        for widget in self.cat_grid.winfo_children():
            widget.destroy()
            
        cats = data.get("categories", [])
        for i, cat in enumerate(cats):
            c_frame = ctk.CTkFrame(self.cat_grid, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
            c_frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="nsew")
            
            allocated = dm.get_allocated_amount(data, cat["id"])
            spent = dm.get_spent_amount(data, cat["id"])
            rem = dm.get_remaining_amount(data, cat["id"])
            
            ctk.CTkLabel(c_frame, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT).pack(anchor="w", padx=15, pady=(15, 0))
            color_rem = COLOR_SUCCESS if rem >= 0 else COLOR_ERROR
            ctk.CTkLabel(c_frame, text=f"Remaining: {rem:,.2f} PLN", font=FONT_MONO, text_color=color_rem).pack(anchor="w", padx=15)
            
            progress = spent / allocated if allocated > 0 else 0
            pb = ctk.CTkProgressBar(c_frame, height=8, progress_color=cat.get("color", COLOR_PRIMARY), fg_color=COLOR_SURFACE_2)
            pb.pack(fill="x", padx=15, pady=(10, 15))
            pb.set(min(progress, 1.0))
            
        total_exp = dm.get_total_expenses(data)
        count = len(data.get("expenses", []))
        self.total_exp_lbl.configure(text=f"Total Expenses: {total_exp:,.2f} PLN ({count} items)")

class IncomeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        ctk.CTkLabel(self, text="Business Income", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=10)
        
        self.vars = {
            "gross": ctk.StringVar(),
            "vat": ctk.StringVar(),
            "tax": ctk.StringVar(),
            "zus": ctk.StringVar()
        }
        
        fields = [("Gross invoice amount", "gross"), ("VAT deducted", "vat"), ("Income tax deducted", "tax"), ("ZUS deducted", "zus")]
        
        for label, key in fields:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=label, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
            entry = ctk.CTkEntry(row, textvariable=self.vars[key], font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, width=150)
            entry.pack(side="right")
            entry.bind("<KeyRelease>", self.calculate)
            entry.bind("<FocusOut>", lambda e, v=self.vars[key]: self.format_on_blur_money(e, v, self.calculate))
            
        sep = ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER)
        sep.pack(fill="x", padx=20, pady=10)
        
        res_row = ctk.CTkFrame(card, fg_color="transparent")
        res_row.pack(fill="x", padx=20, pady=(10, 20))
        ctk.CTkLabel(res_row, text="Net income:", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.net_lbl = ctk.CTkLabel(res_row, text="0.00 PLN", font=FONT_MONO_LG, text_color=COLOR_INCOME)
        self.net_lbl.pack(side="right")
        
        # Category Split Section
        self.split_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        self.split_card.pack(fill="x", pady=10)
        
        header_row = ctk.CTkFrame(self.split_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header_row, text="Category Split", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        extra_btn = ctk.CTkButton(header_row, text="+ Extra Income", width=120, command=self.show_extra_income_dialog)
        extra_btn.pack(side="right", padx=10)
        
        self.sum_warning = ctk.CTkLabel(header_row, text="", font=FONT_BODY, text_color=COLOR_WARNING)
        self.sum_warning.pack(side="right")
        
        self.cat_rows_frame = ctk.CTkFrame(self.split_card, fg_color="transparent")
        self.cat_rows_frame.pack(fill="x", padx=20, pady=10)
        
        self.cat_vars = {}
        self.cat_lbls = {}
        self.cat_built = False
        
    def build_cat_rows(self):
        for widget in self.cat_rows_frame.winfo_children():
            widget.destroy()
            
        data = self.controller.data
        cats = data.get("categories", [])
        
        for cat in cats:
            row = ctk.CTkFrame(self.cat_rows_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=120, anchor="w").pack(side="left")
            
            var = ctk.StringVar(value=str(cat["percent"]))
            self.cat_vars[cat["id"]] = var
            
            entry = ctk.CTkEntry(row, textvariable=var, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, width=60)
            entry.pack(side="left", padx=10)
            ctk.CTkLabel(row, text="%", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left")
            
            entry.bind("<KeyRelease>", self.calculate_split)
            entry.bind("<FocusOut>", lambda e, v=var: self.format_on_blur_pct(e, v, self.calculate_split))
            
            lbl = ctk.CTkLabel(row, text="0.00 PLN", font=FONT_MONO, text_color=cat.get("color", COLOR_PRIMARY))
            lbl.pack(side="right", padx=(10, 0))
            
            del_btn = ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_SURFACE_2, command=lambda cid=cat["id"]: self.delete_category(cid))
            del_btn.pack(side="right")
            
            self.cat_lbls[cat["id"]] = lbl
            
        add_btn = ctk.CTkButton(self.cat_rows_frame, text="+ Add Category", fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_SURFACE_2, command=self.add_category)
        add_btn.pack(anchor="w", pady=(10, 0))
        self.cat_built = True

    def format_on_blur_pct(self, event, var, callback):
        val = var.get()
        if val:
            try:
                var.set(f"{float(val):.1f}")
                callback()
            except: pass

    def format_on_blur_money(self, event, var, callback):
        val = var.get()
        if val:
            try:
                var.set(f"{float(val):.2f}")
                callback()
            except: pass

    def delete_category(self, cat_id):
        cats = self.controller.data.get("categories", [])
        if len(cats) <= 2: return
        self.controller.data["categories"] = [c for c in cats if c["id"] != cat_id]
        self.build_cat_rows()
        self.calculate_split()
        self.controller.save_data()
        
    def add_category(self):
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="Add Category")
        name = dialog.get_input()
        if name:
            new_cat = {"id": dm.generate_id(), "name": name, "percent": 0.0, "color": COLOR_PRIMARY}
            self.controller.data.setdefault("categories", []).append(new_cat)
            self.build_cat_rows()
            self.calculate_split()
            self.controller.save_data()

    def show_extra_income_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Extra Income")
        dialog.geometry("400x350")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Description:", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        desc_entry = ctk.CTkEntry(dialog)
        desc_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Target:", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        cats = ["All categories proportionally"] + [c["name"] for c in self.controller.data.get("categories", [])]
        cat_menu = ctk.CTkOptionMenu(dialog, values=cats)
        cat_menu.pack(fill="x", padx=20)
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                desc = desc_entry.get()
                if not desc or amt <= 0: return
                
                target = None
                sel_cat = cat_menu.get()
                if sel_cat != "All categories proportionally":
                    target = next((c["id"] for c in self.controller.data.get("categories", []) if c["name"] == sel_cat), None)
                
                new_inc = {
                    "id": dm.generate_id(),
                    "amount": amt,
                    "description": desc,
                    "target_category": target,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                self.controller.data.setdefault("additional_income", []).append(new_inc)
                self.controller.save_data()
                dialog.destroy()
            except: pass
            
        btn = ctk.CTkButton(dialog, text="Save", command=save)
        btn.pack(pady=20)
        
    def calculate_split(self, event=None):
        try:
            total_pct = 0.0
            parsed_pcts = {}
            for cat_id, v in self.cat_vars.items():
                val_str = v.get()
                clean_str = "".join(c for c in val_str.replace(",", ".") if c.isdigit() or c == ".")
                parts = clean_str.split(".")
                if len(parts) > 2:
                    clean_str = parts[0] + "." + "".join(parts[1:])
                if clean_str != val_str:
                    v.set(clean_str)
                    val_str = clean_str
                pct = float(val_str) if val_str else 0.0
                parsed_pcts[cat_id] = pct
                total_pct += pct
                
            if abs(total_pct - 100.0) > 0.01:
                self.sum_warning.configure(text=f"Warning: Sum is {total_pct}% (must be 100%)")
                # Do not save if it doesn't sum to 100%
            else:
                self.sum_warning.configure(text="")
                
            net = self.controller.data["business"].get("net_income", 0.0)
            for cat in self.controller.data.get("categories", []):
                if cat["id"] in parsed_pcts:
                    new_pct = parsed_pcts[cat["id"]]
                    cat["percent"] = new_pct
                    amt = net * (new_pct / 100.0)
                    self.cat_lbls[cat["id"]].configure(text=f"{amt:,.2f} PLN".replace(",", " "))
                    
            if abs(total_pct - 100.0) <= 0.01:
                self.controller.save_data()
        except Exception as e:
            pass

    def calculate(self, event=None):
        try:
            def parse_val(v):
                s = v.get()
                clean_s = "".join(c for c in s.replace(",", ".") if c.isdigit() or c == ".")
                parts = clean_s.split(".")
                if len(parts) > 2:
                    clean_s = parts[0] + "." + "".join(parts[1:])
                if clean_s != s:
                    v.set(clean_s)
                    s = clean_s
                return float(s) if s else 0.0
                
            gross = parse_val(self.vars["gross"])
            vat = parse_val(self.vars["vat"])
            tax = parse_val(self.vars["tax"])
            zus = parse_val(self.vars["zus"])
            net = gross - vat - tax - zus
            
            self.net_lbl.configure(text=f"{net:,.2f} PLN".replace(",", " "))
            
            b = self.controller.data["business"]
            b["gross_invoice"] = gross
            b["vat_deducted"] = vat
            b["income_tax_deducted"] = tax
            b["zus_deducted"] = zus
            b["net_income"] = net
            
            self.calculate_split() # update split labels with new net income
        except:
            pass

    def refresh(self):
        if not self.cat_built:
            self.build_cat_rows()
            
        b = self.controller.data["business"]
        self.vars["gross"].set(str(b.get("gross_invoice", 0.0)))
        self.vars["vat"].set(str(b.get("vat_deducted", 0.0)))
        self.vars["tax"].set(str(b.get("income_tax_deducted", 0.0)))
        self.vars["zus"].set(str(b.get("zus_deducted", 0.0)))
        self.calculate()

class ExpensesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Expenses", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 10))
        
        self.cat_strip = ctk.CTkFrame(self, fg_color="transparent")
        self.cat_strip.pack(fill="x", pady=10)
        
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True)
        bottom_frame.grid_columnconfigure(0, weight=2)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)
        
        list_card = ctk.CTkFrame(bottom_frame, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(list_card, text="Expense List", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=20)
        
        self.scroll_list = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_card = ctk.CTkFrame(bottom_frame, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        form_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(form_card, text="Add Expense", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=20)
        
        self.f_date = ctk.CTkEntry(form_card, placeholder_text="DD/MM/YYYY", fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.f_date.pack(fill="x", padx=20, pady=5)
        self.f_amount_var = ctk.StringVar()
        self.f_amount = ctk.CTkEntry(form_card, textvariable=self.f_amount_var, placeholder_text="Amount (PLN)", fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.f_amount.pack(fill="x", padx=20, pady=5)
        self.f_amount.bind("<KeyRelease>", self.format_amount)
        self.f_amount.bind("<FocusOut>", lambda e: self.format_on_blur_amount())
        self.f_desc = ctk.CTkEntry(form_card, placeholder_text="Description", fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
        self.f_desc.pack(fill="x", padx=20, pady=5)
        
        self.f_cat = ctk.CTkOptionMenu(form_card, values=[], fg_color=COLOR_SURFACE_2, button_color=COLOR_PRIMARY, text_color=COLOR_TEXT)
        self.f_cat.pack(fill="x", padx=20, pady=5)
        
        btn = ctk.CTkButton(form_card, text="Add Expense", command=self.add_expense)
        btn.pack(fill="x", padx=20, pady=20)
        
    def format_amount(self, event=None):
        val = self.f_amount_var.get()
        clean_val = "".join(c for c in val.replace(",", ".") if c.isdigit() or c == ".")
        parts = clean_val.split(".")
        if len(parts) > 2:
            clean_val = parts[0] + "." + "".join(parts[1:])
        if clean_val != val:
            self.f_amount_var.set(clean_val)
            
    def format_on_blur_amount(self):
        val = self.f_amount_var.get()
        if val:
            try:
                self.f_amount_var.set(f"{float(val):.2f}")
            except: pass

    def add_expense(self):
        try:
            amt = float(self.f_amount.get().replace(",", "."))
            desc = self.f_desc.get()
            if not desc or amt <= 0: return
            
            cat_name = self.f_cat.get()
            cat_id = next((c["id"] for c in self.controller.data.get("categories", []) if c["name"] == cat_name), "daily_life")
            
            new_exp = {
                "id": dm.generate_id(),
                "date": self.f_date.get() or datetime.now().strftime("%d/%m/%Y"),
                "amount": amt,
                "description": desc,
                "category_id": cat_id,
            }
            self.controller.data.setdefault("expenses", []).append(new_exp)
            self.controller.save_data()
            
            self.f_amount.delete(0, 'end')
            self.f_desc.delete(0, 'end')
            self.refresh()
        except:
            pass

    def delete_expense(self, exp_id):
        self.controller.data["expenses"] = [e for e in self.controller.data.get("expenses", []) if e["id"] != exp_id]
        self.controller.save_data()
        self.refresh()

    def refresh(self):
        data = self.controller.data
        cat_names = [c["name"] for c in data.get("categories", [])]
        if cat_names:
            self.f_cat.configure(values=cat_names)
            if not self.f_cat.get(): self.f_cat.set(cat_names[0])
            
        for w in self.cat_strip.winfo_children():
            w.destroy()
            
        for cat in data.get("categories", []):
            c_frame = ctk.CTkFrame(self.cat_strip, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            c_frame.pack(side="left", fill="both", expand=True, padx=5)
            rem = dm.get_remaining_amount(data, cat["id"])
            ctk.CTkLabel(c_frame, text=f"{cat['name']}\n{rem:,.2f} PLN", font=FONT_BODY, text_color=COLOR_TEXT).pack(pady=10)
            
        for w in self.scroll_list.winfo_children():
            w.destroy()
            
        for exp in reversed(data.get("expenses", [])):
            row = ctk.CTkFrame(self.scroll_list, fg_color=COLOR_SURFACE_2, corner_radius=8)
            row.pack(fill="x", pady=2)
            
            lbl_text = f"{exp.get('date', '')} | {exp.get('description', '')}"
            ctk.CTkLabel(row, text=lbl_text, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=5)
            
            del_btn = ctk.CTkButton(row, text="🗑", width=30, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda eid=exp["id"]: self.delete_expense(eid))
            del_btn.pack(side="right", padx=5)
            
            amt_text = f"{exp.get('amount', 0):,.2f} PLN"
            ctk.CTkLabel(row, text=amt_text, font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=10)

class CashFlowView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Cash Flow Buffer", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        self.card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        self.card.pack(fill="x", pady=10)
        
        self.rows_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.rows_frame.pack(fill="x", padx=20, pady=20)
        
        sep = ctk.CTkFrame(self.card, height=1, fg_color=COLOR_BORDER)
        sep.pack(fill="x", padx=20)
        
        self.summary_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=20)
        
        self.tot_topup_lbl = ctk.CTkLabel(self.summary_frame, text="Total to top up: 0.00 PLN", font=FONT_BODY, text_color=COLOR_TEXT)
        self.tot_topup_lbl.pack(anchor="w", pady=2)
        
        self.net_inc_lbl = ctk.CTkLabel(self.summary_frame, text="Net income this month: 0.00 PLN", font=FONT_BODY, text_color=COLOR_TEXT)
        self.net_inc_lbl.pack(anchor="w", pady=2)
        
        sep2 = ctk.CTkFrame(self.summary_frame, height=1, fg_color=COLOR_BORDER)
        sep2.pack(fill="x", pady=10)
        
        self.rem_sav_lbl = ctk.CTkLabel(self.summary_frame, text="Remaining for savings: 0.00 PLN", font=FONT_TITLE, text_color=COLOR_SUCCESS)
        self.rem_sav_lbl.pack(anchor="w")
        
        self.current_vars = {}
        self.topup_lbls = {}
        self.built = False
        
    def build_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()
            
        buffer_data = self.controller.data.get("cashflow_buffer", {})
        minimums = buffer_data.get("minimums", {})
        current = buffer_data.get("current_on_account", {})
        
        for cat_id, min_val in minimums.items():
            row = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
            row.pack(fill="x", pady=10)
            
            lbl_name = cat_id.replace("_", " ").title()
            ctk.CTkLabel(row, text=lbl_name, font=FONT_LABEL, text_color=COLOR_TEXT, width=150, anchor="w").pack(side="left")
            
            ctk.CTkLabel(row, text=f"Minimum: {min_val:,.2f} PLN", font=FONT_BODY, text_color=COLOR_TEXT_MUTED, width=180, anchor="w").pack(side="left")
            
            ctk.CTkLabel(row, text="I currently have:", font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=(10, 5))
            
            var = ctk.StringVar(value=str(current.get(cat_id, 0.0)))
            self.current_vars[cat_id] = var
            entry = ctk.CTkEntry(row, textvariable=var, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, width=100)
            entry.pack(side="left", padx=5)
            ctk.CTkLabel(row, text="PLN", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left")
            
            entry.bind("<KeyRelease>", self.calculate)
            entry.bind("<FocusOut>", lambda e, v=var: self.format_on_blur(e, v))
            
            ctk.CTkLabel(row, text="→ Top up:", font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=(20, 5))
            t_lbl = ctk.CTkLabel(row, text="0.00 PLN", font=FONT_MONO, text_color=COLOR_PRIMARY)
            t_lbl.pack(side="left")
            self.topup_lbls[cat_id] = t_lbl
            
        self.built = True
        
    def format_on_blur(self, event, var):
        val = var.get()
        if val:
            try:
                var.set(f"{float(val):.2f}")
                self.calculate()
            except: pass
        
    def calculate(self, event=None):
        try:
            buffer_data = self.controller.data.get("cashflow_buffer", {})
            minimums = buffer_data.get("minimums", {})
            
            total_topup = 0.0
            
            for cat_id, var in self.current_vars.items():
                val_str = var.get()
                if "," in val_str:
                    val_str = val_str.replace(",", ".")
                    var.set(val_str)
                cur_val = float(val_str) if val_str else 0.0
                buffer_data.setdefault("current_on_account", {})[cat_id] = cur_val
                
                min_val = minimums.get(cat_id, 0.0)
                topup = max(0.0, min_val - cur_val)
                total_topup += topup
                self.topup_lbls[cat_id].configure(text=f"{topup:,.2f} PLN".replace(",", " "))
                
            net_income = self.controller.data.get("business", {}).get("net_income", 0.0)
            rem = net_income - total_topup
            
            self.tot_topup_lbl.configure(text=f"Total to top up: {total_topup:,.2f} PLN".replace(",", " "))
            self.net_inc_lbl.configure(text=f"Net income this month: {net_income:,.2f} PLN".replace(",", " "))
            
            self.rem_sav_lbl.configure(
                text=f"Remaining for savings: {rem:,.2f} PLN".replace(",", " "),
                text_color=COLOR_SUCCESS if rem >= 0 else COLOR_ERROR
            )
            
            self.controller.save_data()
        except:
            pass

    def refresh(self):
        if not self.built:
            self.build_rows()
            
        buffer_data = self.controller.data.get("cashflow_buffer", {})
        current = buffer_data.get("current_on_account", {})
        
        for cat_id, var in self.current_vars.items():
            var.set(str(current.get(cat_id, 0.0)))
            
        self.calculate()

class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="History", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(card, text="Monthly history will appear here.", text_color=COLOR_TEXT_MUTED).pack(pady=40)

    def refresh(self):
        pass

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="Settings", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(card, text="Settings configuration will appear here.", text_color=COLOR_TEXT_MUTED).pack(pady=40)

    def refresh(self):
        pass

if __name__ == "__main__":
    app = FlorinApp()
    app.mainloop()
