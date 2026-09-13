from __future__ import annotations
from recall_desk.ports import NotFound, Permanent

class SimNotion:
    def __init__(self, world): self.world = world
    def list_pages(self): return list(self.world.pages.values())
    def get_page_outline(self, page_id): return [b for b in self.world.outlines[page_id] if not b.archived]
    def list_image_blocks(self, page_id): return [b for b in self.get_page_outline(page_id) if b.type == "image"]
    def get_block(self, block_id):
        if block_id in self.world.inaccessible_blocks: raise NotFound(404, "missing")
        for blocks in self.world.outlines.values():
            for block in blocks:
                if block.block_id == block_id: return block
        raise NotFound(404, "missing")
    def archive_block(self, block_id):
        block = self.get_block(block_id)
        if block.archived: raise Permanent(400, "already archived")
        for blocks in self.world.outlines.values():
            for index, item in enumerate(blocks):
                if item.block_id == block_id: blocks[index] = item.model_copy(update={"archived": True})
        self.world.effect("archive_block", block_id, {})
