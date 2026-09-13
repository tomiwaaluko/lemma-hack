import json
from datetime import UTC, datetime
from pathlib import Path


def _pair(block, left, right):
    if not isinstance(block, dict):
        return 0, 0
    return int(block.get(left, 0) or 0), int(block.get(right, 0) or 0)


def _flag(value):
    return json.dumps(bool(value))


def _utc_now():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _cell(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def write_report(
    metrics,
    gate,
    records,
    rules_passed,
    fault_outcomes,
    crash_line,
    duplicate_effects,
    model_id,
    frozen,
    commit,
    out_md="eval/report.md",
    out_json="eval/results.json",
):
    """Write eval/report.md and eval/results.json from measured inputs."""
    metrics_data = metrics or {}
    gate_data = gate or {}
    records = list(records or [])
    fault_outcomes = dict(fault_outcomes or {})
    cases_a, cases_b = _pair(metrics_data.get("decisive_cases"), "a", "b")
    runs_x, runs_y = _pair(metrics_data.get("decisive_runs"), "x", "y")
    generated_at = _utc_now()
    lines = [
        "# Recall Desk eval report",
        "",
        f"Generated at: {generated_at}",
        f"Commit: {commit}",
        f"Model: {model_id}",
        f"Frozen: {'yes' if frozen else 'no'}",
        "",
        "## Gate",
    ]
    for key in ("critical_ok", "decisive_ok", "scope_ok", "rules_ok", "passed"):
        lines.append(f"{key}: {_flag(gate_data.get(key))}")
    lines.extend(
        [
            "",
            "## Decision eval",
            f"Critical errors: {int(metrics_data.get('critical_errors', 0) or 0)}",
            f"Decisive coverage (cases): {cases_a}/{cases_b} definite-gold cases",
            f"Decisive coverage (runs): {runs_x}/{runs_y} definite-gold runs",
        ]
    )
    for key in ("final_accuracy", "safe_abstentions", "downgrades_by_rule", "raw_to_final_changes", "pass_k", "scope_pass"):
        if key in metrics_data:
            lines.append(f"{key}: {metrics_data[key]}")
    c9 = metrics_data.get("c9_tool_use")
    if isinstance(c9, str):
        lines.append(c9)
    elif "c9_tool_use" in metrics_data:
        lines.append(f"c9_tool_use: {_flag(c9)}")
    if records:
        lines.extend(
            [
                "",
                "| case_id | run_index | raw_verdict | final_verdict | downgrades | critical | correct_definite |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in records:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(record.get("case_id")),
                        _cell(record.get("run_index")),
                        _cell(record.get("raw_verdict")),
                        _cell(record.get("final_verdict")),
                        _cell(record.get("downgrades")),
                        _cell(record.get("critical")),
                        _cell(record.get("correct_definite")),
                    ]
                )
                + " |"
            )
    lines.extend(["", "## Rules test suite", f"rules_passed: {_flag(rules_passed)}", "", "## Faults"])
    for name, ok in fault_outcomes.items():
        lines.append(f"{name}: {_flag(ok)}")
    lines.extend(
        [
            "",
            "## Crash convergence",
            crash_line,
            f"Duplicate external effects: {int(duplicate_effects)}",
            "",
        ]
    )
    md_path = Path(out_md)
    json_path = Path(out_json)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "commit": commit,
                "model_id": model_id,
                "frozen": bool(frozen),
                "metrics": metrics,
                "gate": gate,
                "records": records,
                "rules_passed": bool(rules_passed),
                "fault_outcomes": fault_outcomes,
                "crash_line": crash_line,
                "duplicate_effects": int(duplicate_effects),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
