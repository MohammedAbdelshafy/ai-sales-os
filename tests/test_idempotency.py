"""Idempotency: two identical runs produce byte-identical deterministic outputs."""

import tempfile
import unittest
from pathlib import Path

from ai_sales_os.cli import cmd_qualify
from types import SimpleNamespace

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
DETERMINISTIC = ["next_actions.csv", "exceptions.md", "qualified.json"]


def run(out_dir: Path, run_id: str):
    args = SimpleNamespace(
        opps=str(SAMPLES / "opportunities.csv"),
        icp=str(SAMPLES / "icp.yaml"),
        out=str(out_dir),
        run_date="2026-10-06",
        run_id=run_id,
    )
    self_code = cmd_qualify(args)
    return self_code


class TestIdempotency(unittest.TestCase):
    def test_two_runs_identical_outputs(self):
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            out1, out2 = Path(t1), Path(t2)
            self.assertEqual(run(out1, "run-a"), 0)
            self.assertEqual(run(out2, "run-a"), 0)
            for name in DETERMINISTIC:
                a = (out1 / name).read_bytes()
                b = (out2 / name).read_bytes()
                self.assertEqual(a, b, f"{name} differs between runs")

    def test_same_inputs_same_run_id_bytes(self):
        # even the meta file is deterministic apart from run_timestamp
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            run(Path(t1), "fixed-id")
            run(Path(t2), "fixed-id")
            for name in DETERMINISTIC:
                self.assertEqual(
                    (Path(t1) / name).read_bytes(),
                    (Path(t2) / name).read_bytes(),
                )

    def test_run_meta_records_inputs(self):
        import json
        with tempfile.TemporaryDirectory() as t:
            run(Path(t), "meta-check")
            meta = json.loads((Path(t) / "run_meta.json").read_text())
            self.assertEqual(meta["run_id"], "meta-check")
            self.assertEqual(meta["run_date"], "2026-10-06")
            self.assertEqual(meta["rows_evaluated"], 7)
            self.assertIn("opportunities_sha256", meta)


if __name__ == "__main__":
    unittest.main()
