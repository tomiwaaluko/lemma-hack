from __future__ import annotations
from recall_desk.domain import Outcome
def verify_notion_removed(notion,block_id): return notion.get_block(block_id).archived
def verify_trello_hold(trello,card_id,list_id,label_id,request_id):
    card=trello.get_card(card_id); return card.list_id==list_id and label_id in card.label_ids and any(f'[recall-desk {request_id} ' in c.text for c in trello.list_comments(card_id))
