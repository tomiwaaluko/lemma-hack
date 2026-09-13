# Runtime Contract

## Verdicts

REMOVE

PRESERVE

UNCERTAIN

## Final results

FAILED_SAFE

PARTIAL

NEEDS_FOLLOW_UP

COMPLETE

## Execution states

RUNNING

INTERRUPTED

FINISHED

## Runtime application boundaries

Runtime ports:

- Notion runtime reads + archive
- Trello runtime reads + move / label / comment
- Airtable registry reads/writes

DemoResetPort:

- restoration only
- must never be provided to normal runtime execution

## Model/code boundary

Model answers: “What does this occurrence mean under the approved scope?”

Code answers: “What are we permitted to do about it?”

## Write invariant

No content write may target an occurrence outside the validated REMOVE set.

## Idempotency

Stable operation IDs.

Trello markers:

```
[recall-desk {request_id} {run_id} {op_id}]
```

Unknown external-write result:

```
UNKNOWN
→ read target state
→ VERIFIED if effect exists
→ retry only if effect is absent and retry remains safe
```
