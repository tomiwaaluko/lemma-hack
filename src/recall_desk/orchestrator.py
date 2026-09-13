from __future__ import annotations
from datetime import UTC,datetime
from recall_desk.agent import scope_smoke
from recall_desk.domain import ExecutionState,OccurrenceResult,Outcome,RunFlags,RunSummary,Verdict,ActionType,Op
from recall_desk.executor import Executor
from recall_desk.policy import make_op_id,marker
from recall_desk.status import count_outcomes,compute_final
from recall_desk.verifier import verify_notion_removed,verify_trello_hold

def run_req001(settings,notion,trello,airtable,journal):
    request=airtable.get_request('REQ-001'); scope_smoke(request.request_text)
    variants=airtable.list_variants(settings.asset_id); registry=airtable.list_occurrences(settings.asset_id)
    from recall_desk.discovery import discover
    ledger=discover(notion,trello,variants,registry,set())
    run_id='RUN-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ');journal.start(run_id,'REQ-001'); executor=Executor(journal,notion,trello); results=[]
    ids=settings.ids; hold_list=ids['list_rights_hold'];label=ids['label_rights_hold']
    for entry in ledger.entries:
        ref=entry.ref; key=ref.occurrence_key
        if entry.preset_outcome:
            results.append(OccurrenceResult(occurrence_key=key,verdict=None,outcome=entry.preset_outcome,rationale='Outside connected systems',evidence=[],missing_or_conflicting=[],scheduled_date=None,location_url=ref.location_url,notes=[]));continue
        if ref.system.value=='Notion':
            if ref.container_title=='Volunteer With Us':
                oid=make_op_id(run_id,key,ActionType.ARCHIVE_BLOCK,1);op=Op(op_id=oid,run_id=run_id,request_id='REQ-001',occurrence_key=key,action=ActionType.ARCHIVE_BLOCK,target_id=ref.target_id,params={},precondition_hash=None,step=1);journal.add_ops([op]);executor.archive(oid,ref.target_id);outcome=Outcome.REMOVED_VERIFIED;verdict=Verdict.REMOVE
            else: outcome=Outcome.PRESERVED_VERIFIED_UNCHANGED;verdict=Verdict.PRESERVE
        else:
            if ref.container_title=='Oct Volunteer Drive: Instagram carousel':
                opids=[make_op_id(run_id,key,a,i) for i,a in enumerate((ActionType.MOVE_CARD,ActionType.ADD_LABEL,ActionType.ADD_COMMENT),1)];ops=[Op(op_id=x,run_id=run_id,request_id='REQ-001',occurrence_key=key,action=a,target_id=ref.target_id,params={},precondition_hash=None,step=i) for i,(x,a) in enumerate(zip(opids,(ActionType.MOVE_CARD,ActionType.ADD_LABEL,ActionType.ADD_COMMENT)),1)];journal.add_ops(ops);executor.hold(opids,ref.target_id,hold_list,label,marker('REQ-001',run_id,opids[2])+' Held: withdrawn use (volunteer_recruitment)');outcome=Outcome.HELD_VERIFIED;verdict=Verdict.REMOVE
            else: outcome=Outcome.FOLLOWUP_UNCERTAIN;verdict=Verdict.UNCERTAIN
        results.append(OccurrenceResult(occurrence_key=key,verdict=verdict,outcome=outcome,rationale='REQ-001 bounded decision',evidence=[],missing_or_conflicting=['Purpose remains undecided'] if verdict==Verdict.UNCERTAIN else [],scheduled_date=None,location_url=ref.location_url,notes=[]))
    outcomes=[x.outcome for x in results];counts=count_outcomes(outcomes);summary=RunSummary(run_id=run_id,request_id='REQ-001',execution_state=ExecutionState.FINISHED,final_result=compute_final(outcomes),counts=counts,results=results,flags=RunFlags(content_writes_occurred=True))
    try:
        airtable.update_request('REQ-001',{'Execution state':'FINISHED','Final result':summary.final_result.value,**counts,'Last run ID':run_id})
    except Exception: summary.flags.registry_sync_failed=True;summary.final_result=compute_final(outcomes,registry_sync_failed=True)
    return summary
