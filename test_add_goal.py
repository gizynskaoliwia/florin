import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import customtkinter as ctk
from views.emergency_fund import EmergencyFundView
from theme import *
import data_manager as dm

class MockController:
    def __init__(self):
        self.config = dm.get_config()

app = ctk.CTk()
app.geometry("800x600")

controller = MockController()
view = EmergencyFundView(app, controller)
view.pack(fill="both", expand=True)

# Simulate going into edit mode
view.toggle_edit()
app.update()
print("Edit mode toggled.")

# Simulate clicking Add goal
for refs in view.section_refs:
    mode = refs["mode"]
    print(f"Goals before add: {dm.get_emergency_fund_settings()[mode].get('custom_goals', [])}")

app.destroy()
