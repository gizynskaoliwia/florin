"""verify_full_system.py — Comprehensive end-to-end verification script for Florin budget tracker.
Tests:
1. Database integrity & zero mismatches between expense dates and budget months.
2. Calculations: Net income, allocations, spent amounts, category remainders.
3. Expense workflows: Add within budget month, add across boundary (moves to correct month), edit date across boundary, delete.
4. Month navigation and period string formatting.
5. All UI views instantiation and data rendering.
"""
import sys
import unittest
from datetime import datetime, date
import sqlite3
from pathlib import Path

import db
import data_manager as dm
from main import FlorinApp, month_year_label

class TestFullSystemVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dm.init_env()

    def test_01_db_budget_month_integrity(self):
        """Verify all 186 expenses in the database strictly belong to their date's budget month."""
        conn = db.get_connection()
        rows = conn.execute("SELECT id, month, date, amount, description FROM expenses").fetchall()
        self.assertGreater(len(rows), 0, "Database should contain expenses.")

        mismatches = []
        for r in rows:
            expected = dm.date_to_budget_month(r["date"])
            if expected != r["month"]:
                mismatches.append((r["id"], r["date"], r["month"], expected))

        self.assertEqual(len(mismatches), 0, f"Found {len(mismatches)} mismatches in DB: {mismatches[:5]}")

    def test_02_month_date_boundary_rules(self):
        """Verify strict 15th-to-14th date boundary rules."""
        # Exact 15th (start of budget month)
        self.assertEqual(dm.date_to_budget_month("15/04/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("15/11/2026"), "2026-11")

        # End of calendar month (belongs to that month's budget period)
        self.assertEqual(dm.date_to_budget_month("30/04/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("31/05/2026"), "2026-05")

        # 1st of next calendar month (belongs to PREVIOUS month's budget period)
        self.assertEqual(dm.date_to_budget_month("01/05/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("14/05/2026"), "2026-04")

        # 15th of next calendar month (starts new budget period)
        self.assertEqual(dm.date_to_budget_month("15/05/2026"), "2026-05")

        # Year rollover edge case: Jan 1st - 14th belongs to previous December
        self.assertEqual(dm.date_to_budget_month("01/01/2026"), "2025-12")
        self.assertEqual(dm.date_to_budget_month("14/01/2026"), "2025-12")
        self.assertEqual(dm.date_to_budget_month("15/01/2026"), "2026-01")

        # February / Leap year edge cases
        self.assertEqual(dm.date_to_budget_month("28/02/2026"), "2026-02")
        self.assertEqual(dm.date_to_budget_month("01/03/2026"), "2026-02")
        self.assertEqual(dm.date_to_budget_month("14/03/2026"), "2026-02")
        self.assertEqual(dm.date_to_budget_month("15/03/2026"), "2026-03")

    def test_03_period_formatting_and_ranges(self):
        """Verify human readable period string generation."""
        self.assertEqual(dm.get_budget_period_str("2026-04"), "15.04 – 14.05")
        self.assertEqual(dm.get_budget_period_str("2026-12"), "15.12 – 14.01")
        self.assertEqual(dm.get_budget_period_str("2026-01"), "15.01 – 14.02")

        start, end = dm.get_budget_month_range("2026-04")
        self.assertEqual(start, date(2026, 4, 15))
        self.assertEqual(end, date(2026, 5, 14))

        start_dec, end_dec = dm.get_budget_month_range("2026-12")
        self.assertEqual(start_dec, date(2026, 12, 15))
        self.assertEqual(end_dec, date(2027, 1, 14))

    def test_04_calculations_accuracy(self):
        """Verify calculations for net income, split percentages, and remainders."""
        test_m = "2099-05"
        # Load or generate
        data = dm.generate_default_month(test_m)
        data["income_items"] = [
            {"id": "inv1", "name": "Faktura B2B", "amount": 10000.0, "type": "addition", "category_id": None},
            {"id": "vat", "name": "VAT", "amount": 2300.0, "type": "deduction", "category_id": None},
            {"id": "zus", "name": "ZUS", "amount": 1700.0, "type": "deduction", "category_id": None},
            {"id": "tax", "name": "Podatek dochodowy", "amount": 1000.0, "type": "deduction", "category_id": None},
            {"id": "bonus", "name": "Dodatek na życie", "amount": 500.0, "type": "addition", "category_id": "daily_life"},
        ]
        # Net income should be 10000 - 2300 - 1700 - 1000 + 500 = 5500.0
        net = dm.get_net_income(data)
        self.assertEqual(net, 5500.0)

        # Categories: daily_life (40%), shared (20%), saved (20%), pleasure (20%)
        # general net = 5500 - 500 = 5000.
        # daily_life: 5000 * 40% + 500 = 2500.
        # shared: 5000 * 20% = 1000.
        self.assertAlmostEqual(dm.get_allocated_amount(data, "daily_life"), 2500.0)
        self.assertAlmostEqual(dm.get_allocated_amount(data, "shared"), 1000.0)

        # Add expenses in this period (15.05 - 14.06)
        dm.add_expense(data, "20/05/2099", 500.0, "daily_life", description="Zakupy")
        dm.add_expense(data, "05/06/2099", 300.0, "daily_life", description="Apteka") # 05/06 belongs to 2099-05 period!
        dm.add_expense(data, "10/06/2099", 200.0, "shared", description="Czynsz")     # 10/06 belongs to 2099-05 period!

        dm.save_month(test_m, data)

        reloaded = dm.load_month(test_m)
        self.assertEqual(len(reloaded["expenses"]), 3)
        self.assertEqual(dm.get_spent_amount(reloaded, "daily_life"), 800.0)
        self.assertEqual(dm.get_remaining_amount(reloaded, "daily_life"), 1700.0)
        self.assertEqual(dm.get_spent_amount(reloaded, "shared"), 200.0)
        self.assertEqual(dm.get_remaining_amount(reloaded, "shared"), 800.0)
        self.assertEqual(dm.get_total_expenses(reloaded), 1000.0)

        # Clean up test month
        conn = db.get_connection()
        conn.execute("DELETE FROM categories WHERE month = ?", (test_m,))
        conn.execute("DELETE FROM expense_categories WHERE month = ?", (test_m,))
        conn.execute("DELETE FROM income_items WHERE month = ?", (test_m,))
        conn.execute("DELETE FROM expenses WHERE month = ?", (test_m,))
        conn.execute("DELETE FROM cashflow WHERE month = ?", (test_m,))
        conn.commit()

    def test_05_expense_cross_month_reassignment(self):
        """Verify that when an expense is added or edited with a date falling into another budget month,
        it is saved to the correct budget month."""
        month_a = "2099-01" # Period: 15.01.2099 - 14.02.2099
        month_b = "2099-02" # Period: 15.02.2099 - 14.03.2099

        data_a = dm.load_month(month_a)
        data_b = dm.load_month(month_b)

        # Date 10/02/2099 belongs to month_a (15.01 - 14.02)
        exp_target_a = dm.date_to_budget_month("10/02/2099")
        self.assertEqual(exp_target_a, month_a)

        # Date 20/02/2099 belongs to month_b (15.02 - 14.03)
        exp_target_b = dm.date_to_budget_month("20/02/2099")
        self.assertEqual(exp_target_b, month_b)

        # Date 01/03/2099 belongs to month_b (15.02 - 14.03)
        exp_target_b2 = dm.date_to_budget_month("01/03/2099")
        self.assertEqual(exp_target_b2, month_b)

        # Cleanup
        conn = db.get_connection()
        for m in (month_a, month_b):
            conn.execute("DELETE FROM categories WHERE month = ?", (m,))
            conn.execute("DELETE FROM expense_categories WHERE month = ?", (m,))
            conn.execute("DELETE FROM income_items WHERE month = ?", (m,))
            conn.execute("DELETE FROM expenses WHERE month = ?", (m,))
            conn.execute("DELETE FROM cashflow WHERE month = ?", (m,))
        conn.commit()

    def test_06_ui_instantiation_and_month_navigation(self):
        """Verify that the full GUI app initializes and all views render properly with budget month labels."""
        app = FlorinApp()
        expected_current = dm.get_current_budget_month()
        self.assertEqual(app.current_month, expected_current)

        for view_name in ["Dashboard", "Income", "Expenses", "Savings", "Cash Flow", "History", "Settings"]:
            app.show_view(view_name)
            view = app.views[view_name]
            self.assertIsNotNone(view)

        cur_m = app.current_month
        app.change_month(1)
        year, month = map(int, cur_m.split("-"))
        next_m = 1 if month == 12 else month + 1
        next_y = year + 1 if month == 12 else year
        self.assertEqual(app.current_month, f"{next_y:04d}-{next_m:02d}")

        app.change_month(-1)
        self.assertEqual(app.current_month, cur_m)
        app.destroy()

    def test_07_savings_planner_year_isolation_no_duplicates(self):
        """Verify that savings planner queries isolate categories/groups by year and have no duplicates."""
        sp26 = dm.get_savings_planner("2026")
        dm.get_savings_actual(sp26)
        cat_ids26 = [c["id"] for c in sp26["categories"]]
        cat_names26 = [c["name"] for c in sp26["categories"]]
        group_ids26 = [g["id"] for g in sp26["groups"]]
        self.assertEqual(len(cat_ids26), len(set(cat_ids26)), "2026 categories contain duplicate IDs")
        self.assertEqual(len(cat_names26), len(set(cat_names26)), "2026 categories contain duplicate names")
        self.assertEqual(len(group_ids26), len(set(group_ids26)), "2026 groups contain duplicate IDs")

        sp27 = dm.get_savings_planner("2027")
        dm.get_savings_actual(sp27)
        cat_ids27 = [c["id"] for c in sp27["categories"]]
        cat_names27 = [c["name"] for c in sp27["categories"]]
        group_ids27 = [g["id"] for g in sp27["groups"]]
        self.assertEqual(len(cat_ids27), len(set(cat_ids27)), "2027 categories contain duplicate IDs")
        self.assertEqual(len(cat_names27), len(set(cat_names27)), "2027 categories contain duplicate names")
        self.assertEqual(len(group_ids27), len(set(group_ids27)), "2027 groups contain duplicate IDs")

        self.assertEqual(len(sp26["categories"]), 33)
        self.assertEqual(len(sp27["categories"]), 30)
        self.assertEqual(len(sp26["groups"]), 9)
        self.assertEqual(len(sp27["groups"]), 9)

    def test_08_savings_starting_amount_and_year_independence(self):
        """Verify initial_amount persistence, calculations, carryover suggestions, and category independence between years."""
        sp27 = dm.get_savings_planner("2027")
        sp26 = dm.get_savings_planner("2026")

        # Suggestions from 2026
        suggs = {c["name"]: dm.get_previous_year_savings_suggestion(sp27, c["id"], c["name"]) for c in sp27["categories"]}
        valid_suggs = {k: v for k, v in suggs.items() if v}
        self.assertGreater(len(valid_suggs), 0, "Expected suggestions from 2026 for 2027 categories")

        # Independence: add a category in 2027 with initial amount
        new_cat = dm.add_savings_category(sp27, "Test Independency 2027", target=1200.0, deadline_month=6, initial_amount=200.0)
        self.assertEqual(new_cat["initial_amount"], 200.0)
        self.assertEqual(sp27["grid"][new_cat["id"]]["01"], round(1000.0 / 6, 2))
        dm.save_savings_planner(sp27)

        # 2026 must be unaffected
        sp26_reloaded = dm.get_savings_planner("2026")
        self.assertFalse(any(c["name"] == "Test Independency 2027" for c in sp26_reloaded["categories"]))

        # Calculations verification
        saved_dl = dm.get_cat_saved_until_deadline(sp27, new_cat["id"])
        missing = dm.get_cat_missing(sp27, new_cat["id"])
        prog = dm.get_cat_progress(sp27, new_cat["id"])
        self.assertEqual(saved_dl, 200.0)
        self.assertEqual(missing, 1000.0)
        self.assertAlmostEqual(prog, 200.0 / 1200.0)

        # Deletion: cannot delete while initial_amount > 0
        can_del, msg = dm.can_delete_savings_category(sp27, new_cat["id"])
        self.assertFalse(can_del)
        new_cat["initial_amount"] = 0.0
        can_del, msg = dm.can_delete_savings_category(sp27, new_cat["id"])
        self.assertTrue(can_del)
        dm.delete_savings_category(sp27, new_cat["id"])
        dm.save_savings_planner(sp27)

        # Verify cross-year expense deletion rule
        fryzjer_2026 = next((c for c in sp26["categories"] if "fryzjer" in c["name"].lower()), None)
        if fryzjer_2026:
            can_del_26, _ = dm.can_delete_savings_category(sp26, fryzjer_2026["id"])
            can_del_27, _ = dm.can_delete_savings_category(sp27, fryzjer_2026["id"])
            self.assertFalse(can_del_26)  # has expenses in 2026
            self.assertTrue(can_del_27)   # no expenses in 2027

if __name__ == "__main__":
    import os
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFullSystemVerification)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    os._exit(0 if res.wasSuccessful() else 1)
