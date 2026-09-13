from __future__ import annotations

from dataclasses import dataclass
import pytest

import recall_desk.orchestrator as orchestrator
from recall_desk.domain import (
    ActionType,
    FinalResult,
    NotionBlock,
    NotionPage,
    Op,
    OpState,
    PermissionRequest,
    TrelloCard,
    TrelloComment,
    Variant,
)
from recall_desk.executor import Executor
from recall_desk.journal import Journal
from recall_desk.ports import UnknownOutcome


def _op(op_id: str, action: ActionType, *, target_id: str = "target") -> Op:
    return Op(
        op_id=op_id,
        run_id="RUN-001",
        request_id="REQ-001",
        occurrence_key="notion:block:block-1",
        action=action,
        target_id=target_id,
        params={},
        precondition_hash=None,
        step=1,
    )


def _state(journal: Journal, op_id: str) -> str:
    row = journal.db.execute("select state from ops where op_id = ?", (op_id,)).fetchone()
    assert row is not None
    return row["state"]


class RecordingNotion:
    def __init__(self, journal: Journal | None = None, op_id: str | None = None) -> None:
        self.journal = journal
        self.op_id = op_id
        self.block = NotionBlock(
            block_id="block-1",
            page_id="page-1",
            type="image",
            text="",
            image_url="https://assets.example.test/asset.jpg",
            caption="Volunteer flyer",
            archived=False,
            link_urls=[],
        )
        self.archive_calls = 0
        self.state_at_archive: str | None = None
        self.raise_after_apply = False

    def list_pages(self) -> list[NotionPage]:
        return [NotionPage(page_id="page-1", title="Volunteer With Us", public_url=None)]

    def list_image_blocks(self, page_id: str) -> list[NotionBlock]:
        return [] if self.block.archived else [self.block]

    def get_block(self, block_id: str) -> NotionBlock:
        assert block_id == self.block.block_id
        return self.block

    def archive_block(self, block_id: str) -> None:
        assert block_id == self.block.block_id
        self.archive_calls += 1
        if self.journal is not None and self.op_id is not None:
            self.state_at_archive = _state(self.journal, self.op_id)
        self.block = self.block.model_copy(update={"archived": True})
        if self.raise_after_apply:
            raise UnknownOutcome()


class RecordingTrello:
    def __init__(self) -> None:
        self.card = TrelloCard(
            card_id="card-1",
            name="Oct Volunteer Drive: Instagram carousel",
            list_id="scheduled",
            desc="Volunteer recruitment",
            label_ids=[],
            due=None,
            attachments=[],
        )
        self.comments: list[TrelloComment] = []
        self.move_calls = 0
        self.label_calls = 0
        self.comment_calls = 0
        self.fail_comment = False

    def get_card(self, card_id: str) -> TrelloCard:
        assert card_id == self.card.card_id
        return self.card

    def list_comments(self, card_id: str) -> list[TrelloComment]:
        assert card_id == self.card.card_id
        return list(self.comments)

    def move_card(self, card_id: str, list_id: str) -> None:
        assert card_id == self.card.card_id
        self.move_calls += 1
        self.card = self.card.model_copy(update={"list_id": list_id})

    def add_label(self, card_id: str, label_id: str) -> None:
        assert card_id == self.card.card_id
        self.label_calls += 1
        self.card = self.card.model_copy(update={"label_ids": [*self.card.label_ids, label_id]})

    def add_comment(self, card_id: str, text: str) -> None:
        assert card_id == self.card.card_id
        self.comment_calls += 1
        if self.fail_comment:
            raise RuntimeError("comment endpoint unavailable")
        self.comments.append(TrelloComment(action_id=f"comment-{self.comment_calls}", text=text))


class ReadFailingAirtable:
    def get_request(self, request_id: str) -> PermissionRequest:
        return PermissionRequest(request_id=request_id, asset_id="AST-001", request_text="withdraw volunteers")

    def list_variants(self, asset_id: str) -> list[Variant]:
        return [Variant(variant_id="VAR-001", asset_id=asset_id, filename="asset.jpg", canonical_url="https://assets.example.test/asset.jpg")]

    def list_occurrences(self, asset_id: str):
        raise RuntimeError("Airtable occurrence read unavailable")


class RecordingAirtable:
    def __init__(self, *, fail_update: bool = False) -> None:
        self.fail_update = fail_update
        self.update_calls: list[dict[str, object]] = []

    def get_request(self, request_id: str) -> PermissionRequest:
        return PermissionRequest(request_id=request_id, asset_id="AST-001", request_text="withdraw volunteers")

    def list_variants(self, asset_id: str) -> list[Variant]:
        return [Variant(variant_id="VAR-001", asset_id=asset_id, filename="asset.jpg", canonical_url="https://assets.example.test/asset.jpg")]

    def list_occurrences(self, asset_id: str) -> list[object]:
        return []

    def update_request(self, request_id: str, fields: dict[str, object]) -> None:
        self.update_calls.append(fields)
        if self.fail_update:
            raise RuntimeError("Airtable request update unavailable")


class EmptyTrello:
    def list_cards(self) -> list[TrelloCard]:
        return []


