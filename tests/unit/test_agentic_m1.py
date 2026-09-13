from __future__ import annotations

import json
from types import SimpleNamespace

from recall_desk.adapters.sim import SimAirtable, SimNotion, SimTrello, SimWorld
from recall_desk.agent import interpret_decision, interpret_scope
from recall_desk.config import load_settings
from recall_desk.domain import Purpose, ScopeBasis, ScopeSpec, Verdict, WithdrawnPurpose
from recall_desk.evidence import EvidenceContext, build_packet
from recall_desk.journal import Journal
from recall_desk.orchestrator import run_req001
from recall_desk.policy import rights_hold_case
from recall_desk.rules import RuleContext, validate
from recall_desk.snapshot import load_snapshot


class _Client:
    def __init__(self, payload): self.payload = payload; self.messages = self; self.kwargs = None
    def create(self, **kwargs): self.kwargs = kwargs; return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(self.payload))])


def _scope(*_args, **_kwargs):
    return ScopeSpec(
        withdrawn_purposes=[WithdrawnPurpose(purpose=Purpose.volunteer_recruitment, quote="stop using my photo to recruit volunteers")],
        retained_content=[],
        ambiguities=[],
    )


def _preserve(*_args):
    packet = _args[2]
    item = packet.items[0]
    return {"occurrence_key": packet.occurrence_key, "verdict": "PRESERVE", "observed_purposes": ["program_documentation"], "scope_basis": "PURPOSE_NOT_WITHDRAWN", "evidence": [{"evidence_id": item.evidence_id, "quote": item.text}], "rationale": "Documentation is not withdrawn.", "missing_or_conflicting": []}


def _run(tmp_path, decision_provider):
    world = SimWorld.from_snapshot(load_snapshot())
    summary = run_req001(load_settings(), SimNotion(world), SimTrello(world), SimAirtable(world), Journal(tmp_path / "run.db"), scope_provider=_scope, decision_provider=decision_provider)
    return summary, world


def test_scope_model_json_parses_to_scope_spec_and_retained_content():
    client = _Client({"withdrawn_purposes": [{"purpose": "volunteer_recruitment", "quote": "stop using my photo to recruit volunteers"}], "retained_content": [{"container_ref": "page-n2", "quote": "keep the workshop"}], "ambiguities": []})
    scope = interpret_scope("stop using my photo to recruit volunteers; keep the workshop", "consent", client=client)

    assert scope.withdrawn_purposes[0].purpose == Purpose.volunteer_recruitment
    assert scope.retained_content[0].container_ref == "page-n2"
    assert client.kwargs["output_config"]["format"]["type"] == "json_schema"


def test_occurrence_model_json_is_validated_against_the_packet():
    world = SimWorld.from_snapshot(load_snapshot())
    page = next(page for page in SimNotion(world).list_pages() if page.title == "Volunteer With Us")
    block = next(block for block in SimNotion(world).list_image_blocks(page.page_id))
    from recall_desk.domain import OccurrenceRef, System
    ref = OccurrenceRef(occurrence_key=f"notion:block:{block.block_id}", system=System.Notion, variant_id="VAR-001-B", container_id=page.page_id, container_title=page.title, target_id=block.block_id, location_url=page.public_url, registered=True)
    packet = build_packet(ref, SimNotion(world), SimTrello(world), EvidenceContext({}, {}, {page.page_id: page.title}, {page.page_id: True}))
    raw = interpret_decision(_scope(), packet, "consent", client=_Client({"occurrence_key": packet.occurrence_key, "verdict": "REMOVE", "observed_purposes": ["volunteer_recruitment"], "scope_basis": "WITHDRAWN_PURPOSE", "evidence": [{"evidence_id": packet.items[0].evidence_id, "quote": packet.items[0].text}], "rationale": "Recruitment use is withdrawn.", "missing_or_conflicting": []}))

    validated = validate(raw, RuleContext(ref.occurrence_key, ref.container_id, {item.evidence_id: item for item in packet.items}, _scope()))
    assert validated.final.verdict == Verdict.REMOVE


def test_invalid_citation_downgrades_model_remove_to_uncertain():
    scope = _scope()
    raw = {"occurrence_key": "key", "verdict": "REMOVE", "observed_purposes": ["volunteer_recruitment"], "scope_basis": "WITHDRAWN_PURPOSE", "evidence": [{"evidence_id": "E404", "quote": "invented"}], "rationale": "x", "missing_or_conflicting": []}

    result = validate(raw, RuleContext("key", "container", {}, scope))
    assert result.final.verdict == Verdict.UNCERTAIN


def test_model_failure_downgrades_to_uncertain_without_content_mutation(tmp_path):
    summary, world = _run(tmp_path, lambda *_args: (_ for _ in ()).throw(RuntimeError("model unavailable")))

    assert summary.counts["Removed"] == 0
    assert summary.counts["Uncertain"] == 5
    assert not [effect for effect in world.effects if effect.action in {"archive_block", "move_card", "add_label", "add_comment"}]


def test_orchestrator_follows_model_preserve_verdict_not_fixture_title(tmp_path):
    summary, world = _run(tmp_path, _preserve)

    assert summary.counts["Removed"] == 0
    assert summary.counts["Preserved"] == 5
    assert SimNotion(world).get_block("c6fd67e0-87d5-40fb-a27e-75de6df3dac4").archived is False
    assert not [effect for effect in world.effects if effect.action in {"archive_block", "move_card", "add_label", "add_comment"}]


def test_rights_hold_case_requires_the_configured_hold_list():
    world = SimWorld.from_snapshot(load_snapshot())
    card = SimTrello(world).get_card("6aa6f75b30a189362e5fd0b8")
    comments = []

    assert rights_hold_case(card, comments, "REQ-001", "label", "hold") == "C"
    held = card.model_copy(update={"list_id": "hold", "label_ids": ["label"]})
    from recall_desk.domain import TrelloComment
    assert rights_hold_case(held, [TrelloComment(action_id="x", text="[recall-desk REQ-001 x]")], "REQ-001", "label", "hold") == "A"


def test_preserve_and_uncertain_results_verify_initial_state_is_unchanged(tmp_path):
    summary, world = _run(tmp_path, _preserve)

    assert all(result.outcome.value != "Action failed" for result in summary.results)
    assert SimNotion(world).get_block("fa07d443-94fb-4c46-afd2-2ee388f28f5c").archived is False
    assert SimTrello(world).get_card("6aa6f763644e485160dab57c").list_id == "6aa6f729bd56ec9218932d83"
