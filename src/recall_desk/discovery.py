from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from recall_desk.domain import (
    Bucket, CoverageEntry, CoverageLedger, ListRole, NotionBlock, OccurrenceRef,
    Outcome, RegistryRow, System, TrelloCard, TrelloList, Variant,
)
from recall_desk.ports import NotFound


@dataclass(frozen=True)
class IdentifierMatch:
    kind: Literal["MATCH", "NONE", "AMBIGUOUS"]
    variant_id: str | None = None


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", ""))


def filename_of(value: str) -> str:
    return urlsplit(value).path.rsplit("/", 1)[-1].lower()


def match_identifier(url: str | None, filename: str | None, variants: list[Variant]) -> IdentifierMatch:
    url_matches = {
        item.variant_id for item in variants if url and normalize_url(item.canonical_url) == normalize_url(url)
    }
    filename_matches = {
        item.variant_id for item in variants
        if filename and item.filename.lower() == filename.lower()
    }
    if len(url_matches) > 1 or len(filename_matches) > 1:
        return IdentifierMatch("AMBIGUOUS")
    candidates = url_matches | filename_matches
    if len(candidates) > 1:
        return IdentifierMatch("AMBIGUOUS")
    if candidates:
        return IdentifierMatch("MATCH", candidates.pop())
    return IdentifierMatch("NONE")


def list_roles(lists: list[TrelloList], names: dict[str, str]) -> dict[str, ListRole]:
    expected = {
        names["ideas"]: ListRole.PLANNED,
        names["in_production"]: ListRole.PLANNED,
        names["scheduled"]: ListRole.PLANNED,
        names["published"]: ListRole.PUBLISHED,
        names["rights_hold"]: ListRole.RIGHTS_HOLD,
    }
    return {item.list_id: expected[item.name] for item in lists if item.name in expected}


def _entry(ref: OccurrenceRef, bucket: Bucket, outcome: Outcome | None = None, note: str = "") -> CoverageEntry:
    return CoverageEntry(ref=ref, bucket=bucket, preset_outcome=outcome, note=note)


def discover(notion, trello, variants: list[Variant], registry: list[RegistryRow], prior_verified_archives: set[str]) -> CoverageLedger:
    entries: dict[str, CoverageEntry] = {}
    registered = {row.occurrence_key: row for row in registry}
    pages = {page.page_id: page for page in notion.list_pages()}
    for page_id, page in pages.items():
        for block in notion.list_image_blocks(page_id):
            match = match_identifier(block.image_url, filename_of(block.image_url) if block.image_url else None, variants)
            if match.kind == "NONE":
                continue
            key = f"notion:block:{block.block_id}"
            ref = OccurrenceRef(occurrence_key=key, system=System.Notion, variant_id=match.variant_id,
                                container_id=page_id, container_title=page.title, target_id=block.block_id,
                                location_url=page.public_url, registered=key in registered)
            if match.kind == "AMBIGUOUS":
                entries[key] = _entry(ref, Bucket.AMBIGUOUS_IDENTIFIER, Outcome.FOLLOWUP_AMBIGUOUS_IDENTIFIER)
            else:
                entries[key] = _entry(ref, Bucket.CANDIDATE)
    for card in trello.list_cards():
        matches = [match_identifier(a.url, a.filename, variants) for a in card.attachments]
        matching = [m for m in matches if m.kind != "NONE"]
        if not matching:
            continue
        key = f"trello:card:{card.card_id}"
        ambiguous = any(m.kind == "AMBIGUOUS" for m in matching) or len({m.variant_id for m in matching}) > 1
        ref = OccurrenceRef(occurrence_key=key, system=System.Trello,
                            variant_id=None if ambiguous else matching[0].variant_id,
                            container_id=card.card_id, container_title=card.name, target_id=card.card_id,
                            location_url=None, registered=key in registered)
        entries[key] = _entry(ref, Bucket.AMBIGUOUS_IDENTIFIER, Outcome.FOLLOWUP_AMBIGUOUS_IDENTIFIER) if ambiguous else _entry(ref, Bucket.CANDIDATE)
    for key, row in registered.items():
        if row.system == System.External:
            ref = OccurrenceRef(occurrence_key=key, system=row.system, variant_id=row.variant_id,
                                container_id=key, container_title=row.location_label, target_id=key,
                                location_url=row.location_url, registered=True)
            entries[key] = _entry(ref, Bucket.EXTERNAL, Outcome.MANUAL_OUTSIDE_CONNECTED)
            continue
        if key in entries:
            continue
        if row.system == System.Notion:
            block_id = key.removeprefix("notion:block:")
            try:
                block: NotionBlock = notion.get_block(block_id)
            except NotFound:
                ref = OccurrenceRef(occurrence_key=key, system=row.system, variant_id=row.variant_id,
                                    container_id="", container_title=row.location_label, target_id=block_id,
                                    location_url=row.location_url, registered=True)
                entries[key] = _entry(ref, Bucket.INACCESSIBLE, Outcome.INACCESSIBLE)
                continue
            page = pages.get(block.page_id)
            ref = OccurrenceRef(occurrence_key=key, system=row.system, variant_id=row.variant_id,
                                container_id=block.page_id, container_title=page.title if page else row.location_label,
                                target_id=block_id, location_url=page.public_url if page else row.location_url, registered=True)
            if block.archived:
                outcome = Outcome.REMOVED_VERIFIED if block_id in prior_verified_archives else Outcome.FOLLOWUP_PREEXISTING_REMOVAL
                entries[key] = _entry(ref, Bucket.ALREADY_REMOVED, outcome)
            else:
                entries[key] = _entry(ref, Bucket.CANDIDATE)
        else:
            card_id = key.removeprefix("trello:card:")
            try:
                card: TrelloCard = trello.get_card(card_id)
                entries[key] = _entry(OccurrenceRef(occurrence_key=key, system=row.system, variant_id=row.variant_id,
                    container_id=card.card_id, container_title=card.name, target_id=card.card_id,
                    location_url=None, registered=True), Bucket.CANDIDATE)
            except NotFound:
                entries[key] = _entry(OccurrenceRef(occurrence_key=key, system=row.system, variant_id=row.variant_id,
                    container_id="", container_title=row.location_label, target_id=card_id,
                    location_url=row.location_url, registered=True), Bucket.INACCESSIBLE, Outcome.INACCESSIBLE)
    return CoverageLedger(entries=list(entries.values()))
