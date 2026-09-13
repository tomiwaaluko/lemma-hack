from __future__ import annotations

from datetime import UTC, datetime

from recall_desk.agent import interpret_decision, interpret_scope
from recall_desk.discovery import discover
from recall_desk.domain import ActionType, ExecutionState, FinalResult, OccurrenceResult, Op, Outcome, RunFlags, RunSummary, System, Verdict
from recall_desk.evidence import EvidenceContext, build_packet, state_hash
from recall_desk.executor import Executor
from recall_desk.policy import make_op_id, marker
from recall_desk.rules import RuleContext, uncertain_from, validate, validate_scope
from recall_desk.status import count_outcomes, compute_final
from recall_desk.verifier import verify_notion_removed, verify_trello_hold


def _safe_failure(run_id, *, scope=False):
    return RunSummary(run_id=run_id, request_id="REQ-001", execution_state=ExecutionState.FINISHED, final_result=FinalResult.FAILED_SAFE, counts=count_outcomes([]), results=[], flags=RunFlags(registry_read_failed=not scope, scope_rejected=scope))


def _result(ref, decision, outcome, note=""):
    return OccurrenceResult(occurrence_key=ref.occurrence_key, verdict=decision.verdict if decision else None, outcome=outcome, rationale=decision.rationale if decision else "Outside connected systems", evidence=decision.evidence if decision else [], missing_or_conflicting=decision.missing_or_conflicting if decision else [], scheduled_date=None, location_url=ref.location_url, notes=[note] if note else [])


