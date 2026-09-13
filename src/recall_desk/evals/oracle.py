from __future__ import annotations

from dataclasses import dataclass, field

from recall_desk.domain import FinalResult


@dataclass(frozen=True)
class ScenarioFacts:
    request_id: str
    ids: dict[str, str]
    registry_read_fails: bool = False
    sync_fails: bool = False
    gold_verdicts: dict[str, str] = field(default_factory=dict)


def oracle_final_result(world, facts: ScenarioFacts) -> FinalResult:
    """A deliberately journal-free outcome oracle over observable state."""
    if facts.registry_read_fails:
        return FinalResult.FAILED_SAFE
    if facts.sync_fails:
        return FinalResult.PARTIAL
    return FinalResult.NEEDS_FOLLOW_UP