@dataclass(frozen=True)
class RunSettings:
    asset_id: str = "AST-001"
    ids: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.ids is None:
            object.__setattr__(self, "ids", {"list_rights_hold": "hold", "label_rights_hold": "label"})


def test_sent_is_durable_before_notion_archive_write(tmp_path):
    journal = Journal(tmp_path / "recall.db")
    op = _op("archive-1", ActionType.ARCHIVE_BLOCK, target_id="block-1")
    journal.add_ops([op])
    notion = RecordingNotion(journal, op.op_id)

    Executor(journal, notion, None).archive(op.op_id, "block-1")

    assert notion.state_at_archive == OpState.SENT
    assert _state(journal, op.op_id) == OpState.VERIFIED


def test_notion_unknown_outcome_reads_back_applied_archive_without_retry(tmp_path):
    journal = Journal(tmp_path / "recall.db")
    op = _op("archive-unknown", ActionType.ARCHIVE_BLOCK, target_id="block-1")
    journal.add_ops([op])
    notion = RecordingNotion()
    notion.raise_after_apply = True

    Executor(journal, notion, None).archive(op.op_id, "block-1")

    assert notion.block.archived is True
    assert notion.archive_calls == 1
    assert _state(journal, op.op_id) == OpState.VERIFIED


def test_trello_comment_failure_keeps_card_moved_and_labeled(tmp_path):
    journal = Journal(tmp_path / "recall.db")
    ops = [
        _op("move-1", ActionType.MOVE_CARD, target_id="card-1"),
        _op("label-1", ActionType.ADD_LABEL, target_id="card-1"),
        _op("comment-1", ActionType.ADD_COMMENT, target_id="card-1"),
    ]
    journal.add_ops(ops)
    trello = RecordingTrello()
    trello.fail_comment = True

    with pytest.raises(RuntimeError, match="comment endpoint unavailable"):
        Executor(journal, None, trello).hold(
            [op.op_id for op in ops], "card-1", "hold", "label", "[recall-desk REQ-001 RUN-001 comment-1] Held"
        )

    assert trello.card.list_id == "hold"
    assert trello.card.label_ids == ["label"]
    assert trello.comments == []
    assert [_state(journal, op.op_id) for op in ops] == [OpState.VERIFIED, OpState.VERIFIED, OpState.SENT]


def test_trello_existing_exact_request_marker_prevents_duplicate_comment(tmp_path):
    journal = Journal(tmp_path / "recall.db")
    ops = [
        _op("move-2", ActionType.MOVE_CARD, target_id="card-1"),
        _op("label-2", ActionType.ADD_LABEL, target_id="card-1"),
        _op("comment-2", ActionType.ADD_COMMENT, target_id="card-1"),
    ]
    journal.add_ops(ops)
    trello = RecordingTrello()
    trello.card = trello.card.model_copy(update={"list_id": "hold", "label_ids": ["label"]})
    marker = "[recall-desk REQ-001 RUN-001 comment-2]"
    trello.comments = [TrelloComment(action_id="existing", text=f"{marker} Held")]

    Executor(journal, None, trello).hold([op.op_id for op in ops], "card-1", "hold", "label", f"{marker} Held")

    assert trello.comment_calls == 0
    assert [comment.text for comment in trello.comments] == [f"{marker} Held"]


def test_critical_airtable_initial_read_failure_prevents_content_mutation(monkeypatch, tmp_path):
    monkeypatch.setattr(orchestrator, "scope_smoke", lambda request_text: None)
    notion = RecordingNotion()

    with pytest.raises(RuntimeError, match="occurrence read unavailable"):
        orchestrator.run_req001(RunSettings(), notion, EmptyTrello(), ReadFailingAirtable(), Journal(tmp_path / "recall.db"))

    assert notion.archive_calls == 0


def test_registry_bookkeeping_failure_keeps_content_result_and_counts(monkeypatch, tmp_path):
    monkeypatch.setattr(orchestrator, "scope_smoke", lambda request_text: None)
    airtable = RecordingAirtable(fail_update=True)
    notion = RecordingNotion()

    summary = orchestrator.run_req001(RunSettings(), notion, EmptyTrello(), airtable, Journal(tmp_path / "recall.db"))

    assert notion.block.archived is True
    assert summary.flags.registry_sync_failed is True
    assert summary.final_result == FinalResult.PARTIAL
    assert summary.counts == {
        "Removed": 1,
        "Held": 0,
        "Preserved": 0,
        "Uncertain": 0,
        "Manual": 0,
        "Other follow-up": 0,
        "Failed": 0,
    }
    assert airtable.update_calls[0]["Removed"] == 1


def test_rerun_skips_already_archived_content_without_duplicate_write(monkeypatch, tmp_path):
    monkeypatch.setattr(orchestrator, "scope_smoke", lambda request_text: None)
    notion = RecordingNotion()
    airtable = RecordingAirtable()

    first = orchestrator.run_req001(RunSettings(), notion, EmptyTrello(), airtable, Journal(tmp_path / "first.db"))
    second = orchestrator.run_req001(RunSettings(), notion, EmptyTrello(), airtable, Journal(tmp_path / "second.db"))

    assert first.counts["Removed"] == 1
    assert second.counts["Removed"] == 0
    assert notion.archive_calls == 1
