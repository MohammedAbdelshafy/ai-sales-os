"""Qualification engine: score each opportunity against the ICP.

Every rule emits pass/fail plus the exact evidence that produced it.
Nothing is inferred: missing or unparsable data fails closed with evidence.
"""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import date, datetime
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+)$")


def parse_value(raw: str | None):
    """Parse a money value like '$1,250.00' or '1250'. Returns (number, evidence)."""
    if raw is None:
        return None, "value is missing"
    text = raw.strip().replace(",", "")
    text = text.lstrip("$").strip()
    if text == "":
        return None, "value is empty"
    try:
        return float(text), f"value parsed as {float(text):g}"
    except ValueError:
        return None, f"value {raw!r} is not a number"


def parse_date(raw: str | None):
    """Parse a date string. Returns (date | None, evidence)."""
    if raw is None or raw.strip() == "":
        return None, "last_touch_date is missing"
    text = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).date(), f"last_touch_date parsed as {text}"
        except ValueError:
            continue
    return None, f"last_touch_date {raw!r} is not a recognized date"


def extract_domain(contact: str | None):
    """Extract an email domain from a contact field; None if not an email."""
    if not contact:
        return None
    m = EMAIL_RE.match(contact.strip())
    if not m:
        return None
    return m.group(1).lower()


def is_suppressed(row: dict, cfg: dict) -> tuple[bool, str]:
    raw = (row.get("suppressed") or "").strip().lower()
    if raw and raw in [v.lower() for v in cfg["suppressed_values"]]:
        return True, f"suppressed flag set to {row.get('suppressed')!r}"
    return False, "no suppression flag set"


def evaluate_row(row: dict, cfg: dict, run_date: date) -> dict:
    """Evaluate one opportunity row. Returns the evidence record."""
    rules = []

    # Rule 1: required fields present
    missing = [f for f in cfg["required_fields"]
               if not (row.get(f) or "").strip()]
    rules.append({
        "rule": "required_fields",
        "passed": not missing,
        "evidence": ("all required fields present"
                     if not missing
                     else f"missing required fields: {', '.join(missing)}"),
    })

    # Rule 2: value within ICP band
    value, value_ev = parse_value(row.get("value"))
    if value is None:
        value_pass, value_evidence = False, f"unparseable value — {value_ev}"
    elif cfg["min_value"] <= value <= cfg["max_value"]:
        value_pass, value_evidence = True, (
            f"{value_ev}; inside band "
            f"[{cfg['min_value']:g}, {cfg['max_value']:g}]"
        )
    else:
        value_pass, value_evidence = False, (
            f"{value_ev}; outside band "
            f"[{cfg['min_value']:g}, {cfg['max_value']:g}]"
        )
    rules.append({"rule": "value_band", "passed": value_pass,
                  "evidence": value_evidence})

    # Rule 3: stage allowed
    stage = (row.get("stage") or "").strip()
    if cfg["allowed_stages"]:
        stage_pass = stage in cfg["allowed_stages"]
        stage_ev = (f"stage {stage!r} is allowed"
                    if stage_pass
                    else f"stage {stage!r} not in allowed stages "
                         f"{cfg['allowed_stages']}")
    else:
        stage_pass, stage_ev = True, f"no stage restriction configured; stage={stage!r}"
    rules.append({"rule": "stage_allowed", "passed": stage_pass,
                  "evidence": stage_ev})

    # Rule 4: contact domain not excluded
    domain = extract_domain(row.get("contact"))
    if domain is None:
        dom_pass = True
        dom_ev = (f"contact {row.get('contact')!r} is not an email; "
                  "no domain exclusion applies")
    elif domain in cfg["excluded_domains"]:
        dom_pass, dom_ev = False, f"domain {domain!r} is excluded"
    else:
        dom_pass, dom_ev = True, f"domain {domain!r} is not excluded"
    rules.append({"rule": "domain_allowed", "passed": dom_pass,
                  "evidence": dom_ev})

    # Rule 5: freshness
    touch, touch_ev = parse_date(row.get("last_touch_date"))
    if touch is None:
        days = None
        fresh_pass, fresh_ev = False, f"cannot assess freshness — {touch_ev}"
    else:
        days = (run_date - touch).days
        if days < 0:
            fresh_pass, fresh_ev = False, (
                f"last touch {touch.isoformat()} is in the future "
                f"({-days} days ahead of run date)"
            )
        elif days <= cfg["stale_after_days"]:
            fresh_pass, fresh_ev = True, (
                f"last touch {days} days ago "
                f"(<= stale threshold {cfg['stale_after_days']})"
            )
        else:
            fresh_pass, fresh_ev = False, (
                f"last touch {days} days ago "
                f"(> stale threshold {cfg['stale_after_days']})"
            )
    rules.append({"rule": "freshness", "passed": fresh_pass,
                  "evidence": fresh_ev})

    suppressed, supp_ev = is_suppressed(row, cfg)

    passed = sum(1 for r in rules if r["passed"])
    qualified = not suppressed and all(r["passed"] for r in rules)

    return {
        "row": row,
        "rules": rules,
        "passed": passed,
        "total_rules": len(rules),
        "score": round(passed / len(rules), 4) if rules else 0.0,
        "qualified": qualified,
        "suppressed": suppressed,
        "suppression_evidence": supp_ev,
        "value_parsed": value,
        "days_since_last_touch": days,
        "domain": domain,
    }


def read_opportunities(path: str | Path) -> tuple[list[dict], list[dict]]:
    """Read the opportunities CSV.

    Returns (rows, provenance_records). rows keep raw string values;
    provenance_records pair each row with its 1-based data row number.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"opportunities file not found: {p}")
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("opportunities CSV is empty or has no header")
        fieldnames = [h.strip() for h in reader.fieldnames]
        rows = []
        for i, raw in enumerate(reader, start=1):
            row = {(k.strip() if k else ""): (v.strip() if isinstance(v, str) else v)
                   for k, v in raw.items() if k}
            rows.append({"data": row, "row_number": i})
    return rows, fieldnames


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
