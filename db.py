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
    conn.executescript(SCHEMA_SQL)


SCHEMA_SQL = """
-- App settings (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Cashflow targets (managed in Settings)
CREATE TABLE IF NOT EXISTS cashflow_targets (
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
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

-- Savings categories
CREATE TABLE IF NOT EXISTS savings_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target REAL NOT NULL DEFAULT 0.0,
    deadline_month INTEGER NOT NULL DEFAULT 12,
    group_id TEXT,
    next_year_target REAL
);

-- Savings planning grid (planned amounts per category per month)
CREATE TABLE IF NOT EXISTS savings_grid (
    category_id TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (category_id, month_key)
);

-- Savings assumed available per month
CREATE TABLE IF NOT EXISTS savings_assumed (
    month_key TEXT PRIMARY KEY,
    amount REAL NOT NULL DEFAULT 0.0
);

-- Savings actual grid (actual saved per category per month)
CREATE TABLE IF NOT EXISTS savings_actual_grid (
    category_id TEXT NOT NULL,
    month_key TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (category_id, month_key)
);

-- Savings actual available per month
CREATE TABLE IF NOT EXISTS savings_actual_available (
    month_key TEXT PRIMARY KEY,
    amount REAL NOT NULL DEFAULT 0.0
);

-- Savings spent tracking
CREATE TABLE IF NOT EXISTS savings_spent (
    category_id TEXT PRIMARY KEY,
    amount REAL NOT NULL DEFAULT 0.0
);

-- Migration tracking
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
