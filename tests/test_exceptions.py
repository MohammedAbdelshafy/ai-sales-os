"""Exception detection tests: stale + missing fields land in exceptions.md."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from ai_sales_os.icp import validate
from ai_sales_os.qualify import evaluate_row
from ai_sales_os.report import write_exceptions

RUN = date(2026, 10, 6)
CFG = validate({
    "min_value": 500,
    "max_value": 5000,
    "allowed_stages": ["new", "contacted"],
    "required_fields": ["contact", "owner"],
    "excluded_domains": [],
    "stale_after_days": 21,
})


def ev(row, row_number):
    e = evaluate_row(row, CFG, RUN)
    e["row_number"] = row_number
    return e


ROWS = [
    {"id": "e-1", "company": "Fresh Co", "contact": "a@x.com", "stage": "new",
     "value": "900", "last_touch_date": "2026-10-01", "owner": "sam"},  # clean
    {"id": "e-2", "company": "Stale Co", "contact": "b@x.com", "stage": "contacted",
     "value": "900", "last_touch_date": "2026-08-01", "owner": "sam"},  # stale
    {"id": "e-3", "company": "Thin Co", "contact": "", "stage": "new",
     "value": "900", "last_touch_date": "2026-10-01", "owner": ""},  # missing
    {"id": "e-4", "company": "Rich Co", "contact": "d@x.com", "stage": "new",
     "value": "50000", "last_touch_date": "2026-10-01", "owner": "sam"},  # band
    {"id": "e-5", "company": "Quiet Co", "contact": "e@x.com", "stage": "contacted",
     "value": "900", "last_touch_date": "", "owner": "sam",
     "suppressed": "yes"},  # suppressed
]


class TestExceptions(unittest.TestCase):
    def setUp(self):
        self.evaluated = [ev(r, i + 1) for i, r in enumerate(ROWS)]
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "exceptions.md"
        write_exceptions(self.path, self.evaluated, CFG)
        self.text = self.path.read_text(encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_record_in_no_section(self):
        for section in self.text.split("## ")[1:]:
            self.assertNotIn("e-1", section.split("\n\n")[1])

    def test_stale_record_in_stale_section(self):
        stale = self.text.split("## 2. Stale deals")[1].split("## 3.")[0]
        self.assertIn("e-2", stale)
        self.assertIn("66 days ago", stale)

    def test_missing_fields_record_in_missing_section(self):
        missing = self.text.split("## 1. Missing required data")[1].split("## 2.")[0]
        self.assertIn("e-3", missing)
        self.assertIn("contact", missing)
        self.assertIn("owner", missing)

    def test_out_of_band_record_in_band_section(self):
        band = self.text.split("## 3. Value outside ICP band")[1].split("## 4.")[0]
        self.assertIn("e-4", band)

    def test_suppressed_record_in_suppressed_section(self):
        supp = self.text.split("## 4. Suppressed or excluded")[1]
        self.assertIn("e-5", supp)

    def test_suppressed_not_double_counted_as_stale(self):
        stale = self.text.split("## 2. Stale deals")[1].split("## 3.")[0]
        self.assertNotIn("e-5", stale)

    def test_sections_appear_in_fixed_order(self):
        idx = [self.text.index(f"## {i}.") for i in (1, 2, 3, 4)]
        self.assertEqual(idx, sorted(idx))

    def test_source_row_numbers_present(self):
        self.assertIn("source row 2", self.text)
        self.assertIn("source row 5", self.text)


if __name__ == "__main__":
    unittest.main()
