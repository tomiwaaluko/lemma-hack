from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from recall_desk.adapters.sim import SimAirtable, SimNotion, SimTrello, SimWorld
from recall_desk.config import load_settings
from recall_desk.domain import semantic_hash
from recall_desk.journal import Journal
from recall_desk.orchestrator import run_req001
from recall_desk.ports import SimulatedCrash
from recall_desk.snapshot import load_snapshot


@dataclass(frozen=True)
class CrashPoint:
    name: str
    journal_label_contains: str | None = None
    after_apply_prefix: str | None = None


MINIMUM_CRASH_POINTS = (
    CrashPoint("before_first_write", journal_label_contains=":PRECHECK_OK:ARCHIVE_BLOCK"),
    CrashPoint("sent_outcome_unknown", journal_label_contains=":SENT:ARCHIVE_BLOCK"),
    CrashPoint("applied_before_ack", after_apply_prefix="archive_block:"),
    CrashPoint("between_hold_substeps", journal_label_contains=":VERIFIED:MOVE_CARD"),
    CrashPoint("before_registry_sync", journal_label_contains=":SENT:UPSERT_OCCURRENCES"),
)


@dataclass(frozen=True)
class CrashRun:
    summary: object
    world_hash: str
    content_effects: list[object]


def _run(world: SimWorld, journal: Journal, *, run_id: str, scope_provider, decision_provider):
    return run_req001(
        load_settings(), SimNotion(world), SimTrello(world), SimAirtable(world), journal,
        run_id=run_id, scope_provider=scope_provider, decision_provider=decision_provider,
    )


def _content_effects(world: SimWorld) -> list[object]:
    return [effect for effect in world.effects if effect.action in {"archive_block", "move_card", "add_label", "add_comment"}]


def _result(summary, world: SimWorld) -> CrashRun:
    return CrashRun(summary=summary, world_hash=semantic_hash(world.view()), content_effects=_content_effects(world))


def run_reference(directory: Path, *, scope_provider, decision_provider) -> CrashRun:
    directory.mkdir(parents=True, exist_ok=True)
    world = SimWorld.from_snapshot(load_snapshot())
    journal = Journal(directory / "recall.db")
    return _result(_run(world, journal, run_id="RUN-CRASH", scope_provider=scope_provider, decision_provider=decision_provider), world)


def run_with_crash(directory: Path, point: CrashPoint, *, scope_provider, decision_provider) -> CrashRun:
    directory.mkdir(parents=True, exist_ok=True)
    world = SimWorld.from_snapshot(load_snapshot())
    fired = False

    def hit(label: str, *, journal_label: bool) -> None:
        nonlocal fired
        wanted = point.journal_label_contains if journal_label else point.after_apply_prefix
        if not fired and wanted and wanted in label:
            fired = True
            raise SimulatedCrash(label)

    journal = Journal(directory / "recall.db", crash_hook=lambda label: hit(label, journal_label=True))
    world.crash_after_apply = lambda label: hit(label, journal_label=False)
    try:
        _run(world, journal, run_id="RUN-CRASH", scope_provider=scope_provider, decision_provider=decision_provider)
    except SimulatedCrash:
        pass
    else:
        raise AssertionError(f"crash point was not reached: {point.name}")
    finally:
        journal.close()
    if not fired:
        raise AssertionError(f"crash point was not reached: {point.name}")
    world.crash_after_apply = None
    recovered = _run(world, Journal(directory / "recall.db"), run_id="RUN-CRASH", scope_provider=scope_provider, decision_provider=decision_provider)
    return _result(recovered, world)


def crash_report_line(passed: int, tested: int, matrix: str) -> str:
    return f"Crash points converged: {passed}/{tested} ({matrix})"
