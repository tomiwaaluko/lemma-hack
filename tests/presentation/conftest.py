from __future__ import annotations

import pytest

from recall_desk.domain import (
    Citation,
    ExecutionState,
    FinalResult,
    OccurrenceResult,
    Outcome,
    RunFlags,
    RunSummary,
    Verdict,
)

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


def make_result(**overrides) -> OccurrenceResult:
    payload = {
        "occurrence_key": "notion:block:n1",
        "verdict": Verdict.REMOVE,
        "outcome": Outcome.REMOVED_VERIFIED,
        "rationale": "Withdrawn recruitment use.",
        "evidence": [Citation(evidence_id="E1", quote="volunteer mentor")],
        "missing_or_conflicting": [],
        "scheduled_date": None,
        "location_url": "https://example.test/n1",
        "notes": [],
    }
    payload.update(overrides)
    return OccurrenceResult(**payload)


def section_26_results() -> list[OccurrenceResult]:
    return [
        make_result(
            occurrence_key="notion:block:n1",
            verdict=Verdict.REMOVE,
            outcome=Outcome.REMOVED_VERIFIED,
            rationale="Withdrawn volunteer recruitment caption.",
            evidence=[Citation(evidence_id="E1", quote="volunteer mentor since 2023")],
            location_url="https://example.test/n1",
        ),
        make_result(
            occurrence_key="trello:card:t1",
            verdict=Verdict.REMOVE,
            outcome=Outcome.HELD_VERIFIED,
            rationale="Scheduled recruitment carousel uses the withdrawn purpose.",
            evidence=[Citation(evidence_id="E2", quote="Oct Volunteer Drive")],
            location_url="https://example.test/t1",
        ),
        make_result(
            occurrence_key="notion:block:n2",
            verdict=Verdict.PRESERVE,
            outcome=Outcome.PRESERVED_VERIFIED_UNCHANGED,
            rationale="Explicitly retained 2024 Spring Workshop Recap.",
            evidence=[Citation(evidence_id="E3", quote="robotics table on day two")],
            location_url="https://example.test/n2",
        ),
        make_result(
            occurrence_key="notion:block:n3",
            verdict=Verdict.PRESERVE,
            outcome=Outcome.PRESERVED_VERIFIED_UNCHANGED,
            rationale="Fundraising purpose was never withdrawn.",
            evidence=[Citation(evidence_id="E4", quote="Your gifts funded 38 workshops")],
            location_url="https://example.test/n3",
        ),
        make_result(
            occurrence_key="trello:card:t2",
            verdict=Verdict.UNCERTAIN,
            outcome=Outcome.FOLLOWUP_UNCERTAIN,
            rationale="Closing slide purpose is undecided.",
            evidence=[
                Citation(evidence_id="E5", quote="Dana suggested using it to promote fall mentor sign-ups"),
                Citation(evidence_id="E6", quote="Marcus thinks it should just be a thank-you"),
            ],
            missing_or_conflicting=[T2_MISSING_EVIDENCE],
            location_url="https://example.test/t2",
            notes=["Discovered during scan"],
        ),
        make_result(
            occurrence_key="external:fall-2024-flyer",
            verdict=None,
            outcome=Outcome.MANUAL_OUTSIDE_CONNECTED,
            rationale="Printed flyer is outside connected systems.",
            evidence=[],
            location_url=None,
            notes=["500 copies distributed"],
        ),
    ]


def make_summary(**overrides) -> RunSummary:
    payload = {
        "run_id": "RUN-001",
        "request_id": "REQ-001",
        "execution_state": ExecutionState.FINISHED,
        "final_result": FinalResult.NEEDS_FOLLOW_UP,
        "counts": dict(SECTION_26_COUNTS),
        "results": section_26_results(),
        "flags": RunFlags(),
    }
    payload.update(overrides)
    return RunSummary(**payload)


@pytest.fixture
def section_26_summary() -> RunSummary:
    return make_summary()


@pytest.fixture
def sync_failed_summary() -> RunSummary:
    return make_summary(
        final_result=FinalResult.PARTIAL,
        flags=RunFlags(registry_sync_failed=True, content_writes_occurred=True),
    )


@pytest.fixture
def preexisting_hold_summary() -> RunSummary:
    result = make_result(
        occurrence_key="trello:card:preexisting",
        verdict=None,
        outcome=Outcome.FOLLOWUP_PREEXISTING_HOLD,
        rationale="Card was already in Rights Hold before this request.",
        evidence=[],
        missing_or_conflicting=["No same-request marker on the existing hold"],
        location_url="https://example.test/preexisting",
        notes=["Attributed to a prior hold"],
    )
    return make_summary(
        counts={
            "Removed": 0,
            "Held": 0,
            "Preserved": 0,
            "Uncertain": 0,
            "Manual": 0,
            "Other follow-up": 1,
            "Failed": 0,
        },
        results=[result],
        flags=RunFlags(),
    )
