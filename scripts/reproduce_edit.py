import sys
sys.path.append('c:/Users/ogizy/.gemini/antigravity-ide/scratch/budget_tracker')
import main, data_manager as dm
from pathlib import Path

def repro_edit():
    dm.init_env()
    
    # 1. Create a dummy data structure
    month_str = "2026-08"
    data = {"month": month_str, "expenses": []}
    
    # 2. Add an expense
    exp = dm.add_expense(data, "01/08/2026", 100.0, "cat1", description="Test Repro")
    exp_id = exp["id"]
    
    # Save it
    dm.save_month(month_str, data)
    
    # Check DB
    conn = dm.get_connection()
    count_before = conn.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (exp_id,)).fetchone()[0]
    total_before = conn.execute("SELECT COUNT(*) FROM expenses WHERE description = 'Test Repro'").fetchone()[0]
    print(f"Before edit: ID count = {count_before}, Total count = {total_before}")
    
    # 3. Edit the expense (same month)
    dm.edit_expense(data, exp_id, amount=200.0, description="Test Repro Edited")
    dm.save_month(month_str, data)
    
    # Check DB
    count_after = conn.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (exp_id,)).fetchone()[0]
    total_after = conn.execute("SELECT COUNT(*) FROM expenses WHERE description LIKE 'Test Repro%'").fetchone()[0]
    amount_after = conn.execute("SELECT amount FROM expenses WHERE id = ?", (exp_id,)).fetchone()[0]
    print(f"After same-month edit: ID count = {count_after}, Total count = {total_after}, Amount = {amount_after}")
    
    # 4. Clean up
    conn.execute("DELETE FROM expenses WHERE description LIKE 'Test Repro%'")
    conn.commit()

if __name__ == "__main__":
    repro_edit()
