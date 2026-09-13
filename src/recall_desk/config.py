from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    model_default: str
    model_backup: str
    request_id: str
    asset_id: str
    list_names: dict[str, str]
    label_name: str
    db_path: str
    airtable_rate_limit_wait_s: int
    max_retries: int
    verify_rereads: int
    verify_window_s: float
    tool_budget: int
    investigation_concurrency: int
    emergency_fallback: bool
    ids: dict[str, Any] = Field(default_factory=dict)
    notion_api_key: str = ""
    notion_root_page_id: str = ""
    trello_api_key: str = ""
    trello_token: str = ""
    trello_board_id: str = ""
    airtable_token: str = ""
    airtable_base_id: str = ""
    anthropic_api_key: str = ""


def load_settings(
    env_file: str = ".env",
    toml_path: str = "config/recall.toml",
    ids_path: str = "fixtures/ids.toml",
) -> Settings:
    load_dotenv(env_file)
    with Path(toml_path).open("rb") as handle:
        data = tomllib.load(handle)

    ids: dict[str, Any] = {}
    ids_file = Path(ids_path)
    if ids_file.is_file():
        with ids_file.open("rb") as handle:
            loaded = tomllib.load(handle)
        ids = dict(loaded) if loaded else {}

    return Settings(
        **data,
        ids=ids,
        notion_api_key=os.getenv("NOTION_API_KEY", ""),
        notion_root_page_id=os.getenv("NOTION_ROOT_PAGE_ID", ""),
        trello_api_key=os.getenv("TRELLO_API_KEY", ""),
        trello_token=os.getenv("TRELLO_TOKEN", ""),
        trello_board_id=os.getenv("TRELLO_BOARD_ID", ""),
        airtable_token=os.getenv("AIRTABLE_TOKEN", ""),
        airtable_base_id=os.getenv("AIRTABLE_BASE_ID", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )
