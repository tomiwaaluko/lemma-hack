from __future__ import annotations

from pathlib import Path

from recall_desk.adapters.faults import FaultPlan, wrap_port
from recall_desk.adapters.sim import SimAirtable, SimNotion, SimTrello, SimWorld
from recall_desk.config import load_settings
from recall_desk.domain import Purpose, ScopeSpec, WithdrawnPurpose
from recall_desk.journal import Journal
from recall_desk.orchestrator import run_req001
from recall_desk.snapshot import load_snapshot


def _scope(*_args, **_kwargs):
    return ScopeSpec(withdrawn_purposes=[WithdrawnPurpose(purpose=Purpose.volunteer_recruitment, quote="stop using my photo to recruit volunteers")], retained_content=[], ambiguities=[])


def _decision(_scope, ref, packet, _consent):
    item = packet.items[0]
    if ref.target_id in {"c6fd67e0-87d5-40fb-a27e-75de6df3dac4", "6aa6f75b30a189362e5fd0b8"}:
        return {"occurrence_key": packet.occurrence_key, "verdict": "REMOVE", "observed_purposes": ["volunteer_recruitment"], "scope_basis": "WITHDRAWN_PURPOSE", "evidence": [{"evidence_id": item.evidence_id, "quote": item.text}], "rationale": "Recruitment use is withdrawn.", "missing_or_conflicting": []}
    if ref.target_id in {"fa07d443-94fb-4c46-afd2-2ee388f28f5c", "f4884441-b313-4084-9e2f-aa3acbb3d8de"}:
        return {"occurrence_key": packet.occurrence_key, "verdict": "PRESERVE", "observed_purposes": ["program_documentation"], "scope_basis": "PURPOSE_NOT_WITHDRAWN", "evidence": [{"evidence_id": item.evidence_id, "quote": item.text}], "rationale": "Documentation purpose remains valid.", "missing_or_conflicting": []}
    return {"occurrence_key": packet.occurrence_key, "verdict": "UNCERTAIN", "observed_purposes": [], "scope_basis": "NONE", "evidence": [], "rationale": "Purpose is unresolved.", "missing_or_conflicting": ["ambiguous purpose"]}


def scenario(tmp_path: Path, plan: FaultPlan | None = None, *, world: SimWorld | None = None, journal: Journal | None = None, run_id: str | None = None):
    """Run the fixed M1 world through deterministic simulator ports."""
    world = world or SimWorld.from_snapshot(load_snapshot())
    settings = load_settings()
    journal = journal or Journal(tmp_path / "recall.db")
    notion = wrap_port(SimNotion(world), "notion", plan or FaultPlan())
    trello = wrap_port(SimTrello(world), "trello", plan or FaultPlan())
    airtable = wrap_port(SimAirtable(world), "airtable", plan or FaultPlan())
    summary = run_req001(
        settings, notion, trello, airtable, journal,
        run_id=run_id, scope_provider=_scope, decision_provider=_decision,
    )
    return summary, world, journal
