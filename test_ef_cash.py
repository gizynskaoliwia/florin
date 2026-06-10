import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import customtkinter as ctk
from views.emergency_fund import EmergencyFundView
from theme import *
import data_manager as dm

class MockController:
    def __init__(self):
        self.config = dm.get_config()
        self.config["enable_ef_personal"] = "true"
        self.config["enable_ef_shared"] = "true"
        self.views = {}

app = ctk.CTk()
app.geometry("800x600")

controller = MockController()
view = EmergencyFundView(app, controller)
view.pack(fill="both", expand=True)

# Start editing
view.toggle_edit()

for refs in view.section_refs:
    mode = refs["mode"]
    print(f"\n--- Testing mode: {mode} ---")
    
    # Simulate typing 1000 into cash_var
    refs["cash_var"].set("1000")
    
    # Manually trigger the event handlers or just toggle edit to save
    # In EmergencyFundView, we save when toggle_edit is called
    
view.toggle_edit() # Saves and refreshes

for refs in view.section_refs:
    mode = refs["mode"]
    data = dm.get_emergency_fund_settings().get(mode, {})
    print(f"{mode} cash_allocated in DB: {data.get('cash_allocated')}")
    
    # Let's check target_no_cash
    target = view.calculate_target(data)
    print(f"{mode} target: {target}")
    print(f"{mode} cash_allocated: {data.get('cash_allocated', 0.0)}")
    print(f"{mode} target_no_cash: {target - data.get('cash_allocated', 0.0)}")
    
app.destroy()
