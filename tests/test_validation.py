"""Config validation + rule-accessor tests."""

import unittest

from ai_sales_os.icp import validate
from ai_sales_os.qualify import evaluate_row, rule
from datetime import date

RUN = date(2026, 10, 6)
CFG = validate({})


class TestValidation(unittest.TestCase):
    def test_bool_min_value_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            validate({"min_value": True})
        self.assertIn("numeric", str(ctx.exception))

    def test_bool_max_value_rejected(self):
        with self.assertRaises(ValueError):
            validate({"max_value": False})

    def test_bool_stale_after_days_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            validate({"stale_after_days": True})
        self.assertIn("non-negative integer", str(ctx.exception))

    def test_zero_stale_after_days_still_allowed(self):
        cfg = validate({"stale_after_days": 0})
        self.assertEqual(cfg["stale_after_days"], 0)

    def test_int_and_float_values_still_allowed(self):
        cfg = validate({"min_value": 10, "max_value": 99.5})
        self.assertEqual(cfg["min_value"], 10)
        self.assertEqual(cfg["max_value"], 99.5)


class TestRuleAccessor(unittest.TestCase):
    def test_rule_found_by_name(self):
        ev = evaluate_row({"contact": "a@b.com"}, CFG, RUN)
        r = rule(ev, "freshness")
        self.assertEqual(r["rule"], "freshness")

    def test_rule_unknown_name_raises(self):
        ev = evaluate_row({"contact": "a@b.com"}, CFG, RUN)
        with self.assertRaises(KeyError):
            rule(ev, "no_such_rule")


if __name__ == "__main__":
    unittest.main()
