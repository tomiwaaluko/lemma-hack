from __future__ import annotations
from recall_desk.domain import Asset, Outcome, PermissionRequest, RegistryRow, Variant

class SimAirtable:
    def __init__(self, world): self.world=world
    def get_request(self, request_id): return PermissionRequest(**self.world.request)
    def get_asset(self, asset_id): return Asset(**self.world.asset)
    def list_variants(self, asset_id): return [Variant(**v) for v in self.world.variants]
    def list_occurrences(self, asset_id): return [RegistryRow(**row) for row in self.world.registry]
    def read_occurrence_fields(self, keys): return {r['occurrence_key']:r for r in self.world.registry if r['occurrence_key'] in keys}
    def read_request_fields(self, request_id): return dict(self.world.request)
    def upsert_occurrences(self, rows):
        found={r['occurrence_key']:i for i,r in enumerate(self.world.registry)}
        for row in rows:
            if row['Occurrence key'] in found: self.world.registry[found[row['Occurrence key']]].update(row)
            else: self.world.registry.append(row)
        self.world.effect('upsert_occurrences','Occurrences',{'count':len(rows)})
    def update_request(self, request_id, fields): self.world.request.update(fields); self.world.effect('update_request',request_id,fields)
    def append_restriction(self, asset_id, text):
        if text in self.world.asset.get('restrictions',''): return
        self.world.asset['restrictions']='\n'.join(x for x in [self.world.asset.get('restrictions',''),text] if x); self.world.effect('append_restriction',asset_id,{'text':text})
