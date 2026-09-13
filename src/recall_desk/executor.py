from __future__ import annotations
from recall_desk.domain import OpState

class Executor:
    def __init__(self,journal,notion,trello): self.journal,self.notion,self.trello=journal,notion,trello
    def archive(self,op_id,block_id):
        self.journal.transition(op_id,OpState.SENT)
        try: self.notion.archive_block(block_id)
        except Exception:
            if not self.notion.get_block(block_id).archived: self.journal.transition(op_id,OpState.FAILED); raise
        if not self.notion.get_block(block_id).archived: self.journal.transition(op_id,OpState.VERIFY_FAILED); raise RuntimeError('Notion archive unverified')
        self.journal.transition(op_id,OpState.VERIFIED)
    def hold(self,ops,card_id,hold_list,label_id,comment):
        card=self.trello.get_card(card_id)
        if card.list_id!=hold_list:
            self.journal.transition(ops[0],OpState.SENT);self.trello.move_card(card_id,hold_list);self.journal.transition(ops[0],OpState.VERIFIED)
        if label_id not in self.trello.get_card(card_id).label_ids:
            self.journal.transition(ops[1],OpState.SENT);self.trello.add_label(card_id,label_id);self.journal.transition(ops[1],OpState.VERIFIED)
        if not any(comment.split(']')[0]+']' in item.text for item in self.trello.list_comments(card_id)):
            self.journal.transition(ops[2],OpState.SENT);self.trello.add_comment(card_id,comment);self.journal.transition(ops[2],OpState.VERIFIED)
        card=self.trello.get_card(card_id)
        if card.list_id!=hold_list or label_id not in card.label_ids or not any(comment.split(']')[0]+']' in item.text for item in self.trello.list_comments(card_id)): raise RuntimeError('Trello hold unverified')
