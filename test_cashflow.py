import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

app_data = dm.load_month_data(dm.get_config().get("last_month", "2026-04"))
cf = dm.get_cashflow(app_data)
targets = dm.get_cashflow_targets(dm.get_config())

net_income = dm.get_net_income(app_data)
total_topup = sum(max(0.0, target["target"] - cf.get("current_accounts", {}).get(target["id"], {}).get("balance", 0.0)) for target in targets)
shared_actual = cf.get("shared_actual", 0.0)
saved_actual = cf.get("saved_actual", 0.0)
actual_saved = net_income - total_topup - shared_actual - saved_actual

print("Cashflow calculation:")
print(f"Net Income: {net_income}")
print(f"Total Topup: {total_topup}")
print(f"Shared Actual: {shared_actual}")
print(f"Saved Actual: {saved_actual}")
print(f"Actual Saved (remainder): {actual_saved}")

# Let's see what happens if I adjust shared_actual vs saved_actual
print("\n--- Test Shared Update ---")
cf["shared_actual"] = 500.0
actual_saved = net_income - total_topup - cf["shared_actual"] - cf.get("saved_actual", 0.0)
print(f"Shared Actual: 500.0")
print(f"Actual Saved (remainder): {actual_saved}")

print("\n--- Test Saved Update ---")
cf["saved_actual"] = 1000.0
actual_saved = net_income - total_topup - cf.get("shared_actual", 0.0) - cf["saved_actual"]
print(f"Saved Actual: 1000.0")
print(f"Actual Saved (remainder): {actual_saved}")
