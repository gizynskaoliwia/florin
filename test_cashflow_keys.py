import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

app_data = dm.load_data()
cf = dm.get_cashflow(app_data)
print("Keys in cashflow:", list(cf.keys()))
