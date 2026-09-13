from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from recall_desk.domain import EvidenceItem, EvidencePacket, OccurrenceRef, System, semantic_hash


@dataclass(frozen=True)
class EvidenceContext:
    list_names_by_id: dict[str, str]
    label_names_by_id: dict[str, str]
    page_titles: dict[str, str]
    page_published: dict[str, bool]


def _items(lines: Iterable[tuple[str, str]], start: int = 1) -> list[EvidenceItem]:
    return [EvidenceItem(evidence_id=f"E{index}", source=source, text=text)
            for index, (source, text) in enumerate(lines, start=start)]


def build_packet(ref: OccurrenceRef, notion, trello, ctx: EvidenceContext) -> EvidencePacket:
    if ref.system == System.Notion:
        outline = notion.get_page_outline(ref.container_id)
        index = next(i for i, block in enumerate(outline) if block.block_id == ref.target_id)
        target = outline[index]
        before = [block for block in outline[max(0, index - 3):index] if block.text]
        after = [block for block in outline[index + 1:index + 4] if block.text]
        heading = next((block.text for block in reversed(outline[:index]) if block.type.startswith("heading") and block.text), None)
        lines: list[tuple[str, str]] = [("notion", f"Page title: {ctx.page_titles.get(ref.container_id, ref.container_title)}"),
                                         ("notion", f"Page published: {'yes' if ctx.page_published.get(ref.container_id, False) else 'no'}")]
        if heading:
            lines.append(("notion", f"Nearest heading: {heading}"))
        lines.extend(("notion", block.text) for block in before)
        if target.caption:
            lines.append(("notion", f"Caption: {target.caption}"))
        lines.extend(("notion", block.text) for block in after)
        lines.extend(("notion", f"Link: {url}") for block in outline for url in block.link_urls)
    else:
        card = trello.get_card(ref.target_id)
        labels = ", ".join(ctx.label_names_by_id.get(label_id, label_id) for label_id in card.label_ids)
        attachments = ", ".join(f"{a.filename} ({a.url})" for a in card.attachments)
        lines = [("trello", f"Card name: {card.name}"), ("trello", f"List: {ctx.list_names_by_id.get(card.list_id, card.list_id)}"),
                 ("trello", f"Labels: {labels}"), ("trello", f"Due: {card.due or ''}")]
        if card.desc:
            lines.append(("trello", f"Description: {card.desc}"))
        lines.append(("trello", f"Attachments: {attachments}"))
    items = _items(lines)
    return EvidencePacket(occurrence_key=ref.occurrence_key, items=items, state_hash=state_hash(ref, notion, trello, ctx))


def state_hash(ref: OccurrenceRef, notion, trello, ctx: EvidenceContext) -> str:
    if ref.system == System.Notion:
        block = notion.get_block(ref.target_id)
        outline = notion.get_page_outline(ref.container_id)
        texts = [block.text for block in outline if block.text] + [url for block in outline for url in block.link_urls]
        return semantic_hash({"archived": block.archived, "image_url": block.image_url, "caption": block.caption,
                              "page_id": block.page_id, "evidence_texts": texts})
    card = trello.get_card(ref.target_id)
    return semantic_hash({"list_id": card.list_id, "name": card.name, "desc": card.desc,
                          "label_ids": sorted(card.label_ids), "attachment_ids": sorted(a.attachment_id for a in card.attachments)})


class EvidenceReader:
    def __init__(self, notion, trello, ctx: EvidenceContext, consent_terms: str, board_id: str,
                 known_page_ids: set[str], start_index: int = 1) -> None:
        self.notion, self.trello, self.ctx = notion, trello, ctx
        self.consent_terms, self.board_id, self.known_page_ids = consent_terms, board_id, known_page_ids
        self._next = start_index
        self._items: list[EvidenceItem] = []

    def _assign(self, lines: list[tuple[str, str]]) -> list[EvidenceItem]:
        result = _items(lines, self._next)
        self._next += len(result)
        self._items.extend(result)
        return result

    def get_page_outline(self, page_id: str) -> list[EvidenceItem]:
        return self._assign([("notion", block.text) for block in self.notion.get_page_outline(page_id) if block.text])

    def get_linked_content(self, url: str) -> list[EvidenceItem]:
        for page_id in self.known_page_ids:
            if page_id.replace("-", "") in url:
                return self.get_page_outline(page_id)
        if self.board_id in url:
            return self._assign([("trello", "Linked content: Trello board")])
        return self._assign([("linked", "Linked content: outside connected systems")])

    def get_consent_terms(self) -> list[EvidenceItem]:
        return self._assign([("airtable", self.consent_terms)])

    @property
    def items(self) -> list[EvidenceItem]:
        return list(self._items)


def render_items(items: list[EvidenceItem]) -> str:
    return "\n".join(f"{item.evidence_id} [{item.source}]: {item.text}" for item in items)
