# data_manager.py
import json
import uuid
from pathlib import Path
from datetime import datetime
import msoffcrypto
import openpyxl
import io

DATA_DIR = Path("data")
CONFIG_FILE = Path("config.json")

def init_env():
    DATA_DIR.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config({
            "last_month": datetime.now().strftime("%Y-%m"),
            "theme": "light",
            "business_defaults": {
                "vat": 0.0,
                "tax": 0.0,
                "zus": 0.0
            },
            "cashflow_targets": [
                {"id": "daily_life", "name": "Daily Life", "target": 2000.0},
                {"id": "pleasure", "name": "Pleasure", "target": 1100.0},
                {"id": "business_expenses", "name": "Business Fees", "target": 2760.0}
            ]
        })

def get_config():
    init_env()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def _get_previous_month_str(month_str):
    """Return YYYY-MM string for the month before month_str."""
    year, month = int(month_str[:4]), int(month_str[5:7])
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"

def generate_default_month(month_str):
    # Carry over categories/expense_categories from previous month if available
    prev = _get_previous_month_str(month_str)
    prev_path = get_month_filepath(prev)
    if prev_path.exists():
        with open(prev_path, "r", encoding="utf-8") as f:
            prev_data = json.load(f)
        categories = prev_data.get("categories", [
            {"id": "daily_life", "name": "Daily Life", "percent": 40, "color": "#C9A86B"},
            {"id": "shared", "name": "Shared", "percent": 20, "color": "#6B98C9"},
            {"id": "saved", "name": "Saved", "percent": 20, "color": "#6BAD8A"},
            {"id": "pleasure", "name": "Pleasure", "percent": 20, "color": "#C96B98"},
        ])
        expense_categories = prev_data.get("expense_categories", list(DEFAULT_EXPENSE_CATEGORIES))
    else:
        categories = [
            {"id": "daily_life", "name": "Daily Life", "percent": 40, "color": "#C9A86B"},
            {"id": "shared", "name": "Shared", "percent": 20, "color": "#6B98C9"},
            {"id": "saved", "name": "Saved", "percent": 20, "color": "#6BAD8A"},
            {"id": "pleasure", "name": "Pleasure", "percent": 20, "color": "#C96B98"},
        ]
        expense_categories = list(DEFAULT_EXPENSE_CATEGORIES)

    # Seed income_items from default_income_items in config (amount=0)
    config = get_config()
    default_items = config.get("default_income_items", [])
    income_items = [
        {"id": generate_id(), "name": di["name"], "amount": 0.0, "type": di["type"], "category_id": None}
        for di in default_items
    ]

    return {
        "month": month_str,
        "income_items": income_items,
        "categories": categories,
        "expense_categories": expense_categories,
        "expenses": [],
        "cashflow": {
            "current_accounts": {},
            "shared_actual": 0.0,
            "shared_assumed": 0.0,
            "saved_assumed": 0.0,
        }
    }


def migrate_month_data(data):
    """Migrate old business/additional_income format to income_items."""
    if "income_items" in data:
        return data
    items = []
    biz = data.pop("business", {})
    if biz.get("gross_invoice", 0.0) > 0:
        items.append({"id": generate_id(), "name": "Gross Invoice", "amount": biz["gross_invoice"], "type": "addition", "category_id": None})
    if biz.get("vat_deducted", 0.0) > 0:
        items.append({"id": generate_id(), "name": "VAT", "amount": biz["vat_deducted"], "type": "deduction", "category_id": None})
    if biz.get("income_tax_deducted", 0.0) > 0:
        items.append({"id": generate_id(), "name": "Income Tax", "amount": biz["income_tax_deducted"], "type": "deduction", "category_id": None})
    if biz.get("zus_deducted", 0.0) > 0:
        items.append({"id": generate_id(), "name": "ZUS", "amount": biz["zus_deducted"], "type": "deduction", "category_id": None})
    for inc in data.pop("additional_income", []):
        items.append({"id": inc.get("id", generate_id()), "name": inc.get("description", "Extra"), "amount": inc["amount"], "type": "addition", "category_id": inc.get("target_category")})
    data["income_items"] = items
    return data

