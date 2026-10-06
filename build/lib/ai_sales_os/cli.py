"""Command-line interface for ai-sales-os."""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

from . import __version__
from .actions import recommend
from .icp import load_config
from .qualify import evaluate_row, read_opportunities, sha256_file
from .report import (write_exceptions, write_next_actions, write_qualified,
                     write_run_meta)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="ai-sales-os",
        description="Evidence-backed sales opportunity qualifier: ICP scoring, "
                    "next-action queue with deadlines, manager exception reports.",
    )
    p.add_argument("--version", action="version", version=f"ai-sales-os {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("qualify", help="Qualify opportunities against an ICP config")
    q.add_argument("--opps", required=True, help="opportunities CSV file")
    q.add_argument("--icp", required=True, help="ICP config file (YAML or JSON)")
    q.add_argument("--out", required=True, help="output directory")
    q.add_argument("--run-date", default=None,
                   help="run date YYYY-MM-DD (default: today); deadlines derive from this")
    q.add_argument("--run-id", default=None,
                   help="run id recorded in run_meta.json (default: random uuid)")
    return p.parse_args(argv)


def cmd_qualify(args) -> int:
    opps_path = Path(args.opps)
    icp_path = Path(args.icp)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.run_date:
        try:
            run_date = datetime.strptime(args.run_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"error: --run-date must be YYYY-MM-DD, got {args.run_date!r}",
                  file=sys.stderr)
            return 2
    else:
        run_date = date.today()
    run_id = args.run_id or str(uuid.uuid4())

    try:
        cfg = load_config(icp_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: cannot load ICP config: {exc}", file=sys.stderr)
        return 2
    try:
        rows, _fields = read_opportunities(opps_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: cannot read opportunities: {exc}", file=sys.stderr)
        return 2

    evaluated = []
    for item in rows:
        ev = evaluate_row(item["data"], cfg, run_date)
        ev["row_number"] = item["row_number"]
        evaluated.append(ev)

    actions = [recommend(ev, cfg, run_date) for ev in evaluated]

    provenance = {
        "source_file": opps_path.name,
        "icp_file": icp_path.name,
    }
    write_next_actions(out_dir / "next_actions.csv", actions)
    write_exceptions(out_dir / "exceptions.md", evaluated, cfg)
    write_qualified(out_dir / "qualified.json", evaluated, provenance)
    write_run_meta(
        out_dir / "run_meta.json",
        run_id=run_id,
        run_date=run_date.isoformat(),
        opps_file=opps_path.name,
        icp_file=icp_path.name,
        opps_sha256=sha256_file(opps_path),
        icp_sha256=sha256_file(icp_path),
        row_count=len(evaluated),
        qualified_count=sum(1 for ev in evaluated if ev["qualified"]),
    )

    qualified = sum(1 for ev in evaluated if ev["qualified"])
    print(f"evaluated {len(evaluated)} rows, {qualified} qualified -> {out_dir}")
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.command == "qualify":
        return cmd_qualify(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
