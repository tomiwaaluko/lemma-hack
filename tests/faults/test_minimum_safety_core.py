from __future__ import annotations

from recall_desk.adapters.faults import FaultKind, FaultPlan, FaultRule
from recall_desk.domain import FinalResult, Outcome
from recall_desk.evals.oracle import ScenarioFacts, oracle_final_result

from .helpers import scenario


def _content_effects(world):
    return [effect for effect in world.effects if effect.action in {"archive_block", "move_card", "add_label", "add_comment"}]


def test_f1_unknown_notion_archive_ack_is_read_back_without_duplicate_write(tmp_path):
    summary, world, journal = scenario(tmp_path, FaultPlan([FaultRule("notion", "archive_block", 1, FaultKind.APPLY_THEN_DROP)]))

    assert summary.counts["Removed"] == 1
    assert world.effects[0].action == "archive_block"
    assert len([effect for effect in world.effects if effect.action == "archive_block"]) == 1
    assert journal.states_for_action("ARCHIVE_BLOCK") == ["VERIFIED"]


def test_f4_partial_trello_hold_repairs_only_missing_safe_substep_on_rerun(tmp_path):
    failed, world, _ = scenario(tmp_path, FaultPlan([FaultRule("trello", "add_comment", 1, FaultKind.HTTP_401)]))

    assert failed.final_result == FinalResult.PARTIAL
    assert failed.counts["Failed"] == 1
    assert world.cards["6aa6f75b30a189362e5fd0b8"].list_id == "6aa6f742cf8902339a999830"
    assert not world.comments["6aa6f75b30a189362e5fd0b8"]
    first_effect_count = len(_content_effects(world))

    repaired, world, _ = scenario(tmp_path, world=world)

    assert repaired.counts["Held"] == 1
    assert len(world.comments["6aa6f75b30a189362e5fd0b8"]) == 1
    assert [effect.action for effect in _content_effects(world)[first_effect_count:]] == ["add_comment"]


def test_f5_lost_trello_comment_ack_reconciles_by_request_marker(tmp_path):
    summary, world, _ = scenario(tmp_path, FaultPlan([FaultRule("trello", "add_comment", 1, FaultKind.APPLY_THEN_DROP)]))

    assert summary.counts["Held"] == 1
    comments = world.comments["6aa6f75b30a189362e5fd0b8"]
    assert len(comments) == 1
    assert comments[0]["text"].startswith("[recall-desk REQ-001 ")


def test_f8_critical_airtable_read_failure_is_safe_before_content_mutation(tmp_path):
    summary, world, _ = scenario(tmp_path, FaultPlan([FaultRule("airtable", "get_request", 1, FaultKind.HTTP_401)]))

    assert summary.final_result == FinalResult.FAILED_SAFE
    assert world.effects == []


def test_f9_registry_sync_failure_is_partial_without_inflating_occurrence_counts(tmp_path):
    summary, world, _ = scenario(tmp_path, FaultPlan([FaultRule("airtable", "upsert_occurrences", 0, FaultKind.HTTP_401)]))

    assert summary.flags.registry_sync_failed is True
    assert summary.final_result == FinalResult.PARTIAL
    assert summary.counts == {"Removed": 1, "Held": 1, "Preserved": 2, "Uncertain": 1, "Manual": 1, "Other follow-up": 0, "Failed": 0}
    assert {effect.action for effect in _content_effects(world)} == {"archive_block", "move_card", "add_label", "add_comment"}


def test_f12_successful_rerun_adds_no_content_effects_or_marker(tmp_path):
    first, world, _ = scenario(tmp_path)
    effects_before = list(_content_effects(world))

    second, world, _ = scenario(tmp_path, world=world)

    assert first.counts["Removed"] == second.counts["Removed"] == 1
    assert second.counts["Held"] == 1
    assert _content_effects(world) == effects_before
    assert len(world.comments["6aa6f75b30a189362e5fd0b8"]) == 1


def test_oracle_is_independent_and_reports_follow_up_for_m1_world(tmp_path):
    _, world, _ = scenario(tmp_path)
    facts = ScenarioFacts(request_id="REQ-001", ids={"n1": "c6fd67e0-87d5-40fb-a27e-75de6df3dac4"})

    assert oracle_final_result(world, facts) == FinalResult.NEEDS_FOLLOW_UP
