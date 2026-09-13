from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    REMOVE = "REMOVE"
    PRESERVE = "PRESERVE"
    UNCERTAIN = "UNCERTAIN"


class Purpose(StrEnum):
    volunteer_recruitment = "volunteer_recruitment"
    fundraising_donor = "fundraising_donor"
    program_documentation = "program_documentation"
    social_promotion = "social_promotion"
    press = "press"
    internal = "internal"
    unknown = "unknown"


class ScopeBasis(StrEnum):
    WITHDRAWN_PURPOSE = "WITHDRAWN_PURPOSE"
    RETAINED_CONTENT = "RETAINED_CONTENT"
    PURPOSE_NOT_WITHDRAWN = "PURPOSE_NOT_WITHDRAWN"
    NONE = "NONE"


class System(StrEnum):
    Notion = "Notion"
    Trello = "Trello"
    External = "External"


class Bucket(StrEnum):
    CANDIDATE = "CANDIDATE"
    ALREADY_REMOVED = "ALREADY_REMOVED"
    INACCESSIBLE = "INACCESSIBLE"
    EXTERNAL = "EXTERNAL"
    AMBIGUOUS_IDENTIFIER = "AMBIGUOUS_IDENTIFIER"


class Outcome(StrEnum):
    REMOVED_VERIFIED = "Removed – verified"
    HELD_VERIFIED = "Held – verified"
    PRESERVED_VERIFIED_UNCHANGED = "Preserved – verified unchanged"
    FOLLOWUP_UNCERTAIN = "Needs follow-up – uncertain"
    FOLLOWUP_AMBIGUOUS_IDENTIFIER = "Needs follow-up – ambiguous identifier"
    FOLLOWUP_STATE_CHANGED_REPEATEDLY = "Needs follow-up – state changed repeatedly"
    FOLLOWUP_APPEARED_DURING_RUN = "Needs follow-up – appeared during run"
    FOLLOWUP_PREEXISTING_HOLD = "Needs follow-up – pre-existing hold"
    FOLLOWUP_PREEXISTING_REMOVAL = "Needs follow-up – pre-existing removal"
    MANUAL_OUTSIDE_CONNECTED = "Manual – outside connected systems"
    INACCESSIBLE = "Inaccessible"
    ACTION_FAILED = "Action failed"


class ExecutionState(StrEnum):
    RUNNING = "RUNNING"
    INTERRUPTED = "INTERRUPTED"
    FINISHED = "FINISHED"


class FinalResult(StrEnum):
    FAILED_SAFE = "FAILED_SAFE"
    PARTIAL = "PARTIAL"
    NEEDS_FOLLOW_UP = "NEEDS_FOLLOW_UP"
    COMPLETE = "COMPLETE"


class OpState(StrEnum):
    PLANNED = "PLANNED"
    PRECHECK_OK = "PRECHECK_OK"
    DRIFTED = "DRIFTED"
    SENT = "SENT"
    ACKED = "ACKED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"
    VERIFY_FAILED = "VERIFY_FAILED"


class ActionType(StrEnum):
    ARCHIVE_BLOCK = "ARCHIVE_BLOCK"
    MOVE_CARD = "MOVE_CARD"
    ADD_LABEL = "ADD_LABEL"
    ADD_COMMENT = "ADD_COMMENT"
    APPEND_RESTRICTION = "APPEND_RESTRICTION"
    UPSERT_OCCURRENCES = "UPSERT_OCCURRENCES"
    UPDATE_REQUEST = "UPDATE_REQUEST"


CONTENT_ACTIONS = frozenset(
    {
        ActionType.ARCHIVE_BLOCK,
        ActionType.MOVE_CARD,
        ActionType.ADD_LABEL,
        ActionType.ADD_COMMENT,
    }
)


class ListRole(StrEnum):
    PLANNED = "PLANNED"
    PUBLISHED = "PUBLISHED"
    RIGHTS_HOLD = "RIGHTS_HOLD"


class Variant(BaseModel):
    variant_id: str
    asset_id: str
    filename: str
    canonical_url: str


class Asset(BaseModel):
    asset_id: str
    title: str
    consent_terms: str
    restrictions: str


class PermissionRequest(BaseModel):
    request_id: str
    asset_id: str
    request_text: str


