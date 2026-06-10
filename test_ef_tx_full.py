import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

def test_ef_tx(mode):
    print(f"\n--- Testing mode: {mode} ---")
    
    # Get current
    data = dm.get_emergency_fund_settings().get(mode, {})
    print(f"Initial actual_saved: {data.get('actual_saved')}")
    
    # 1. Snapshot
    dm.add_emergency_fund_transaction(mode, "2026-06-01", "snapshot", 1000.0, "Test snapshot")
    data = dm.get_emergency_fund_settings().get(mode, {})
    print(f"After snapshot 1000: {data.get('actual_saved')}")
    
    # 2. Deposit
    dm.add_emergency_fund_transaction(mode, "2026-06-02", "deposit", 200.0, "Test deposit")
    data = dm.get_emergency_fund_settings().get(mode, {})
    print(f"After deposit 200: {data.get('actual_saved')} (EXPECTED: 1200 or 1000 depending on logic)")
    
    # 3. Withdrawal
    dm.add_emergency_fund_transaction(mode, "2026-06-03", "withdrawal", 300.0, "Test withdrawal")
    data = dm.get_emergency_fund_settings().get(mode, {})
    print(f"After withdrawal 300: {data.get('actual_saved')} (EXPECTED: 900 or 1000)")

test_ef_tx("shared")
test_ef_tx("personal")

