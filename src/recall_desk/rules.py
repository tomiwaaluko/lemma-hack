from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from recall_desk.domain import Citation, Decision, EvidenceItem, Purpose, ScopeBasis, ScopeSpec, ValidatedDecision, Verdict

@dataclass(frozen=True)
class RuleContext:
    occurrence_key:str; container_id:str; evidence:dict[str,EvidenceItem]; scope:ScopeSpec
def normalize_ws(s:str)->str: return " ".join(s.split())
def uncertain_from(ctx, reasons): return Decision(occurrence_key=ctx.occurrence_key,verdict=Verdict.UNCERTAIN,observed_purposes=[],scope_basis=ScopeBasis.NONE,evidence=[],rationale="Downgraded by rules",missing_or_conflicting=list(reasons))
def validate(raw:dict[str,Any],ctx:RuleContext)->ValidatedDecision:
    try: decision=Decision(**raw)
    except Exception: return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=uncertain_from(ctx,["R1: invalid decision shape"]),downgrades=["R1"])
    if decision.occurrence_key!=ctx.occurrence_key: return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=uncertain_from(ctx,["R1: wrong occurrence key"]),downgrades=["R1"])
    for citation in decision.evidence:
        item=ctx.evidence.get(citation.evidence_id)
        if item is None or normalize_ws(citation.quote) not in normalize_ws(item.text): return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=uncertain_from(ctx,["R2: invalid citation"]),downgrades=["R2"])
    withdrawn={x.purpose for x in ctx.scope.withdrawn_purposes}; retained={x.container_ref for x in ctx.scope.retained_content}
    if decision.verdict==Verdict.REMOVE and (decision.scope_basis!=ScopeBasis.WITHDRAWN_PURPOSE or not set(decision.observed_purposes)&withdrawn or not decision.evidence or ctx.container_id in retained):
        reason="R3: REMOVE on retained content" if ctx.container_id in retained else "R3: invalid REMOVE"
        return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=uncertain_from(ctx,[reason]),downgrades=[reason])
    if decision.verdict==Verdict.PRESERVE:
        ok=(decision.scope_basis==ScopeBasis.RETAINED_CONTENT and ctx.container_id in retained) or (decision.scope_basis==ScopeBasis.PURPOSE_NOT_WITHDRAWN and bool(decision.observed_purposes) and not(set(decision.observed_purposes)&withdrawn) and Purpose.unknown not in decision.observed_purposes)
        if not ok or not decision.evidence: return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=uncertain_from(ctx,["R4: invalid PRESERVE"]),downgrades=["R4"])
    if decision.verdict==Verdict.UNCERTAIN and not decision.missing_or_conflicting:
        decision=decision.model_copy(update={"missing_or_conflicting":["R5: explanation required"]}); return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=decision,downgrades=["R5"])
    return ValidatedDecision(occurrence_key=ctx.occurrence_key,raw=raw,final=decision,downgrades=[])
def validate_scope(raw,request_text,container_ids):
    try: scope=ScopeSpec(**raw)
    except Exception:return None,["invalid scope shape"]
    errors=[]
    for x in scope.withdrawn_purposes:
        if x.purpose==Purpose.unknown:errors.append("unknown withdrawn purpose")
        if normalize_ws(x.quote) not in normalize_ws(request_text):errors.append("withdrawn quote missing")
    for x in scope.retained_content:
        if x.container_ref not in container_ids:errors.append("unknown retained container")
        if normalize_ws(x.quote) not in normalize_ws(request_text):errors.append("retained quote missing")
    return (None,errors) if errors else (scope,[])
