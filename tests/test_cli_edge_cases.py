"""CLI edge-case tests: clean errors, no tracebacks, sensible exit codes."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ai_sales_os.cli import main

HERE = Path(__file__).resolve().parent.parent
SAMPLE_OPPS = HERE / "samples" / "opportunities.csv"
SAMPLE_ICP = HERE / "samples" / "icp.yaml"


def run_cli(argv):
    """Run main(argv), capturing stdout/stderr. Returns (exit_code, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCliEdgeCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def test_invalid_run_date_exits_2_without_creating_out_dir(self):
        code, _out, err = run_cli([
            "qualify", "--opps", str(SAMPLE_OPPS), "--icp", str(SAMPLE_ICP),
            "--out", str(self.out_dir), "--run-date", "2026-13-99",
        ])
        self.assertEqual(code, 2)
        self.assertIn("YYYY-MM-DD", err)
        self.assertNotIn("Traceback", err)
        self.assertFalse(self.out_dir.exists(),
                         "a bad --run-date must not leave an output dir behind")

    def test_out_pointing_at_file_exits_2_with_clean_error(self):
        blocker = Path(self.tmp.name) / "blocker"
        blocker.write_text("i am a file, not a directory")
        code, _out, err = run_cli([
            "qualify", "--opps", str(SAMPLE_OPPS), "--icp", str(SAMPLE_ICP),
            "--out", str(blocker), "--run-date", "2026-10-06",
        ])
        self.assertEqual(code, 2)
        self.assertIn("cannot create output directory", err)
        self.assertNotIn("Traceback", err)

    def test_missing_opps_file_exits_2(self):
        code, _out, err = run_cli([
            "qualify", "--opps", str(Path(self.tmp.name) / "nope.csv"),
            "--icp", str(SAMPLE_ICP), "--out", str(self.out_dir),
            "--run-date", "2026-10-06",
        ])
        self.assertEqual(code, 2)
        self.assertIn("cannot read opportunities", err)
        self.assertNotIn("Traceback", err)

    def test_missing_icp_file_exits_2(self):
        code, _out, err = run_cli([
            "qualify", "--opps", str(SAMPLE_OPPS),
            "--icp", str(Path(self.tmp.name) / "nope.yaml"),
            "--out", str(self.out_dir), "--run-date", "2026-10-06",
        ])
        self.assertEqual(code, 2)
        self.assertIn("cannot load ICP config", err)

    def test_empty_csv_header_only_succeeds_with_zero_rows(self):
        empty = Path(self.tmp.name) / "empty.csv"
        empty.write_text("id,company,contact,stage,value,last_touch_date,owner,source,suppressed\n")
        code, out, err = run_cli([
            "qualify", "--opps", str(empty), "--icp", str(SAMPLE_ICP),
            "--out", str(self.out_dir), "--run-date", "2026-10-06",
        ])
        self.assertEqual(code, 0)
        self.assertIn("evaluated 0 rows, 0 qualified", out)
        self.assertTrue((self.out_dir / "qualified.json").exists())
        self.assertTrue((self.out_dir / "exceptions.md").exists())

    def test_qualify_help_shows_example_and_exit_codes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["qualify", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("ai-sales-os qualify", out.getvalue())
        self.assertIn("Exit codes", out.getvalue())

    def test_sample_run_still_reports_expected_result(self):
        code, out, _err = run_cli([
            "qualify", "--opps", str(SAMPLE_OPPS), "--icp", str(SAMPLE_ICP),
            "--out", str(self.out_dir), "--run-date", "2026-10-06",
        ])
        self.assertEqual(code, 0)
        self.assertIn("evaluated 7 rows, 1 qualified", out)


if __name__ == "__main__":
    unittest.main()
