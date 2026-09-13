# Recall Desk Hackathon Truth

## Product

Recall Desk handles scoped changes to media permissions.

Demo: Amara asks Riverbend Youth Makerspace to stop using her photo for volunteer recruitment while explicitly keeping the 2024 Spring Workshop Recap.

Expected main-demo outcomes:

- N1 → REMOVE
- N2 → PRESERVE
- N3 → PRESERVE
- T1 → REMOVE / Held in Rights Hold
- T2 → UNCERTAIN
- external printed flyer → Manual
- final result → NEEDS_FOLLOW_UP

## Systems

Airtable: what the organization is allowed to do.

Notion: what is live.

Trello: what is planned.

## Architecture

The model:

- interprets approved scope
- investigates occurrence purpose
- outputs REMOVE / PRESERVE / UNCERTAIN
- has read-only investigation tools

Code:

- validates evidence
- maps verdicts to allowed actions
- journals before sending
- executes writes
- reconciles unknown outcomes by reading
- verifies independently
- computes final status

## Non-negotiable safety rules

- Human approves ScopeSpec once before content mutation.
- No model mutation tools.
- No content mutation outside validated REMOVE.
- UNCERTAIN never grants write authority.
- SENT must be durable before external write.
- Unknown outcomes are reconciled by reading before retry.
- No blind retries.
- Maximum one re-evaluation after drift.
- reset + check-fixtures before every live take.
- independent verifier does not trust executor journal state.

## Build order

M0 → M1 → M2 → M3 → presentation → video → submission

For details, see the [final implementation plan](docs/superpowers/plans/2026-09-13-recall-desk-implementation.md).