class RegistryRow(BaseModel):
    occurrence_key: str
    variant_id: str | None
    system: System
    location_label: str
    location_url: str | None
    source: Literal["Registered", "Discovered"]
    outcome: Outcome | None
    last_run_id: str | None


class NotionPage(BaseModel):
    page_id: str
    title: str
    public_url: str | None


class NotionBlock(BaseModel):
    block_id: str
    page_id: str
    type: str
    text: str
    image_url: str | None
    caption: str
    archived: bool
    link_urls: list[str]


class TrelloList(BaseModel):
    list_id: str
    name: str


class TrelloAttachment(BaseModel):
    attachment_id: str
    filename: str
    url: str


class TrelloComment(BaseModel):
    action_id: str
    text: str


class TrelloCard(BaseModel):
    card_id: str
    name: str
    list_id: str
    desc: str
    label_ids: list[str]
    due: str | None
    attachments: list[TrelloAttachment]


class OccurrenceRef(BaseModel):
    occurrence_key: str
    system: System
    variant_id: str | None
    container_id: str
    container_title: str
    target_id: str
    location_url: str | None
    registered: bool


class CoverageEntry(BaseModel):
    ref: OccurrenceRef
    bucket: Bucket
    preset_outcome: Outcome | None
    note: str


class CoverageLedger(BaseModel):
    entries: list[CoverageEntry]

    def candidates(self) -> list[CoverageEntry]:
        return [entry for entry in self.entries if entry.bucket == Bucket.CANDIDATE]


class EvidenceItem(BaseModel):
    evidence_id: str
    source: str
    text: str


class EvidencePacket(BaseModel):
    occurrence_key: str
    items: list[EvidenceItem]
    state_hash: str


class WithdrawnPurpose(BaseModel):
    purpose: Purpose
    quote: str


class RetainedContent(BaseModel):
    container_ref: str
    quote: str


class ScopeSpec(BaseModel):
    withdrawn_purposes: list[WithdrawnPurpose]
    retained_content: list[RetainedContent]
    ambiguities: list[str]


class Citation(BaseModel):
    evidence_id: str
    quote: str


class Decision(BaseModel):
    occurrence_key: str
    verdict: Verdict
    observed_purposes: list[Purpose]
    scope_basis: ScopeBasis
    evidence: list[Citation] = Field(max_length=4)
    rationale: str = Field(max_length=300)
    missing_or_conflicting: list[str]


class ValidatedDecision(BaseModel):
    occurrence_key: str
    raw: dict[str, Any] | None
    final: Decision
    downgrades: list[str]


class Op(BaseModel):
    op_id: str
    run_id: str
    request_id: str
    occurrence_key: str | None
    action: ActionType
    target_id: str
    params: dict[str, Any]
    precondition_hash: str | None
    step: int


class OccurrenceResult(BaseModel):
    occurrence_key: str
    verdict: Verdict | None
    outcome: Outcome
    rationale: str
    evidence: list[Citation]
    missing_or_conflicting: list[str]
    scheduled_date: str | None
    location_url: str | None
    notes: list[str]


class RunFlags(BaseModel):
    registry_read_failed: bool = False
    scope_rejected: bool = False
    content_writes_occurred: bool = False
    registry_sync_failed: bool = False


class RunSummary(BaseModel):
    run_id: str
    request_id: str
    execution_state: ExecutionState
    final_result: FinalResult | None
    counts: dict[str, int]
    results: list[OccurrenceResult]
    flags: RunFlags


VOLATILE_KEYS = frozenset(
    {
        "last_edited_time",
        "created_time",
        "last_edited_by",
        "created_by",
        "request_id",
        "dateLastActivity",
        "pos",
        "createdTime",
        "Last verified at",
    }
)

_LIST_SORT_KEYS = (
    "block_id",
    "card_id",
    "attachment_id",
    "action_id",
    "occurrence_key",
    "page_id",
    "list_id",
)


def _dict_sort_key(item: dict[str, Any]) -> str:
    for key in _LIST_SORT_KEYS:
        if key in item:
            return str(item[key])
    return ""


def normalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: normalize(value)
            for key, value in sorted(obj.items())
            if key not in VOLATILE_KEYS
        }
    if isinstance(obj, list):
        items = [normalize(item) for item in obj]
        if items and all(isinstance(item, dict) for item in items):
            items.sort(key=_dict_sort_key)
        return items
    return obj


def semantic_hash(obj: Any) -> str:
    payload = json.dumps(normalize(obj), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
