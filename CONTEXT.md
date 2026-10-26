---
type: repository
status: active
owner_repo: MohammedAbdelshafy/ai-sales-os
product_name: Sales Follow-Up Workspace
source_of_truth: https://github.com/MohammedAbdelshafy/ai-sales-os
---

# Sales Follow-Up Workspace CONTEXT

One job: turn approved opportunity records into a ranked work queue and make the next action clear.

## Inputs
- Usage and criteria: [README](README.md)
- Implementation: [ai_sales_os](ai_sales_os/)
- Tests: [tests](tests/)
- Example inputs: [samples](samples/)

## Process
1. Read the supplied opportunities file and declared qualification rules.
2. Keep source, row, owner, stage, timestamps and suppression state visible.
3. Qualify only against provided criteria and available evidence.
4. Produce next actions and deadlines from the documented rules.
5. Flag missing, stale, suppressed or ambiguous records for review.
6. Prepare follow-up assets but never send them.

## Output
A qualification queue, next-action list and manager exceptions report.

## Check
Run the test suite. Verify that future-dated records, suppression, missing fields and unclear cases are handled as documented. Do not equate a score with a guaranteed sale.
