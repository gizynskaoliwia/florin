import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_scan():
    db_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'florin.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search for exactly "Odbudowa" and "Wybielanie" to see if they exist multiple times
    query = """
        SELECT id, month, date, amount, description
        FROM expenses
        WHERE description LIKE '%Odbudowa%' OR description LIKE '%Wybielanie%'
    """
    rows = cursor.execute(query).fetchall()

    if not rows:
        logging.info("No matching records found for 'Odbudowa' or 'Wybielanie'.")
    else:
        logging.info("Found following records for 'Odbudowa' and 'Wybielanie':")
        for r in rows:
            logging.info(f"ID: {r['id']}, Month: {r['month']}, Date: {r['date']}, Amount: {r['amount']}, Desc: {r['description']}")

    # Fuzzy match by amount + category across months
    fuzzy_query = """
        SELECT amount, savings_category_id, COUNT(*) as cnt
        FROM expenses
        WHERE savings_category_id IS NOT NULL
        GROUP BY amount, savings_category_id
        HAVING cnt > 1
    """
    fuzzy = cursor.execute(fuzzy_query).fetchall()
    
    if not fuzzy:
        logging.info("No fuzzy duplicates found across months.")
    else:
        logging.info(f"Found {len(fuzzy)} groups of fuzzy duplicates across months.")

    conn.close()

if __name__ == "__main__":
    run_scan()
