from __future__ import annotations

from typing import Any

from recall_desk.adapters.live.http import ApiClient
from recall_desk.domain import Asset, Outcome, PermissionRequest, RegistryRow, System, Variant


class LiveAirtable:
    """Normalized Airtable runtime adapter; the ApiClient base URL includes the base ID."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self._variant_record_to_id: dict[str, str] = {}
        self._request_records: dict[str, str] = {}
        self._asset_records: dict[str, str] = {}

    def _records(self, table: str, formula: str | None = None) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        params = {} if formula is None else {"filterByFormula": formula}
        while True:
            payload = self.client.request("GET", f"/{table}", params=params or None, is_write=False)
            records.extend(payload.get("records", []))
            cursor = payload.get("offset")
            if not cursor:
                return records
            params = {**params, "offset": cursor}

    def get_request(self, request_id: str) -> PermissionRequest:
        fields = self.read_request_fields(request_id)
        asset = fields.get("Asset", [])
        asset_id = asset[0] if isinstance(asset, list) and asset else str(asset)
        if asset_id not in self._asset_records.values():
            asset_record = self.client.request("GET", f"/Assets/{asset_id}", is_write=False)
            asset_id = str(asset_record["fields"]["Asset ID"])
            self._asset_records[asset_id] = asset_record["id"]
        else:
            asset_id = next(key for key, record_id in self._asset_records.items() if record_id == asset_id)
        return PermissionRequest(
            request_id=str(fields["Request ID"]), asset_id=asset_id, request_text=str(fields["Request text"])
        )

    def get_asset(self, asset_id: str) -> Asset:
        records = self._records("Assets", "{Asset ID}='" + asset_id.replace("'", "\\'") + "'")
        record = records[0]
        self._asset_records[asset_id] = record["id"]
        fields = record["fields"]
        return Asset(
            asset_id=str(fields["Asset ID"]),
            title=str(fields.get("Title", "")),
            consent_terms=str(fields.get("Consent terms", "")),
            restrictions=str(fields.get("Restrictions", "")),
        )

    def list_variants(self, asset_id: str) -> list[Variant]:
        asset = self.get_asset(asset_id)
        asset_record_id = self._asset_records[asset.asset_id]
        variants: list[Variant] = []
        for record in self._records("Variants"):
            fields = record["fields"]
            if asset_record_id not in fields.get("Asset", []):
                continue
            variant = Variant(
                variant_id=str(fields["Variant ID"]),
                asset_id=asset.asset_id,
                filename=str(fields["Filename"]),
                canonical_url=str(fields["Canonical URL"]),
            )
            variants.append(variant)
            self._variant_record_to_id[record["id"]] = variant.variant_id
        return variants

    def list_occurrences(self, asset_id: str) -> list[RegistryRow]:
        variants = self.list_variants(asset_id)
        allowed = {variant.variant_id for variant in variants}
        rows: list[RegistryRow] = []
        for record in self._records("Occurrences"):
            fields = record["fields"]
            linked = fields.get("Variant", [])
            variant_id = self._variant_record_to_id.get(linked[0]) if linked else None
            if variant_id not in allowed:
                continue
            value = fields.get("Outcome")
            rows.append(
                RegistryRow(
                    occurrence_key=str(fields["Occurrence key"]),
                    variant_id=variant_id,
                    system=System(fields["System"]),
                    location_label=str(fields.get("Location label", "")),
                    location_url=fields.get("Location URL"),
                    source=fields.get("Source", "Registered"),
                    outcome=Outcome(value) if value else None,
                    last_run_id=fields.get("Last run ID"),
                )
            )
        return rows

    def read_occurrence_fields(self, keys: list[str]) -> dict[str, dict[str, Any]]:
        wanted = set(keys)
        return {
            str(record["fields"]["Occurrence key"]): dict(record["fields"])
            for record in self._records("Occurrences")
            if record["fields"].get("Occurrence key") in wanted
        }

    def read_request_fields(self, request_id: str) -> dict[str, Any]:
        records = self._records("Permission Changes", "{Request ID}='" + request_id.replace("'", "\\'") + "'")
        record = records[0]
        self._request_records[request_id] = record["id"]
        return dict(record["fields"])

    def upsert_occurrences(self, rows: list[dict[str, Any]]) -> None:
        for start in range(0, len(rows), 10):
            self.client.request(
                "PATCH",
                "/Occurrences",
                json={
                    "records": [{"fields": row} for row in rows[start : start + 10]],
                    "performUpsert": {"fieldsToMergeOn": ["Occurrence key"]},
                },
                is_write=True,
            )

    def update_request(self, request_id: str, fields: dict[str, Any]) -> None:
        record_id = self._request_records.get(request_id)
        if record_id is None:
            self.read_request_fields(request_id)
            record_id = self._request_records[request_id]
        self.client.request(
            "PATCH", f"/Permission Changes/{record_id}", json={"fields": fields}, is_write=True
        )

    def append_restriction(self, asset_id: str, text: str) -> None:
        asset = self.get_asset(asset_id)
        if text in asset.restrictions:
            return
        restrictions = "\n".join(part for part in (asset.restrictions, text) if part)
        self.client.request(
            "PATCH",
            f"/Assets/{self._asset_records[asset_id]}",
            json={"fields": {"Restrictions": restrictions}},
            is_write=True,
        )
