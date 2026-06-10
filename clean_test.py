import sys
sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

conn = dm.get_connection()
conn.execute("DELETE FROM emergency_fund_transactions WHERE note LIKE 'Test%'")
conn.commit()

dm._recalculate_emergency_fund_actual(conn, "shared")
dm._recalculate_emergency_fund_actual(conn, "personal")
conn.commit()
