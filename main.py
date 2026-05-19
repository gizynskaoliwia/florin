# main.py
import tkinter as tk
import customtkinter as ctk
import data_manager as dm
from theme import *
from datetime import datetime
from pathlib import Path
from i18n import t

class FlorinApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        apply_theme()
        self.config = dm.get_config()
        self.current_month = datetime.now().strftime("%Y-%m")
        self.config["last_month"] = self.current_month
        dm.save_config(self.config)
        self.data = dm.load_month(self.current_month)
        
        self.title("Florin")
        try:
            self.iconbitmap("logo2.ico")
        except:
            pass
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=COLOR_BG)
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1280) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1280x800+{x}+{y}")
        
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
            ("Expenses", "🧾"), ("Savings", "🎯"),
            ("Cash Flow", "💧"), ("History", "📅"), 
            ("Settings", "⚙️"), ("Help", "❓")
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
        self.views["Savings"] = SavingsView(self.main_container, self)
        self.views["Cash Flow"] = CashFlowView(self.main_container, self)
        self.views["History"] = HistoryView(self.main_container, self)
        self.views["Settings"] = SettingsView(self.main_container, self)
        self.views["Help"] = HelpView(self.main_container, self)
        
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
        dialog.geometry("400x320")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Name:", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 5))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                item = {"id": dm.generate_id(), "name": name, "amount": amt, "type": item_type, "category_id": None}
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
        dialog.geometry("400x320")
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
        
        def save():
            try:
                amt = float(amt_entry.get().replace(",", "."))
                name = name_entry.get().strip()
                if not name or amt <= 0:
                    return
                item["name"] = name
                item["amount"] = amt
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

        # Month filter state
        now = datetime.now()
        self.filter_month = now.month
        self.filter_year = now.year

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Expenses", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(header, text="⚙ Categories", width=120, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.open_category_manager).pack(side="right", padx=5)
        ctk.CTkButton(header, text="+ Add Expense", width=120, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.open_add_expense).pack(side="right", padx=5)

        # Month selector
        month_bar = ctk.CTkFrame(self, fg_color="transparent")
        month_bar.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(month_bar, text="◀", width=30, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._prev_month).pack(side="left")
        self._month_label = ctk.CTkLabel(month_bar, text="", font=FONT_LABEL, text_color=COLOR_TEXT)
        self._month_label.pack(side="left", padx=10)
        ctk.CTkButton(month_bar, text="▶", width=30, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._next_month).pack(side="left")

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
        dialog.geometry("480x580")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        data = self.controller.data

        # Date field with calendar toggle
        ctk.CTkLabel(dialog, text="Date (DD/MM/YYYY):", anchor="w").pack(fill="x", padx=20, pady=(15, 3))
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
            cal_win.title("Select Date")
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
            ctk.CTkButton(cal_win, text="Select", command=pick).pack(pady=(0, 10))

        ctk.CTkButton(date_frame, text="📅", width=36, height=36, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=open_calendar).pack(side="right", padx=(5, 0))

        ctk.CTkLabel(dialog, text="Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        amt_entry = ctk.CTkEntry(dialog)
        amt_entry.pack(fill="x", padx=20)
        if edit_exp:
            amt_entry.insert(0, f"{edit_exp['amount']:.2f}")

        # Expense Category with inline creation
        ctk.CTkLabel(dialog, text="Expense Category:", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        exp_cats = dm.get_expense_categories(data)
        exp_cat_names = [c["name"] for c in exp_cats] + ["+ Create new category..."]
        if not exp_cats:
            exp_cat_names = ["(none)", "+ Create new category..."]
        exp_cat_var = ctk.StringVar(value=exp_cat_names[0])
        if edit_exp:
            cur = next((c["name"] for c in exp_cats if c["id"] == edit_exp.get("expense_category_id")), exp_cat_names[0])
            exp_cat_var.set(cur)

        exp_cat_menu = ctk.CTkOptionMenu(dialog, values=exp_cat_names, variable=exp_cat_var, command=lambda val: self._on_exp_cat_select(val, exp_cat_var, exp_cat_menu, dialog, data))
        exp_cat_menu.pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text="Funding Source:", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        split_cats = data.get("categories", [])
        sp = dm.get_savings_planner()
        sav_cats = sp.get("categories", [])
        source_names = [f"💰 {c['name']}" for c in split_cats] + [f"🎯 {c['name']}" for c in sav_cats]
        if not source_names:
            source_names = ["(none)"]
        source_var = ctk.StringVar(value=source_names[0])
        if edit_exp:
            if edit_exp.get("savings_category_id"):
                cur_sav = next((f"🎯 {c['name']}" for c in sav_cats if c["id"] == edit_exp["savings_category_id"]), source_names[0])
                source_var.set(cur_sav)
            else:
                cur_split = next((f"💰 {c['name']}" for c in split_cats if c["id"] == edit_exp.get("category_id")), source_names[0])
                source_var.set(cur_split)
        ctk.CTkOptionMenu(dialog, values=source_names, variable=source_var).pack(fill="x", padx=20)

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
            date_val = date_entry.get().strip()
            try:
                datetime.strptime(date_val, "%d/%m/%Y")
                date_error_lbl.configure(text="")
            except ValueError:
                date_error_lbl.configure(text="Invalid date. Use DD/MM/YYYY format.")
                return
            exp_cats_current = dm.get_expense_categories(data)
            exp_cat_id = next((c["id"] for c in exp_cats_current if c["name"] == exp_cat_var.get()), None)
            desc = desc_entry.get().strip()
            tags = [t.strip() for t in tags_entry.get().split(",") if t.strip()]

            # Parse funding source
            source = source_var.get()
            split_id = None
            savings_cat_id = None
            if source.startswith("💰 "):
                name = source[2:].strip()
                split_id = next((c["id"] for c in split_cats if c["name"] == name), None)
            elif source.startswith("🎯 "):
                name = source[2:].strip()
                savings_cat_id = next((c["id"] for c in sav_cats if c["name"] == name), None)

            if edit_exp:
                dm.edit_expense(data, edit_exp["id"], date=date_val, amount=amt, expense_category_id=exp_cat_id, category_id=split_id, savings_category_id=savings_cat_id, description=desc, tags=tags)
            else:
                exp = dm.add_expense(data, date_val, amt, split_id, expense_category_id=exp_cat_id, description=desc, tags=tags)
                exp["savings_category_id"] = savings_cat_id
            self.controller.save_data()
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Save", command=save).pack(fill="x", padx=20, pady=15)

    def _on_exp_cat_select(self, val, exp_cat_var, exp_cat_menu, parent_dialog, data):
        if val != "+ Create new category...":
            return
        d = ctk.CTkInputDialog(text="New category name:", title="Create Category")
        name = d.get_input()
        if name and name.strip():
            dm.add_expense_category(data, name.strip())
            self.controller.save_data()
            exp_cats = dm.get_expense_categories(data)
            new_names = [c["name"] for c in exp_cats] + ["+ Create new category..."]
            exp_cat_menu.configure(values=new_names)
            exp_cat_var.set(name.strip())
        else:
            exp_cat_var.set(exp_cat_menu.cget("values")[0] if exp_cat_menu.cget("values") else "(none)")

    # --- Category Manager Dialog ---
    def open_category_manager(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Expense Categories")
        dialog.geometry("440x500")
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

    # --- Month navigation ---
    def _prev_month(self):
        if self.filter_month == 1:
            self.filter_month = 12
            self.filter_year -= 1
        else:
            self.filter_month -= 1
        self.refresh()

    def _next_month(self):
        if self.filter_month == 12:
            self.filter_month = 1
            self.filter_year += 1
        else:
            self.filter_month += 1
        self.refresh()

    # --- Delete expense ---
    def delete_expense(self, exp_id):
        dm.delete_expense(self.controller.data, exp_id)
        self.controller.save_data()
        self.refresh()

    # --- Refresh / Build Table ---
    def refresh(self):
        data = self.controller.data

        # Update month label
        self._month_label.configure(text=f"{MONTH_FULL[self.filter_month - 1]} {self.filter_year}")

        # Filter expenses to selected month
        def _in_month(exp):
            try:
                d = datetime.strptime(exp["date"], "%d/%m/%Y")
                return d.month == self.filter_month and d.year == self.filter_year
            except:
                return False
        filtered_expenses = [e for e in data.get("expenses", []) if _in_month(e)]

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
        for exp in filtered_expenses:
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
            filtered = [e for e in filtered_expenses if self.active_tag in e.get("tags", [])]
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
                # Show savings badge if funded from savings
                if exp.get("savings_category_id"):
                    sp = dm.get_savings_planner()
                    sav_name = next((c["name"] for c in sp.get("categories", []) if c["id"] == exp["savings_category_id"]), "?")
                    split_name = f"🎯 {sav_name}"
                left_text = f"{date_txt}  {desc_txt}"
                if tags:
                    left_text += f"  [{', '.join(tags)}]"
                ctk.CTkLabel(row, text=left_text, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=5)
                ctk.CTkButton(row, text="🗑", width=26, height=26, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda eid=exp["id"]: self.delete_expense(eid)).pack(side="right", padx=3, pady=3)
                ctk.CTkButton(row, text="✎", width=26, height=26, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=1, pady=3)
                ctk.CTkLabel(row, text=f"{exp['amount']:,.2f}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=5, pady=5)
                badge_color = COLOR_SUCCESS if exp.get("savings_category_id") else COLOR_TEXT_MUTED
                ctk.CTkLabel(row, text=split_name, font=FONT_SMALL, text_color=badge_color).pack(side="right", padx=5, pady=5)
            return

        # Default: grouped by expense category (accordion)
        grouped = {}
        for exp in filtered_expenses:
            key = exp.get("expense_category_id") or "uncategorized"
            grouped.setdefault(key, []).append(exp)
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
            breakdown = {}
            for exp in expenses:
                if exp.get("savings_category_id"):
                    key = f"sav:{exp['savings_category_id']}"
                else:
                    key = exp.get("category_id") or "unknown"
                breakdown[key] = breakdown.get(key, 0.0) + exp["amount"]
            if breakdown:
                sp = dm.get_savings_planner()
                sav_cats_map = {c["id"]: c["name"] for c in sp.get("categories", [])}
                def resolve_name(sid):
                    if sid.startswith("sav:"):
                        return f"Savings - {sav_cats_map.get(sid[4:], '?')}"
                    return split_cats.get(sid, sid)
                parts = [f"{resolve_name(sid)}: {amt:,.2f}" for sid, amt in breakdown.items()]
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
                    if exp.get("savings_category_id"):
                        sp = dm.get_savings_planner()
                        sav_name = next((c["name"] for c in sp.get("categories", []) if c["id"] == exp["savings_category_id"]), "?")
                        split_name = f"🎯 {sav_name}"
                    left_text = f"{date_txt}  {desc_txt}"
                    if tags:
                        left_text += f"  [{', '.join(tags)}]"
                    ctk.CTkLabel(row, text=left_text, font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=10, pady=5)
                    ctk.CTkButton(row, text="🗑", width=26, height=26, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda eid=exp["id"]: self.delete_expense(eid)).pack(side="right", padx=3, pady=3)
                    ctk.CTkButton(row, text="✎", width=26, height=26, fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER, command=lambda e=exp: self.open_add_expense(edit_exp=e)).pack(side="right", padx=1, pady=3)
                    ctk.CTkLabel(row, text=f"{exp['amount']:,.2f}", font=FONT_MONO, text_color=COLOR_EXPENSE).pack(side="right", padx=5, pady=5)
                    badge_color = COLOR_SUCCESS if exp.get("savings_category_id") else COLOR_TEXT_MUTED
                    ctk.CTkLabel(row, text=split_name, font=FONT_SMALL, text_color=badge_color).pack(side="right", padx=5, pady=5)


MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

class SavingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
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

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(hdr, text="Savings Planner", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.edit_btn = ctk.CTkButton(hdr, text="✎ Edit", width=80, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.toggle_edit)
        self.edit_btn.pack(side="right", padx=5)
        self.add_cat_btn = ctk.CTkButton(hdr, text="+ Category", width=100, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, command=self.add_category_dialog)
        self.add_grp_btn = ctk.CTkButton(hdr, text="+ Group", width=80, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.add_group_dialog)

        # Dual-scroll container (vertical + horizontal)
        self._scroll_container = ctk.CTkFrame(self, fg_color="transparent")
        self._scroll_container.pack(fill="both", expand=True)
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
            self.edit_btn.configure(text="✎ Edit", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER)
            self.add_cat_btn.pack_forget()
            self.add_grp_btn.pack_forget()
        else:
            self.editing = True
            self.edit_btn.configure(text="✓ Done", fg_color=COLOR_PRIMARY, text_color="#FFFFFF", hover_color=COLOR_PRIMARY_HOVER)
            self.add_cat_btn.pack(side="right", padx=5)
            self.add_grp_btn.pack(side="right", padx=5)
        self._rebuild_ui()

    def open_category_editor(self, cat=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Category" if cat else "Add Savings Category")
        dialog.geometry("440x520")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Name:", anchor="w").pack(fill="x", padx=20, pady=(15, 3))
        name_e = ctk.CTkEntry(dialog)
        name_e.pack(fill="x", padx=20)
        if cat:
            name_e.insert(0, cat["name"])

        ctk.CTkLabel(dialog, text="Target Amount (PLN):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        target_e = ctk.CTkEntry(dialog)
        target_e.pack(fill="x", padx=20)
        if cat:
            target_e.insert(0, f"{cat['target']:.2f}")

        ctk.CTkLabel(dialog, text="Deadline Month:", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        deadline_var = ctk.StringVar(value=MONTH_FULL[(cat["deadline_month"] - 1) if cat else 11])
        ctk.CTkOptionMenu(dialog, values=MONTH_FULL, variable=deadline_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text="Group (optional):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        groups = self.sp.get("groups", [])
        group_names = ["None"] + [g["name"] for g in groups]
        group_var = ctk.StringVar(value="None")
        if cat and cat.get("group_id"):
            cur_g = next((g["name"] for g in groups if g["id"] == cat["group_id"]), "None")
            group_var.set(cur_g)
        ctk.CTkOptionMenu(dialog, values=group_names, variable=group_var).pack(fill="x", padx=20)

        ctk.CTkLabel(dialog, text="Next Year Target (optional):", anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        nyt_e = ctk.CTkEntry(dialog)
        nyt_e.pack(fill="x", padx=20)
        if cat and cat.get("next_year_target"):
            nyt_e.insert(0, f"{cat['next_year_target']:.2f}")

        def save():
            name = name_e.get().strip()
            try:
                target = float(target_e.get().replace(",", "."))
                deadline = MONTH_FULL.index(deadline_var.get()) + 1
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
                    monthly_nyt = round(nyt / (12 - deadline), 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            else:
                dm.add_savings_category(self.sp, name, target, deadline, gid, nyt)
                # If next_year_target, fill months after deadline
                if nyt and deadline < 12:
                    new_cat = self.sp["categories"][-1]
                    grid_row = self.sp["grid"][new_cat["id"]]
                    monthly_nyt = round(nyt / (12 - deadline), 2)
                    for m in range(deadline + 1, 13):
                        grid_row[f"{m:02d}"] = monthly_nyt
            dm.save_savings_planner(self.sp)
            dialog.destroy()
            self._rebuild_ui()

        ctk.CTkButton(dialog, text="Save", command=save).pack(fill="x", padx=20, pady=15)

    def add_category_dialog(self):
        self.open_category_editor(cat=None)

    def add_group_dialog(self):
        d = ctk.CTkInputDialog(text="Group name:", title="Add Group")
        name = d.get_input()
        if name and name.strip():
            dm.add_savings_group(self.sp, name.strip())
            dm.save_savings_planner(self.sp)
            self._rebuild_ui()

    def delete_category(self, cat_id):
        dm.delete_savings_category(self.sp, cat_id)
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
        for m in range(1, 13):
            mk = f"{m:02d}"
            allocated = dm.get_month_total_allocated(self.sp, mk)
            assumed = self.sp.get("assumed", {}).get(mk, 0.0)
            remaining = assumed - allocated
            if hasattr(self, 'alloc_lbls') and mk in self.alloc_lbls:
                self.alloc_lbls[mk].configure(text=f"{allocated:,.0f}")
            if hasattr(self, 'remain_lbls') and mk in self.remain_lbls:
                color = COLOR_SUCCESS if remaining >= 0 else COLOR_ERROR
                self.remain_lbls[mk].configure(text=f"{remaining:,.0f}", text_color=color)
        if hasattr(self, 'group_lbls'):
            for (gid, mk), lbl in self.group_lbls.items():
                children = [c for c in self.sp["categories"] if c.get("group_id") == gid]
                total = sum(self.sp.get("grid", {}).get(c["id"], {}).get(mk, 0.0) for c in children)
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
        ctk.CTkLabel(name_frame, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W-50, anchor="w").pack(side="left")
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
                    cell_frame = ctk.CTkFrame(table, fg_color="#FFF3E0", corner_radius=4, width=COL_W, height=26)
                    cell_frame.grid(row=r, column=m+1, padx=1, pady=1)
                    cell_frame.grid_propagate(False)
                    cell_frame.grid_columnconfigure(0, weight=1)
                    cell_frame.grid_rowconfigure((0, 1), weight=1)
                    ctk.CTkLabel(cell_frame, text=f"{val:,.0f}", font=("Segoe UI", 8, "overstrike"), text_color=COLOR_TEXT_MUTED, height=12).grid(row=0, column=0)
                    ctk.CTkLabel(cell_frame, text=f"{adjusted:,.0f}", font=("Segoe UI", 9, "bold"), text_color=COLOR_WARNING, height=12).grid(row=1, column=0)
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

        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(anchor="nw")

        COL_W = 60
        NAME_W = 150

        # Header row
        ctk.CTkLabel(table, text="Category", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        current_m = datetime.now().month
        for m in range(12):
            is_current = (m + 1 == current_m)
            hdr_bg = COLOR_CURRENT_MONTH if is_current else "transparent"
            hdr_color = COLOR_PRIMARY if is_current else COLOR_TEXT_MUTED
            ctk.CTkLabel(table, text=MONTH_LABELS[m], font=FONT_LABEL, text_color=hdr_color, width=COL_W, anchor="center", fg_color=hdr_bg, corner_radius=4).grid(row=0, column=m+1, padx=1, pady=2)
        ctk.CTkLabel(table, text="Progress", font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=100, anchor="center").grid(row=0, column=13, padx=2, pady=2)

        row_idx = 1

        grouped_cats = {}
        ungrouped = []
        for cat in categories:
            gid = cat.get("group_id")
            if gid:
                grouped_cats.setdefault(gid, []).append(cat)
            else:
                ungrouped.append(cat)

        def render_cat_row(cat, r):
            self._render_planning_cat_row(table, cat, r, grid, all_cascades, current_m)

        def render_group_row(group, r):
            collapsed = group["id"] in self.planning_collapsed
            chevron = "▶" if collapsed else "▼"
            lbl = ctk.CTkLabel(table, text=f"{chevron} {group['name']}", font=FONT_LABEL, text_color=COLOR_PRIMARY, width=NAME_W, anchor="w", cursor="hand2")
            lbl.grid(row=r, column=0, padx=2, pady=(6, 1), sticky="w")
            lbl.bind("<Button-1>", lambda e, gid=group["id"]: self.toggle_planning_group(gid))
            self.planning_group_labels[group["id"]] = lbl
            children = [c for c in categories if c.get("group_id") == group["id"]]
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

        for group in groups:
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
        ctk.CTkLabel(table, text="Assumed Available", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(10, 1), sticky="w")
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
        ctk.CTkLabel(table, text="Total Allocated", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            allocated = dm.get_month_total_allocated(sp, mk)
            lbl = ctk.CTkLabel(table, text=f"{allocated:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.alloc_lbls[mk] = lbl
        row_idx += 1

        # Remaining (always read-only)
        ctk.CTkLabel(table, text="Remaining", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            remaining = dm.get_month_remaining(sp, mk)
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
        ctk.CTkLabel(table, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=r, column=0, padx=2, pady=1, sticky="w")
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

        saved = dm.get_cat_total_saved(sp, cat["id"])
        missing = dm.get_cat_missing(sp, cat["id"])
        progress = dm.get_cat_progress(sp, cat["id"])
        spent = dm.get_savings_spent(data, cat["id"])
        balance = saved - spent

        s_lbl = ctk.CTkLabel(table, text=f"{saved:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT, width=55, anchor="center")
        s_lbl.grid(row=r, column=13, padx=1, pady=1)
        m_lbl = ctk.CTkLabel(table, text=f"{missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if missing > 0 else COLOR_SUCCESS, width=55, anchor="center")
        m_lbl.grid(row=r, column=14, padx=1, pady=1)
        p_lbl = ctk.CTkLabel(table, text=f"{progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if progress >= 1.0 else COLOR_TEXT, width=55, anchor="center")
        p_lbl.grid(row=r, column=15, padx=1, pady=1)
        sp_lbl = ctk.CTkLabel(table, text=f"{spent:,.0f}" if spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center")
        sp_lbl.grid(row=r, column=16, padx=1, pady=1)
        b_lbl = ctk.CTkLabel(table, text=f"{balance:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if balance >= 0 else COLOR_ERROR, width=55, anchor="center")
        b_lbl.grid(row=r, column=17, padx=1, pady=1)
        self.actual_summary_lbls[cat["id"]] = {"saved": s_lbl, "missing": m_lbl, "progress": p_lbl, "balance": b_lbl}

    def build_actual_table(self):
        """Render actual savings tracker table (top section)."""
        sp = self.sp
        data = self.controller.data
        categories = sp.get("categories", [])
        groups = sp.get("groups", [])
        actual_grid = sp.get("actual_grid", {})
        plan_grid = sp.get("grid", {})
        actual_available = sp.get("actual_available", {})

        ctk.CTkLabel(self.scroll, text="📊 Actual Savings", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 5))
        table = ctk.CTkFrame(self.scroll, fg_color="transparent")
        table.pack(anchor="nw")

        COL_W = 60
        NAME_W = 150

        ctk.CTkLabel(table, text="Category", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        current_m = datetime.now().month
        for m in range(12):
            is_current = (m + 1 == current_m)
            hdr_bg = COLOR_CURRENT_MONTH if is_current else "transparent"
            hdr_color = COLOR_PRIMARY if is_current else COLOR_TEXT_MUTED
            ctk.CTkLabel(table, text=MONTH_LABELS[m], font=FONT_LABEL, text_color=hdr_color, width=COL_W, anchor="center", fg_color=hdr_bg, corner_radius=4).grid(row=0, column=m+1, padx=1, pady=2)
        for i, h in enumerate(["Saved", "Missing", "%", "Spent", "Balance"]):
            ctk.CTkLabel(table, text=h, font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=55, anchor="center").grid(row=0, column=13+i, padx=1, pady=2)

        row_idx = 1
        grouped_cats = {}
        ungrouped = []
        for cat in categories:
            if cat.get("group_id"):
                grouped_cats.setdefault(cat["group_id"], []).append(cat)
            else:
                ungrouped.append(cat)

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
            g_saved = sum(dm.get_cat_total_saved(sp, c["id"]) for c in children)
            g_missing = sum(dm.get_cat_missing(sp, c["id"]) for c in children)
            g_target_sum = sum(c.get("target", 0) for c in children)
            g_progress = g_saved / g_target_sum if g_target_sum > 0 else 0.0
            g_spent = sum(dm.get_savings_spent(data, c["id"]) for c in children)
            g_balance = g_saved - g_spent
            ctk.CTkLabel(table, text=f"{g_saved:,.0f}", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=13, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_missing:,.0f}", font=FONT_SMALL, text_color=COLOR_WARNING if g_missing > 0 else COLOR_SUCCESS, width=55, anchor="center").grid(row=r, column=14, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_progress*100:.0f}%", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_progress >= 1.0 else COLOR_PRIMARY, width=55, anchor="center").grid(row=r, column=15, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_spent:,.0f}" if g_spent else "–", font=FONT_SMALL, text_color=COLOR_EXPENSE, width=55, anchor="center").grid(row=r, column=16, padx=1, pady=(6, 1))
            ctk.CTkLabel(table, text=f"{g_balance:,.0f}", font=FONT_SMALL, text_color=COLOR_SUCCESS if g_balance >= 0 else COLOR_ERROR, width=55, anchor="center").grid(row=r, column=17, padx=1, pady=(6, 1))

        for cat in ungrouped:
            render_actual_row(cat, row_idx)
            row_idx += 1
        for group in groups:
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
        ctk.CTkLabel(table, text="Actual Available", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(8, 1), sticky="w")
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
        ctk.CTkLabel(table, text="Allocated", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            lbl = ctk.CTkLabel(table, text=f"{dm.get_actual_month_total(sp, mk):,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.actual_alloc_lbls[mk] = lbl
        row_idx += 1
        ctk.CTkLabel(table, text="Remaining", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
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
            spent = dm.get_savings_spent(data, cat_id)
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
        self.build_actual_table()
        ctk.CTkFrame(self.scroll, height=2, fg_color=COLOR_BORDER).pack(fill="x", pady=15)
        ctk.CTkLabel(self.scroll, text="📋 Planning Grid", font=FONT_TITLE, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 5))
        self.build_planner_table()

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
        ctk.CTkLabel(hdr, text="Actual Savings", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")
        self.edit_btn = ctk.CTkButton(hdr, text="✎ Edit", width=80, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self.toggle_edit)
        self.edit_btn.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", orientation="horizontal")
        self.scroll.pack(fill="both", expand=True)

    def toggle_edit(self):
        if self.editing:
            self.save_all()
            self.editing = False
            self.edit_btn.configure(text="✎ Edit", fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, hover_color=COLOR_BORDER)
        else:
            self.editing = True
            self.edit_btn.configure(text="✓ Done", fg_color=COLOR_PRIMARY, text_color="#FFFFFF", hover_color=COLOR_PRIMARY_HOVER)
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
        ctk.CTkLabel(table, text="Category", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        for m in range(12):
            ctk.CTkLabel(table, text=MONTH_LABELS[m], font=FONT_LABEL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center").grid(row=0, column=m+1, padx=1, pady=2)
        # Summary column headers
        sum_cols = ["Saved", "Missing", "%", "Spent", "Balance", ""]
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

        def render_cat_row(cat, r):
            ctk.CTkLabel(table, text=cat["name"], font=FONT_BODY, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=r, column=0, padx=2, pady=1, sticky="w")

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

            # Spent - editable in edit mode
            spent_val = sp.get("spent", {}).get(cat["id"], 0.0)
            if self.editing:
                sp_var = ctk.StringVar(value=f"{spent_val:.0f}" if spent_val else "")
                self.spent_vars[cat["id"]] = sp_var
                sp_e = ctk.CTkEntry(table, textvariable=sp_var, font=FONT_SMALL, width=55, height=26, fg_color=COLOR_SURFACE_2, border_color=COLOR_BORDER, justify="center")
                sp_e.grid(row=r, column=16, padx=1, pady=1)
                sp_e.bind("<KeyRelease>", lambda ev, cid=cat["id"], v=sp_var: self.on_spent_change(cid, v))
                sp_e.bind("<FocusOut>", lambda ev, cid=cat["id"], v=sp_var: self.on_spent_change(cid, v))
            else:
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
            children = [c for c in categories if c.get("group_id") == group["id"]]
            for m in range(12):
                mk = f"{m+1:02d}"
                total = sum(actual_grid.get(c["id"], {}).get(mk, 0.0) for c in children)
                ctk.CTkLabel(table, text=f"{total:,.0f}" if total else "", font=FONT_SMALL, text_color=COLOR_PRIMARY, width=COL_W, anchor="center").grid(row=r, column=m+1, padx=1, pady=(6, 1))

        for cat in ungrouped:
            render_cat_row(cat, row_idx)
            row_idx += 1
        for group in groups:
            render_group_row(group, row_idx)
            row_idx += 1
            for cat in grouped_cats.get(group["id"], []):
                render_cat_row(cat, row_idx)
                row_idx += 1

        row_idx += 1

        # Actual Available (manual)
        ctk.CTkLabel(table, text="Actual Available", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=(10, 1), sticky="w")
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
        ctk.CTkLabel(table, text="Actual Allocated", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
        for m in range(12):
            mk = f"{m+1:02d}"
            allocated = dm.get_actual_month_total(sp, mk)
            lbl = ctk.CTkLabel(table, text=f"{allocated:,.0f}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=COL_W, anchor="center", fg_color=COLOR_SURFACE_2, corner_radius=4)
            lbl.grid(row=row_idx, column=m+1, padx=1, pady=1)
            self.alloc_lbls[mk] = lbl
        row_idx += 1

        # Remaining (auto)
        ctk.CTkLabel(table, text="Remaining", font=FONT_LABEL, text_color=COLOR_TEXT, width=NAME_W, anchor="w").grid(row=row_idx, column=0, padx=2, pady=1, sticky="w")
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

        ctk.CTkLabel(self, text="History", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 10))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        past = dm.get_past_months(self.controller.current_month)
        if not past:
            ctk.CTkLabel(self.scroll, text="No past months found.", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=40)
            return

        for month_str in past:
            data = dm.load_month(month_str)
            net = dm.get_net_income(data)
            total_exp = dm.get_total_expenses(data)
            num_exp = len(data.get("expenses", []))

            card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
            card.pack(fill="x", pady=5)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=20, pady=(15, 5))
            ctk.CTkLabel(hdr, text=month_str, font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
            ctk.CTkLabel(hdr, text=f"Net: {net:,.2f} PLN", font=FONT_MONO, text_color=COLOR_INCOME).pack(side="right")

            details = ctk.CTkFrame(card, fg_color="transparent")
            details.pack(fill="x", padx=20, pady=(0, 15))
            ctk.CTkLabel(details, text=f"Expenses: {total_exp:,.2f} PLN ({num_exp} items)", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(side="left")

            # Category breakdown
            cats = data.get("categories", [])
            cat_text = " · ".join(f"{c['name']} {c['percent']:.0f}%" for c in cats)
            ctk.CTkLabel(details, text=cat_text, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="right")

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(self.scroll, text="Settings", font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))

        # === Default Income Items ===
        inc_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        inc_card.pack(fill="x", pady=(0, 15))

        inc_hdr = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(inc_hdr, text="Default Income Items", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")

        self.inc_items_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        self.inc_items_frame.pack(fill="x", padx=20, pady=(0, 10))

        inc_add_frame = ctk.CTkFrame(inc_card, fg_color="transparent")
        inc_add_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.inc_new_name = ctk.CTkEntry(inc_add_frame, placeholder_text="Item name", width=180)
        self.inc_new_name.pack(side="left", padx=(0, 5))
        self.inc_type_var = ctk.StringVar(value="addition")
        ctk.CTkOptionMenu(inc_add_frame, values=["addition", "deduction"], variable=self.inc_type_var, width=110).pack(side="left", padx=(0, 5))
        ctk.CTkButton(inc_add_frame, text="+ Add", width=70, command=self.add_income_item).pack(side="left")

        # === Cash Flow Targets ===
        card = ctk.CTkFrame(self.scroll, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=(0, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(hdr, text="Cash Flow Targets (Current Accounts)", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")

        self.targets_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.targets_frame.pack(fill="x", padx=20, pady=(0, 10))

        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.new_name = ctk.CTkEntry(add_frame, placeholder_text="Account name", width=180)
        self.new_name.pack(side="left", padx=(0, 5))
        self.new_target = ctk.CTkEntry(add_frame, placeholder_text="Target (PLN)", width=120)
        self.new_target.pack(side="left", padx=(0, 5))
        ctk.CTkButton(add_frame, text="+ Add", width=70, command=self.add_target).pack(side="left")

    # --- Default Income Items ---
    def add_income_item(self):
        name = self.inc_new_name.get().strip()
        if not name:
            return
        dm.add_default_income_item(name, self.inc_type_var.get())
        self.inc_new_name.delete(0, "end")
        self.controller.config = dm.get_config()
        self.refresh()

    def delete_income_item(self, item_id):
        dm.delete_default_income_item(item_id)
        self.controller.config = dm.get_config()
        self.refresh()

    def build_income_items(self):
        for w in self.inc_items_frame.winfo_children():
            w.destroy()
        items = dm.get_default_income_items(self.controller.config)
        for item in items:
            row = ctk.CTkFrame(self.inc_items_frame, fg_color=COLOR_SURFACE_2, corner_radius=8)
            row.pack(fill="x", pady=2)
            sign = "+" if item["type"] == "addition" else "−"
            color = COLOR_SUCCESS if item["type"] == "addition" else COLOR_ERROR
            ctk.CTkLabel(row, text=sign, font=FONT_MONO, text_color=color, width=20).pack(side="left", padx=(10, 5), pady=8)
            ctk.CTkLabel(row, text=item["name"], font=FONT_BODY, text_color=COLOR_TEXT).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=item["type"], font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(row, text="🗑", width=28, height=28, fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_BORDER, command=lambda iid=item["id"]: self.delete_income_item(iid)).pack(side="right", padx=5, pady=5)

    # --- Cash Flow Targets ---
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
        self.build_income_items()
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

class HelpView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._sections = []  # [(heading, content_text, frame_widget)]

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(hdr, text=t("help.title"), font=FONT_DISPLAY, text_color=COLOR_TEXT).pack(side="left")

        # Search box
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        search = ctk.CTkEntry(hdr, textvariable=self._search_var, placeholder_text=t("help.search_placeholder"), width=220)
        search.pack(side="right")

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        self._render_markdown()

    def _load_help_text(self):
        help_path = Path(__file__).parent / "HELP.md"
        try:
            return help_path.read_text(encoding="utf-8")
        except:
            return "# Help\n\nHelp file not found."

    def _render_markdown(self):
        text = self._load_help_text()
        lines = text.split("\n")
        current_heading = ""
        current_lines = []
        sections = []

        def flush():
            if current_heading or current_lines:
                sections.append((current_heading, "\n".join(current_lines)))

        for line in lines:
            if line.startswith("# "):
                flush()
                current_heading = line[2:].strip()
                current_lines = []
            elif line.startswith("## "):
                flush()
                current_heading = line[3:].strip()
                current_lines = []
            elif line.startswith("### "):
                flush()
                current_heading = line[4:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        flush()

        for heading, body in sections:
            frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
            frame.pack(fill="x", pady=(8, 0), anchor="w")

            if heading:
                ctk.CTkLabel(frame, text=heading, font=FONT_TITLE, text_color=COLOR_PRIMARY, anchor="w").pack(fill="x")

            if body.strip():
                rendered = self._format_body(body.strip())
                lbl = ctk.CTkLabel(frame, text=rendered, font=FONT_BODY, text_color=COLOR_TEXT, anchor="w", justify="left", wraplength=700)
                lbl.pack(fill="x", padx=(10, 0), pady=(2, 0))

            self._sections.append((heading.lower(), body.lower(), frame))

    def _format_body(self, text):
        """Light formatting: strip markdown bold/table syntax for display."""
        lines = []
        for line in text.split("\n"):
            line = line.replace("**", "")
            if line.startswith("- "):
                line = "  • " + line[2:]
            elif line.startswith("| ") and "---" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                line = "  " + "  |  ".join(cells)
            elif line.startswith("|") and "---" in line:
                continue
            elif line.startswith("---"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _filter(self):
        query = self._search_var.get().lower().strip()
        any_visible = False
        for heading, body, frame in self._sections:
            if not query or query in heading or query in body:
                frame.pack(fill="x", pady=(8, 0), anchor="w")
                any_visible = True
            else:
                frame.pack_forget()
        # Show "no results" if nothing matches
        if hasattr(self, "_no_results_lbl"):
            self._no_results_lbl.destroy()
        if not any_visible and query:
            self._no_results_lbl = ctk.CTkLabel(self._scroll, text=t("help.no_results"), font=FONT_BODY, text_color=COLOR_TEXT_MUTED)
            self._no_results_lbl.pack(pady=20)

    def refresh(self):
        pass  # Static content, no refresh needed


if __name__ == "__main__":
    app = FlorinApp()
    app.mainloop()
