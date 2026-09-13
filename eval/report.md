# Recall Desk eval report

Generated at: 2026-09-13T22:29:06Z
Commit: 65f0f7a00546c299750541128ad16b87630cd84b
Model: claude-sonnet-5
Frozen: yes

## Gate
critical_ok: true
decisive_ok: false
scope_ok: true
rules_ok: true
passed: false

## Decision eval
Critical errors: 0
Decisive coverage (cases): 2/3 definite-gold cases
Decisive coverage (runs): 2/3 definite-gold runs
final_accuracy: 0.6666666666666666
scope_pass: True

| case_id | run_index | raw_verdict | final_verdict | downgrades | critical | correct_definite |
| --- | --- | --- | --- | --- | --- | --- |
| scope:withdrawn_volunteer_recruitment | 0 | PASS | PASS | [] | False |  |
| scope:retained_2024_spring_workshop_recap | 0 | PASS | PASS | [] | False |  |
| N1 | 0 | REMOVE | REMOVE | [] | False | True |
| N2 | 0 | PRESERVE | PRESERVE | [] | False | True |
| N3 | 0 | UNCERTAIN | UNCERTAIN | [] | False | False |
| T2 | 0 | UNCERTAIN | UNCERTAIN | [] | False |  |

## Rules test suite
rules_passed: true

## Faults

## Crash convergence
Not run (eval-only model decision sprint)
Duplicate external effects: 0
