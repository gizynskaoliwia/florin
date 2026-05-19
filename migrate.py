"""migrate.py — Migrate existing JSON file data into SQLite.

Safe and idempotent: uses migrations table to track completion.
Running twice will not duplicate records.
"""
import json
from pathlib import Path
from db import get_connection

DATA_DIR = Path("data")
CONFIG_FILE = Path("config.json")
MIGRATION_NAME = "json_to_sqlite_v1"


def needs_migration() -> bool:
    """Check if JSON-to-SQLite migration has already been applied."""
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM migrations WHERE name = ?", (MIGRATION_NAME,)).fetchone()
    return row is None


def run_migration():
    """Migrate all JSON data into SQLite. Idempotent."""
    if not needs_migration():
        return
    conn = get_connection()
    _migrate_config(conn)
    _migrate_months(conn)
    _migrate_savings(conn)
    conn.execute("INSERT INTO migrations (name) VALUES (?)", (MIGRATION_NAME,))
    conn.commit()


def _migrate_config(conn):
    """Migrate config.json → settings, cashflow_targets, default_income_items."""
    if not CONFIG_FILE.exists():
        return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Settings
    for key in ("last_month", "theme", "language"):
        val = config.get(key)
        if val is not None:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))

    # Cashflow targets
    for i, t in enumerate(config.get("cashflow_targets", [])):
        conn.execute(
            "INSERT OR REPLACE INTO cashflow_targets (id, name, target, sort_order) VALUES (?, ?, ?, ?)",
            (t["id"], t["name"], t["target"], i)
        )

    # Default income items
    for i, item in enumerate(config.get("default_income_items", [])):
        conn.execute(
            "INSERT OR REPLACE INTO default_income_items (id, name, type, sort_order) VALUES (?, ?, ?, ?)",
            (item["id"], item["name"], item["type"], i)
        )


def _migrate_months(conn):
    """Migrate data/YYYY-MM.json files → categories, expense_categories, income_items, expenses, cashflow."""
    if not DATA_DIR.exists():
        return
    for f in sorted(DATA_DIR.glob("????-??.json")):
        month = f.stem
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Categories (income split)
        for cat in data.get("categories", []):
            conn.execute(
                "INSERT OR REPLACE INTO categories (id, month, name, percent, color) VALUES (?, ?, ?, ?, ?)",
                (cat["id"], month, cat["name"], cat.get("percent", 0), cat.get("color", "#888888"))
            )

        # Expense categories
        for cat in data.get("expense_categories", []):
            conn.execute(
                "INSERT OR REPLACE INTO expense_categories (id, month, name) VALUES (?, ?, ?)",
                (cat["id"], month, cat["name"])
            )

        # Income items
        for item in data.get("income_items", []):
            conn.execute(
                "INSERT OR REPLACE INTO income_items (id, month, name, amount, type, category_id) VALUES (?, ?, ?, ?, ?, ?)",
                (item["id"], month, item["name"], item.get("amount", 0.0), item["type"], item.get("category_id"))
            )

        # Expenses
        for exp in data.get("expenses", []):
            tags = ",".join(exp.get("tags", []))
            conn.execute(
                "INSERT OR REPLACE INTO expenses (id, month, date, amount, category_id, expense_category_id, savings_category_id, description, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (exp["id"], month, exp["date"], exp["amount"], exp.get("category_id"), exp.get("expense_category_id"), exp.get("savings_category_id"), exp.get("description", ""), tags)
            )

        # Cashflow
        cf = data.get("cashflow", {})
        for key, val in cf.items():
            if key == "current_accounts":
                for acct_id, acct in val.items():
                    if isinstance(acct, dict):
                        conn.execute(
                            "INSERT OR REPLACE INTO cashflow (month, key, value, updated_at) VALUES (?, ?, ?, ?)",
                            (month, f"acct:{acct_id}", acct.get("balance", 0.0), acct.get("updated_at"))
                        )
                    else:
                        conn.execute(
                            "INSERT OR REPLACE INTO cashflow (month, key, value) VALUES (?, ?, ?)",
                            (month, f"acct:{acct_id}", float(acct))
                        )
            else:
                if isinstance(val, (int, float)):
                    conn.execute(
                        "INSERT OR REPLACE INTO cashflow (month, key, value) VALUES (?, ?, ?)",
                        (month, key, float(val))
                    )


def _migrate_savings(conn):
    """Migrate data/savings_planner.json → savings tables."""
    sp_file = DATA_DIR / "savings_planner.json"
    if not sp_file.exists():
        return
    with open(sp_file, "r", encoding="utf-8") as f:
        sp = json.load(f)

    # Groups
    for g in sp.get("groups", []):
        conn.execute("INSERT OR REPLACE INTO savings_groups (id, name) VALUES (?, ?)", (g["id"], g["name"]))

    # Categories
    for cat in sp.get("categories", []):
        conn.execute(
            "INSERT OR REPLACE INTO savings_categories (id, name, target, deadline_month, group_id, next_year_target) VALUES (?, ?, ?, ?, ?, ?)",
            (cat["id"], cat["name"], cat.get("target", 0), cat.get("deadline_month", 12), cat.get("group_id"), cat.get("next_year_target"))
        )

    # Planning grid
    for cat_id, months in sp.get("grid", {}).items():
        for mk, amt in months.items():
            if amt:
                conn.execute(
                    "INSERT OR REPLACE INTO savings_grid (category_id, month_key, amount) VALUES (?, ?, ?)",
                    (cat_id, mk, amt)
                )

    # Assumed available
    for mk, amt in sp.get("assumed", {}).items():
        if amt:
            conn.execute(
                "INSERT OR REPLACE INTO savings_assumed (month_key, amount) VALUES (?, ?)",
                (mk, amt)
            )

    # Actual grid
    for cat_id, months in sp.get("actual_grid", {}).items():
        for mk, amt in months.items():
            if amt:
                conn.execute(
                    "INSERT OR REPLACE INTO savings_actual_grid (category_id, month_key, amount) VALUES (?, ?, ?)",
                    (cat_id, mk, amt)
                )

    # Actual available
    for mk, amt in sp.get("actual_available", {}).items():
        if amt:
            conn.execute(
                "INSERT OR REPLACE INTO savings_actual_available (month_key, amount) VALUES (?, ?)",
                (mk, amt)
            )

    # Spent
    for cat_id, amt in sp.get("spent", {}).items():
        if amt:
            conn.execute(
                "INSERT OR REPLACE INTO savings_spent (category_id, amount) VALUES (?, ?)",
                (cat_id, amt)
            )
