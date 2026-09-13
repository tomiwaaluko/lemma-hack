from pathlib import Path

import pytest
from pydantic import ValidationError

from recall_desk.config import load_settings
from recall_desk.domain import (
    Bucket,
    Citation,
    CoverageEntry,
    CoverageLedger,
    Decision,
    OccurrenceRef,
    Outcome,
    Purpose,
    ScopeBasis,
    System,
    Verdict,
    semantic_hash,
)


def _decision(**overrides):
    payload = {
        "occurrence_key": "notion:block:n1",
        "verdict": Verdict.REMOVE,
        "observed_purposes": [Purpose.volunteer_recruitment],
        "scope_basis": ScopeBasis.WITHDRAWN_PURPOSE,
        "evidence": [Citation(evidence_id="E1", quote="volunteer")],
        "rationale": "Withdrawn recruitment use.",
        "missing_or_conflicting": [],
    }
    payload.update(overrides)
    return Decision(**payload)


def _ref(key: str) -> OccurrenceRef:
    return OccurrenceRef(
        occurrence_key=key,
        system=System.Notion,
        variant_id="VAR-001-A",
        container_id="page-1",
        container_title="Page",
        target_id=key,
        location_url=None,
        registered=True,
    )


def _entry(key: str, bucket: Bucket) -> CoverageEntry:
    return CoverageEntry(
        ref=_ref(key),
        bucket=bucket,
        preset_outcome=None,
        note="",
    )


def test_D1_outcome_has_exactly_12_members_with_locked_strings():
    assert len(Outcome) == 12
    assert {member.name for member in Outcome} == {
        "REMOVED_VERIFIED",
        "HELD_VERIFIED",
        "PRESERVED_VERIFIED_UNCHANGED",
        "FOLLOWUP_UNCERTAIN",
        "FOLLOWUP_AMBIGUOUS_IDENTIFIER",
        "FOLLOWUP_STATE_CHANGED_REPEATEDLY",
        "FOLLOWUP_APPEARED_DURING_RUN",
        "FOLLOWUP_PREEXISTING_HOLD",
        "FOLLOWUP_PREEXISTING_REMOVAL",
        "MANUAL_OUTSIDE_CONNECTED",
        "INACCESSIBLE",
        "ACTION_FAILED",
    }
    assert Outcome.REMOVED_VERIFIED == "Removed – verified"
    assert Outcome.HELD_VERIFIED == "Held – verified"
    assert Outcome.PRESERVED_VERIFIED_UNCHANGED == "Preserved – verified unchanged"
    assert Outcome.FOLLOWUP_UNCERTAIN == "Needs follow-up – uncertain"
    assert Outcome.FOLLOWUP_AMBIGUOUS_IDENTIFIER == "Needs follow-up – ambiguous identifier"
    assert Outcome.FOLLOWUP_STATE_CHANGED_REPEATEDLY == "Needs follow-up – state changed repeatedly"
    assert Outcome.FOLLOWUP_APPEARED_DURING_RUN == "Needs follow-up – appeared during run"
    assert Outcome.FOLLOWUP_PREEXISTING_HOLD == "Needs follow-up – pre-existing hold"
    assert Outcome.FOLLOWUP_PREEXISTING_REMOVAL == "Needs follow-up – pre-existing removal"
    assert Outcome.MANUAL_OUTSIDE_CONNECTED == "Manual – outside connected systems"
    assert Outcome.INACCESSIBLE == "Inaccessible"
    assert Outcome.ACTION_FAILED == "Action failed"


def test_D2_decision_with_five_citations_fails_validation():
    citations = [Citation(evidence_id=f"E{i}", quote="q") for i in range(5)]
    with pytest.raises(ValidationError):
        _decision(evidence=citations)


def test_D3_decision_rationale_of_301_characters_fails_validation():
    with pytest.raises(ValidationError):
        _decision(rationale="x" * 301)


def test_D4_candidates_returns_only_candidate_entries():
    ledger = CoverageLedger(
        entries=[
            _entry("candidate", Bucket.CANDIDATE),
            _entry("removed", Bucket.ALREADY_REMOVED),
            _entry("gone", Bucket.INACCESSIBLE),
            _entry("flyer", Bucket.EXTERNAL),
            _entry("ambiguous", Bucket.AMBIGUOUS_IDENTIFIER),
        ]
    )
    candidates = ledger.candidates()
    assert [entry.bucket for entry in candidates] == [Bucket.CANDIDATE]
    assert [entry.ref.occurrence_key for entry in candidates] == ["candidate"]


def test_H1_objects_differing_only_in_last_edited_time_hash_equal():
    left = {"block_id": "b1", "caption": "Amara", "last_edited_time": "2024-01-01T00:00:00.000Z"}
    right = {"block_id": "b1", "caption": "Amara", "last_edited_time": "2026-09-13T16:00:00.000Z"}
    assert semantic_hash(left) == semantic_hash(right)


def test_H2_equivalent_blocks_in_different_order_hash_equal():
    first = [
        {"block_id": "b2", "text": "two"},
        {"block_id": "b1", "text": "one"},
    ]
    second = [
        {"block_id": "b1", "text": "one"},
        {"block_id": "b2", "text": "two"},
    ]
    assert semantic_hash(first) == semantic_hash(second)


def test_H3_objects_differing_in_caption_hash_differ():
    left = {"block_id": "b1", "caption": "Amara, volunteer mentor since 2023"}
    right = {"block_id": "b1", "caption": "Amara leading the robotics table on day two"}
    assert semantic_hash(left) != semantic_hash(right)


def test_C1_load_settings_temp_toml_without_ids_file(tmp_path: Path):
    toml_path = tmp_path / "recall.toml"
    toml_path.write_text(
        """
model_default = "claude-sonnet-5"
model_backup = "claude-opus-5"
request_id = "REQ-001"
asset_id = "AST-001"
label_name = "Rights hold"
db_path = "recall.db"
airtable_rate_limit_wait_s = 30
max_retries = 3
verify_rereads = 3
verify_window_s = 2.0
tool_budget = 3
investigation_concurrency = 3
emergency_fallback = false

[list_names]
ideas = "Ideas"
in_production = "In Production"
scheduled = "Scheduled"
published = "Published"
rights_hold = "Rights Hold"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    settings = load_settings(
        env_file=str(tmp_path / ".env"),
        toml_path=str(toml_path),
        ids_path=str(tmp_path / "ids.toml"),
    )
    assert settings.ids == {}
    assert settings.model_default == "claude-sonnet-5"
