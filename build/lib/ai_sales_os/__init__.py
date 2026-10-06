"""ai-sales-os: evidence-backed sales opportunity qualifier.

Ingests approved opportunity records (CSV), qualifies them against a declared
ICP config (YAML or JSON) with per-rule pass/fail evidence, recommends next
actions with deterministic deadlines, and produces a manager exception report.

Never auto-sends anything; ambiguous or sensitive cases go to exceptions.md.
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
