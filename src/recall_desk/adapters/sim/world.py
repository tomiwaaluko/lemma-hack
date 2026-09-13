from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from recall_desk.domain import NotionBlock, NotionPage, TrelloCard, semantic_hash
from recall_desk.snapshot import Snapshot


@dataclass(frozen=True)
class Effect:
    action: str
    target_id: str
    params: dict[str, Any]


class SimWorld:
    def __init__(self, snap: Snapshot) -> None:
        self.snap = snap
        self.pages = {p["page_id"]: NotionPage(**p) for p in snap.pages}
        self.outlines = {key: [NotionBlock(**block) for block in value] for key, value in snap.outlines.items()}
        self.cards = {card["card_id"]: TrelloCard(**card) for card in snap.cards}
        self.comments = {key: list(value) for key, value in snap.comments.items()}
        self.registry = list(snap.registry)
        self.request, self.asset, self.variants = dict(snap.request), dict(snap.asset), list(snap.variants)
        self.lists, self.labels = list(snap.lists), dict(snap.labels)
        self.effects: list[Effect] = []
        self.crash_after_apply: Callable[[str], None] | None = None
        self.inaccessible_blocks: set[str] = set()
        self.inaccessible_cards: set[str] = set()

    @classmethod
    def from_snapshot(cls, snap: Snapshot, overlay: dict[str, Any] | None = None) -> "SimWorld":
        world = cls(snap)
        overlay = overlay or {}
        world.inaccessible_blocks = set(overlay.get("inaccessible_blocks", []))
        world.inaccessible_cards = set(overlay.get("inaccessible_cards", []))
        return world

    def effect(self, action: str, target_id: str, params: dict[str, Any]) -> None:
        self.effects.append(Effect(action, target_id, params))
        if self.crash_after_apply: self.crash_after_apply(f"{action}:{target_id}")

    def view(self) -> dict[str, Any]:
        return {"outlines": {key: [item.model_dump(mode="json") for item in value] for key, value in self.outlines.items()},
                "cards": {key: value.model_dump(mode="json") for key, value in self.cards.items()},
                "comments": self.comments, "registry": self.registry, "request": self.request, "asset": self.asset}

    def set_card_list_direct(self, card_id: str, list_id: str) -> None:
        self.cards[card_id] = self.cards[card_id].model_copy(update={"list_id": list_id})
    def set_caption_direct(self, block_id: str, caption: str) -> None:
        for blocks in self.outlines.values():
            for index, block in enumerate(blocks):
                if block.block_id == block_id: blocks[index] = block.model_copy(update={"caption": caption})
    def set_desc_direct(self, card_id: str, desc: str) -> None:
        self.cards[card_id] = self.cards[card_id].model_copy(update={"desc": desc})
