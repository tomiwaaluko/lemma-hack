from __future__ import annotations

from typing import Any, Protocol

from recall_desk.domain import (
    Asset,
    NotionBlock,
    NotionPage,
    PermissionRequest,
    RegistryRow,
    TrelloCard,
    TrelloComment,
    TrelloList,
    Variant,
)


class AdapterError(Exception):
    """A known failure at an external-adapter boundary."""


class Transient(AdapterError):
    def __init__(self, retry_after: float | None, before_send: bool) -> None:
        self.retry_after = retry_after
        self.before_send = before_send
        super().__init__(f"transient adapter failure (before_send={before_send})")


class UnknownOutcome(AdapterError):
    """A write may have reached the external service, but its result is unknown."""


class Permanent(AdapterError):
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"permanent adapter failure ({status})")


class NotFound(Permanent):
    """A known HTTP 404 rejection."""


class SimulatedCrash(BaseException):
    def __init__(self, label: str) -> None:
        self.label = label
        super().__init__(label)


class NotionPort(Protocol):
    def list_pages(self) -> list[NotionPage]: ...

    def list_image_blocks(self, page_id: str) -> list[NotionBlock]: ...

    def get_page_outline(self, page_id: str) -> list[NotionBlock]: ...

    def get_block(self, block_id: str) -> NotionBlock: ...

    def archive_block(self, block_id: str) -> None: ...


class TrelloPort(Protocol):
    def list_lists(self) -> list[TrelloList]: ...

    def list_labels(self) -> dict[str, str]: ...

    def list_cards(self) -> list[TrelloCard]: ...

    def get_card(self, card_id: str) -> TrelloCard: ...

    def list_comments(self, card_id: str) -> list[TrelloComment]: ...

    def move_card(self, card_id: str, list_id: str) -> None: ...

    def add_label(self, card_id: str, label_id: str) -> None: ...

    def add_comment(self, card_id: str, text: str) -> None: ...


class AirtablePort(Protocol):
    def get_request(self, request_id: str) -> PermissionRequest: ...

    def get_asset(self, asset_id: str) -> Asset: ...

    def list_variants(self, asset_id: str) -> list[Variant]: ...

    def list_occurrences(self, asset_id: str) -> list[RegistryRow]: ...

    def read_occurrence_fields(self, keys: list[str]) -> dict[str, dict[str, Any]]: ...

    def read_request_fields(self, request_id: str) -> dict[str, Any]: ...

    def upsert_occurrences(self, rows: list[dict[str, Any]]) -> None: ...

    def update_request(self, request_id: str, fields: dict[str, Any]) -> None: ...

    def append_restriction(self, asset_id: str, text: str) -> None: ...


class DemoResetPort(Protocol):
    def restore_block(self, block_id: str) -> None: ...

    def restore_card_list(self, card_id: str, list_id: str) -> None: ...

    def remove_label(self, card_id: str, label_id: str) -> None: ...

    def delete_marked_comments(
        self, card_id: str, marker_prefix: str = "[recall-desk"
    ) -> int: ...

    def airtable_cleanup(
        self, request_id: str, asset_id: str, registered_keys: list[str]
    ) -> None: ...
