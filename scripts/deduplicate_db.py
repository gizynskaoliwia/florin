import sqlite3
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def deduplicate():
    db_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'florin.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find duplicates grouped by logical fields
    query = """
        SELECT date, amount, category_id, expense_category_id, savings_category_id, description, COUNT(*) as cnt
        FROM expenses
        GROUP BY date, amount, category_id, expense_category_id, savings_category_id, description
        HAVING cnt > 1
    """
    duplicates = cursor.execute(query).fetchall()

    if not duplicates:
        logging.info("No duplicates found in the database.")
        return

    changelog = []
    
    for dup in duplicates:
        # Fetch all rows for this logical group
        sel_query = """
            SELECT id, month, date, amount, category_id, expense_category_id, savings_category_id, description, tags
            FROM expenses
            WHERE date = ? AND amount = ? AND COALESCE(category_id, '') = ? AND COALESCE(expense_category_id, '') = ? AND COALESCE(savings_category_id, '') = ? AND description = ?
        """
        rows = cursor.execute(sel_query, (
            dup["date"], dup["amount"],
            dup["category_id"] or '', dup["expense_category_id"] or '', dup["savings_category_id"] or '',
            dup["description"]
        )).fetchall()
        
        # Keep the first one, delete the rest
        keep_id = rows[0]["id"]
        delete_ids = [r["id"] for r in rows[1:]]
        
        for r in rows[1:]:
            changelog.append(dict(r))
            cursor.execute("DELETE FROM expenses WHERE id = ?", (r["id"],))
            logging.info(f"Deleted duplicate expense ID {r['id']} (kept {keep_id}) - Amount: {r['amount']} PLN")

    conn.commit()
    conn.close()

    # Write changelog
    changelog_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'dedup_changelog.json'
    with open(changelog_path, 'w', encoding='utf-8') as f:
        json.dump(changelog, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Deduplication complete. {len(changelog)} duplicates removed.")
    logging.info(f"Changelog saved to {changelog_path}")

if __name__ == "__main__":
    deduplicate()
