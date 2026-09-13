from __future__ import annotations

import argparse
import subprocess

from recall_desk.adapters.sim import SimAirtable, SimNotion, SimTrello, SimWorld
from recall_desk.agent import interpret_decision, interpret_scope
from recall_desk.discovery import discover
from recall_desk.domain import Purpose, Verdict
from recall_desk.evals.report import write_report
from recall_desk.evidence import EvidenceContext, build_packet
from recall_desk.rules import RuleContext, uncertain_from, validate, validate_scope
from recall_desk.snapshot import load_snapshot


MODEL = "claude-sonnet-5"
CASES = (
    ("N1", "c6fd67e0-87d5-40fb-a27e-75de6df3dac4", Verdict.REMOVE),
    ("N2", "fa07d443-94fb-4c46-afd2-2ee388f28f5c", Verdict.PRESERVE),
    ("N3", "f4884441-b313-4084-9e2f-aa3acbb3d8de", Verdict.PRESERVE),
    ("T2", "6aa6f763644e485160dab57c", Verdict.UNCERTAIN),
)


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _context(world: SimWorld) -> EvidenceContext:
    notion, trello = SimNotion(world), SimTrello(world)
    pages = notion.list_pages()
    return EvidenceContext(
        {item.list_id: item.name for item in trello.list_lists()},
        trello.list_labels(),
        {page.page_id: page.title for page in pages},
        {page.page_id: bool(page.public_url) for page in pages},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the frozen, read-only Recall Desk decision evaluation.")
    parser.add_argument("--rules-passed", action="store_true", help="Record a separately verified pytest result.")
    parser.add_argument("--commit", default=_commit())
    args = parser.parse_args(argv)

    snapshot = load_snapshot()
    world = SimWorld.from_snapshot(snapshot)
    notion, trello, airtable = SimNotion(world), SimTrello(world), SimAirtable(world)
    pages, cards = notion.list_pages(), trello.list_cards()
    containers = {page.page_id: page.title for page in pages} | {card.card_id: card.name for card in cards}
    scope_errors: list[str] = []
    try:
        interpreted_scope = interpret_scope(snapshot.request["request_text"], snapshot.asset["consent_terms"], known_containers=containers)
        scope, scope_errors = validate_scope(interpreted_scope.model_dump(), snapshot.request["request_text"], set(containers))
    except Exception as error:
        scope, scope_errors = None, [f"scope model failure: {type(error).__name__}"]

    scope_cases = {
        "withdrawn_volunteer_recruitment": bool(scope and Purpose.volunteer_recruitment in {item.purpose for item in scope.withdrawn_purposes}),
        "retained_2024_spring_workshop_recap": bool(scope and snapshot.pages and any(item.container_ref == next(page["page_id"] for page in snapshot.pages if page["title"] == "2024 Spring Workshop Recap") for item in scope.retained_content)),
    }
    records = [
        {"case_id": f"scope:{name}", "run_index": 0, "raw_verdict": "PASS" if passed else "FAIL", "final_verdict": "PASS" if passed else "FAIL", "downgrades": scope_errors, "critical": False, "correct_definite": None}
        for name, passed in scope_cases.items()
    ]

    ledger = discover(notion, trello, airtable.list_variants(snapshot.asset["asset_id"]), airtable.list_occurrences(snapshot.asset["asset_id"]), set())
    entries = {entry.ref.target_id: entry for entry in ledger.candidates()}
    context = _context(world)
    decisive_total = decisive_correct = critical_errors = 0
    for case_id, target_id, gold in CASES:
        entry = entries[target_id]
        packet = build_packet(entry.ref, notion, trello, context)
        raw: dict = {}
        if scope is None:
            final = uncertain_from(RuleContext(entry.ref.occurrence_key, entry.ref.container_id, {}, interpreted_scope), ["scope unavailable"])
            downgrades = ["scope unavailable"]
        else:
            try:
                raw = interpret_decision(scope, packet, snapshot.asset["consent_terms"])
                validated = validate(raw, RuleContext(entry.ref.occurrence_key, entry.ref.container_id, {item.evidence_id: item for item in packet.items}, scope))
                final, downgrades = validated.final, validated.downgrades
            except Exception as error:
                final = uncertain_from(RuleContext(entry.ref.occurrence_key, entry.ref.container_id, {item.evidence_id: item for item in packet.items}, scope), [f"decision model failure: {type(error).__name__}"])
                downgrades = ["decision model failure"]
        definite = gold in {Verdict.REMOVE, Verdict.PRESERVE}
        correct = final.verdict == gold
        unsupported_remove = raw.get("verdict") == Verdict.REMOVE and final.verdict != Verdict.REMOVE
        critical = (gold == Verdict.REMOVE and final.verdict == Verdict.PRESERVE) or (gold == Verdict.PRESERVE and final.verdict == Verdict.REMOVE) or unsupported_remove
        if definite:
            decisive_total += 1
            decisive_correct += int(correct)
        critical_errors += int(critical)
        records.append({"case_id": case_id, "run_index": 0, "gold": gold.value, "raw_verdict": raw.get("verdict", "ERROR"), "final_verdict": final.verdict.value, "downgrades": downgrades, "critical": critical, "correct_definite": correct if definite else None})

    accuracy = decisive_correct / decisive_total if decisive_total else 0.0
    scope_pass = all(scope_cases.values())
    gate = {"critical_ok": critical_errors == 0, "decisive_ok": accuracy >= 0.85, "scope_ok": scope_pass, "rules_ok": args.rules_passed}
    gate["passed"] = all(gate.values())
    metrics = {"critical_errors": critical_errors, "decisive_cases": {"a": decisive_correct, "b": decisive_total}, "decisive_runs": {"x": decisive_correct, "y": decisive_total}, "final_accuracy": accuracy, "scope_pass": scope_pass, "scope_cases": scope_cases}
    write_report(metrics, gate, records, args.rules_passed, {}, "Not run (eval-only model decision sprint)", 0, MODEL, True, args.commit)
    print(f"gate={'PASS' if gate['passed'] else 'FAIL'} decisive={decisive_correct}/{decisive_total} critical={critical_errors} scope={sum(scope_cases.values())}/{len(scope_cases)}")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
