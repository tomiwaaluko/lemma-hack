from __future__ import annotations

from typing import Any

from recall_desk.adapters.live.http import ApiClient


class LiveReset:
    """Demo-only restoration capability; never supplied to runtime execution."""

    def __init__(self, notion: ApiClient, trello: ApiClient, airtable: ApiClient) -> None:
        self.notion = notion
        self.trello = trello
        self.airtable = airtable

    def restore_block(self, block_id: str) -> None:
        self.notion.request("PATCH", f"/blocks/{block_id}", json={"archived": False}, is_write=True)

    def restore_card_list(self, card_id: str, list_id: str) -> None:
        self.trello.request("PUT", f"/cards/{card_id}", params={"idList": list_id}, is_write=True)

    def remove_label(self, card_id: str, label_id: str) -> None:
        self.trello.request("DELETE", f"/cards/{card_id}/idLabels/{label_id}", is_write=True)

    def delete_marked_comments(self, card_id: str, marker_prefix: str = "[recall-desk") -> int:
        actions = self.trello.request(
            "GET", f"/cards/{card_id}/actions", params={"filter": "commentCard"}, is_write=False
        )
        matches = [item for item in actions if item.get("data", {}).get("text", "").startswith(marker_prefix)]
        for action in matches:
            self.trello.request("DELETE", f"/actions/{action['id']}", is_write=True)
        return len(matches)

    def airtable_cleanup(self, request_id: str, asset_id: str, registered_keys: list[str]) -> None:
        # The concrete table cleanup is performed through normalized field reads to stay schema-safe.
        records = self.airtable.request("GET", "/Occurrences", is_write=False).get("records", [])
        discovered = [record["id"] for record in records if record.get("fields", {}).get("Source") == "Discovered"]
        if discovered:
            self.airtable.request("DELETE", "/Occurrences", params={"records[]": discovered[0]}, is_write=True)
        clear = {"Verdict": None, "Outcome": None, "Rationale": None, "Evidence quotes": None,
                 "Missing or conflicting evidence": None, "Last run ID": None, "Last verified at": None}
        for record in records:
            if record.get("fields", {}).get("Occurrence key") in registered_keys:
                self.airtable.request("PATCH", f"/Occurrences/{record['id']}", json={"fields": clear}, is_write=True)
        request_rows = self.airtable.request(
            "GET", "/Permission Changes", params={"filterByFormula": "{Request ID}='" + request_id + "'"}, is_write=False
        ).get("records", [])
        if request_rows:
            request_clear = {key: None for key in (
                "Interpreted scope", "Scope approved", "Approved by", "Approved at", "Execution state",
                "Final result", "Removed", "Held", "Preserved", "Uncertain", "Manual", "Other follow-up",
                "Failed", "Report summary", "Last run ID",
            )}
            self.airtable.request("PATCH", f"/Permission Changes/{request_rows[0]['id']}", json={"fields": request_clear}, is_write=True)
        asset_rows = self.airtable.request(
            "GET", "/Assets", params={"filterByFormula": "{Asset ID}='" + asset_id + "'"}, is_write=False
        ).get("records", [])
        if asset_rows:
            self.airtable.request("PATCH", f"/Assets/{asset_rows[0]['id']}", json={"fields": {"Restrictions": None}}, is_write=True)
