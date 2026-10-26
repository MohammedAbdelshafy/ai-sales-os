---
type: repository
status: active
owner_repo: MohammedAbdelshafy/ai-sales-os
product_name: Sales Follow-Up Workspace
source_of_truth: https://github.com/MohammedAbdelshafy/ai-sales-os
---

# Sales Follow-Up Workspace CONTEXT

One job: help a sales team see which supplied opportunities deserve attention and what the next action should be.

## Inputs
- Commands and limitations: [README](README.md)
- Implementation: [ai_sales_os](ai_sales_os/)
- Tests: [tests](tests/)
- Samples: [samples](samples/)

## Process
1. Read the approved opportunity records and declared qualification criteria.
2. Preserve source details, owner, stage, timestamps and suppression state.
3. Apply only the stated rules and the available evidence.
4. Produce next actions with clear reasons/deadlines.
5. Flag missing, stale, excluded or ambiguous rows for human review.
6. Prepare follow-up material; do not send it automatically.

## Output
A qualification queue, next-action list and exception report.

## Check
Run the repository tests and verify that suppressed/excluded records stay out of work queues, reasons remain traceable, and no external communication is sent.
