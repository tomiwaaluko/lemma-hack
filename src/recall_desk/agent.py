from __future__ import annotations

import json
import os
import winreg
from typing import Any

from anthropic import Anthropic

from recall_desk.domain import EvidencePacket, ScopeSpec
from recall_desk.evidence import render_items


def _api_key() -> str:
    if value := os.getenv("ANTHROPIC_API_KEY"):
        return value
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        return str(winreg.QueryValueEx(key, "ANTHROPIC_API_KEY")[0])


_PURPOSES = ["volunteer_recruitment", "fundraising_donor", "program_documentation", "social_promotion", "press", "internal", "unknown"]
_SCOPE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["withdrawn_purposes", "retained_content", "ambiguities"], "properties": {"withdrawn_purposes": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["purpose", "quote"], "properties": {"purpose": {"enum": _PURPOSES}, "quote": {"type": "string"}}}}, "retained_content": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["container_ref", "quote"], "properties": {"container_ref": {"type": "string"}, "quote": {"type": "string"}}}}, "ambiguities": {"type": "array", "items": {"type": "string"}}}}
_DECISION_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["occurrence_key", "verdict", "observed_purposes", "scope_basis", "evidence", "rationale", "missing_or_conflicting"], "properties": {"occurrence_key": {"type": "string"}, "verdict": {"enum": ["REMOVE", "PRESERVE", "UNCERTAIN"]}, "observed_purposes": {"type": "array", "items": {"enum": _PURPOSES}}, "scope_basis": {"enum": ["WITHDRAWN_PURPOSE", "RETAINED_CONTENT", "PURPOSE_NOT_WITHDRAWN", "NONE"]}, "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["evidence_id", "quote"], "properties": {"evidence_id": {"type": "string"}, "quote": {"type": "string"}}}}, "rationale": {"type": "string", "maxLength": 300}, "missing_or_conflicting": {"type": "array", "items": {"type": "string"}}}}


def _json_response(client: Any, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    response = client.messages.create(model="claude-sonnet-5", max_tokens=2000, output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}}, messages=[{"role": "user", "content": prompt}])
    text = "".join(getattr(item, "text", "") for item in response.content).strip()
    if text.startswith("```"):
        text = "\n".join(text.splitlines()[1:-1]).strip()
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("model response must be a JSON object")
    return result


def interpret_scope(request_text: str, consent_terms: str, *, known_containers: dict[str, str] | None = None, client: Any | None = None) -> ScopeSpec:
    containers = "\n".join(f"- {key}: {title}" for key, title in (known_containers or {}).items())
    raw = _json_response(client or Anthropic(api_key=_api_key()), f"""Interpret this permission-change request. Return JSON only with withdrawn_purposes, retained_content, ambiguities.
withdrawn_purposes: purpose (volunteer_recruitment, fundraising_donor, program_documentation, social_promotion, press, internal, unknown) and an exact request quote.
retained_content: a supplied container_ref and exact request quote. Do not infer withdrawals beyond the request.
Request: {request_text}
Consent terms: {consent_terms}
Known containers:\n{containers}""", _SCOPE_SCHEMA)
    return ScopeSpec(**raw)


def interpret_decision(scope: ScopeSpec, packet: EvidencePacket, consent_terms: str, *, client: Any | None = None) -> dict[str, Any]:
    return _json_response(client or Anthropic(api_key=_api_key()), f"""Decide one occurrence under the immutable approved scope. Return one JSON object only, with this exact schema:
{{"occurrence_key":"{packet.occurrence_key}","verdict":"REMOVE|PRESERVE|UNCERTAIN","observed_purposes":["volunteer_recruitment|fundraising_donor|program_documentation|social_promotion|press|internal|unknown"],"scope_basis":"WITHDRAWN_PURPOSE|RETAINED_CONTENT|PURPOSE_NOT_WITHDRAWN|NONE","evidence":[{{"evidence_id":"E1","quote":"exact evidence text"}}],"rationale":"brief text","missing_or_conflicting":["brief text"]}}
Use `evidence_id`, never `id`; cite at most 4 supplied evidence IDs and quote their text exactly. verdict is REMOVE, PRESERVE, or UNCERTAIN. REMOVE needs cited evidence for a withdrawn purpose. PRESERVE needs cited retained or non-withdrawn purpose evidence. If insufficient, choose UNCERTAIN. You cannot change scope or perform writes.
Approved scope: {scope.model_dump_json()}
Consent terms: {consent_terms}
Occurrence key: {packet.occurrence_key}
Evidence:\n{render_items(packet.items)}""", _DECISION_SCHEMA)
