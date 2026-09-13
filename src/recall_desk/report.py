from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from recall_desk.domain import OccurrenceResult, Outcome, RunSummary

try:
    from recall_desk.status import COUNT_KEYS as _IMPORTED_COUNT_KEYS
except ImportError:
    COUNT_KEYS: tuple[str, ...] = (
        "Removed",
        "Held",
        "Preserved",
        "Uncertain",
        "Manual",
        "Other follow-up",
        "Failed",
    )
else:
    COUNT_KEYS = tuple(_IMPORTED_COUNT_KEYS)

FOLLOWUP_OUTCOMES = frozenset(
    {
        Outcome.FOLLOWUP_UNCERTAIN,
        Outcome.FOLLOWUP_AMBIGUOUS_IDENTIFIER,
        Outcome.FOLLOWUP_STATE_CHANGED_REPEATEDLY,
        Outcome.FOLLOWUP_APPEARED_DURING_RUN,
        Outcome.FOLLOWUP_PREEXISTING_HOLD,
        Outcome.FOLLOWUP_PREEXISTING_REMOVAL,
        Outcome.MANUAL_OUTSIDE_CONNECTED,
        Outcome.INACCESSIBLE,
    }
)


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", str(value))


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _join(parts: Iterable[str]) -> str:
    return "; ".join(part for part in parts if part)


def _counts(summary: RunSummary) -> dict[str, int]:
    return {key: int(summary.counts.get(key, 0)) for key in COUNT_KEYS}


def _collateral_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("description", "message", "text"):
            if key in payload and payload[key] is not None:
                return str(payload[key])
        return _join(str(value) for value in payload.values() if value is not None)
    return "" if payload is None else str(payload)


def _result_dict(result: OccurrenceResult) -> dict[str, Any]:
    return {
        "occurrence_key": result.occurrence_key,
        "verdict": _enum_value(result.verdict),
        "outcome": result.outcome.value,
        "rationale": result.rationale,
        "evidence": [
            {"evidence_id": item.evidence_id, "quote": item.quote} for item in result.evidence
        ],
        "missing_or_conflicting": list(result.missing_or_conflicting),
        "scheduled_date": result.scheduled_date,
        "location_url": result.location_url,
        "notes": list(result.notes),
    }


def render_json(summary: RunSummary) -> dict:
    flags = summary.flags
    return {
        "run_id": summary.run_id,
        "request_id": summary.request_id,
        "execution_state": summary.execution_state.value,
        "final_result": _enum_value(summary.final_result),
        "counts": _counts(summary),
        "results": [_result_dict(result) for result in summary.results],
        "flags": {
            "registry_read_failed": flags.registry_read_failed,
            "scope_rejected": flags.scope_rejected,
            "content_writes_occurred": flags.content_writes_occurred,
            "registry_sync_failed": flags.registry_sync_failed,
        },
    }


def render_markdown(summary: RunSummary, events: list[dict]) -> str:
    counts = _counts(summary)
    final_result = _enum_value(summary.final_result) or ""
    lines = [
        f"# Recall Desk run {summary.run_id}",
        "",
        f"Request ID: {summary.request_id}",
        f"Execution state: {summary.execution_state.value}",
        f"Final result: {final_result}",
        "",
        "| Count | N |",
        "| --- | --- |",
    ]
    for key in COUNT_KEYS:
        lines.append(f"| {key} | {counts[key]} |")

    flags = summary.flags
    lines.extend(
        [
            "",
            "## Flags",
            f"registry_read_failed: {str(flags.registry_read_failed).lower()}",
            f"scope_rejected: {str(flags.scope_rejected).lower()}",
            f"content_writes_occurred: {str(flags.content_writes_occurred).lower()}",
            f"registry_sync_failed: {str(flags.registry_sync_failed).lower()}",
        ]
    )
    if flags.registry_sync_failed:
        lines.extend(["", "Registry synchronization failed"])

    for event in events:
        if event.get("kind") != "collateral_change":
            continue
        text = _collateral_text(event.get("payload"))
        if text:
            lines.extend(["", f"Collateral changes detected: {text}"])

    lines.extend(
        [
            "",
            "| Key | Location | Verdict | Outcome | Rationale | Evidence | Missing or conflicting | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in summary.results:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(result.occurrence_key),
                    _cell(result.location_url),
                    _cell(_enum_value(result.verdict)),
                    _cell(result.outcome.value),
                    _cell(result.rationale),
                    _cell(_join(item.quote for item in result.evidence)),
                    _cell(_join(result.missing_or_conflicting)),
                    _cell(_join(result.notes)),
                ]
            )
            + " |"
        )

    followups = [result for result in summary.results if result.outcome in FOLLOWUP_OUTCOMES]
    if followups:
        lines.extend(["", "## Manual follow-up"])
        for result in followups:
            lines.extend(
                [
                    "",
                    f"### {result.occurrence_key}",
                    f"- Outcome: {result.outcome.value}",
                    f"- Location: {result.location_url or ''}",
                    f"- Evidence: {_join(item.quote for item in result.evidence)}",
                    f"- Missing or conflicting: {_join(result.missing_or_conflicting)}",
                    f"- Scheduled: {result.scheduled_date or ''}",
                    f"- Notes: {_join(result.notes)}",
                    f"- Rationale: {result.rationale}",
                ]
            )

    return "\n".join(lines) + "\n"
