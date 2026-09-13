from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from recall_desk.domain import semantic_hash


@dataclass
class Snapshot:
    pages: list[dict[str, Any]]
    outlines: dict[str, list[dict[str, Any]]]
    lists: list[dict[str, Any]]
    labels: dict[str, str]
    cards: list[dict[str, Any]]
    comments: dict[str, list[dict[str, Any]]]
    request: dict[str, Any]
    asset: dict[str, Any]
    variants: list[dict[str, Any]]
    registry: list[dict[str, Any]]
    hashes: dict[str, str]

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def page_hash_view(page: Any, outline: list[Any]) -> dict[str, Any]:
    return {"page": _dump(page), "outline": [_dump(block) for block in outline]}


def card_hash_view(card: Any, comments: list[Any]) -> dict[str, Any]:
    return {"card": _dump(card), "comments": [_dump(comment) for comment in comments]}


def _dump(value: Any) -> dict[str, Any]:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else dict(value)


def take_snapshot(notion, trello, airtable, settings) -> Snapshot:
    pages = [page for page in notion.list_pages() if page.title != "Riverbend Website"]
    outlines = {page.page_id: notion.get_page_outline(page.page_id) for page in pages}
    lists, labels, cards = trello.list_lists(), trello.list_labels(), trello.list_cards()
    comments = {card.card_id: trello.list_comments(card.card_id) for card in cards}
    request = airtable.get_request(settings.request_id)
    asset = airtable.get_asset(settings.asset_id)
    variants = airtable.list_variants(settings.asset_id)
    registry = airtable.list_occurrences(settings.asset_id)
    hashes = {f"page:{page.page_id}": semantic_hash(page_hash_view(page, outlines[page.page_id])) for page in pages}
    hashes.update({f"card:{card.card_id}": semantic_hash(card_hash_view(card, comments[card.card_id])) for card in cards})
    return Snapshot([_dump(page) for page in pages], {key: [_dump(v) for v in value] for key, value in outlines.items()},
                    [_dump(value) for value in lists], labels, [_dump(value) for value in cards],
                    {key: [_dump(value) for value in values] for key, values in comments.items()}, _dump(request), _dump(asset),
                    [_dump(value) for value in variants], [_dump(value) for value in registry], hashes)


def build_ids(snap: Snapshot) -> dict[str, str]:
    page_names = {"Volunteer With Us": "N1", "2024 Spring Workshop Recap": "N2", "Annual Impact Report 2024": "N3"}
    result: dict[str, str] = {}
    seen: set[str] = set()
    for page in snap.pages:
        title = page["title"]
        if title in seen:
            raise ValueError(f"duplicate page title: {title}")
        seen.add(title)
        if title in page_names:
            result[page_names[title]] = page["page_id"]
        if title == "Riverbend Website":
            result["ROOT"] = page["page_id"]
    next_page = 4
    for page in snap.pages:
        if page["title"] == "Riverbend Website" or page["page_id"] in result.values():
            continue
        result[f"N{next_page}"] = page["page_id"]
        next_page += 1
    for logical, page_id in [("N1", result.get("N1")), ("N2", result.get("N2")), ("N3", result.get("N3"))]:
        if page_id:
            image = next((block for block in snap.outlines[page_id] if block["type"] == "image"), None)
            if image:
                result[f"{logical}_image_block"] = image["block_id"]
    card_names = {"Oct Volunteer Drive: Instagram carousel": "T1", "Workshop anniversary throwback": "T2", "Mentor spotlight: Jordan": "T3"}
    card_seen: set[str] = set()
    unassigned_cards: list[dict[str, Any]] = []
    for card in snap.cards:
        if card["name"] in card_seen:
            raise ValueError(f"duplicate card title: {card['name']}")
        card_seen.add(card["name"])
        logical = card_names.get(card["name"])
        if logical:
            result[logical] = card["card_id"]
        else:
            unassigned_cards.append(card)
    next_card = 4
    for card in unassigned_cards:
        result[f"T{next_card}"] = card["card_id"]
        next_card += 1
    by_name = {item["name"]: item["list_id"] for item in snap.lists}
    for name, key in (("Ideas", "list_ideas"), ("In Production", "list_in_production"), ("Scheduled", "list_scheduled"), ("Published", "list_published"), ("Rights Hold", "list_rights_hold")):
        if name in by_name: result[key] = by_name[name]
    for label_id, name in snap.labels.items():
        if name == "Rights hold": result["label_rights_hold"] = label_id
    return result


def write_snapshot(snap: Snapshot, snapshot_path: str | Path = "fixtures/live_snapshot.json", ids_path: str | Path = "fixtures/ids.toml") -> None:
    Path(snapshot_path).parent.mkdir(parents=True, exist_ok=True)
    Path(snapshot_path).write_text(json.dumps(snap.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ids = build_ids(snap)
    lines = [f'{key} = "{value}"' for key, value in sorted(ids.items())]
    Path(ids_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_snapshot(path: str | Path = "fixtures/live_snapshot.json") -> Snapshot:
    return Snapshot(**json.loads(Path(path).read_text(encoding="utf-8")))


def archive_journal(db_path: str | Path, archive_dir: str | Path, now: datetime | None = None) -> Path | None:
    source = Path(db_path)
    if not source.exists(): return None
    destination_dir = Path(archive_dir); destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    destination = destination_dir / f"recall-{stamp}.db"
    source.replace(destination)
    return destination


def reset_to_snapshot(reset, notion, trello, snap: Snapshot, request_id: str, asset_id: str) -> list[str]:
    changes: list[str] = []
    for page_id, blocks in snap.outlines.items():
        for block in blocks:
            if block["archived"]:
                continue
            current = notion.get_block(block["block_id"])
            if current.archived:
                reset.restore_block(block["block_id"]); changes.append(f"block:{block['block_id']}")
    for card in snap.cards:
        current = trello.get_card(card["card_id"])
        if current.list_id != card["list_id"]:
            reset.restore_card_list(card["card_id"], card["list_id"]); changes.append(f"card:{card['card_id']}")
        for label_id in current.label_ids:
            if label_id not in card["label_ids"]:
                reset.remove_label(card["card_id"], label_id); changes.append(f"label:{card['card_id']}")
        reset.delete_marked_comments(card["card_id"])
    reset.airtable_cleanup(request_id, asset_id, [row["occurrence_key"] for row in snap.registry])
    return changes


def check_fixtures(notion, trello, airtable, snap: Snapshot) -> list[str]:
    mismatches: list[str] = []
    for page in snap.pages:
        current = notion.get_page_outline(page["page_id"])
        if semantic_hash(page_hash_view(page, current)) != snap.hashes[f"page:{page['page_id']}"]:
            mismatches.append(f"page:{page['page_id']}")
    for card in snap.cards:
        current = trello.get_card(card["card_id"])
        comments = trello.list_comments(card["card_id"])
        if semantic_hash(card_hash_view(current, comments)) != snap.hashes[f"card:{card['card_id']}"]:
            mismatches.append(f"card:{card['card_id']}")
    rows = airtable.list_occurrences(snap.asset["asset_id"])
    if {row.occurrence_key for row in rows} != {row["occurrence_key"] for row in snap.registry} or any(row.outcome for row in rows):
        mismatches.append("airtable:occurrences")
    return mismatches
