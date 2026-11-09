"""db.py — SQLite database layer for Florin budget tracker.

Handles:
- OS-appropriate database file location
- Schema creation and migrations
- Connection management
"""
import sqlite3
import sys
from pathlib import Path

_DB_NAME = "florin.db"


def get_db_path() -> Path:
    """Return OS-appropriate path for the SQLite database file."""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local" / "Florin"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Florin"
    else:
        base = Path.home() / ".local" / "share" / "florin"
    base.mkdir(parents=True, exist_ok=True)
    return base / _DB_NAME


_connection = None


def get_connection() -> sqlite3.Connection:
    """Get or create a singleton database connection."""
    global _connection
    if _connection is None:
        db_path = get_db_path()
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        _init_schema(_connection)
    return _connection


def close():
    """Close the database connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None


def _init_schema(conn: sqlite3.Connection):
    """Create all tables if they don't exist."""
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emergency_fund_transactions'")
    transactions_table_exists = cur.fetchone() is not None

    conn.executescript(SCHEMA_SQL)
    
    # Check if initial_amount exists in savings_categories
    cur = conn.execute("PRAGMA table_info(savings_categories)")
    cols = [col["name"] for col in cur.fetchall()]
    if "initial_amount" not in cols:
        conn.execute("ALTER TABLE savings_categories ADD COLUMN initial_amount REAL NOT NULL DEFAULT 0.0")

    # Check if allocations column exists, if not, add it
    cur = conn.execute("PRAGMA table_info(emergency_fund_settings)")
    columns = [col["name"] for col in cur.fetchall()]
    if "allocations" not in columns:
        conn.execute("ALTER TABLE emergency_fund_settings ADD COLUMN allocations TEXT NOT NULL DEFAULT '{\"80% CELU OBLIGACJE\": 80.0, \"20% CELU KONTO OSZCZ.\": 20.0}'")
    if "manual_target" not in columns:
        conn.execute("ALTER TABLE emergency_fund_settings ADD COLUMN manual_target REAL DEFAULT NULL")
    if "custom_goals" not in columns:
        conn.execute("ALTER TABLE emergency_fund_settings ADD COLUMN custom_goals TEXT NOT NULL DEFAULT '[]'")

    if not transactions_table_exists:
        import uuid
        from datetime import datetime
        rows = conn.execute("SELECT mode, actual_saved FROM emergency_fund_settings").fetchall()
        today = datetime.now().strftime("%Y-%m-%d")
        for row in rows:
            mode = row["mode"]
            amount = row["actual_saved"]
            if amount > 0:
                conn.execute(
                    "INSERT INTO emergency_fund_transactions (id, mode, date, type, amount, created_at) VALUES (?, ?, ?, 'deposit', ?, datetime('now'))",
                    (str(uuid.uuid4()), mode, today, amount)
                )

    # Migrate emergency_fund_transactions to snapshot model
    cur = conn.execute("PRAGMA table_info(emergency_fund_transactions)")
    columns = [col["name"] for col in cur.fetchall()]
    if columns and "note" not in columns:
        import uuid
        from datetime import datetime
        
        # We must drop the CHECK constraint, so we recreate the table
        conn.execute("""
            CREATE TABLE emergency_fund_transactions_new (
                id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("INSERT INTO emergency_fund_transactions_new (id, mode, date, type, amount, created_at) SELECT id, mode, date, type, amount, created_at FROM emergency_fund_transactions")
        conn.execute("DROP TABLE emergency_fund_transactions")
        conn.execute("ALTER TABLE emergency_fund_transactions_new RENAME TO emergency_fund_transactions")
        
        # Inject current actual_saved as a snapshot to not lose the balance!
        rows = conn.execute("SELECT mode, actual_saved FROM emergency_fund_settings").fetchall()
        today = datetime.now().strftime("%Y-%m-%d")
        for row in rows:
            mode = row["mode"]
            amount = row["actual_saved"]
            conn.execute(
                "INSERT INTO emergency_fund_transactions (id, mode, date, type, amount, note, created_at) VALUES (?, ?, ?, 'snapshot', ?, 'Migrated balance snapshot', datetime('now'))",
                (str(uuid.uuid4()), mode, today, amount)
            )

    # Migrate cashflow_targets to per-month schema
    cur = conn.execute("PRAGMA table_info(cashflow_targets)")
    cf_cols = [col["name"] for col in cur.fetchall()]
    if cf_cols and "month" not in cf_cols:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS default_cashflow_targets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target REAL NOT NULL DEFAULT 0.0,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO default_cashflow_targets (id, name, target, sort_order)
            SELECT id, name, target, sort_order FROM cashflow_targets
        """)
        existing_targets = conn.execute("SELECT id, name, target, sort_order FROM cashflow_targets").fetchall()

        months_rows = conn.execute("""
            SELECT DISTINCT month FROM categories
            UNION SELECT DISTINCT month FROM cashflow
            UNION SELECT DISTINCT month FROM expenses
        """).fetchall()
        all_months = [r[0] for r in months_rows if r[0]]
        if not all_months:
            from datetime import datetime
            all_months = [datetime.now().strftime("%Y-%m")]

        conn.execute("""
            CREATE TABLE cashflow_targets_new (
                id TEXT NOT NULL,
                month TEXT NOT NULL,
                name TEXT NOT NULL,
                target REAL NOT NULL DEFAULT 0.0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (id, month)
            )
        """)
        for m in all_months:
            for t in existing_targets:
                conn.execute(
                    "INSERT OR IGNORE INTO cashflow_targets_new (id, month, name, target, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (t["id"], m, t["name"], t["target"], t["sort_order"])
                )
        conn.execute("DROP TABLE cashflow_targets")
        conn.execute("ALTER TABLE cashflow_targets_new RENAME TO cashflow_targets")

    # Seed default_cashflow_targets if empty
    cur = conn.execute("SELECT COUNT(*) FROM default_cashflow_targets")
    if cur.fetchone()[0] == 0:
        import uuid
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES (?, 'Daily Life', 1500.0, 0)", (str(uuid.uuid4()),))
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES (?, 'Pleasure', 500.0, 1)", (str(uuid.uuid4()),))
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES (?, 'Business', 700.0, 2)", (str(uuid.uuid4()),))
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES ('e5b5285f-a36b-5789-a9e8-b6e05eac3187', 'Wspólne konto wykończenie', 4800.0, 3)")
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES ('6943145f-c167-5715-b8a1-0c4216645295', 'Wspólne konto', 600.0, 4)")
        conn.execute("INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES ('88dbc084-3544-5eb7-a804-11a146d23627', 'Wspólne wesele', 200.0, 5)")

    # Migration: add shared buffer targets to default templates and existing months
    row = conn.execute("SELECT 1 FROM migrations WHERE name = 'shared_goals_to_cashflow_buffers_v1'").fetchone()
    if not row:
        shared_defaults = [
            ("e5b5285f-a36b-5789-a9e8-b6e05eac3187", "Wspólne konto wykończenie", 4800.0, 3),
            ("6943145f-c167-5715-b8a1-0c4216645295", "Wspólne konto", 600.0, 4),
            ("88dbc084-3544-5eb7-a804-11a146d23627", "Wspólne wesele", 200.0, 5),
        ]
        cur = conn.execute("SELECT name FROM default_cashflow_targets")
        existing_defs = {r["name"].lower() for r in cur.fetchall()}
        for tid, name, target, s_order in shared_defaults:
            if name.lower() not in existing_defs:
                conn.execute(
                    "INSERT INTO default_cashflow_targets (id, name, target, sort_order) VALUES (?, ?, ?, ?)",
                    (tid, name, target, s_order)
                )

        months = [r[0] for r in conn.execute("SELECT DISTINCT month FROM cashflow_targets").fetchall()]
        for m in months:
            m_targets = {r["name"].lower() for r in conn.execute("SELECT name FROM cashflow_targets WHERE month = ?", (m,)).fetchall()}
            for tid, name, target, s_order in shared_defaults:
                if name.lower() not in m_targets:
                    conn.execute(
                        "INSERT INTO cashflow_targets (id, month, name, target, sort_order) VALUES (?, ?, ?, ?, ?)",
                        (tid, m, name, target, s_order)
                    )

        conn.execute("UPDATE cashflow SET value = 0.0 WHERE key = 'shared_actual'")
        conn.execute("INSERT OR IGNORE INTO migrations (name) VALUES ('shared_goals_to_cashflow_buffers_v1')")


