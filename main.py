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
        net = dm.get_net_income(data)
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
        self.editing = False
        
        # Header with title + edit toggle
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(title_row, text="Income", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.edit_btn = ctk.CTkButton(title_row, text="✎ Edit", width=80, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.toggle_edit)
        self.edit_btn.pack(side="right")
        
        # Net total summary card
        total_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        total_card.pack(fill="x", pady=(0, 10))
        total_row = ctk.CTkFrame(total_card, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(total_row, text="Total Income", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.net_lbl = ctk.CTkLabel(total_row, text="0.00 PLN", font=FONT_MONO_LG, text_color=COLOR_INCOME)
        self.net_lbl.pack(side="right")
        
        # Items list card
        items_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        items_card.pack(fill="both", expand=True, pady=5)
        
        hdr = ctk.CTkFrame(items_card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(hdr, text="Items", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.add_addition_btn = ctk.CTkButton(hdr, text="+ Addition", width=100, fg_color=COLOR_SUCCESS, hover_color="#5A9D7A", command=lambda: self.add_item("addition"))
        self.add_deduction_btn = ctk.CTkButton(hdr, text="− Deduction", width=100, fg_color=COLOR_ERROR, hover_color="#B05A5A", command=lambda: self.add_item("deduction"))
        
        self.items_scroll = ctk.CTkScrollableFrame(items_card, fg_color="transparent")
        self.items_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Category Split Section
        self.split_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        self.split_card.pack(fill="x", pady=10)
        
        header_row = ctk.CTkFrame(self.split_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header_row, text="Category Split", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        
        self.sum_warning = ctk.CTkLabel(header_row, text="", font=FONT_BODY, text_color=COLOR_WARNING)
        self.sum_warning.pack(side="right")
        
        self.cat_rows_frame = ctk.CTkFrame(self.split_card, fg_color="transparent")
        self.cat_rows_frame.pack(fill="x", padx=20, pady=10)
        
        self.cat_vars = {}
        self.cat_lbls = {}
        self.cat_built = False

    def toggle_edit(self):
        self.editing = not self.editing
        if self.editing:
            self.edit_btn.configure(text="✓ Done", fg_color=COLOR_PRIMARY, text_color="#FFFFFF", hover_color=COLOR_PRIMARY_HOVER)
            self.add_addition_btn.pack(side="right", padx=5)
            self.add_deduction_btn.pack(side="right", padx=5)
        else:
            self.edit_btn.configure(text="✎ Edit", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER)
            self.add_addition_btn.pack_forget()
            self.add_deduction_btn.pack_forget()
        self.build_items_list()
        self.build_cat_rows()
        self.calculate_split()

    def add_item(self, item_type):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Add {'Addition' if item_type == 'addition' else 'Deduction'}")
        dialog.geometry("400x280")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Name:", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        
        cat_var = ctk.StringVar(value="None")
        if item_type == "addition":
            ctk.CTkLabel(dialog, text="Target category:", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
            cats = ["None"] + [c["name"] for c in self.controller.data.get("categories", [])]
            ctk.CTkOptionMenu(dialog, values=cats, variable=cat_var).pack(fill="x", padx=20)
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                cat_id = None
                if cat_var.get() != "None":
                    cat_id = next((c["id"] for c in self.controller.data.get("categories", []) if c["name"] == cat_var.get()), None)
                item = {"id": dm.generate_id(), "name": name, "amount": amt, "type": item_type, "category_id": cat_id}
                self.controller.data.setdefault("income_items", []).append(item)
                self.controller.save_data()
                dialog.destroy()
                self.refresh()
            except:
                pass
        
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

    def edit_item(self, item_id):
        item = next((i for i in self.controller.data.get("income_items", []) if i["id"] == item_id), None)
        if not item:
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Item")
        dialog.geometry("400x280")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Name:", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.insert(0, item["name"])
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.insert(0, str(item["amount"]))
        amt_entry.pack(fill="x", padx=20)
        
        cat_var = ctk.StringVar(value="None")
        if item["type"] == "addition":
            ctk.CTkLabel(dialog, text="Target category:", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
            cats = ["None"] + [c["name"] for c in self.controller.data.get("categories", [])]
            cur_cat = next((c["name"] for c in self.controller.data.get("categories", []) if c["id"] == item.get("category_id")), "None")
            cat_var.set(cur_cat)
            ctk.CTkOptionMenu(dialog, values=cats, variable=cat_var).pack(fill="x", padx=20)
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                item["name"] = name
                item["amount"] = amt
                if item["type"] == "addition":
                    item["category_id"] = next((c["id"] for c in self.controller.data.get("categories", []) if c["name"] == cat_var.get()), None)
                self.controller.save_data()
                dialog.destroy()
                self.refresh()
            except:
                pass
        
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

    def delete_item(self, item_id):
        self.controller.data["income_items"] = [i for i in self.controller.data.get("income_items", []) if i["id"] != item_id]
        self.controller.save_data()
        self.refresh()

    def build_items_list(self):
        for w in self.items_scroll.winfo_children():
            w.destroy()
        
        items = self.controller.data.get("income_items", [])
        cats = {c["id"]: c for c in self.controller.data.get("categories", [])}
        
        for item in items:
            is_add = item["type"] == "addition"
            row_color = "#E8F5E9" if is_add else "#FFEBEE"
            row = ctk.CTkFrame(self.items_scroll, fg_color=row_color, corner_radius=8)
            row.pack(fill="x", pady=2)
            
            sign = "+" if is_add else "−"
            sign_color = COLOR_SUCCESS if is_add else COLOR_ERROR
            ctk.CTkLabel(row, text=sign, font=FONT_MONO_LG, text_color=sign_color, width=24).pack(side="left", padx=(10, 5), pady=8)
            ctk.CTkLabel(row, text=item["name"], font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=5, pady=8)
            
            # Category badge
            cat_id = item.get("category_id")
            if cat_id and cat_id in cats:
                badge = ctk.CTkLabel(row, text=cats[cat_id]["name"], font=FONT_SMALL, text_color="#FFFFFF", fg_color=cats[cat_id].get("color", COLOR_PRIMARY), corner_radius=6, width=70)
                badge.pack(side="left", padx=10, pady=8)
            
            if self.editing:
                ctk.CTkButton(row, text="🗑", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.delete_item(iid)).pack(side="right", padx=5, pady=8)
                ctk.CTkButton(row, text="✎", width=28, height=28, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.edit_item(iid)).pack(side="right", padx=2, pady=8)
            
            # Amount
            amt_text = f"{sign} {item['amount']:,.2f} PLN".replace(",", " ")
            ctk.CTkLabel(row, text=amt_text, font=FONT_MONO, text_color=sign_color).pack(side="right", padx=10, pady=8)
        
    def build_cat_rows(self):
        for widget in self.cat_rows_frame.winfo_children():
            widget.destroy()
        self.cat_vars = {}
        self.cat_lbls = {}
            
        data = self.controller.data
        cats = data.get("categories", [])
        
        for cat in cats:
            row = ctk.CTkFrame(self.cat_rows_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=120, anchor="w").pack(side="left")
            
            var = ctk.StringVar(value=str(cat["percent"]))
            self.cat_vars[cat["id"]] = var
            
            if self.editing:
                entry = ctk.CTkEntry(row, textvariable=var, font=FONT_MONO, text_color=COLOR_TEXT, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, width=60)
                entry.pack(side="left", padx=10)
                ctk.CTkLabel(row, text="%", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left")
                entry.bind("<KeyRelease>", self.calculate_split)
                entry.bind("<FocusOut>", lambda e, v=var: self.format_on_blur_pct(e, v))
                del_btn = ctk.CTkButton(row, text="×", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_SURFACE_2, command=lambda cid=cat["id"]: self.delete_category(cid))
                del_btn.pack(side="right")
            else:
                ctk.CTkLabel(row, text=f"{cat['percent']:.1f}%", font=FONT_MONO, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10)
            
            lbl = ctk.CTkLabel(row, text="0.00 PLN", font=FONT_MONO, text_color=cat.get("color", COLOR_PRIMARY))
            lbl.pack(side="right", padx=(10, 0))
            self.cat_lbls[cat["id"]] = lbl
        
        if self.editing:
            add_btn = ctk.CTkButton(self.cat_rows_frame, text="+ Add Category", fg_color="transparent", text_color=COLOR_PRIMARY, hover_color=COLOR_SURFACE_2, command=self.add_category)
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
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="Add Category")
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
                self.sum_warning.configure(text=f"Warning: Sum is {total_pct:.1f}% (must be 100%)")
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
                    self.cat_lbls[cat["id"]].configure(text=f"{amt:,.2f} PLN".replace(",", " "))
                    
            if abs(total_pct - 100.0) <= 0.01:
                self.controller.save_data()
        except:
            pass

    def refresh(self):
        if not self.cat_built:
            self.build_cat_rows()
        self.build_items_list()
        net = dm.get_net_income(self.controller.data)
        self.net_lbl.configure(text=f"{net:,.2f} PLN".replace(",", " "))
        self.calculate_split()

class ExpensesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Expenses", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(header, text="⚙ Categories", width=120, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.open_category_manager).pack(side="right", padx=5)
        ctk.CTkButton(header, text="+ Add Expense", width=120, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.open_add_expense).pack(side="right", padx=5)

        # Split bucket summary strip
        self.split_strip = ctk.CTkFrame(self, fg_color="transparent")
        self.split_strip.pack(fill="x", pady=(0, 5))

        # Tag filter bar
        self.tag_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.tag_bar.pack(fill="x", pady=(0, 10))
        self.active_tag = None  # None = no filter
        self.expanded_cats = {}  # cat_id -> bool, tracks accordion state

        # Main content: scrollable table grouped by expense category
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    # --- Add Expense Dialog ---
    def open_add_expense(self, edit_exp=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Expense" if edit_exp else "Add Expense")
        dialog.geometry("440x420")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        data = self.controller.data

        ctk.CTkLabel(dialog, text="Date (DD/MM/YYYY):", anchor="w").pack(fill="x", padx=20, pady=(15, 3))
        date_entry = ctk.CTkEntry(dialog)
        date_entry.pack(fill="x", padx=20)
        date_entry.insert(0, edit_exp["date"] if edit_exp else datetime.now().strftime("%d/%m/%Y"))

        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        if edit_exp:
            amt_entry.insert(0, f"{edit_exp['amount']:.2f}")

        ctk.CTkLabel(dialog, text="Expense Category:", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        exp_cats = dm.get_expense_categories(data)
        exp_cat_names = [c["name"] for c in exp_cats] or ["(none)"]
        exp_cat_var = ctk.StringVar(value=exp_cat_names[0])
        if edit_exp:
            cur = next((c["name"] for c in exp_cats if c["id"] == edit_exp.get("expense_category_id")), exp_cat_names[0])
            exp_cat_var.set(cur)
        ctk.CTkOptionMenu(dialog, values=exp_cat_names, variable=exp_cat_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text="Income Split Bucket:", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        split_cats = data.get("categories", [])
        split_names = [c["name"] for c in split_cats] or ["(none)"]
        split_var = ctk.StringVar(value=split_names[0])
        if edit_exp:
            cur_split = next((c["name"] for c in split_cats if c["id"] == edit_exp.get("category_id")), split_names[0])
            split_var.set(cur_split)
        ctk.CTkOptionMenu(dialog, values=split_names, variable=split_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text="Description (optional):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        desc_entry = ctk.CTkEntry(dialog)
        desc_entry.pack(fill="x", padx=20)
        if edit_exp:
            desc_entry.insert(0, edit_exp.get("description", ""))

        ctk.CTkLabel(dialog, text="Tags (comma-separated, optional):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        tags_entry = ctk.CTkEntry(dialog)
        tags_entry.pack(fill="x", padx=20)
        if edit_exp:
            tags_entry.insert(0, ", ".join(edit_exp.get("tags", [])))

        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                if amt <= 0:
                    return
            except:
                return
            date_val = date_entry.get().strip() or datetime.now().strftime("%d/%m/%Y")
            exp_cat_id = next((c["id"] for c in exp_cats if c["name"] == exp_cat_var.get()), None)
            split_id = next((c["id"] for c in split_cats if c["name"] == split_var.get()), None)
            desc = desc_entry.get().strip()
            tags = [t.strip() for t in tags_entry.get().split(",") if t.strip()]

            if edit_exp:
                dm.edit_expense(data, edit_exp["id"], date=date_val, amount=amt, expense_category_id=exp_cat_id, category_id=split_id, description=desc, tags=tags)
            else:
                dm.add_expense(data, date_val, amt, split_id, expense_category_id=exp_cat_id, description=desc, tags=tags)
            self.controller.save_data()
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Save", command=save).pack(fill="x", padx=20, pady=15)

    # --- Category Manager Dialog ---
    def open_category_manager(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Expense Categories")
        dialog.geometry("400x450")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        data = self.controller.data

        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def rebuild():
            for w in list_frame.winfo_children():
                w.destroy()
            for cat in dm.get_expense_categories(data):
                row = ctk.CTkFrame(list_frame, fg_color=COLOR_SURFACE_2, corner_radius=8)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=8)
                ctk.CTkButton(row, text="🗑", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda cid=cat["id"]: do_delete(cid)).pack(side="right", padx=5, pady=5)
                ctk.CTkButton(row, text="✎", width=28, height=28, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda cid=cat["id"], cn=cat["name"]: do_edit(cid, cn)).pack(side="right", padx=2, pady=5)

        def do_delete(cid):
            dm.delete_expense_category(data, cid)
            self.controller.save_data()
            rebuild()

        def do_edit(cid, current_name):
            d = ctk.CTkInputDialog(text="New name:", title="Rename Category")
            new_name = d.get_input()
            if new_name and new_name.strip():
                dm.edit_expense_category(data, cid, new_name.strip())
                self.controller.save_data()
                rebuild()

        rebuild()

        # Add new category
        add_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=10)
        new_entry = ctk.CTkEntry(add_frame, placeholder_text="New category name")
        new_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def do_add():
            name = new_entry.get().strip()
            if name:
                dm.add_expense_category(data, name)
                self.controller.save_data()
                new_entry.delete(0, "end")
                rebuild()

        ctk.CTkButton(add_frame, text="Add", width=60, command=do_add).pack(side="right")

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

    # --- Delete expense ---
    def delete_expense(self, exp_id):
        dm.delete_expense(self.controller.data, exp_id)
        self.controller.save_data()
        self.refresh()

    # --- Refresh / Build Table ---
    def refresh(self):
        data = self.controller.data

        # Ensure expense_categories exist (migration for old data)
        if "expense_categories" not in data:
            data["expense_categories"] = list(dm.DEFAULT_EXPENSE_CATEGORIES)

        # Split bucket summary strip
        for w in self.split_strip.winfo_children():
            w.destroy()
        for cat in data.get("categories", []):
            allocated = dm.get_allocated_amount(data, cat["id"])
            spent = dm.get_spent_amount(data, cat["id"])
            rem = allocated - spent
            color = COLOR_SUCCESS if rem >= 0 else COLOR_ERROR
            pill = ctk.CTkFrame(self.split_strip, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            pill.pack(side="left", fill="both", expand=True, padx=3)
            ctk.CTkLabel(pill, text=cat["name"], font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=(8, 0))
            ctk.CTkLabel(pill, text=f"{rem:,.2f} PLN", font=FONT_MONO, text_color=color).pack(pady=(0, 8))

        # Build tag bar
        for w in self.tag_bar.winfo_children():
            w.destroy()
        all_tags = set()
        for exp in data.get("expenses", []):
            for t in exp.get("tags", []):
                all_tags.add(t)
        if all_tags:
            ctk.CTkLabel(self.tag_bar, text="Tags:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 5))
            for tag in sorted(all_tags):
                is_active = self.active_tag == tag
                btn_fg = COLOR_PRIMARY if is_active else COLOR_SURFACE_2
                btn_text_color = "#FFFFFF" if is_active else COLOR_TEXT
                btn = ctk.CTkButton(self.tag_bar, text=tag, height=24, width=len(tag)*8+20, font=FONT_SMALL, fg_color=btn_fg, text_color=btn_text_color, hover_color=COLOR_PRIMARY_HOVER if is_active else COLOR_BORDER, corner_radius=12, command=lambda t=tag: self.set_tag_filter(t))
                btn.pack(side="left", padx=2)
            if self.active_tag:
                ctk.CTkButton(self.tag_bar, text="✕ Clear", height=24, width=60, font=FONT_SMALL, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda: self.set_tag_filter(self.active_tag)).pack(side="left", padx=5)

        # Table content
        for w in self.scroll.winfo_children():
            w.destroy()

        split_cats = {c["id"]: c["name"] for c in data.get("categories", [])}

        # If tag filter active: show flat list of matching expenses + total
        if self.active_tag:
            filtered = [e for e in data.get("expenses", []) if self.active_tag in e.get("tags", [])]
            total = sum(e["amount"] for e in filtered)

            hdr = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
            hdr.pack(fill="x", pady=(5, 5))
            ctk.CTkLabel(hdr, text=f"  Tag: \"{self.active_tag}\" ({len(filtered)} expenses)", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(hdr, text=f"Total: {total:,.2f} PLN  ", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=10, pady=8)

            for exp in sorted(filtered, key=lambda e: e.get("date", ""), reverse=True):
                row = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE_2, corner_radius=8)
                row.pack(fill="x", pady=1, padx=10)
                date_txt = exp.get("date", "")
                desc_txt = exp.get("description", "")
                tags = exp.get("tags", [])
                split_name = split_cats.get(exp.get("category_id", ""), "?")
                left_text = f"{date_txt}  {desc_txt}"
                if tags:
                    left_text += f"  [{', '.join(tags)}]"
                ctk.CTkLabel(row, text=left_text, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=5)
                ctk.CTkButton(row, text="🗑", width=26, height=26, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda eid=exp["id"]: self.delete_expense(eid)).pack(side="right", padx=3, pady=3)
                ctk.CTkButton(row, text="✎", width=26, height=26, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=1, pady=3)
                ctk.CTkLabel(row, text=f"{exp['amount']:,.2f}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=5, pady=5)
                ctk.CTkLabel(row, text=split_name, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=5, pady=5)
            return

        # Default: grouped by expense category (accordion)
        grouped = dm.get_expenses_by_expense_category(data)
        exp_cats = {c["id"]: c["name"] for c in dm.get_expense_categories(data)}

        cat_order = list(exp_cats.keys())
        if "uncategorized" in grouped and "uncategorized" not in cat_order:
            cat_order.append("uncategorized")

        for cat_id in cat_order:
            expenses = grouped.get(cat_id, [])
            if not expenses:
                continue
            cat_name = exp_cats.get(cat_id, "Uncategorized")
            total = sum(e["amount"] for e in expenses)
            is_expanded = self.expanded_cats.get(cat_id, False)
            chevron = "▲" if is_expanded else "▼"

            # Clickable header
            hdr = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER, cursor="hand2")
            hdr.pack(fill="x", pady=(10, 2))
            ctk.CTkLabel(hdr, text=f"  {chevron}  {cat_name}", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(hdr, text=f"Total: {total:,.2f} PLN  ", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=10, pady=8)
            # Bind click on header and all children
            hdr.bind("<Button-1>", lambda e, cid=cat_id: self.toggle_category(cid))
            for child in hdr.winfo_children():
                child.bind("<Button-1>", lambda e, cid=cat_id: self.toggle_category(cid))

            # Split breakdown (always visible)
            breakdown = dm.get_expense_category_split_breakdown(data, cat_id)
            if breakdown:
                parts = [f"{split_cats.get(sid, sid)}: {amt:,.2f}" for sid, amt in breakdown.items()]
                bd_text = "    ↳ " + " · ".join(parts)
                ctk.CTkLabel(self.scroll, text=bd_text, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(0, 4))

            # Expense rows (only when expanded)
            if is_expanded:
                for exp in sorted(expenses, key=lambda e: e.get("date", ""), reverse=True):
                    row = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE_2, corner_radius=8)
                    row.pack(fill="x", pady=1, padx=10)
                    date_txt = exp.get("date", "")
                    desc_txt = exp.get("description", "")
                    tags = exp.get("tags", [])
                    split_name = split_cats.get(exp.get("category_id", ""), "?")
                    left_text = f"{date_txt}  {desc_txt}"
                    if tags:
                        left_text += f"  [{', '.join(tags)}]"
                    ctk.CTkLabel(row, text=left_text, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=5)
                    ctk.CTkButton(row, text="🗑", width=26, height=26, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda eid=exp["id"]: self.delete_expense(eid)).pack(side="right", padx=3, pady=3)
                    ctk.CTkButton(row, text="✎", width=26, height=26, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=1, pady=3)
                    ctk.CTkLabel(row, text=f"{exp['amount']:,.2f}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=5, pady=5)
                    ctk.CTkLabel(row, text=split_name, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=5, pady=5)

class CashFlowView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.editing = False

        # Header with edit toggle
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(hdr, text="Cash Flow", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.edit_btn = ctk.CTkButton(hdr, text="✎ Edit", width=80, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.toggle_edit)
        self.edit_btn.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.built = False
        self.balance_vars = {}
        self.topup_lbls = {}
        self.timestamp_lbls = {}
        self.shared_assumed_var = ctk.StringVar(value="0.00")
        self.saved_assumed_var = ctk.StringVar(value="0.00")
        self.shared_actual_var = ctk.StringVar(value="0.00")
        self.saved_actual_lbl = None
        self.total_topup_lbl = None
        self.net_income_lbl = None

    def toggle_edit(self):
        if self.editing:
            self.calculate()
            self.editing = False
            self.edit_btn.configure(text="✎ Edit", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER)
        else:
            self.editing = True
            self.edit_btn.configure(text="✓ Done", fg_color=COLOR_PRIMARY, text_color="#FFFFFF", hover_color=COLOR_PRIMARY_HOVER)
        self.build()

    def build(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        data = self.controller.data
        config = self.controller.config
        targets = dm.get_cashflow_targets(config)
        cf = dm.get_cashflow(data)

        # === Current Accounts ===
        ctk.CTkLabel(self.scroll, text="Accounts to Replenish", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 8))

        p1_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        p1_card.pack(fill="x", pady=(0, 15))

        # Column headers
        hdr_row = ctk.CTkFrame(p1_card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(hdr_row, text="Account", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(hdr_row, text="Target", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=100, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(hdr_row, text="Current Balance", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=130, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(hdr_row, text="To Transfer", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=100, anchor="w").pack(side="left", padx=5)

        self.balance_vars = {}
        self.topup_lbls = {}
        self.timestamp_lbls = {}

        for t in targets:
            tid = t["id"]
            acct = cf.get("current_accounts", {}).get(tid, {"balance": 0.0, "updated_at": ""})

            row = ctk.CTkFrame(p1_card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)

            ctk.CTkLabel(row, text=t["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{t['target']:,.2f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=100, anchor="w").pack(side="left", padx=5)

            var = ctk.StringVar(value=f"{acct['balance']:.2f}" if acct["balance"] else "0.00")
            self.balance_vars[tid] = var

            if self.editing:
                entry = ctk.CTkEntry(row, textvariable=var, font=FONT_MONO, width=110, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
                entry.pack(side="left", padx=5)
                entry.bind("<KeyRelease>", self.calculate)
                entry.bind("<FocusOut>", lambda e, v=var, tid_=tid: self.on_balance_blur(v, tid_))
            else:
                ctk.CTkLabel(row, text=var.get(), font=FONT_MONO, text_color=COLOR_TEXT, width=110, anchor="w").pack(side="left", padx=5)

            topup_lbl = ctk.CTkLabel(row, text="0.00", font=FONT_MONO, text_color=COLOR_PRIMARY, width=100, anchor="w")
            topup_lbl.pack(side="left", padx=5)
            self.topup_lbls[tid] = topup_lbl

            ts_text = acct.get("updated_at", "")
            ts_lbl = ctk.CTkLabel(row, text=f"Updated: {ts_text}" if ts_text else "", font=FONT_SMALL, text_color=COLOR_TEXT_FAINT)
            ts_lbl.pack(side="right", padx=10)
            self.timestamp_lbls[tid] = ts_lbl

        # Total to transfer
        tot_row = ctk.CTkFrame(p1_card, fg_color="transparent")
        tot_row.pack(fill="x", padx=15, pady=(10, 15))
        ctk.CTkLabel(tot_row, text="Total to transfer:", font=FONT_LABEL, text_color=COLOR_TEXT).pack(side="left")
        self.total_topup_lbl = ctk.CTkLabel(tot_row, text="0.00 PLN", font=FONT_MONO_LG, text_color=COLOR_PRIMARY)
        self.total_topup_lbl.pack(side="left", padx=10)

        # === Savings & Shared Goals ===
        ctk.CTkLabel(self.scroll, text="Savings & Shared Goals", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", pady=(10, 8))

        p2_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        p2_card.pack(fill="x", pady=(0, 15))

        cats = data.get("categories", [])
        shared_cat = next((c for c in cats if c["id"] == "shared"), None)
        saved_cat = next((c for c in cats if c["id"] == "saved"), None)
        shared_calc = dm.get_allocated_amount(data, "shared") if shared_cat else 0.0
        saved_calc = dm.get_allocated_amount(data, "saved") if saved_cat else 0.0

        # Grid header
        g_hdr = ctk.CTkFrame(p2_card, fg_color="transparent")
        g_hdr.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(g_hdr, text="", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(g_hdr, text="Shared", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=140, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(g_hdr, text="Saved", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=140, anchor="center").pack(side="left", padx=10)

        # Row: Calculated (always read-only)
        r_calc = ctk.CTkFrame(p2_card, fg_color="transparent")
        r_calc.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(r_calc, text="Calculated", font=FONT_LABEL, text_color=COLOR_TEXT, width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(r_calc, text=f"{shared_calc:,.2f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=140, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=6).pack(side="left", padx=10, pady=2)
        ctk.CTkLabel(r_calc, text=f"{saved_calc:,.2f}", font=FONT_MONO, text_color=COLOR_TEXT_MUTED, width=140, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=6).pack(side="left", padx=10, pady=2)

        # Row: Assumed
        r_assumed = ctk.CTkFrame(p2_card, fg_color="transparent")
        r_assumed.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(r_assumed, text="Assumed", font=FONT_LABEL, text_color=COLOR_TEXT, width=120, anchor="w").pack(side="left")
        self.shared_assumed_var.set(f"{cf.get('shared_assumed', 0.0):.2f}")
        self.saved_assumed_var.set(f"{cf.get('saved_assumed', 0.0):.2f}")
        if self.editing:
            ctk.CTkEntry(r_assumed, textvariable=self.shared_assumed_var, font=FONT_MONO, width=140, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=10)
            ctk.CTkEntry(r_assumed, textvariable=self.saved_assumed_var, font=FONT_MONO, width=140, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER).pack(side="left", padx=10)
        else:
            ctk.CTkLabel(r_assumed, text=self.shared_assumed_var.get(), font=FONT_MONO, text_color=COLOR_TEXT, width=140, anchor="center").pack(side="left", padx=10)
            ctk.CTkLabel(r_assumed, text=self.saved_assumed_var.get(), font=FONT_MONO, text_color=COLOR_TEXT, width=140, anchor="center").pack(side="left", padx=10)

        # Row: Actual
        r_actual = ctk.CTkFrame(p2_card, fg_color="transparent")
        r_actual.pack(fill="x", padx=15, pady=(4, 15))
        ctk.CTkLabel(r_actual, text="Actual", font=FONT_LABEL, text_color=COLOR_TEXT, width=120, anchor="w").pack(side="left")
        self.shared_actual_var.set(f"{cf.get('shared_actual', 0.0):.2f}")
        if self.editing:
            shared_entry = ctk.CTkEntry(r_actual, textvariable=self.shared_actual_var, font=FONT_MONO, width=140, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER)
            shared_entry.pack(side="left", padx=10)
            shared_entry.bind("<KeyRelease>", self.calculate)
            shared_entry.bind("<FocusOut>", lambda e: self.calculate())
        else:
            ctk.CTkLabel(r_actual, text=self.shared_actual_var.get(), font=FONT_MONO, text_color=COLOR_TEXT, width=140, anchor="center").pack(side="left", padx=10)

        self.saved_actual_lbl = ctk.CTkLabel(r_actual, text="0.00", font=FONT_MONO_LG, text_color=COLOR_SUCCESS, width=140, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=6)
        self.saved_actual_lbl.pack(side="left", padx=10, pady=2)

        # Net income display
        sep = ctk.CTkFrame(p2_card, height=1, fg_color=COLOR_BORDER)
        sep.pack(fill="x", padx=15)
        net_row = ctk.CTkFrame(p2_card, fg_color="transparent")
        net_row.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(net_row, text="Net Income:", font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left")
        self.net_income_lbl = ctk.CTkLabel(net_row, text="0.00 PLN", font=FONT_MONO, text_color=COLOR_INCOME)
        self.net_income_lbl.pack(side="left", padx=10)

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
            self.timestamp_lbls[tid].configure(text=f"Updated: {acct['updated_at']}")
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
                val_str = var.get().replace(",", ".")
                balance = float(val_str) if val_str else 0.0
                cf.setdefault("current_accounts", {}).setdefault(tid, {"balance": 0.0, "updated_at": ""})["balance"] = balance
                topup = max(0.0, t["target"] - balance)
                total_topup += topup
                self.topup_lbls[tid].configure(text=f"{topup:,.2f}")

            self.total_topup_lbl.configure(text=f"{total_topup:,.2f} PLN")

            # Part 2: save all manual values
            net_income = dm.get_net_income(data)
            self.net_income_lbl.configure(text=f"{net_income:,.2f} PLN")

            shared_actual = float(self.shared_actual_var.get().replace(",", ".") or "0")
            cf["shared_actual"] = shared_actual

            shared_assumed = float(self.shared_assumed_var.get().replace(",", ".") or "0")
            cf["shared_assumed"] = shared_assumed

            saved_assumed = float(self.saved_assumed_var.get().replace(",", ".") or "0")
            cf["saved_assumed"] = saved_assumed

            # Actual Saved = Net Income - Total Top-ups - Shared Actual
            actual_saved = net_income - total_topup - shared_actual
            color = COLOR_SUCCESS if actual_saved >= 0 else COLOR_ERROR
            self.saved_actual_lbl.configure(text=f"{actual_saved:,.2f}", text_color=color)

            self.controller.save_data()
        except:
            pass

    def refresh(self):
        self.build()

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

        # Cash Flow Targets card
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(hdr, text="Cash Flow Targets (Current Accounts)", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")

        self.targets_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.targets_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Add row
        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.new_name = ctk.CTkEntry(add_frame, placeholder_text="Account name", width=180)
        self.new_name.pack(side="left", padx=(0, 5))
        self.new_target = ctk.CTkEntry(add_frame, placeholder_text="Target (PLN)", width=120)
        self.new_target.pack(side="left", padx=(0, 5))
        ctk.CTkButton(add_frame, text="+ Add", width=70, command=self.add_target).pack(side="left")

    def add_target(self):
        name = self.new_name.get().strip()
        try:
            amt = float(self.new_target.get().replace(",", "."))
        except:
            return
        if not name or amt <= 0:
            return
        dm.add_cashflow_target(name, amt)
        self.new_name.delete(0, "end")
        self.new_target.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_target(self, tid):
        dm.delete_cashflow_target(tid)
        self.controller.config = dm.get_config()
        self.refresh()

    def save_edit(self, tid, name_var, amt_var):
        name = name_var.get().strip()
        try:
            amt = float(amt_var.get().replace(",", "."))
        except:
            return
        if name and amt > 0:
            dm.edit_cashflow_target(tid, name=name, target_amount=amt)
            self.controller.config = dm.get_config()

    def refresh(self):
        for w in self.targets_frame.winfo_children():
            w.destroy()
        targets = dm.get_cashflow_targets(self.controller.config)
        for t in targets:
            row = ctk.CTkFrame(self.targets_frame, fg_color=COLOR_SURFACE_2, corner_radius=8)
            row.pack(fill="x", pady=3)
            name_var = ctk.StringVar(value=t["name"])
            amt_var = ctk.StringVar(value=f"{t['target']:.2f}")
            ctk.CTkEntry(row, textvariable=name_var, font=FONT_BODY, width=180, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER).pack(side="left", padx=(10, 5), pady=8)
            ctk.CTkEntry(row, textvariable=amt_var, font=FONT_MONO, width=100, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text="PLN", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkButton(row, text="💾", width=28, height=28, fg_color="transparent", text_color=COLOR_SUCCESS, hover_color=COLOR_BORDER, command=lambda tid=t["id"], n=name_var, a=amt_var: self.save_edit(tid, n, a)).pack(side="right", padx=2, pady=5)
            ctk.CTkButton(row, text="🗑", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda tid=t["id"]: self.delete_target(tid)).pack(side="right", padx=5, pady=5)

if __name__ == "__main__":
    app = FlorinApp()
    app.mainloop()
