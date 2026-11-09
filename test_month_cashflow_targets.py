import unittest
import os
import shutil
import sqlite3
from pathlib import Path

import db
TEST_DB_PATH = Path(__file__).parent / "test_cashflow_temp.db"
orig_get_db_path = db.get_db_path
db.get_db_path = lambda: TEST_DB_PATH

import data_manager as dm

class TestMonthCashflowTargets(unittest.TestCase):
    def setUp(self):
        db.close()
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass
        # Initialize schema in fresh test DB
        _ = db.get_connection()

    def tearDown(self):
        db.close()
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        db.close()
        db.get_db_path = orig_get_db_path
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass

    def test_default_cashflow_targets(self):
        defaults = dm.get_default_cashflow_targets()
        self.assertTrue(len(defaults) >= 6)
        names = [d["name"] for d in defaults]
        self.assertIn("Daily Life", names)
        self.assertIn("Pleasure", names)
        self.assertIn("Business", names)
        self.assertIn("Wspólne konto wykończenie", names)
        self.assertIn("Wspólne konto", names)
        self.assertIn("Wspólne wesele", names)

        # Add a default target
        new_def = dm.add_default_cashflow_target("Emergency Default", 3000.0)
        defaults_after = dm.get_default_cashflow_targets()
        self.assertEqual(len(defaults_after), len(defaults) + 1)
        self.assertIn("Emergency Default", [d["name"] for d in defaults_after])

        # Edit default target
        dm.edit_default_cashflow_target(new_def["id"], name="Emergency Renamed", target_amount=3500.0)
        defaults_edited = dm.get_default_cashflow_targets()
        edited_item = [d for d in defaults_edited if d["id"] == new_def["id"]][0]
        self.assertEqual(edited_item["name"], "Emergency Renamed")
        self.assertEqual(edited_item["target"], 3500.0)

        # Delete default target
        dm.delete_default_cashflow_target(new_def["id"])
        defaults_final = dm.get_default_cashflow_targets()
        self.assertNotIn("Emergency Renamed", [d["name"] for d in defaults_final])

    def test_month_specific_isolation(self):
        month_a = "2026-04"
        month_b = "2026-05"

        # Load month A - should have initial defaults
        data_a = dm.load_month(month_a)
        targets_a = dm.get_cashflow_targets(data=data_a, month=month_a)
        self.assertTrue(len(targets_a) >= 3)
        orig_count = len(targets_a)

        # Add a custom target ONLY to month A
        custom_a = dm.add_cashflow_target("Apteczka A", 250.0, month=month_a, data=data_a)
        dm.save_month(month_a, data_a)

        # Verify month A has the new target
        data_a_reloaded = dm.load_month(month_a)
        targets_a_reloaded = data_a_reloaded.get("cashflow_targets", [])
        self.assertEqual(len(targets_a_reloaded), orig_count + 1)
        self.assertIn("Apteczka A", [t["name"] for t in targets_a_reloaded])

        # Load month B
        data_b = dm.load_month(month_b)
        targets_b = data_b.get("cashflow_targets", [])
        
        # Now change target amount in month B and add new one
        first_b = targets_b[0]
        dm.edit_cashflow_target(first_b["id"], target_amount=9999.0, month=month_b, data=data_b)
        custom_b = dm.add_cashflow_target("Wakacje B", 4000.0, month=month_b, data=data_b)
        dm.save_month(month_b, data_b)

        # Check month B
        data_b_reloaded = dm.load_month(month_b)
        targets_b_reloaded = data_b_reloaded["cashflow_targets"]
        b_target_map = {t["id"]: t for t in targets_b_reloaded}
        self.assertEqual(b_target_map[first_b["id"]]["target"], 9999.0)
        self.assertIn("Wakacje B", [t["name"] for t in targets_b_reloaded])

        # Check month A - verify it was NOT modified by month B changes
        data_a_check = dm.load_month(month_a)
        targets_a_check = data_a_check["cashflow_targets"]
        a_target_map = {t["id"]: t for t in targets_a_check}
        self.assertNotEqual(a_target_map[first_b["id"]]["target"], 9999.0)
        self.assertNotIn("Wakacje B", [t["name"] for t in targets_a_check])
        self.assertIn("Apteczka A", [t["name"] for t in targets_a_check])

        # Delete a target in month A
        dm.delete_cashflow_target(custom_a["id"], month=month_a, data=data_a_check)
        dm.save_month(month_a, data_a_check)

        data_a_after_del = dm.load_month(month_a)
        self.assertNotIn("Apteczka A", [t["name"] for t in data_a_after_del["cashflow_targets"]])

    def test_legacy_database_migration(self):
        leg_path = Path(__file__).parent / "legacy_test_tmp.db"
        if leg_path.exists():
            leg_path.unlink()
        try:
            conn = sqlite3.connect(str(leg_path))
            conn.row_factory = sqlite3.Row
            # Create old cashflow_targets table
            conn.execute("""
                CREATE TABLE cashflow_targets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    target REAL NOT NULL DEFAULT 0.0,
                    sort_order INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.execute("INSERT INTO cashflow_targets VALUES ('t1', 'Daily Life', 1500.0, 0)")
            conn.execute("INSERT INTO cashflow_targets VALUES ('t2', 'Pleasure', 500.0, 1)")
            conn.execute("INSERT INTO cashflow_targets VALUES ('t3', 'Business', 700.0, 2)")
            
            # Create categories with months
            conn.execute("CREATE TABLE categories (id TEXT, month TEXT, name TEXT)")
            conn.execute("INSERT INTO categories VALUES ('c1', '2026-04', 'Daily Life')")
            conn.execute("INSERT INTO categories VALUES ('c2', '2026-05', 'Daily Life')")
            conn.commit()

            # Now run _init_schema to trigger migration
            db._init_schema(conn)

            # Check that cashflow_targets now has month column
            cols = [c["name"] for c in conn.execute("PRAGMA table_info(cashflow_targets)").fetchall()]
            self.assertIn("month", cols)

            # Check that both months have all 6 targets (3 legacy + 3 shared defaults)
            rows_04 = conn.execute("SELECT id, name, target FROM cashflow_targets WHERE month = '2026-04' ORDER BY sort_order").fetchall()
            self.assertEqual(len(rows_04), 6)
            self.assertEqual(rows_04[0]["name"], "Daily Life")
            self.assertEqual(rows_04[0]["target"], 1500.0)

            rows_05 = conn.execute("SELECT id, name, target FROM cashflow_targets WHERE month = '2026-05' ORDER BY sort_order").fetchall()
            self.assertEqual(len(rows_05), 6)

            # Check default_cashflow_targets exists and has templates
            defaults = conn.execute("SELECT name, target FROM default_cashflow_targets ORDER BY sort_order").fetchall()
            self.assertEqual(len(defaults), 6)
            self.assertEqual(defaults[0]["name"], "Daily Life")
            conn.close()
        finally:
            if leg_path.exists():
                try:
                    leg_path.unlink()
                except Exception:
                    pass

    def test_cashflow_view_edit_mode_rendering(self):
        import customtkinter as ctk
        import views.cashflow as cf

        root = ctk.CTk()
        try:
            month = "2026-10"
            data = dm.load_month(month)

            class Controller:
                current_month = month
                config = dm.get_config()
                def __init__(self, d): self.data = d
                def save_data(self): pass
                def change_month(self, delta): pass
                def show_view(self, view): pass

            ctrl = Controller(data)
            view = cf.CashFlowView(root, ctrl)

            # View mode
            view.editing = False
            view.build()
            self.assertEqual(len(view.balance_vars), len(data.get("cashflow_targets", [])))

            # Toggle to edit mode
            view.toggle_edit()
            self.assertTrue(view.editing)
            # Ensure all targets rendered in edit mode
            self.assertEqual(len(view.balance_vars), len(data.get("cashflow_targets", [])))
            self.assertEqual(len(view.target_vars), len(data.get("cashflow_targets", [])))

            # Toggle back
            view.toggle_edit()
            self.assertFalse(view.editing)
        finally:
            root.destroy()

if __name__ == "__main__":
    unittest.main()
