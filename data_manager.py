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
            "buffer_minimums": {
                "daily_life": 2000.0,
                "pleasure": 1100.0,
                "business_expenses": 2760.0
            }
        })

def get_config():
    init_env()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def generate_default_month(month_str):
    config = get_config()
    defaults = config.get("business_defaults", {"vat": 0.0, "tax": 0.0, "zus": 0.0})
    return {
        "month": month_str,
        "business": {
            "gross_invoice": 0.0,
            "vat_deducted": defaults.get("vat", 0.0),
            "income_tax_deducted": defaults.get("tax", 0.0),
            "zus_deducted": defaults.get("zus", 0.0),
            "net_income": 0.0
        },
        "additional_income": [],
        "categories": [
            { "id": "daily_life", "name": "Daily Life", "percent": 40, "color": "#C9A86B" },
            { "id": "shared", "name": "Shared", "percent": 20, "color": "#6B98C9" },
            { "id": "saved", "name": "Saved", "percent": 20, "color": "#6BAD8A" },
            { "id": "pleasure", "name": "Pleasure", "percent": 20, "color": "#C96B98" }
        ],
        "expenses": [],
        "cashflow_buffer": {
            "minimums": config.get("buffer_minimums", {
                "daily_life": 2000.0,
                "pleasure": 1100.0,
                "business_expenses": 2760.0
            }),
            "current_on_account": {
                "daily_life": 0.0,
                "pleasure": 0.0,
                "business_expenses": 0.0
            }
        }
    }

def get_month_filepath(month_str):
    return DATA_DIR / f"{month_str}.json"

def load_month(month_str):
    init_env()
    filepath = get_month_filepath(month_str)
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    data = generate_default_month(month_str)
    save_month(month_str, data)
    return data

def save_month(month_str, data):
    init_env()
    with open(get_month_filepath(month_str), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_id():
    return str(uuid.uuid4())

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

# --- Helper calculations ---
def get_allocated_amount(data, category_id):
    net_income = data.get("business", {}).get("net_income", 0.0)
    for cat in data.get("categories", []):
        if cat["id"] == category_id:
            return net_income * (cat["percent"] / 100.0)
    return 0.0

def get_spent_amount(data, category_id):
    total = 0.0
    for exp in data.get("expenses", []):
        if exp["category_id"] == category_id:
            total += exp["amount"]
    return total

def get_total_expenses(data):
    return sum(exp["amount"] for exp in data.get("expenses", []))

def get_remaining_amount(data, category_id):
    allocated = get_allocated_amount(data, category_id)
    for inc in data.get("additional_income", []):
        if inc.get("target_category") == category_id:
            allocated += inc["amount"]
    spent = get_spent_amount(data, category_id)
    return allocated - spent
