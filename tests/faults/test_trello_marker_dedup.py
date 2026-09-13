from __future__ import annotations

from recall_desk.adapters.sim import SimNotion, SimTrello, SimWorld
from recall_desk.domain import ActionType, Op
from recall_desk.executor import Executor
from recall_desk.journal import Journal
from recall_desk.policy import marker
from recall_desk.snapshot import load_snapshot


CARD_ID = "6aa6f75b30a189362e5fd0b8"
HOLD_LIST = "6aa6f742cf8902339a999830"
LABEL_ID = "6aa6f706da9b20af3482110a"


def _hold(tmp_path, world, request_id, run_id, text):
    journal = Journal(tmp_path / f"{run_id}.db")
    journal.start(run_id, request_id)
    actions = (ActionType.MOVE_CARD, ActionType.ADD_LABEL, ActionType.ADD_COMMENT)
    op_ids = [f"{run_id}-{index}" for index in range(3)]
    journal.add_ops([Op(op_id=op_id, run_id=run_id, request_id=request_id, occurrence_key="trello:card:test", action=action, target_id=CARD_ID, params={}, precondition_hash=None, step=index + 1) for index, (op_id, action) in enumerate(zip(op_ids, actions))])
    Executor(journal, SimNotion(world), SimTrello(world)).hold(op_ids, CARD_ID, HOLD_LIST, LABEL_ID, request_id, text)


def test_same_request_different_run_marker_is_not_duplicated(tmp_path):
    world = SimWorld.from_snapshot(load_snapshot())
    world.comments[CARD_ID].append({"action_id": "old", "text": marker("REQ-001", "RUN-OLD", "OP-OLD")})

    _hold(tmp_path, world, "REQ-001", "RUN-NEW", marker("REQ-001", "RUN-NEW", "OP-NEW"))

    assert len(world.comments[CARD_ID]) == 1


def test_same_exact_marker_is_not_duplicated(tmp_path):
    world = SimWorld.from_snapshot(load_snapshot())
    text = marker("REQ-001", "RUN-ONE", "OP-ONE")
    world.comments[CARD_ID].append({"action_id": "old", "text": text})

    _hold(tmp_path, world, "REQ-001", "RUN-ONE", text)

    assert len(world.comments[CARD_ID]) == 1


def test_different_request_marker_does_not_suppress_new_request_marker(tmp_path):
    world = SimWorld.from_snapshot(load_snapshot())
    world.comments[CARD_ID].append({"action_id": "old", "text": marker("REQ-001", "RUN-OLD", "OP-OLD")})

    _hold(tmp_path, world, "REQ-002", "RUN-NEW", marker("REQ-002", "RUN-NEW", "OP-NEW"))

    assert len(world.comments[CARD_ID]) == 2


def test_partial_hold_repair_keeps_existing_request_marker(tmp_path):
    world = SimWorld.from_snapshot(load_snapshot())
    world.comments[CARD_ID].append({"action_id": "old", "text": marker("REQ-001", "RUN-OLD", "OP-OLD")})

    _hold(tmp_path, world, "REQ-001", "RUN-NEW", marker("REQ-001", "RUN-NEW", "OP-NEW"))

    card = SimTrello(world).get_card(CARD_ID)
    assert card.list_id == HOLD_LIST
    assert LABEL_ID in card.label_ids
    assert len(world.comments[CARD_ID]) == 1
