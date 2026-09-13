from __future__ import annotations
class SimReset:
    def __init__(self, world): self.world=world
    def restore_block(self, block_id):
        for blocks in self.world.outlines.values():
            for i,b in enumerate(blocks):
                if b.block_id==block_id: blocks[i]=b.model_copy(update={'archived':False})
    def restore_card_list(self, card_id, list_id): self.world.set_card_list_direct(card_id,list_id)
    def remove_label(self, card_id, label_id):
        card=self.world.cards[card_id]; self.world.cards[card_id]=card.model_copy(update={'label_ids':[x for x in card.label_ids if x!=label_id]})
    def delete_marked_comments(self, card_id, marker_prefix='[recall-desk'):
        old=self.world.comments.get(card_id,[]); self.world.comments[card_id]=[x for x in old if not x['text'].startswith(marker_prefix)]; return len(old)-len(self.world.comments[card_id])
    def airtable_cleanup(self, request_id, asset_id, registered_keys):
        self.world.registry=[row for row in self.world.registry if row.get('source')!='Discovered']
        for row in self.world.registry: row.update({'outcome':None,'last_run_id':None})
        self.world.asset['restrictions']=''
