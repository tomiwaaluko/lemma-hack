from __future__ import annotations
from recall_desk.domain import OpState
from recall_desk.policy import has_request_marker
from recall_desk.ports import UnknownOutcome

class Executor:
    def __init__(self,journal,notion,trello): self.journal,self.notion,self.trello=journal,notion,trello
    def _write(self,op_id,write,confirmed):
        self.journal.transition(op_id,OpState.PRECHECK_OK)
        self.journal.transition(op_id,OpState.SENT)
        try: write()
        except Exception as error:
            if not confirmed():
                self.journal.transition(op_id,OpState.UNKNOWN if isinstance(error, UnknownOutcome) else OpState.FAILED)
                raise
        if not confirmed(): self.journal.transition(op_id,OpState.VERIFY_FAILED); raise RuntimeError('write unverified')
        self.journal.transition(op_id,OpState.VERIFIED)
    def archive(self,op_id,block_id):
        confirmed=lambda: self.notion.get_block(block_id).archived
        if confirmed(): self.journal.transition(op_id,OpState.VERIFIED); return
        self._write(op_id,lambda: self.notion.archive_block(block_id),confirmed)
    def hold(self,ops,card_id,hold_list,label_id,request_id,comment):
        card=self.trello.get_card(card_id)
        if card.list_id!=hold_list:
            self._write(ops[0],lambda: self.trello.move_card(card_id,hold_list),lambda: self.trello.get_card(card_id).list_id==hold_list)
        if label_id not in self.trello.get_card(card_id).label_ids:
            self._write(ops[1],lambda: self.trello.add_label(card_id,label_id),lambda: label_id in self.trello.get_card(card_id).label_ids)
        if not has_request_marker(self.trello.list_comments(card_id),request_id):
            self._write(ops[2],lambda: self.trello.add_comment(card_id,comment),lambda: any(comment.split(']')[0]+']' in item.text for item in self.trello.list_comments(card_id)))
        card=self.trello.get_card(card_id)
        if card.list_id!=hold_list or label_id not in card.label_ids or not has_request_marker(self.trello.list_comments(card_id),request_id): raise RuntimeError('Trello hold unverified')
