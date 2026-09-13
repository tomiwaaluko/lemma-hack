from __future__ import annotations

import json
from pathlib import Path

from recall_desk.adapters.live.notion import parse_block, parse_page
from recall_desk.adapters.live.trello import LiveTrello, parse_card, parse_comment


SAMPLES = Path(__file__).parent.parent / "samples"


def _sample(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def test_NL1_parses_external_image_url_caption_and_type():
    block = parse_block(_sample("notion_external_image.json"), "page-1")

    assert block.image_url == "https://assets.example.test/amara-portrait-square.jpg"
    assert block.caption == "Amara, volunteer mentor since 2023"
    assert block.type == "image"


def test_NL2_parses_paragraph_text_and_hyperlink():
    block = parse_block(_sample("notion_paragraph_link.json"), "page-1")

    assert block.text == "Apply to volunteer today."
    assert "https://riverbend.example.test/volunteer" in block.link_urls


def test_NL3_parses_archived_block():
    block = parse_block(_sample("notion_archived_block.json"), "page-1")

    assert block.archived is True


def test_NL4_parses_page_title_and_public_url():
    page = parse_page(_sample("notion_page.json"))

    assert page.title == "Volunteer With Us"
    assert page.public_url == "https://riverbend.example.test/volunteer-with-us"


def test_trello_TL1_parses_uploaded_attachment_and_card_fields():
    card = parse_card(_sample("trello_card_uploaded.json"))

    assert card.card_id == "card-t1"
    assert card.name == "Oct Volunteer Drive: Instagram carousel"
    assert card.desc == "A recruitment carousel for new volunteer mentors."
    assert card.list_id == "list-scheduled"
    assert card.label_ids == ["label-rights-hold"]
    assert card.due == "2026-10-01T14:00:00.000Z"
    assert card.attachments[0].filename == "volunteer-drive-banner-2025.jpg"
    assert card.attachments[0].url.endswith("volunteer-drive-banner-2025.jpg")


def test_trello_TL2_uses_url_basename_for_link_attachment_without_file_name():
    card = parse_card(_sample("trello_card_link.json"))

    assert card.attachments[0].filename == "amara-okafor-portrait.jpg"
    assert card.attachments[0].url == "https://assets.example.test/photos/amara-okafor-portrait.jpg?download=1"


def test_trello_TL3_parses_comment_action_text():
    comment = parse_comment(_sample("trello_comment.json"))

    assert comment.action_id == "comment-action-1"
    assert comment.text == "[recall-desk REQ-001 RUN-001 OP-003] Held: withdrawn use."


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None, dict | None, bool]] = []

    def request(self, method, path, *, json=None, params=None, is_write):
        self.calls.append((method, path, json, params, is_write))
        if path.endswith("/lists"):
            return [{"id": "list-hold", "name": "Rights Hold"}]
        if path.endswith("/labels"):
            return [{"id": "label-hold", "name": "Rights hold"}]
        return []


def test_trello_TL4_maps_lists_and_labels_to_port_shapes():
    trello = LiveTrello(_RecordingClient(), "board-1")

    assert trello.list_lists()[0].name == "Rights Hold"
    assert trello.list_labels() == {"label-hold": "Rights hold"}


def test_trello_TL5_constructs_single_write_requests():
    client = _RecordingClient()
    trello = LiveTrello(client, "board-1")

    trello.move_card("card-1", "list-hold")
    trello.add_label("card-1", "label-hold")
    trello.add_comment("card-1", "held")

    assert client.calls == [
        ("PUT", "/cards/card-1", None, {"idList": "list-hold"}, True),
        ("POST", "/cards/card-1/idLabels", None, {"value": "label-hold"}, True),
        ("POST", "/cards/card-1/actions/comments", None, {"text": "held"}, True),
    ]
