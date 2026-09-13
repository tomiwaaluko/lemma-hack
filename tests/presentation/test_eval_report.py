from __future__ import annotations

import json
from pathlib import Path

from recall_desk.evals.report import write_report

METRICS = {
    "critical_errors": 0,
    "final_accuracy": 0.91,
    "safe_abstentions": 2,
    "downgrades_by_rule": {"R2": 1},
    "raw_to_final_changes": 1,
    "decisive_cases": {"a": 11, "b": 12},
    "decisive_runs": {"x": 20, "y": 22},
    "pass_k": {"C5": 0.8},
    "scope_pass": True,
    "c9_tool_use": True,
}

GATE = {
    "critical_ok": True,
    "decisive_ok": True,
    "scope_ok": True,
    "rules_ok": True,
    "passed": True,
}

RECORDS = [
    {
        "case_id": "C1",
        "run_index": 0,
        "raw_verdict": "REMOVE",
        "final_verdict": "REMOVE",
        "downgrades": [],
        "tool_calls": [],
        "critical": False,
        "correct_definite": True,
    }
]

FAULT_OUTCOMES = {"F1": True, "F4": True, "F5": True, "F8": True, "F9": True, "F12": True}
CRASH_LINE = "Crash points converged: 3/3 (before first write, SENT, after verify)"
C9_FALLBACK = "not met (emergency fallback)"


def _write(tmp_path: Path, **overrides):
    out_md = tmp_path / "eval" / "report.md"
    out_json = tmp_path / "eval" / "results.json"
    kwargs = {
        "metrics": METRICS,
        "gate": GATE,
        "records": RECORDS,
        "rules_passed": True,
        "fault_outcomes": FAULT_OUTCOMES,
        "crash_line": CRASH_LINE,
        "duplicate_effects": 0,
        "model_id": "claude-sonnet-5",
        "frozen": False,
        "commit": "abc1234",
        "out_md": str(out_md),
        "out_json": str(out_json),
    }
    kwargs.update(overrides)
    write_report(**kwargs)
    return out_md, out_json


def test_ER1_metrics_a_over_b_print_exact_case_line(tmp_path: Path):
    out_md, _ = _write(tmp_path)
    markdown = out_md.read_text(encoding="utf-8")
    a = METRICS["decisive_cases"]["a"]
    b = METRICS["decisive_cases"]["b"]
    x = METRICS["decisive_runs"]["x"]
    y = METRICS["decisive_runs"]["y"]

    assert f"Critical errors: {METRICS['critical_errors']}" in markdown
    assert f"Decisive coverage (cases): {a}/{b} definite-gold cases" in markdown
    assert f"Decisive coverage (runs): {x}/{y} definite-gold runs" in markdown
    assert CRASH_LINE in markdown
    assert "Duplicate external effects: 0" in markdown
    assert "11/12" in markdown
    assert "12/12" not in markdown


def test_ER2_frozen_true_prints_frozen_yes(tmp_path: Path):
    out_md, _ = _write(tmp_path, frozen=True)
    markdown = out_md.read_text(encoding="utf-8")

    assert "Frozen: yes" in markdown
    assert "Frozen: no" not in markdown


def test_ER3_results_json_round_trip_contains_metrics_and_gate(tmp_path: Path):
    _, out_json = _write(tmp_path, frozen=True, commit="def5678")
    payload = json.loads(out_json.read_text(encoding="utf-8"))

    assert payload["metrics"] == METRICS
    assert payload["gate"] == GATE
    assert payload["records"] == RECORDS
    assert payload["rules_passed"] is True
    assert payload["fault_outcomes"] == FAULT_OUTCOMES
    assert payload["crash_line"] == CRASH_LINE
    assert payload["duplicate_effects"] == 0
    assert payload["model_id"] == "claude-sonnet-5"
    assert payload["frozen"] is True
    assert payload["commit"] == "def5678"
    json.dumps(payload)


def test_ER4_emergency_fallback_string_printed_verbatim(tmp_path: Path):
    metrics = dict(METRICS)
    metrics["c9_tool_use"] = C9_FALLBACK
    out_md, out_json = _write(tmp_path, metrics=metrics)
    markdown = out_md.read_text(encoding="utf-8")
    payload = json.loads(out_json.read_text(encoding="utf-8"))

    assert f"\n{C9_FALLBACK}\n" in markdown
    assert "c9_tool_use: " not in markdown
    assert payload["metrics"]["c9_tool_use"] == C9_FALLBACK
