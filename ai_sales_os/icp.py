"""ICP (ideal customer profile) config loading and validation.

Accepts YAML (parsed with the stdlib-only yaml_lite subset) or JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from .yaml_lite import load as yaml_load

DEFAULTS = {
    "min_value": 0.0,
    "max_value": float("inf"),
    "allowed_stages": [],
    "required_fields": [],
    "excluded_domains": [],
    "stale_after_days": 30,
    "suppressed_values": ["true", "1", "yes"],
}


def load_config(path: str | Path) -> dict:
    """Load and normalize an ICP config file (YAML or JSON)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"ICP config not found: {p}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        raw = json.loads(text)
    elif suffix in (".yaml", ".yml"):
        raw = yaml_load(text)
    else:
        # try JSON first, fall back to YAML subset
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            raw = yaml_load(text)
    if not isinstance(raw, dict):
        raise ValueError("ICP config must be a mapping")
    return validate(raw)


def validate(raw: dict) -> dict:
    cfg = dict(DEFAULTS)
    cfg.update(raw)

    if not isinstance(cfg["min_value"], (int, float)):
        raise ValueError("icp.min_value must be numeric")
    if not isinstance(cfg["max_value"], (int, float)):
        raise ValueError("icp.max_value must be numeric")
    if cfg["min_value"] > cfg["max_value"]:
        raise ValueError("icp.min_value must be <= icp.max_value")
    if not isinstance(cfg["stale_after_days"], int) or cfg["stale_after_days"] < 0:
        raise ValueError("icp.stale_after_days must be a non-negative integer")

    for key in ("allowed_stages", "required_fields", "excluded_domains",
               "suppressed_values"):
        val = cfg[key]
        if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
            raise ValueError(f"icp.{key} must be a list of strings")
        cfg[key] = [v.strip() for v in val]

    cfg["excluded_domains"] = [d.lower() for d in cfg["excluded_domains"]]
    return cfg
