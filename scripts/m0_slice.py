from __future__ import annotations

import os
import sys
import time
import winreg

from recall_desk.adapters.live.airtable import LiveAirtable
from recall_desk.adapters.live.http import ApiClient
from recall_desk.adapters.live.notion import LiveNotion
from recall_desk.adapters.live.reset import LiveReset
from recall_desk.adapters.live.trello import LiveTrello
from recall_desk.config import load_settings
from recall_desk.discovery import discover
from recall_desk.evidence import EvidenceContext, build_packet


N1_IMAGE_BLOCK_ID = "c6fd67e0-87d5-40fb-a27e-75de6df3dac4"
ROOT_ID = "3daf279e-86cf-81bb-90a4-e9589d691df6"
BOARD_ID = "6aa6f706da9b20af34821101"


def _user_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        return str(winreg.QueryValueEx(key, name)[0])


def live_ports():
    settings = load_settings()
    notion_http = ApiClient("https://api.notion.com/v1", {"Authorization": f"Bearer {_user_env('NOTION_API_KEY')}", "Notion-Version": "2022-06-28"})
    trello_http = ApiClient("https://api.trello.com/1", {}, base_params={"key": _user_env("TRELLO_API_KEY"), "token": _user_env("TRELLO_TOKEN")})
    airtable_http = ApiClient(f"https://api.airtable.com/v0/{_user_env('AIRTABLE_BASE_ID')}", {"Authorization": f"Bearer {_user_env('AIRTABLE_TOKEN')}"}, default_retry_after_s=settings.airtable_rate_limit_wait_s)
    return settings, LiveNotion(notion_http, ROOT_ID), LiveTrello(trello_http, BOARD_ID), LiveAirtable(airtable_http), LiveReset(notion_http, trello_http, airtable_http)


def main() -> int:
    try:
        settings, notion, trello, airtable, reset = live_ports()
        variants = airtable.list_variants(settings.asset_id)
        registry = airtable.list_occurrences(settings.asset_id)
        ledger = discover(notion, trello, variants, registry, set())
        candidate = next(entry for entry in ledger.candidates() if entry.ref.target_id == N1_IMAGE_BLOCK_ID)
        pages = {page.page_id: page for page in notion.list_pages()}
        context = EvidenceContext({}, {}, {key: page.title for key, page in pages.items()}, {})
        before = build_packet(candidate.ref, notion, trello, context)
        notion.archive_block(N1_IMAGE_BLOCK_ID)
        for _ in range(3):
            if notion.get_block(N1_IMAGE_BLOCK_ID).archived:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("archive did not become visible")
        reset.restore_block(N1_IMAGE_BLOCK_ID)
        for _ in range(3):
            if not notion.get_block(N1_IMAGE_BLOCK_ID).archived:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("restore did not become visible")
        after = build_packet(candidate.ref, notion, trello, context)
        if before.state_hash != after.state_hash:
            raise RuntimeError("restored block hash differs from baseline")
    except Exception as error:
        print(f"M0 FAIL: {error}")
        return 1
    print("M0 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
