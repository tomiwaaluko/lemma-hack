from __future__ import annotations
from recall_desk.domain import TrelloComment
from recall_desk.ports import NotFound, Permanent

class SimTrello:
    def __init__(self, world): self.world = world
    def list_lists(self):
        from recall_desk.domain import TrelloList
        return [TrelloList(**item) for item in self.world.lists]
    def list_labels(self): return dict(self.world.labels)
    def list_cards(self): return list(self.world.cards.values())
    def get_card(self, card_id):
        if card_id in self.world.inaccessible_cards or card_id not in self.world.cards: raise NotFound(404, "missing")
        return self.world.cards[card_id]
    def list_comments(self, card_id): return [TrelloComment(**item) for item in self.world.comments.get(card_id, [])]
    def move_card(self, card_id, list_id): self.world.set_card_list_direct(card_id, list_id); self.world.effect("move_card", card_id, {"list_id": list_id})
    def add_label(self, card_id, label_id):
        card=self.get_card(card_id)
        if label_id in card.label_ids: raise Permanent(400, "label present")
        self.world.cards[card_id]=card.model_copy(update={"label_ids": card.label_ids+[label_id]}); self.world.effect("add_label", card_id, {"label_id":label_id})
    def add_comment(self, card_id, text):
        action_id=f"sim-comment-{len(self.world.comments.get(card_id, []))+1}"; self.world.comments.setdefault(card_id, []).append({"action_id":action_id,"text":text}); self.world.effect("add_comment",card_id,{"text":text})
