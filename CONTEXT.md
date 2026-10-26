---
type: repository
status: active
owner_repo: MohammedAbdelshafy/ai-sales-os
product_name: Sales Follow-Up Workspace
source_of_truth: https://github.com/MohammedAbdelshafy/ai-sales-os
---

# Sales Follow-Up Workspace CONTEXT

One job: help a person decide which opportunity needs attention next and why.

## Inputs
- Usage and fields: [README](README.md)
- Implementation: [ai_sales_os](ai_sales_os/)
- Tests: [tests](tests/)

## Process
1. Read approved opportunity rows and the declared qualification rules.
2. Keep source file and row provenance.
3. Show which rules passed or failed and what evidence supports the result.
4. Create next actions and deadlines from the inputs.
5. Report missing, stale, future-dated, excluded and suppressed records.
6. Leave messages as drafts for human review.

## Output
A qualification queue, next-action list and exception report.

## Check
Run the tests and the deterministic sample. Ensure the same inputs and run date produce the same core outputs. Do not send outreach automatically or call a score a verified conversion.