def run_req001(settings, notion, trello, airtable, journal, *, run_id=None, scope_provider=interpret_scope, decision_provider=None):
    run_id = run_id or "RUN-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        request, asset = airtable.get_request("REQ-001"), airtable.get_asset(settings.asset_id)
        variants, registry, pages, cards = airtable.list_variants(settings.asset_id), airtable.list_occurrences(settings.asset_id), notion.list_pages(), trello.list_cards()
    except Exception:
        return _safe_failure(run_id)
    containers = {page.page_id: page.title for page in pages} | {card.card_id: card.name for card in cards}
    try:
        raw_scope = scope_provider(request.request_text, asset.consent_terms, known_containers=containers)
        scope, errors = validate_scope(raw_scope.model_dump(), request.request_text, set(containers))
        if scope is None: return _safe_failure(run_id, scope=True)
    except Exception:
        return _safe_failure(run_id, scope=True)

    ledger = discover(notion, trello, variants, registry, journal.reconcilable_archives_for_request("REQ-001"))
    context = EvidenceContext({item.list_id: item.name for item in trello.list_lists()}, trello.list_labels(), {page.page_id: page.title for page in pages}, {page.page_id: bool(page.public_url) for page in pages})
    journal.start(run_id, "REQ-001")
    executor, results = Executor(journal, notion, trello), []
    hold_list, label = settings.ids["list_rights_hold"], settings.ids["label_rights_hold"]
    planned_lists = {settings.ids["list_ideas"], settings.ids["list_in_production"], settings.ids["list_scheduled"]}

    for entry in ledger.entries:
        ref = entry.ref
        if entry.preset_outcome:
            results.append(_result(ref, None, entry.preset_outcome)); continue
        try:
            packet = build_packet(ref, notion, trello, context)
        except Exception:
            packet = None
        if packet is None:
            decision = uncertain_from(RuleContext(ref.occurrence_key, ref.container_id, {}, scope), ["evidence unavailable"])
        else:
            try:
                raw = decision_provider(scope, ref, packet, asset.consent_terms) if decision_provider else interpret_decision(scope, packet, asset.consent_terms)
                decision = validate(raw, RuleContext(ref.occurrence_key, ref.container_id, {item.evidence_id: item for item in packet.items}, scope)).final
            except Exception:
                decision = uncertain_from(RuleContext(ref.occurrence_key, ref.container_id, {item.evidence_id: item for item in packet.items}, scope), ["model decision unavailable"])
        before_hash = packet.state_hash if packet else None
        if decision.verdict == Verdict.REMOVE and ref.system == System.Notion:
            op_id = make_op_id(run_id, ref.occurrence_key, ActionType.ARCHIVE_BLOCK, 1)
            journal.add_ops([Op(op_id=op_id, run_id=run_id, request_id="REQ-001", occurrence_key=ref.occurrence_key, action=ActionType.ARCHIVE_BLOCK, target_id=ref.target_id, params={}, precondition_hash=before_hash, step=1)])
            try: executor.archive(op_id, ref.target_id); outcome = Outcome.REMOVED_VERIFIED if verify_notion_removed(notion, ref.target_id) else Outcome.ACTION_FAILED
            except Exception: outcome = Outcome.ACTION_FAILED
        elif decision.verdict == Verdict.REMOVE and ref.system == System.Trello:
            card = trello.get_card(ref.target_id)
            if card.list_id not in planned_lists and card.list_id != hold_list:
                outcome = Outcome.ACTION_FAILED
            else:
                actions = (ActionType.MOVE_CARD, ActionType.ADD_LABEL, ActionType.ADD_COMMENT)
                op_ids = [make_op_id(run_id, ref.occurrence_key, action, index) for index, action in enumerate(actions, 1)]
                journal.add_ops([Op(op_id=op_id, run_id=run_id, request_id="REQ-001", occurrence_key=ref.occurrence_key, action=action, target_id=ref.target_id, params={}, precondition_hash=before_hash, step=index) for index, (op_id, action) in enumerate(zip(op_ids, actions), 1)])
                try: executor.hold(op_ids, ref.target_id, hold_list, label, marker("REQ-001", run_id, op_ids[2]) + " Held: withdrawn use"); outcome = Outcome.HELD_VERIFIED if verify_trello_hold(trello, ref.target_id, hold_list, label, "REQ-001") else Outcome.ACTION_FAILED
                except Exception: outcome = Outcome.ACTION_FAILED
        elif decision.verdict == Verdict.PRESERVE:
            outcome = Outcome.PRESERVED_VERIFIED_UNCHANGED if before_hash == state_hash(ref, notion, trello, context) else Outcome.ACTION_FAILED
        else:
            outcome = Outcome.FOLLOWUP_UNCERTAIN if before_hash == state_hash(ref, notion, trello, context) else Outcome.ACTION_FAILED
        results.append(_result(ref, decision, outcome, "state unchanged" if outcome in {Outcome.PRESERVED_VERIFIED_UNCHANGED, Outcome.FOLLOWUP_UNCERTAIN} else ""))

    outcomes, counts = [result.outcome for result in results], count_outcomes([result.outcome for result in results])
    summary = RunSummary(run_id=run_id, request_id="REQ-001", execution_state=ExecutionState.FINISHED, final_result=compute_final(outcomes), counts=counts, results=results, flags=RunFlags(content_writes_occurred=any(result.outcome in {Outcome.REMOVED_VERIFIED, Outcome.HELD_VERIFIED} for result in results)))
    try:
        sync_id = make_op_id(run_id, "registry", ActionType.UPSERT_OCCURRENCES, 1)
        journal.add_ops([Op(op_id=sync_id, run_id=run_id, request_id="REQ-001", occurrence_key=None, action=ActionType.UPSERT_OCCURRENCES, target_id="Occurrences", params={}, precondition_hash=None, step=1)])
        journal.transition(sync_id, "PRECHECK_OK"); journal.transition(sync_id, "SENT"); airtable.upsert_occurrences([]); journal.transition(sync_id, "VERIFIED")
        airtable.update_request("REQ-001", {"Execution state": "FINISHED", "Final result": summary.final_result.value, **counts, "Last run ID": run_id})
    except Exception:
        summary.flags.registry_sync_failed = True; summary.final_result = compute_final(outcomes, registry_sync_failed=True)
    journal.finish(run_id)
    return summary
