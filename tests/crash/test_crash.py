from __future__ import annotations

import pytest

from recall_desk.evals.crash import MINIMUM_CRASH_POINTS, crash_report_line, run_reference, run_with_crash
from tests.faults.helpers import _decision, _scope


@pytest.mark.parametrize("point", MINIMUM_CRASH_POINTS, ids=lambda point: point.name)
def test_minimum_crash_points_converge_without_duplicate_content_effects(tmp_path, point):
    reference = run_reference(tmp_path / "reference", scope_provider=_scope, decision_provider=_decision)
    recovered = run_with_crash(tmp_path / point.name, point, scope_provider=_scope, decision_provider=_decision)

    assert recovered.world_hash == reference.world_hash
    assert recovered.summary.final_result == reference.summary.final_result
    assert recovered.content_effects == reference.content_effects


def test_crash_report_line_has_required_format():
    assert crash_report_line(5, 5, "minimum set") == "Crash points converged: 5/5 (minimum set)"
