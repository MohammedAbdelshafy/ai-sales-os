# ai-sales-os

A command-line tool that turns an approved opportunities CSV into an
evidence-backed qualification queue: per-row ICP pass/fail evidence, a
next-action list with deterministic deadlines, and a manager exception report.

It implements the AI Sales OS workflow: ingest approved records, preserve
provenance (source file, row number), owner, stage, timestamps and suppression
state, qualify only against a declared ICP and available evidence, recommend
next actions with deadlines, and escalate ambiguous cases. It never auto-sends
outreach; follow-up assets are prepared for human review.

## Install

Requires Python 3.9+ (stdlib only, no dependencies).

```bash
git clone https://github.com/MohammedAbdelshafy/ai-sales-os.git
cd ai-sales-os
```

## Usage

```bash
python3 -m ai_sales_os qualify \
  --opps samples/opportunities.csv \
  --icp samples/icp.yaml \
  --out ./out \
  --run-date 2026-10-06
```

Expected result with the sample data: `evaluated 7 rows, 1 qualified -> ./out`

Exit codes: `0` = success; `2` = input or usage error (missing file, bad
`--run-date`, unreadable config, unwritable output directory). Error details
go to stderr; no traceback is printed for these expected failures.

## Inputs

- `opportunities.csv` — one row per opportunity. Recognized columns: `id`,
  `company`, `contact`, `stage`, `value`, `last_touch_date`, `owner`, `source`,
  `suppressed`. Unknown columns are ignored; missing recognized columns are
  treated as blank.
- ICP config (`icp.yaml` or JSON):
  - `min_value` / `max_value` — deal-size band (numbers)
  - `allowed_stages` — list of stage names considered workable
  - `required_fields` — list of columns that must be non-empty
  - `excluded_domains` — email domains that are never worked
  - `stale_after_days` — deals older than this since last touch are stale
  - `suppressed_values` (optional) — strings treated as "suppressed" in the
    `suppressed` column

## Outputs (in `--out`)

- `next_actions.csv` — `id, action, deadline, reason`. Deadlines derive from
  (stage, days-since-last-touch, `--run-date`) only.
- `exceptions.md` — manager report: missing required data, stale or
  future-dated deals, value outside the ICP band, suppressed/excluded
  records. A `last_touch_date` in the future fails the freshness rule and is
  listed here (it is not treated as stale).
- `qualified.json` — full per-row evidence: each rule's pass/fail + evidence,
  score, and provenance (source file, row number, ICP file used).
- `run_meta.json` — run id, run date, run timestamp, input file checksums.

## Determinism / idempotency

Re-running with the same inputs and the same `--run-date` produces
byte-identical `next_actions.csv`, `exceptions.md` and `qualified.json`.
Timestamps and random run ids go only into `run_meta.json`. Omit
`--run-date` to default to today's date.

## Tests

```bash
python3 -m unittest discover -s tests
```

Covers: ICP pass/fail rules, deadline computation, exception detection
(stale + missing fields), and idempotency (two runs → identical outputs).

## Limits

- Reads CSV and YAML/JSON from local files only; it does not connect to any
  CRM. Updating CRM records is deliberately out of scope — export the CSVs
  and re-import after human review.
- The built-in YAML parser supports only simple mappings, nested mappings
  and lists; complex YAML features are rejected — use JSON in that case.
- Value parsing handles plain numbers and `$1,250.00`-style amounts; dates
  accept `YYYY-MM-DD` plus a few common variants. Unparseable values fail
  closed with evidence rather than being guessed.
- Recommendations are for a human to review. The tool never sends email,
  messages, or calls.

## License

MIT — see [LICENSE](LICENSE).
