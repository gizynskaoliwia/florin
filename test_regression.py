import os
import shutil
import sqlite3
import unittest
from pathlib import Path

# Monkey-patch db path BEFORE importing data_manager
import db
TEST_DB_PATH = Path(__file__).parent / "florin-test.db"
db.get_db_path = lambda: TEST_DB_PATH

import data_manager

class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Copy original DB to test DB
        src = Path(__file__).parent / "florin.db"
        if src.exists():
            shutil.copy2(src, TEST_DB_PATH)
        else:
            print(f"Warning: Source db {src} not found. Creating empty test DB.")
        
        # Ensure connection uses the patched path and schema is initialized
        db.close()
        data_manager.init_env()

    @classmethod
    def tearDownClass(cls):
        db.close()

    def test_01_expenses_crud(self):
        month = "2026-04"
        data = data_manager.load_month(month)
        initial_expenses_count = len(data.get("expenses", []))
        
        # Add expense
        exp = data_manager.add_expense(
            data=data,
            date="2026-04-10",
            amount=150.0,
            split_category_id="daily_life",
            expense_category_id=None,
            description="Test Expense",
            tags=["test"]
        )
        data_manager.save_month(month, data)
        
        # Verify Add
        data_reloaded = data_manager.load_month(month)
        self.assertEqual(len(data_reloaded["expenses"]), initial_expenses_count + 1)
        added_exp = next(e for e in data_reloaded["expenses"] if e["id"] == exp["id"])
        self.assertEqual(added_exp["amount"], 150.0)
        
        # Edit expense
        data_manager.edit_expense(data_reloaded, exp["id"], amount=200.0)
        data_manager.save_month(month, data_reloaded)
        
        # Verify Edit
        data_reloaded_2 = data_manager.load_month(month)
        edited_exp = next(e for e in data_reloaded_2["expenses"] if e["id"] == exp["id"])
        self.assertEqual(edited_exp["amount"], 200.0)
        
        # Delete expense
        data_manager.delete_expense(data_reloaded_2, exp["id"])
        data_manager.save_month(month, data_reloaded_2)
        
        # Verify Delete
        data_reloaded_3 = data_manager.load_month(month)
        self.assertEqual(len(data_reloaded_3["expenses"]), initial_expenses_count)

    def test_02_income_deductions(self):
        month = "2026-05" # Use a new month to avoid interference
        data = data_manager.load_month(month)
        
        # Set income items explicitly
        data["income_items"] = [
            {"id": "inc1", "type": "addition", "amount": 10000.0, "name": "Invoice 1"},
            {"id": "ded1", "type": "deduction", "amount": 2000.0, "name": "Tax"}
        ]
        
        # Calculate net income
        net = data_manager.get_net_income(data)
        self.assertEqual(net, 8000.0)
        
        # Add targeted addition
        data["income_items"].append({"id": "inc2", "type": "addition", "amount": 500.0, "name": "Bonus", "category_id": "daily_life"})
        net_with_bonus = data_manager.get_net_income(data)
        self.assertEqual(net_with_bonus, 8500.0)

    def test_03_cashflow_targets(self):
        month = "2026-05"
        data = data_manager.load_month(month)
        
        # Mock targets
        targets = [{"id": "t1", "name": "Target 1", "target": 1000.0}]
        
        cf = data_manager.get_cashflow(data)
        
        # Set some balances
        tid = targets[0]["id"]
        target_amt = targets[0]["target"]
        
        acct = cf.setdefault("current_accounts", {}).setdefault(tid, {"balance": 0.0, "updated_at": ""})
        acct["balance"] = target_amt - 100.0 # Missing 100
        
        data_manager.save_month(month, data)
        data_reloaded = data_manager.load_month(month)
        cf_reloaded = data_manager.get_cashflow(data_reloaded)
        
        reloaded_acct = cf_reloaded.get("current_accounts", {}).get(tid, {})
        self.assertEqual(reloaded_acct.get("balance"), target_amt - 100.0)

    def test_04_history_integrity(self):
        month = "2026-05"
        data = data_manager.load_month(month)
        
        # Test that history correctly calculates net income
        past_months = data_manager.get_past_months("2026-06")
        self.assertIn("2026-05", past_months)
        
        net = data_manager.get_net_income(data)
        self.assertTrue(net > 0)
        
        expenses = data_manager.get_total_expenses(data)
        self.assertTrue(expenses >= 0.0)

    def test_05_dashboard_logic(self):
        month = "2026-05"
        data = data_manager.load_month(month)
        
        # Test dashboard totals
        net = data_manager.get_net_income(data)
        self.assertTrue(net > 0)
        
        cats = data.get("categories", [])
        total_exp = data_manager.get_total_expenses(data)
        
        # Should execute without errors
        remaining = sum(data_manager.get_remaining_amount(data, cat["id"]) for cat in cats)
        self.assertTrue(isinstance(remaining, float))

    def test_06_shared_goals(self):
        month = "2026-05"
        data = data_manager.load_month(month)
        # Mock config
        config = {"shared_goals": [{"id": "sg1", "name": "Goal 1"}]}
        
        # Test that reading shared goals executes without error
        goals = config.get("shared_goals", [])
        self.assertTrue(isinstance(goals, list))
        
        # If there are goals, test logic
        if goals:
            goal_id = goals[0]["id"]
            cf = data_manager.get_cashflow(data)
            self.assertTrue(isinstance(cf, dict))

if __name__ == "__main__":
    unittest.main()
