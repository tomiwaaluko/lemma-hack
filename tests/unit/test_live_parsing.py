from __future__ import annotations

import json
from pathlib import Path

from recall_desk.adapters.live.notion import parse_block, parse_page


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
