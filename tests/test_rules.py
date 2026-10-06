"""ICP pass/fail rule tests."""

import unittest
from datetime import date

from ai_sales_os.qualify import evaluate_row

RUN = date(2026, 10, 6)

CFG = {
    "min_value": 500,
    "max_value": 5000,
    "allowed_stages": ["new", "contacted", "qualified", "negotiating"],
    "required_fields": ["contact", "owner"],
    "excluded_domains": ["spamdomain.example"],
    "stale_after_days": 21,
    "suppressed_values": ["true", "1", "yes"],
}

GOOD_ROW = {
    "id": "t-1",
    "company": "Test Co",
    "contact": "amy@testco.com",
    "stage": "contacted",
    "value": "1200",
    "last_touch_date": "2026-10-01",
    "owner": "sam",
    "source": "referral",
    "suppressed": "",
}


def rule(ev, name):
    return next(r for r in ev["rules"] if r["rule"] == name)


class TestRules(unittest.TestCase):
    def test_all_pass_qualifies(self):
        ev = evaluate_row(GOOD_ROW, CFG, RUN)
        self.assertTrue(ev["qualified"])
        self.assertEqual(ev["score"], 1.0)
        self.assertTrue(all(r["passed"] for r in ev["rules"]))

    def test_missing_required_field_fails(self):
        row = dict(GOOD_ROW, contact="")
        ev = evaluate_row(row, CFG, RUN)
        r = rule(ev, "required_fields")
        self.assertFalse(r["passed"])
        self.assertIn("contact", r["evidence"])
        self.assertFalse(ev["qualified"])

    def test_value_below_min_fails(self):
        ev = evaluate_row(dict(GOOD_ROW, value="100"), CFG, RUN)
        r = rule(ev, "value_band")
        self.assertFalse(r["passed"])
        self.assertIn("outside band", r["evidence"])

    def test_value_above_max_fails(self):
        ev = evaluate_row(dict(GOOD_ROW, value="99999"), CFG, RUN)
        self.assertFalse(rule(ev, "value_band")["passed"])

    def test_value_with_currency_symbols_parses(self):
        ev = evaluate_row(dict(GOOD_ROW, value="$1,250.00"), CFG, RUN)
        self.assertEqual(ev["value_parsed"], 1250.0)
        self.assertTrue(rule(ev, "value_band")["passed"])

    def test_non_numeric_value_fails_closed(self):
        ev = evaluate_row(dict(GOOD_ROW, value="lots"), CFG, RUN)
        r = rule(ev, "value_band")
        self.assertFalse(r["passed"])
        self.assertIsNone(ev["value_parsed"])

    def test_disallowed_stage_fails(self):
        ev = evaluate_row(dict(GOOD_ROW, stage="closed_won"), CFG, RUN)
        r = rule(ev, "stage_allowed")
        self.assertFalse(r["passed"])
        self.assertIn("closed_won", r["evidence"])

    def test_excluded_domain_fails(self):
        ev = evaluate_row(dict(GOOD_ROW, contact="x@spamdomain.example"), CFG, RUN)
        r = rule(ev, "domain_allowed")
        self.assertFalse(r["passed"])
        self.assertIn("spamdomain.example", r["evidence"])

    def test_non_email_contact_domain_rule_passes(self):
        ev = evaluate_row(dict(GOOD_ROW, contact="+15551234567"), CFG, RUN)
        self.assertTrue(rule(ev, "domain_allowed")["passed"])

    def test_stale_date_fails_freshness(self):
        ev = evaluate_row(dict(GOOD_ROW, last_touch_date="2026-08-01"), CFG, RUN)
        r = rule(ev, "freshness")
        self.assertFalse(r["passed"])
        self.assertEqual(ev["days_since_last_touch"], 66)

    def test_fresh_date_passes(self):
        ev = evaluate_row(dict(GOOD_ROW, last_touch_date="2026-10-05"), CFG, RUN)
        self.assertTrue(rule(ev, "freshness")["passed"])
        self.assertEqual(ev["days_since_last_touch"], 1)

    def test_missing_date_fails_closed(self):
        ev = evaluate_row(dict(GOOD_ROW, last_touch_date=""), CFG, RUN)
        r = rule(ev, "freshness")
        self.assertFalse(r["passed"])
        self.assertIsNone(ev["days_since_last_touch"])

    def test_suppressed_row_never_qualifies(self):
        row = dict(GOOD_ROW, suppressed="true")
        ev = evaluate_row(row, CFG, RUN)
        self.assertTrue(ev["suppressed"])
        self.assertFalse(ev["qualified"])

    def test_score_reflects_partial_passes(self):
        row = dict(GOOD_ROW, contact="", value="1")  # 2 rules fail
        ev = evaluate_row(row, CFG, RUN)
        self.assertEqual(ev["passed"], 3)
        self.assertAlmostEqual(ev["score"], 0.6)


if __name__ == "__main__":
    unittest.main()
