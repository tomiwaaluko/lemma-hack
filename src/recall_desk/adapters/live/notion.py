from __future__ import annotations

from typing import Any

from recall_desk.adapters.live.http import ApiClient
from recall_desk.domain import NotionBlock, NotionPage


def _plain_text(items: list[dict[str, Any]]) -> str:
    return "".join(str(item.get("plain_text", "")) for item in items)


def _append_unique(urls: list[str], value: str | None) -> None:
    if value and value not in urls:
        urls.append(value)


def parse_page(obj: dict[str, Any]) -> NotionPage:
    title = ""
    for property_value in obj.get("properties", {}).values():
        if property_value.get("type") == "title":
            title = _plain_text(property_value.get("title", []))
            break

    return NotionPage(
        page_id=obj["id"],
        title=title,
        public_url=obj.get("public_url"),
    )


def parse_block(obj: dict[str, Any], page_id: str) -> NotionBlock:
    block_type = obj["type"]
    content = obj.get(block_type, {})
    rich_text = content.get("rich_text", [])
    link_urls: list[str] = []
    for item in rich_text:
        _append_unique(link_urls, item.get("href"))

    if block_type == "bookmark":
        _append_unique(link_urls, content.get("url"))

    image_url: str | None = None
    caption = ""
    if block_type == "image":
        image_url = (content.get("external") or {}).get("url")
        if image_url is None:
            image_url = (content.get("file") or {}).get("url")
        caption = _plain_text(content.get("caption", []))

    return NotionBlock(
        block_id=obj["id"],
        page_id=page_id,
        type=block_type,
        text=_plain_text(rich_text),
        image_url=image_url,
        caption=caption,
        archived=bool(obj.get("archived", False)),
        link_urls=link_urls,
    )


class LiveNotion:
    def __init__(self, client: ApiClient, root_page_id: str) -> None:
        self.client = client
        self.root_page_id = root_page_id

    def list_pages(self) -> list[NotionPage]:
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {
                "filter": {"property": "object", "value": "page"},
                "page_size": 100,
            }
            if cursor is not None:
                body["start_cursor"] = cursor
            response = self.client.request("POST", "/search", json=body, is_write=False)
            pages.extend(response.get("results", []))
            if not response.get("has_more", False):
                break
            cursor = response.get("next_cursor")
            if cursor is None:
                break

        return [parse_page(page) for page in _root_and_descendants(pages, self.root_page_id)]

    def list_image_blocks(self, page_id: str) -> list[NotionBlock]:
        return [block for block in self.get_page_outline(page_id) if block.type == "image"]

    def get_page_outline(self, page_id: str) -> list[NotionBlock]:
        return [parse_block(block, page_id) for block in self._children(page_id)]

    def get_block(self, block_id: str) -> NotionBlock:
        response = self.client.request("GET", f"/blocks/{block_id}", is_write=False)
        parent = response.get("parent", {})
        return parse_block(response, parent.get("page_id", ""))

    def archive_block(self, block_id: str) -> None:
        self.client.request(
            "PATCH",
            f"/blocks/{block_id}",
            json={"archived": True},
            is_write=True,
        )

    def _children(self, block_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params = {"page_size": "100"}
            if cursor is not None:
                params["start_cursor"] = cursor
            response = self.client.request(
                "GET", f"/blocks/{block_id}/children", params=params, is_write=False
            )
            blocks.extend(response.get("results", []))
            if not response.get("has_more", False):
                break
            cursor = response.get("next_cursor")
            if cursor is None:
                break
        return blocks


def _root_and_descendants(pages: list[dict[str, Any]], root_page_id: str) -> list[dict[str, Any]]:
    included = {root_page_id}
    remaining = list(pages)
    selected: list[dict[str, Any]] = []

    while remaining:
        matched = [
            page
            for page in remaining
            if page.get("id") in included
            or (
                page.get("parent", {}).get("type") == "page_id"
                and page.get("parent", {}).get("page_id") in included
            )
        ]
        if not matched:
            break
        selected.extend(matched)
        included.update(page["id"] for page in matched)
        matched_ids = {page["id"] for page in matched}
        remaining = [page for page in remaining if page.get("id") not in matched_ids]

    return selected
