import sqlite3
conn = sqlite3.connect('C:/Users/ogizy/AppData/Local/Florin/florin.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT month_key, SUM(amount) as m_sum FROM savings_actual_grid GROUP BY month_key").fetchall()
for r in rows:
    print(f"{r['month_key']}: {r['m_sum']}")

print("Categories in DB:")
cats = conn.execute("SELECT id, name FROM savings_categories").fetchall()
for c in cats:
    print(c['name'], c['id'])
    
print("Orphaned Actuals:")
rows = conn.execute("SELECT category_id, month_key, amount FROM savings_actual_grid WHERE category_id NOT IN (SELECT id FROM savings_categories)").fetchall()
for r in rows:
    print(f"ID: {r['category_id']}, month: {r['month_key']}, amt: {r['amount']}")
