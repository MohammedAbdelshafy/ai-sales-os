"""Deadline computation tests: deterministic, stage + days-since-touch driven."""

import unittest
from datetime import date

from ai_sales_os.actions import recommend

RUN = date(2026, 10, 6)
CFG = {
    "min_value": 0,
    "max_value": float("inf"),
    "allowed_stages": [],
    "required_fields": [],
    "excluded_domains": [],
    "stale_after_days": 21,
    "suppressed_values": ["true", "1", "yes"],
}

RULES_PASS = [
    {"rule": "required_fields", "passed": True, "evidence": ""},
    {"rule": "value_band", "passed": True, "evidence": ""},
    {"rule": "stage_allowed", "passed": True, "evidence": ""},
    {"rule": "domain_allowed", "passed": True, "evidence": ""},
    {"rule": "freshness", "passed": True, "evidence": ""},
]


def ev_for(stage, days, suppressed=False, missing_field=False):
    rules = [dict(r) for r in RULES_PASS]
    if missing_field:
        rules[0] = {"rule": "required_fields", "passed": False,
                    "evidence": "missing required fields: owner"}
    return {
        "row": {"id": "d-1", "stage": stage},
        "row_number": 1,
        "rules": rules,
        "suppressed": suppressed,
        "suppression_evidence": "suppressed flag set to 'true'",
        "days_since_last_touch": days,
    }


class TestDeadlines(unittest.TestCase):
    def test_new_stage_deadline_next_day(self):
        rec = recommend(ev_for("new", 0), CFG, RUN)
        self.assertEqual(rec["deadline"], "2026-10-07")
        self.assertEqual(rec["action"], "Initial outreach")

    def test_contacted_stage_deadline_three_days(self):
        rec = recommend(ev_for("contacted", 5), CFG, RUN)
        self.assertEqual(rec["deadline"], "2026-10-09")

    def test_qualified_stage_deadline_five_days(self):
        rec = recommend(ev_for("qualified", 5), CFG, RUN)
        self.assertEqual(rec["deadline"], "2026-10-11")

    def test_negotiating_stage_deadline_seven_days(self):
        rec = recommend(ev_for("negotiating", 5), CFG, RUN)
        self.assertEqual(rec["deadline"], "2026-10-13")

    def test_stale_overrides_stage_playbook(self):
        rec = recommend(ev_for("contacted", 30), CFG, RUN)
        self.assertEqual(rec["action"], "Re-engage or close")
        self.assertEqual(rec["deadline"], "2026-10-08")
        self.assertIn("30 days ago", rec["reason"])

    def test_stale_boundary_not_stale(self):
        # exactly at the threshold is still fresh
        rec = recommend(ev_for("contacted", 21), CFG, RUN)
        self.assertEqual(rec["action"], "Follow-up touch")
        self.assertEqual(rec["deadline"], "2026-10-09")

    def test_missing_data_gets_collection_action(self):
        rec = recommend(ev_for("new", None, missing_field=True), CFG, RUN)
        self.assertEqual(rec["action"], "Collect missing data")
        self.assertEqual(rec["deadline"], "2026-10-09")

    def test_suppressed_gets_no_deadline(self):
        rec = recommend(ev_for("contacted", 5, suppressed=True), CFG, RUN)
        self.assertEqual(rec["deadline"], "")
        self.assertIn("No action", rec["action"])

    def test_deadlines_derive_from_run_date_not_today(self):
        other = date(2025, 1, 15)
        rec = recommend(ev_for("new", 0), CFG, other)
        self.assertEqual(rec["deadline"], "2025-01-16")

    def test_unknown_stage_gets_review_action(self):
        rec = recommend(ev_for("mystery", 3), CFG, RUN)
        self.assertEqual(rec["deadline"], "2026-10-13")


if __name__ == "__main__":
    unittest.main()
