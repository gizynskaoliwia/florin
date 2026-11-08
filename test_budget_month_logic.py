import unittest
from datetime import datetime, date
import data_manager as dm

class TestBudgetMonthLogic(unittest.TestCase):
    def test_date_to_budget_month_boundaries(self):
        # 15th of month starts that budget month
        self.assertEqual(dm.date_to_budget_month("15/04/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("16/04/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("30/04/2026"), "2026-04")

        # 1st - 14th of next month belongs to current budget month
        self.assertEqual(dm.date_to_budget_month("01/05/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("10/05/2026"), "2026-04")
        self.assertEqual(dm.date_to_budget_month("14/05/2026"), "2026-04")

        # 15th of next month starts next budget month
        self.assertEqual(dm.date_to_budget_month("15/05/2026"), "2026-05")

        # Year boundary wrap: 14 January belongs to December of previous year
        self.assertEqual(dm.date_to_budget_month("14/01/2026"), "2025-12")
        self.assertEqual(dm.date_to_budget_month("01/01/2026"), "2025-12")
        self.assertEqual(dm.date_to_budget_month("15/01/2026"), "2026-01")

        # December 15th belongs to December
        self.assertEqual(dm.date_to_budget_month("15/12/2025"), "2025-12")
        self.assertEqual(dm.date_to_budget_month("31/12/2025"), "2025-12")

    def test_date_formats(self):
        # DD/MM/YYYY
        self.assertEqual(dm.date_to_budget_month("05/03/2026"), "2026-02")
        self.assertEqual(dm.date_to_budget_month("20/03/2026"), "2026-03")

        # YYYY-MM-DD
        self.assertEqual(dm.date_to_budget_month("2026-03-05"), "2026-02")
        self.assertEqual(dm.date_to_budget_month("2026-03-20"), "2026-03")

        # datetime and date objects
        self.assertEqual(dm.date_to_budget_month(date(2026, 3, 5)), "2026-02")
        self.assertEqual(dm.date_to_budget_month(datetime(2026, 3, 20, 10, 30)), "2026-03")

    def test_get_budget_period_str(self):
        self.assertEqual(dm.get_budget_period_str("2026-04"), "15.04 – 14.05")
        self.assertEqual(dm.get_budget_period_str("2026-12"), "15.12 – 14.01")
        self.assertEqual(dm.get_budget_period_str("2026-01"), "15.01 – 14.02")

    def test_get_budget_month_range(self):
        start, end = dm.get_budget_month_range("2026-04")
        self.assertEqual(start, date(2026, 4, 15))
        self.assertEqual(end, date(2026, 5, 14))

        start_dec, end_dec = dm.get_budget_month_range("2026-12")
        self.assertEqual(start_dec, date(2026, 12, 15))
        self.assertEqual(end_dec, date(2027, 1, 14))

    def test_is_date_in_budget_month(self):
        self.assertTrue(dm.is_date_in_budget_month("15/04/2026", "2026-04"))
        self.assertTrue(dm.is_date_in_budget_month("05/05/2026", "2026-04"))
        self.assertTrue(dm.is_date_in_budget_month("14/05/2026", "2026-04"))
        self.assertFalse(dm.is_date_in_budget_month("14/04/2026", "2026-04"))
        self.assertFalse(dm.is_date_in_budget_month("15/05/2026", "2026-04"))

    def test_expense_totals_in_budget_month(self):
        # Create a mock month structure
        test_month = "2099-04"
        month_data = {
            "month": test_month,
            "categories": [{"id": "daily_life", "name": "Daily Life", "percent": 100, "color": "#C9A86B"}],
            "income_items": [{"id": "inc1", "name": "Salary", "amount": 5000.0, "type": "addition", "category_id": None}],
            "expense_categories": [],
            "expenses": [
                # In period: 15.04.2099 - 14.05.2099
                {"id": "e1", "date": "15/04/2099", "amount": 100.0, "category_id": "daily_life"},
                {"id": "e2", "date": "02/05/2099", "amount": 250.0, "category_id": "daily_life"},
                {"id": "e3", "date": "14/05/2099", "amount": 50.0, "category_id": "daily_life"},
            ]
        }
        total = dm.get_total_expenses(month_data)
        self.assertEqual(total, 400.0)
        spent = dm.get_spent_amount(month_data, "daily_life")
        self.assertEqual(spent, 400.0)
        remaining = dm.get_remaining_amount(month_data, "daily_life")
        self.assertEqual(remaining, 4600.0)

if __name__ == "__main__":
    unittest.main()

