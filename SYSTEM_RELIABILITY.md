# Recall Desk — system and reliability brief

Recall Desk enforces one approved, scoped media-permission change across Airtable, Notion, and Trello. The model investigates what a use *means*. Code decides what is permitted, records writes, and verifies outcomes.

This brief describes the reliability model. It does not report eval numbers. Measured results, when frozen, come only from `eval/report.md`.

## Architecture

Eight phases, with a hard split:

1. **Code** loads the request, asset, variants, and occurrence registry from Airtable. A failed registry read is `FAILED_SAFE` and writes nothing.
2. **Model + person** turn the request into a scope. A person approves the scope once. They do not approve individual mutations.
3. **Code** discovers coverage by matching registered identifiers, then buckets each occurrence (candidate, already removed, inaccessible, external, ambiguous).
4. **Model** investigates candidates with read-only tools and submits `REMOVE`, `PRESERVE`, or `UNCERTAIN`.
5. **Code** validates evidence. Rules only move a decision toward `UNCERTAIN`. They never upgrade a verdict into `REMOVE` or `PRESERVE`.
6. **Code** maps verdicts to actions and rejects any content-mutation plan that targets an occurrence outside the validated `REMOVE` set.
7. **Code** journals, executes, reconciles, and verifies.
8. **Code** computes the final result (`FAILED_SAFE`, `PARTIAL`, `NEEDS_FOLLOW_UP`, `COMPLETE`) from verified outcomes and run-level flags. The model cannot write that result.

DemoReset restoration is a separate port. It is not given to normal runtime execution.

## Exact identifier matching

Each variant is registered by **canonical URL** and **filename**.

- Exact canonical URL is a match.
- Exact filename is a match only if that filename maps to exactly one registered variant.
- Anything else is not a match.
- Ambiguous identifiers are not sent to the model, are not mutated, and become manual follow-up.

There is no visual recognition, face matching, perceptual hashing, or fuzzy matching. The model reasons about purpose, not asset identity.

## Bounded model investigation

The model receives the approved scope, a fixed purpose list, and a starter evidence packet. It does not receive prior registry verdicts. It has no write tools.

Investigation is budgeted (at most three read-tool calls, then only `submit_decision`). Page and card text is treated as untrusted data. If no valid decision is submitted, the verdict is `UNCERTAIN`.

## Deterministic enforcement

Policy, not the model, chooses the action:

| Verdict | Notion | Trello (planned) |
| --- | --- | --- |
| `REMOVE` | Archive the image block | Hold: move, label, same-request comment |
| `PRESERVE` | No content write; verify unchanged | No content write; verify unchanged |
| `UNCERTAIN` | No content write | No content write |

A Trello card already in Rights Hold is attributed by the same-request marker. Recall Desk does not take credit for a hold it cannot attribute to this request.

## SENT-before-write journal

Every external content write has a stable operation ID. The journal commits `SENT` **before** the HTTP call. On interrupt or resume, `SENT` and `UNKNOWN` are reconciled by reading the live object. They are not blindly resent.

## Unknown outcome reconciliation

If the write's acknowledgment is dropped, timed out, or otherwise unknown:

1. mark `UNKNOWN`
2. read the target
3. if the intended effect is present → `VERIFIED`
4. retry only if the effect is absent and a retry is still safe

That is the opposite of "the call might have worked, send it again."

## Trello composite hold and idempotency

A hold is three writes: move to Rights Hold, add the Rights hold label, add a comment containing `[recall-desk {request_id} {run_id} {op_id}]`.

- A hold is `Held – verified` only when all three are present.
- If a later step fails (for example the label call), the card is not rolled back out of Rights Hold. The occurrence is `Action failed` / `PARTIAL`.
- A later run that sees the same-request marker does not duplicate the hold.

## Fail-safe UNCERTAIN

`UNCERTAIN` is intended safety behavior. Missing or conflicting evidence — including an undecided purpose — yields no content mutation. The report keeps the location, the evidence that was found, and what was missing or contradictory.

The only registry write for that item is bookkeeping. Archiving a Notion block or holding a Trello card is a content mutation and is not allowed.

Any unresolved occurrence, including `UNCERTAIN` and uses outside connected systems, makes the run `NEEDS_FOLLOW_UP`. That is distinct from `PARTIAL` (an action failed or could not be confirmed).

## Connected-system coverage boundary

Coverage is:

- Airtable registry rows for the asset
- connected Notion pages
- the connected Trello board

Registered Notion blocks are also read by known block ID, so an archived block is not missed just because page-child enumeration no longer lists it.

Everything else is listed, not guessed. The printed flyer in the demo is `Manual – outside connected systems`. Mentions of a person's name in text are out of scope. Instagram, email, caches, and already-sent copies are out of scope.

## Honesty

Do not paste metrics into this document. If judges need numbers, show the frozen `eval/report.md` for a specific commit, generated by `recall_desk.evals.report.write_report`.
