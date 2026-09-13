from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from recall_desk.adapters.live.http import ApiClient
from recall_desk.domain import TrelloAttachment, TrelloCard, TrelloComment, TrelloList


CARD_FIELDS = "name,desc,idList,idLabels,due"
ATTACHMENT_FIELDS = "name,url,fileName"


def parse_list(obj: dict[str, Any]) -> TrelloList:
    return TrelloList(list_id=obj["id"], name=obj["name"])


def parse_card(obj: dict[str, Any]) -> TrelloCard:
    attachments = [
        TrelloAttachment(
            attachment_id=attachment["id"],
            filename=_attachment_filename(attachment),
            url=attachment["url"],
        )
        for attachment in obj.get("attachments", [])
    ]
    return TrelloCard(
        card_id=obj["id"],
        name=obj["name"],
        list_id=obj["idList"],
        desc=obj.get("desc", ""),
        label_ids=obj.get("idLabels", []),
        due=obj.get("due"),
        attachments=attachments,
    )


def parse_comment(obj: dict[str, Any]) -> TrelloComment:
    return TrelloComment(action_id=obj["id"], text=obj.get("data", {}).get("text", ""))


def _attachment_filename(attachment: dict[str, Any]) -> str:
    file_name = attachment.get("fileName")
    if file_name:
        return file_name
    return urlsplit(attachment["url"]).path.rsplit("/", maxsplit=1)[-1]


class LiveTrello:
    def __init__(self, client: ApiClient, board_id: str) -> None:
        self.client = client
        self.board_id = board_id

    def list_lists(self) -> list[TrelloList]:
        response = self.client.request("GET", f"/boards/{self.board_id}/lists", is_write=False)
        return [parse_list(item) for item in response]

    def list_labels(self) -> dict[str, str]:
        response = self.client.request("GET", f"/boards/{self.board_id}/labels", is_write=False)
        return {item["id"]: item["name"] for item in response}

    def list_cards(self) -> list[TrelloCard]:
        response = self.client.request(
            "GET",
            f"/boards/{self.board_id}/cards",
            params=_card_params(),
            is_write=False,
        )
        return [parse_card(item) for item in response]

    def get_card(self, card_id: str) -> TrelloCard:
        response = self.client.request(
            "GET", f"/cards/{card_id}", params=_card_params(), is_write=False
        )
        return parse_card(response)

    def list_comments(self, card_id: str) -> list[TrelloComment]:
        response = self.client.request(
            "GET",
            f"/cards/{card_id}/actions",
            params={"filter": "commentCard"},
            is_write=False,
        )
        return [parse_comment(item) for item in response]

    def move_card(self, card_id: str, list_id: str) -> None:
        self.client.request(
            "PUT", f"/cards/{card_id}", params={"idList": list_id}, is_write=True
        )

    def add_label(self, card_id: str, label_id: str) -> None:
        self.client.request(
            "POST",
            f"/cards/{card_id}/idLabels",
            params={"value": label_id},
            is_write=True,
        )

    def add_comment(self, card_id: str, text: str) -> None:
        self.client.request(
            "POST",
            f"/cards/{card_id}/actions/comments",
            params={"text": text},
            is_write=True,
        )


def _card_params() -> dict[str, str]:
    return {
        "attachments": "true",
        "attachment_fields": ATTACHMENT_FIELDS,
        "fields": CARD_FIELDS,
    }
