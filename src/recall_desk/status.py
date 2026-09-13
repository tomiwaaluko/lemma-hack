from __future__ import annotations
from recall_desk.domain import FinalResult, Outcome

COUNT_KEYS=("Removed","Held","Preserved","Uncertain","Manual","Other follow-up","Failed")
def count_outcomes(outcomes):
    counts={key:0 for key in COUNT_KEYS}
    mapping={Outcome.REMOVED_VERIFIED:"Removed",Outcome.HELD_VERIFIED:"Held",Outcome.PRESERVED_VERIFIED_UNCHANGED:"Preserved",Outcome.FOLLOWUP_UNCERTAIN:"Uncertain",Outcome.MANUAL_OUTSIDE_CONNECTED:"Manual",Outcome.ACTION_FAILED:"Failed"}
    for outcome in outcomes:
        counts[mapping.get(outcome,"Other follow-up")]+=1
    return counts
def compute_final(outcomes, *, registry_read_failed=False, scope_rejected=False, registry_sync_failed=False, content_writes_occurred=False):
    if registry_read_failed or scope_rejected: return FinalResult.FAILED_SAFE
    if registry_sync_failed or Outcome.ACTION_FAILED in outcomes: return FinalResult.PARTIAL
    if any(o not in {Outcome.REMOVED_VERIFIED,Outcome.HELD_VERIFIED,Outcome.PRESERVED_VERIFIED_UNCHANGED} for o in outcomes): return FinalResult.NEEDS_FOLLOW_UP
    return FinalResult.COMPLETE
