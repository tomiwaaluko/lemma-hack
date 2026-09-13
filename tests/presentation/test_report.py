from __future__ import annotations

import json
import re

from recall_desk.domain import FinalResult, Outcome
from recall_desk.report import render_json, render_markdown

COUNT_KEYS = (
    "Removed",
    "Held",
    "Preserved",
    "Uncertain",
    "Manual",
    "Other follow-up",
    "Failed",
)

SECTION_26_COUNTS = {
    "Removed": 1,
    "Held": 1,
    "Preserved": 2,
    "Uncertain": 1,
    "Manual": 1,
    "Other follow-up": 0,
    "Failed": 0,
}

T2_MISSING_EVIDENCE = "the purpose of the final slide is undecided"


def _count_row(markdown: str, label: str) -> str | None:
    pattern = rf"\| {re.escape(label)} \| ([^|]+) \|"
    match = re.search(pattern, markdown)
    return None if match is None else match.group(1).strip()


def test_RP1_section_26_markdown_has_result_counts_and_t2_followup(section_26_summary):
    markdown = render_markdown(section_26_summary, [])

    assert markdown.startswith("# Recall Desk run RUN-001")
    assert "Final result: NEEDS_FOLLOW_UP" in markdown
    assert _count_row(markdown, "Other follow-up") == "0"
    assert "## Manual follow-up" in markdown
    assert "trello:card:t2" in markdown
    assert T2_MISSING_EVIDENCE in markdown


def test_RP2_registry_sync_failed_is_run_level_flag(sync_failed_summary):
    markdown = render_markdown(sync_failed_summary, [])
    payload = render_json(sync_failed_summary)

    assert "Registry synchronization failed" in markdown
    assert payload["flags"]["registry_sync_failed"] is True
    assert "registry_sync_failed" not in payload["counts"]
    assert payload["counts"] == SECTION_26_COUNTS
    assert payload["final_result"] == FinalResult.PARTIAL


def test_RP3_preexisting_hold_appears_under_manual_followup(preexisting_hold_summary):
    markdown = render_markdown(preexisting_hold_summary, [])

    followup_index = markdown.index("## Manual follow-up")
    followup = markdown[followup_index:]
    assert "trello:card:preexisting" in followup
    assert Outcome.FOLLOWUP_PREEXISTING_HOLD in followup


def test_markdown_contains_request_id_and_final_result(section_26_summary):
    markdown = render_markdown(section_26_summary, [])

    assert "REQ-001" in markdown
    assert "Final result: NEEDS_FOLLOW_UP" in markdown
    assert "FINISHED" in markdown


def test_markdown_contains_all_seven_count_categories(section_26_summary):
    markdown = render_markdown(section_26_summary, [])

    for key in COUNT_KEYS:
        assert _count_row(markdown, key) == str(SECTION_26_COUNTS[key])


def test_markdown_contains_occurrence_rows(section_26_summary):
    markdown = render_markdown(section_26_summary, [])

    for result in section_26_summary.results:
        assert result.occurrence_key in markdown
        assert result.outcome in markdown
        assert result.rationale in markdown


def test_json_contains_the_same_run_level_values(section_26_summary):
    payload = render_json(section_26_summary)

    assert payload["run_id"] == "RUN-001"
    assert payload["request_id"] == "REQ-001"
    assert payload["execution_state"] == "FINISHED"
    assert payload["final_result"] == "NEEDS_FOLLOW_UP"
    assert payload["counts"] == SECTION_26_COUNTS
    assert [row["occurrence_key"] for row in payload["results"]] == [
        result.occurrence_key for result in section_26_summary.results
    ]
    t2 = next(row for row in payload["results"] if row["occurrence_key"] == "trello:card:t2")
    assert t2["missing_or_conflicting"] == [T2_MISSING_EVIDENCE]
    assert t2["location_url"] == "https://example.test/t2"
    assert t2["notes"] == ["Discovered during scan"]
    assert t2["evidence"][0]["quote"]


def test_registry_sync_does_not_invent_a_count(sync_failed_summary, section_26_summary):
    payload = render_json(sync_failed_summary)
    markdown = render_markdown(sync_failed_summary, [])

    assert list(payload["counts"]) == list(COUNT_KEYS)
    assert payload["counts"] == section_26_summary.counts
    assert sum(payload["counts"].values()) == sum(section_26_summary.counts.values())
    for key in COUNT_KEYS:
        assert _count_row(markdown, key) == str(SECTION_26_COUNTS[key])


def test_serialization_is_deterministic(section_26_summary):
    events = [
        {
            "seq": 1,
            "kind": "collateral_change",
            "payload": {"description": "N4 caption changed"},
            "at": "2026-09-13T16:00:00Z",
        }
    ]

    first_md = render_markdown(section_26_summary, events)
    second_md = render_markdown(section_26_summary, events)
    first_json = render_json(section_26_summary)
    second_json = render_json(section_26_summary)

    assert first_md == second_md
    assert first_json == second_json
    assert json.dumps(first_json, ensure_ascii=False, sort_keys=True) == json.dumps(
        second_json, ensure_ascii=False, sort_keys=True
    )
    assert "Collateral changes detected: N4 caption changed" in first_md


def test_en_dash_outcome_strings_survive_intact(section_26_summary):
    markdown = render_markdown(section_26_summary, [])
    payload = render_json(section_26_summary)
    dumped = json.dumps(payload, ensure_ascii=False)

    assert "Removed – verified" in markdown
    assert "Held – verified" in markdown
    assert "Preserved – verified unchanged" in markdown
    assert "Needs follow-up – uncertain" in markdown
    assert "Manual – outside connected systems" in markdown
    assert "Removed - verified" not in markdown
    assert payload["results"][0]["outcome"] == "Removed – verified"
    assert "Removed – verified" in dumped
    assert "\u2013" in dumped
