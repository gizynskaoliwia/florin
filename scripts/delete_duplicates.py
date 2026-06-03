import sqlite3
import json
from pathlib import Path

def run_cleanup():
    db_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'florin.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Target IDs to delete
    wybielanie_id = "d1d95886-7a13-40a7-8a7e-44858155613c" # Old Jan 1st record
    odbudowa_id = "b44b9729-e415-49a5-a66e-a5085562840c"   # Consolidated record (3750)

    # Fetch them for backup logging
    records = cursor.execute("SELECT * FROM expenses WHERE id IN (?, ?)", (wybielanie_id, odbudowa_id)).fetchall()
    
    if records:
        backup_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'deleted_duplicates_backup.json'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump([dict(r) for r in records], f, indent=2, ensure_ascii=False)
        print(f"Backed up {len(records)} records to {backup_path}")

    # Delete them
    cursor.execute("DELETE FROM expenses WHERE id = ?", (wybielanie_id,))
    cursor.execute("DELETE FROM expenses WHERE id = ?", (odbudowa_id,))
    
    conn.commit()

    # Verify totals
    import sys
    sys.path.append('c:/Users/ogizy/.gemini/antigravity-ide/scratch/budget_tracker')
    import data_manager as dm
    dm.init_env()
    
    sp = dm.get_savings_planner()
    cats = {c['name']: c['id'] for c in sp.get('categories', [])}
    
    o_id = cats.get('Odbudowa')
    w_id = cats.get('Wybielanie')
    
    o_tot = cursor.execute("SELECT SUM(amount) FROM expenses WHERE savings_category_id = ?", (o_id,)).fetchone()[0]
    w_tot = cursor.execute("SELECT SUM(amount) FROM expenses WHERE savings_category_id = ?", (w_id,)).fetchone()[0]
    
    print(f"New total for Odbudowa: {o_tot}")
    print(f"New total for Wybielanie: {w_tot}")

    conn.close()

if __name__ == "__main__":
    run_cleanup()
