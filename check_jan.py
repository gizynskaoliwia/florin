import sqlite3
conn = sqlite3.connect('C:/Users/ogizy/AppData/Local/Florin/florin.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT c.name, a.amount FROM savings_actual_grid a JOIN savings_categories c ON a.category_id = c.id WHERE a.month_key='01'").fetchall()
print("Joined:")
for r in rows:
    print(r['name'], r['amount'])