SCHEMA_SQL = """
-- App settings (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Cashflow targets (per month)
CREATE TABLE IF NOT EXISTS cashflow_targets (
    id TEXT NOT NULL,
    month TEXT NOT NULL,
    name TEXT NOT NULL,
    target REAL NOT NULL DEFAULT 0.0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (id, month)
);

-- Default cashflow targets (templates for new months)
CREATE TABLE IF NOT EXISTS default_cashflow_targets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target REAL NOT NULL DEFAULT 0.0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- Default income items (templates for new months)
CREATE TABLE IF NOT EXISTS default_income_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('addition', 'deduction')),
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- Income split categories (per month: Daily Life, Shared, Saved, Pleasure, etc.)
CREATE TABLE IF NOT EXISTS categories (
    id TEXT NOT NULL,
    month TEXT NOT NULL,
    name TEXT NOT NULL,
    percent REAL NOT NULL DEFAULT 0.0,
    color TEXT NOT NULL DEFAULT '#888888',
    PRIMARY KEY (id, month)
);
CREATE INDEX IF NOT EXISTS idx_categories_month ON categories(month);

-- Expense categories (per month)
CREATE TABLE IF NOT EXISTS expense_categories (
    id TEXT NOT NULL,
    month TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (id, month)
);
CREATE INDEX IF NOT EXISTS idx_expense_categories_month ON expense_categories(month);

-- Income items (per month)
CREATE TABLE IF NOT EXISTS income_items (
    id TEXT PRIMARY KEY,
    month TEXT NOT NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    type TEXT NOT NULL CHECK(type IN ('addition', 'deduction')),
    category_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_income_items_month ON income_items(month);

-- Expenses (per month)
CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    month TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category_id TEXT,
    expense_category_id TEXT,
    savings_category_id TEXT,
    description TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_expenses_month ON expenses(month);
CREATE INDEX IF NOT EXISTS idx_expenses_savings_cat ON expenses(savings_category_id);

-- Explicit user snapshots of a month. These are immutable JSON payloads that
-- support "Save snapshot" without changing the live monthly records.
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    month TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_month ON snapshots(month);

-- Cashflow data (per month, per account)
CREATE TABLE IF NOT EXISTS cashflow (
    month TEXT NOT NULL,
    key TEXT NOT NULL,
    value REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT,
    PRIMARY KEY (month, key)
);

-- Savings groups
CREATE TABLE IF NOT EXISTS savings_groups (
    id TEXT NOT NULL,
    year TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (id, year)
);

-- Savings categories
CREATE TABLE IF NOT EXISTS savings_categories (
    id TEXT NOT NULL,
    year TEXT NOT NULL,
    name TEXT NOT NULL,
    target REAL NOT NULL DEFAULT 0.0,
    deadline_month INTEGER NOT NULL DEFAULT 12,
    group_id TEXT,
    next_year_target REAL,
    initial_amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (id, year)
);

-- Savings planning grid (planned amounts per category per month)
CREATE TABLE IF NOT EXISTS savings_grid (
    category_id TEXT NOT NULL,
    year TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (category_id, year, month_key)
);

-- Savings assumed available per month
CREATE TABLE IF NOT EXISTS savings_assumed (
    year TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (year, month_key)
);

-- Savings actual grid (actual saved per category per month)
CREATE TABLE IF NOT EXISTS savings_actual_grid (
    category_id TEXT NOT NULL,
    year TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (category_id, year, month_key)
);

-- Savings actual available per month
CREATE TABLE IF NOT EXISTS savings_actual_available (
    year TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (year, month_key)
);

-- Savings spent tracking
CREATE TABLE IF NOT EXISTS savings_spent (
    category_id TEXT NOT NULL,
    year TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (category_id, year)
);

-- Shared goals definitions
CREATE TABLE IF NOT EXISTS shared_goals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Shared goals persons
CREATE TABLE IF NOT EXISTS shared_goals_persons (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    name TEXT NOT NULL
);

-- Shared goals monthly data
CREATE TABLE IF NOT EXISTS shared_goals_data (
    goal_id TEXT NOT NULL,
    month_key TEXT NOT NULL,
    person_id TEXT NOT NULL,
    planned REAL NOT NULL DEFAULT 0.0,
    actual REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (goal_id, month_key, person_id)
);

-- Shared goals transactions (withdrawals)
CREATE TABLE IF NOT EXISTS shared_goals_transactions (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS emergency_fund_settings (
    mode TEXT PRIMARY KEY,
    salary REAL NOT NULL DEFAULT 0.0,
    mortgage REAL NOT NULL DEFAULT 0.0,
    living_expenses REAL NOT NULL DEFAULT 0.0,
    selected_goal TEXT NOT NULL DEFAULT '3msc_zycia',
    actual_saved REAL NOT NULL DEFAULT 0.0,
    future_goal TEXT NOT NULL DEFAULT '6msc_zycia',
    cash_allocated REAL NOT NULL DEFAULT 0.0,
    allocations TEXT NOT NULL DEFAULT '{"80% CELU OBLIGACJE": 80.0, "20% CELU KONTO OSZCZ.": 20.0}',
    manual_target REAL DEFAULT NULL,
    custom_goals TEXT NOT NULL DEFAULT '[]'
);

-- Emergency fund transactions
CREATE TABLE IF NOT EXISTS emergency_fund_transactions (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Migration tracking
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