def get_month_filepath(month_str):
    return DATA_DIR / f"{month_str}.json"

def get_past_months(current_month):
    """Return list of month strings (YYYY-MM) that have data files, excluding current."""
    init_env()
    months = []
    for f in DATA_DIR.glob("????-??.json"):
        m = f.stem
        if m != current_month:
            months.append(m)
    months.sort(reverse=True)
    return months

def load_month(month_str):
    init_env()
    filepath = get_month_filepath(month_str)
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = migrate_month_data(data)
        return data
    data = generate_default_month(month_str)
    save_month(month_str, data)
    return data

def save_month(month_str, data):
    init_env()
    with open(get_month_filepath(month_str), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_id():
    return str(uuid.uuid4())

# --- Default Income Items (config-level) ---
def get_default_income_items(config=None):
    if config is None:
        config = get_config()
    return config.get("default_income_items", [])

def add_default_income_item(name, item_type="addition"):
    config = get_config()
    items = config.setdefault("default_income_items", [])
    item = {"id": generate_id(), "name": name, "type": item_type}
    items.append(item)
    save_config(config)
    return item

def delete_default_income_item(item_id):
    config = get_config()
    config["default_income_items"] = [i for i in config.get("default_income_items", []) if i["id"] != item_id]
    save_config(config)

# --- Cashflow Targets (config-level) ---
def get_cashflow_targets(config=None):
    if config is None:
        config = get_config()
    return config.get("cashflow_targets", [])

def add_cashflow_target(name, target_amount):
    config = get_config()
    targets = config.setdefault("cashflow_targets", [])
    t = {"id": generate_id(), "name": name, "target": target_amount}
    targets.append(t)
    save_config(config)
    return t

def edit_cashflow_target(target_id, name=None, target_amount=None):
    config = get_config()
    for t in config.get("cashflow_targets", []):
        if t["id"] == target_id:
            if name is not None:
                t["name"] = name
            if target_amount is not None:
                t["target"] = target_amount
            save_config(config)
            return t
    return None

def delete_cashflow_target(target_id):
    config = get_config()
    config["cashflow_targets"] = [t for t in config.get("cashflow_targets", []) if t["id"] != target_id]
    save_config(config)

# --- Cashflow monthly helpers ---
def get_cashflow(data):
    return data.setdefault("cashflow", {"current_accounts": {}, "shared_actual": 0.0, "shared_assumed": 0.0, "saved_assumed": 0.0})

# --- Savings Planner (Sinking Funds) ---
SAVINGS_FILE = DATA_DIR / "savings_planner.json"

def get_savings_planner():
    init_env()
    if SAVINGS_FILE.exists():
        with open(SAVINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    default = {
        "year": datetime.now().year,
        "categories": [],
        "groups": [],
        "grid": {},        # {cat_id: {"01": 0, "02": 0, ... "12": 0}}
        "assumed": {},     # {"01": 0, ... "12": 0}
    }
    save_savings_planner(default)
    return default

def save_savings_planner(sp):
    init_env()
    with open(SAVINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(sp, f, indent=2)

def add_savings_category(sp, name, target, deadline_month=12, group_id=None, next_year_target=None):
    cat = {
        "id": generate_id(),
        "name": name,
        "target": target,
        "deadline_month": deadline_month,
        "group_id": group_id,
        "next_year_target": next_year_target,
    }
    sp["categories"].append(cat)
    # Init grid with even distribution up to deadline
    months_count = deadline_month
    monthly = round(target / months_count, 2) if months_count > 0 else 0
    grid_row = {f"{m:02d}": monthly if m <= deadline_month else 0.0 for m in range(1, 13)}
    # If next_year_target set, distribute after deadline
    if next_year_target and deadline_month < 12:
        remaining_months = 12 - deadline_month
        monthly_nyt = round(next_year_target / remaining_months, 2)
        for m in range(deadline_month + 1, 13):
            grid_row[f"{m:02d}"] = monthly_nyt
    sp["grid"][cat["id"]] = grid_row
    return cat

def edit_savings_category(sp, cat_id, **fields):
    for cat in sp["categories"]:
        if cat["id"] == cat_id:
            cat.update(fields)
            return cat
    return None

def delete_savings_category(sp, cat_id):
    sp["categories"] = [c for c in sp["categories"] if c["id"] != cat_id]
    sp["grid"].pop(cat_id, None)

def add_savings_group(sp, name):
    g = {"id": generate_id(), "name": name}
    sp["groups"].append(g)
    return g

def edit_savings_group(sp, group_id, name):
    for g in sp["groups"]:
        if g["id"] == group_id:
            g["name"] = name
            return g
    return None

def delete_savings_group(sp, group_id):
    sp["groups"] = [g for g in sp["groups"] if g["id"] != group_id]
    for cat in sp["categories"]:
        if cat.get("group_id") == group_id:
            cat["group_id"] = None

def get_month_total_allocated(sp, month_key):
    """Sum of all categories for a given month."""
    total = 0.0
    for cat_id, months in sp.get("grid", {}).items():
        total += months.get(month_key, 0.0)
    return total

def get_month_remaining(sp, month_key):
    assumed = sp.get("assumed", {}).get(month_key, 0.0)
    allocated = get_month_total_allocated(sp, month_key)
    return assumed - allocated

# --- Actual Savings Tracker ---
def get_savings_actual(sp):
    """Get or init actual tracking data within savings planner."""
    sp.setdefault("actual_grid", {})       # {cat_id: {"01": amt, ...}}
    sp.setdefault("actual_available", {})  # {"01": amt, ...}
    sp.setdefault("spent", {})             # {cat_id: amount}
    return sp

def get_actual_month_total(sp, month_key):
    total = 0.0
    for cat_id, months in sp.get("actual_grid", {}).items():
        total += months.get(month_key, 0.0)
    return total

def get_actual_month_remaining(sp, month_key):
    available = sp.get("actual_available", {}).get(month_key, 0.0)
    allocated = get_actual_month_total(sp, month_key)
    return available - allocated

def get_cat_total_saved(sp, cat_id):
    return sum(sp.get("actual_grid", {}).get(cat_id, {}).values())

def get_cat_missing(sp, cat_id):
    cat = next((c for c in sp.get("categories", []) if c["id"] == cat_id), None)
    if not cat:
        return 0.0
    return max(0.0, cat["target"] - get_cat_total_saved(sp, cat_id))

def get_cat_progress(sp, cat_id):
    """Progress % based on target up to deadline (not full year)."""
    cat = next((c for c in sp.get("categories", []) if c["id"] == cat_id), None)
    if not cat or cat["target"] <= 0:
        return 0.0
    return min(1.0, get_cat_total_saved(sp, cat_id) / cat["target"])

def get_cat_balance(sp, cat_id, monthly_data=None):
    """Total Saved - Spent. If monthly_data provided, pull spent from expenses."""
    saved = get_cat_total_saved(sp, cat_id)
    if monthly_data:
        spent = get_savings_spent(monthly_data, cat_id)
    else:
        spent = sp.get("spent", {}).get(cat_id, 0.0)
    return saved - spent

def get_cat_rollover(sp, cat_id, monthly_data=None):
    """Calculate rollover: balance after deadline if next_year_target exists."""
    cat = next((c for c in sp.get("categories", []) if c["id"] == cat_id), None)
    if not cat or not cat.get("next_year_target"):
        return 0.0
    balance = get_cat_balance(sp, cat_id, monthly_data)
    if balance > 0 and get_cat_progress(sp, cat_id) >= 1.0:
        return balance
    return 0.0

def get_cascade_adjustments(sp, cat_id):
    """Strict per-category surplus cascade deduction.
    
    Algorithm:
    1. Only applies if category target is fully met (progress >= 100%)
    2. Surplus = Total Saved - Total Spent (the unspent excess)
    3. Cascade: deduct from post-deadline planned months left-to-right
    
    Returns {month_key: adjusted_amount} ONLY for affected cells.
    Returns empty dict if no surplus or conditions not met.
    """
    cat = next((c for c in sp.get("categories", []) if c["id"] == cat_id), None)
    if not cat or not cat.get("next_year_target"):
        return {}
    deadline = cat.get("deadline_month", 12)
    if deadline >= 12:
        return {}
    # Gate: target must be fully met for this category
    if get_cat_progress(sp, cat_id) < 1.0:
        return {}
    # Surplus = Saved up to deadline - Total Spent (post-deadline savings are for next year)
    actual_row = sp.get("actual_grid", {}).get(cat_id, {})
    total_saved = sum(actual_row.get(f"{m:02d}", 0.0) for m in range(1, deadline + 1))
    total_spent = _get_all_months_savings_spent(cat_id)
    # No surplus if nothing has been spent yet (goal event hasn't occurred)
    if total_spent <= 0:
        return {}
    surplus = total_saved - total_spent
    if surplus <= 0:
        return {}
    # Cascade loop: only post-deadline months
    grid_row = sp.get("grid", {}).get(cat_id, {})
    adjustments = {}
    remaining_surplus = surplus
    for m in range(deadline + 1, 13):
        if remaining_surplus <= 0:
            break
        mk = f"{m:02d}"
        planned = grid_row.get(mk, 0.0)
        if planned <= 0:
            continue
        if remaining_surplus >= planned:
            adjustments[mk] = 0.0
            remaining_surplus -= planned
        else:
            adjustments[mk] = planned - remaining_surplus
            remaining_surplus = 0.0
    return adjustments


def _get_all_months_savings_spent(savings_cat_id):
    """Sum expenses funded from a savings category across ALL month files."""
    init_env()
    total = 0.0
    for f in DATA_DIR.glob("????-??.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for exp in data.get("expenses", []):
                if exp.get("savings_category_id") == savings_cat_id:
                    total += exp.get("amount", 0.0)
        except:
            pass
    return total

def load_xlsx(filepath: str, password: str = None, sheet_name: str = "kwiecień 2026") -> dict:
    try:
        with open(filepath, 'rb') as f:
            if password:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=password)
                decrypted = io.BytesIO()
                office_file.decrypt(decrypted)
                wb = openpyxl.load_workbook(decrypted, data_only=True)
            else:
                wb = openpyxl.load_workbook(f, data_only=True)
                
        sheet = None
        for name in wb.sheetnames:
            if name.strip().lower() == sheet_name.strip().lower():
                sheet = wb[name]
                break

        if not sheet:
            return {"error": "sheet_not_found", "available_sheets": wb.sheetnames}
            
        # Simplified parser mock for MVP
        return {"status": "success", "message": "Imported basic layout"}
    except Exception as e:
        return {"error": "import_failed", "message": str(e)}

# --- Expense Categories CRUD ---
DEFAULT_EXPENSE_CATEGORIES = [
    {"id": "groceries", "name": "Groceries"},
    {"id": "healthcare", "name": "Healthcare"},
    {"id": "beauty", "name": "Beauty"},
    {"id": "transport", "name": "Transport"},
    {"id": "subscriptions", "name": "Subscriptions"},
    {"id": "household", "name": "Household"},
    {"id": "eating_out", "name": "Eating Out"},
    {"id": "other", "name": "Other"},
]

def get_expense_categories(data):
    return data.get("expense_categories", [])

def add_expense_category(data, name):
    cat = {"id": generate_id(), "name": name}
    data.setdefault("expense_categories", []).append(cat)
    return cat

def edit_expense_category(data, cat_id, new_name):
    for cat in data.get("expense_categories", []):
        if cat["id"] == cat_id:
            cat["name"] = new_name
            return cat
    return None

def delete_expense_category(data, cat_id):
    data["expense_categories"] = [c for c in data.get("expense_categories", []) if c["id"] != cat_id]
    # Remove category from expenses that used it
    for exp in data.get("expenses", []):
        if exp.get("expense_category_id") == cat_id:
            exp["expense_category_id"] = None

# --- Expense CRUD ---
def add_expense(data, date, amount, split_category_id, expense_category_id=None, description="", tags=None):
    exp = {
        "id": generate_id(),
        "date": date,
        "amount": amount,
        "category_id": split_category_id,  # income split bucket
        "expense_category_id": expense_category_id,
        "description": description,
        "tags": tags or [],
    }
    data.setdefault("expenses", []).append(exp)
    return exp

def edit_expense(data, exp_id, **fields):
    for exp in data.get("expenses", []):
        if exp["id"] == exp_id:
            exp.update(fields)
            return exp
    return None

def delete_expense(data, exp_id):
    data["expenses"] = [e for e in data.get("expenses", []) if e["id"] != exp_id]

# --- Summary helpers ---
def get_expenses_by_expense_category(data):
    """Group expenses by expense_category_id. Returns {cat_id: [expenses]}."""
    grouped = {}
    for exp in data.get("expenses", []):
        key = exp.get("expense_category_id") or "uncategorized"
        grouped.setdefault(key, []).append(exp)
    return grouped

def get_expense_category_total(data, expense_cat_id):
    return sum(e["amount"] for e in data.get("expenses", []) if e.get("expense_category_id") == expense_cat_id)

def get_expense_category_split_breakdown(data, expense_cat_id):
    """For an expense category, show how much from each funding source."""
    breakdown = {}
    for exp in data.get("expenses", []):
        if exp.get("expense_category_id") == expense_cat_id:
            if exp.get("savings_category_id"):
                key = f"sav:{exp['savings_category_id']}"
            else:
                key = exp.get("category_id") or "unknown"
            breakdown[key] = breakdown.get(key, 0.0) + exp["amount"]
    return breakdown

# --- Helper calculations ---
def get_net_income(data):
    total = 0.0
    for item in data.get("income_items", []):
        if item["type"] == "addition":
            total += item["amount"]
        else:
            total -= item["amount"]
    return total


def get_allocated_amount(data, category_id):
    net_income = get_net_income(data)
    cat_extra = sum(item["amount"] for item in data.get("income_items", []) if item.get("category_id") == category_id and item["type"] == "addition")
    general_net = net_income - sum(item["amount"] for item in data.get("income_items", []) if item.get("category_id") and item["type"] == "addition")
    for cat in data.get("categories", []):
        if cat["id"] == category_id:
            return general_net * (cat["percent"] / 100.0) + cat_extra
    return 0.0

def get_spent_amount(data, category_id):
    """Sum expenses for income split bucket, excluding savings-funded ones."""
    total = 0.0
    for exp in data.get("expenses", []):
        if exp.get("category_id") == category_id and not exp.get("savings_category_id"):
            total += exp["amount"]
    return total

def get_savings_spent(data, savings_cat_id):
    """Sum expenses funded from a specific savings category."""
    total = 0.0
    for exp in data.get("expenses", []):
        if exp.get("savings_category_id") == savings_cat_id:
            total += exp["amount"]
    return total

def get_total_expenses(data):
    return sum(exp["amount"] for exp in data.get("expenses", []))

def get_remaining_amount(data, category_id):
    allocated = get_allocated_amount(data, category_id)
    spent = get_spent_amount(data, category_id)
    return allocated - spent
