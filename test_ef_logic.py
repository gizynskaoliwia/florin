import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

p_settings = dm.get_emergency_fund_settings().get("personal", {})
print("Personal actual_saved before:", p_settings.get("actual_saved"))

dm.add_emergency_fund_transaction("personal", "2026-06-07", "deposit", 500.0, "Test deposit")

p_settings = dm.get_emergency_fund_settings().get("personal", {})
print("Personal actual_saved after deposit:", p_settings.get("actual_saved"))

dm.delete_emergency_fund_transaction(dm.get_emergency_fund_transactions("personal")[0]["id"], "personal")

p_settings = dm.get_emergency_fund_settings().get("personal", {})
print("Personal actual_saved after delete:", p_settings.get("actual_saved"))
