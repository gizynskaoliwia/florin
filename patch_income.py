import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace add_item
add_item_orig = """    def add_item(self, item_type):
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Add Addition" if item_type == "addition" else "Add Deduction"))
        dialog.geometry("400x320")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=tx("Name:"), anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(fill="x", padx=20)
        
        ctk.CTkLabel(dialog, text=tx("Amount (PLN):"), anchor="w").pack(fill="x", padx=20, pady=(10, 5))
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
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)"""

add_item_new = """    def add_item(self, item_type):
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
        
        from utils import ui_text
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
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)"""

# Replace edit_item
edit_item_orig = """    def edit_item(self, item_id):
        item = next((i for i in self.controller.data.get("income_items", []) if i["id"] == item_id), None)
        if not item:
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title(tx("Edit Item"))
        dialog.geometry("400x320")
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
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)"""

edit_item_new = """    def edit_item(self, item_id):
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
        
        from utils import ui_text
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
        
        ctk.CTkButton(dialog, text=tx("Save"), command=save).pack(pady=20)"""

content = content.replace(add_item_orig, add_item_new)
content = content.replace(edit_item_orig, edit_item_new)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patched main.py")
