# Reliability Model

## Separation

Probabilistic:

- scope interpretation
- semantic occurrence investigation

Deterministic:

- asset matching
- evidence validation
- action policy
- journaling
- preconditions
- execution
- reconciliation
- verification
- final result

## Key guarantees tested

- no mutation outside validated REMOVE
- no blind retry after unknown outcome
- duplicate trigger / rerun does not duplicate external effects
- partial Trello holds are not rolled back
- failed registry synchronization yields PARTIAL
- inaccessible / ambiguous cases do not reach mutation
- crash/resume converges for minimum critical crash points

## Evaluation

Evaluation covers deterministic rule tests, the minimum safety core, crash convergence, live-model decision evaluation, and a frozen machine-generated eval report.

Actual metrics only come from `eval/report.md`.
