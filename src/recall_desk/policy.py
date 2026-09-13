from __future__ import annotations
import hashlib
from dataclasses import dataclass
from recall_desk.domain import ActionType, ListRole, Op, Outcome, ScopeBasis, System, Verdict
class PlanRejected(Exception): pass
@dataclass(frozen=True)
class PolicyIds: rights_hold_list_id:str; label_id:str
def make_op_id(run_id,key,action,step): return 'OP-'+hashlib.sha256(f'{run_id}|{key}|{action}|{step}'.encode()).hexdigest()[:12]
def marker(request_id,run_id,op_id): return f'[recall-desk {request_id} {run_id} {op_id}]'
def has_request_marker(comments,request_id): return any(f'[recall-desk {request_id} ' in c.text for c in comments)
def rights_hold_case(card,comments,request_id,label_id,rights_hold_list_id):
    if card.list_id==rights_hold_list_id:
        if has_request_marker(comments,request_id): return 'A' if label_id in card.label_ids else 'B'
    return 'C'
def validate_content_plan(ops,remove_keys):
    for op in ops:
        if op.action in {ActionType.ARCHIVE_BLOCK,ActionType.MOVE_CARD,ActionType.ADD_LABEL,ActionType.ADD_COMMENT} and op.occurrence_key not in remove_keys: raise PlanRejected(op.occurrence_key)
