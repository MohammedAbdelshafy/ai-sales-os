"""Next-action recommender: deterministic action + deadline per opportunity.

Deadlines are derived from (stage, days-since-last-touch, run_date) only —
never from "today at runtime", so re-runs with the same inputs are identical.
Actions are recommendations for a human; nothing is auto-sent.
"""

from __future__ import annotations

from datetime import date, timedelta

# Stage -> (default action, default deadline offset in days)
STAGE_PLAYBOOK = {
    "new": ("Initial outreach", 1),
    "contacted": ("Follow-up touch", 3),
    "qualified": ("Book discovery call / send proposal", 5),
    "negotiating": ("Negotiation check-in", 7),
    "closed_won": ("Hand off to onboarding", 3),
    "closed_lost": ("Log loss reason; schedule re-nurture review", 30),
}


def recommend(evidence: dict, cfg: dict, run_date: date) -> dict:
    """Build the next-action record for one evaluated opportunity."""
    opp_id = (evidence["row"].get("id") or "").strip() or f"row-{evidence.get('row_number')}"
    stage = (evidence["row"].get("stage") or "").strip()
    days = evidence["days_since_last_touch"]
    stale_limit = cfg["stale_after_days"]

    if evidence["suppressed"]:
        return _rec(opp_id, "No action — suppressed/excluded",
                    None,
                    f"record suppressed ({evidence['suppression_evidence']}); "
                    "leave untouched")
    if not evidence["rules"][0]["passed"]:
        deadline = run_date + timedelta(days=3)
        return _rec(opp_id, "Collect missing data", deadline,
                    evidence["rules"][0]["evidence"])
    if days is not None and days > stale_limit:
        deadline = run_date + timedelta(days=2)
        return _rec(opp_id, "Re-engage or close", deadline,
                    f"deal stale: last touch {days} days ago "
                    f"(threshold {stale_limit})")

    action, offset = STAGE_PLAYBOOK.get(
        stage, ("Review and assign next step", 7))
    deadline = run_date + timedelta(days=offset)
    days_str = "unknown" if days is None else str(days)
    reason = (f"stage={stage!r}; last touch {days_str} days ago; "
              f"playbook action '{action}' due in {offset} days")
    return _rec(opp_id, action, deadline, reason)


def _rec(opp_id, action, deadline, reason):
    return {
        "id": opp_id,
        "action": action,
        "deadline": deadline.isoformat() if deadline else "",
        "reason": reason,
    }
