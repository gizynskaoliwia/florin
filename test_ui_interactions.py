import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import customtkinter as ctk
from views.emergency_fund import EmergencyFundView
from theme import *
import data_manager as dm

class MockController:
    def __init__(self):
        self.config = dm.get_config()
        self.views = {}

app = ctk.CTk()
app.geometry("800x600")

controller = MockController()
view = EmergencyFundView(app, controller)
view.pack(fill="both", expand=True)

# 1. Start editing
view.toggle_edit()

# 2. Add goal
for child in view.sections_container.winfo_children():
    # Find the "+ Dodaj cel" button and click it
    def find_add_btn(w):
        if isinstance(w, ctk.CTkButton) and w.cget("text") == "+ Dodaj cel":
            w.invoke()
            return True
        for c in w.winfo_children():
            if find_add_btn(c): return True
        return False
    find_add_btn(child)

app.update()

# 3. Print the UI
print("After Add Goal click:")
for refs in view.section_refs:
    print(refs.get("goals_vars"))

# 4. Change dropdown
for refs in view.section_refs:
    for n_var, orig_idx in refs.get("goals_vars", []):
        n_var.set("6msc_zycia_kredytu")

app.update()

# 5. Save
view.toggle_edit()
app.update()

# 6. Verify
for refs in view.section_refs:
    mode = refs["mode"]
    print(f"Goals after save: {dm.get_emergency_fund_settings()[mode].get('custom_goals', [])}")
    
app.destroy()
