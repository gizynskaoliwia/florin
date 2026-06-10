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

# Simulate going into edit mode
view.toggle_edit()
app.update()

# Mock the click of add_new
for refs in view.section_refs:
    mode = refs["mode"]
    data = dm.get_emergency_fund_settings().get(mode, {})
    data.setdefault("custom_goals", []).append({"name": dm.EMERGENCY_FUND_GOAL_OPTIONS[0], "amount": 0.0})
    dm.save_emergency_fund_settings(mode, data)

view.refresh()
app.update()

for refs in view.section_refs:
    print(refs.get("goals_vars"))

view.toggle_edit() # save
app.update()

for refs in view.section_refs:
    mode = refs["mode"]
    print(f"Goals after add and save: {dm.get_emergency_fund_settings()[mode].get('custom_goals', [])}")

app.destroy()
