import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

import tkinter as tk
import customtkinter as ctk
from views.cashflow import CashFlowView

class MockController:
    def __init__(self):
        self.config = dm.get_config()
        self.current_month = self.config.get("last_month", "2026-04")
        self.data = dm.load_month(self.current_month)
        self.views = {}
    def save_data(self):
        dm.save_month(self.current_month, self.data)

app = ctk.CTk()
controller = MockController()
view = CashFlowView(app, controller)
view.pack(fill="both", expand=True)

view.build()

print("Initial states:")
print(f"Net Income Label: {view.net_income_lbl.cget('text') if view.net_income_lbl else 'None'}")
print(f"Total Topup: {view.total_topup_lbl.cget('text')}")
print(f"Shared Actual: {view.shared_actual_var.get()}")
print(f"Saved Actual: {view.saved_actual_var.get()}")
print(f"Hero Saved Actual: {view.saved_actual_lbl.cget('text')}")

view.toggle_edit()
view.shared_actual_var.set("500")
view.saved_actual_var.set("1000")
view.calculate()
view.toggle_edit()

print("\nAfter edit:")
print(f"Shared Actual: {view.shared_actual_var.get()}")
print(f"Saved Actual: {view.saved_actual_var.get()}")
print(f"Hero Saved Actual: {view.saved_actual_lbl.cget('text')}")

app.destroy()
