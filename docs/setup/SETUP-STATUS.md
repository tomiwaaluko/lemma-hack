# Setup Status

Assets: COMPLETE

GitHub asset hosting: COMPLETE

Notion fixture setup: READY — PUBLICATION MANUAL STEP REMAINS. Riverbend Website and N1–N9 are created and content-verified; N1/N2/N3 image block IDs were re-verified by exact external URL and direct REST reads. A disposable root-page block was archived, read directly while archived, confirmed absent from normal child enumeration, restored, and re-archived for cleanup.

Trello fixture setup: PARTIAL. Board, five lists and T1–T12 are created and verified by read-back; move and label attach/detach verified on a probe card that was then archived. Blocked on the connected MCP: "Rights hold" label naming, T1/T2/T3 attachments, and comment add/read/delete. See docs/setup/TRELLO-MANIFEST.md.

Airtable fixture setup: COMPLETE. Base "Riverbend Media Rights" has four tables per spec §2.2, plus AST-001, VAR-001-A/B/C, four Registered occurrence rows (N1/N2/N3 using the verified Notion block IDs, and the external flyer) and REQ-001 with verbatim request text. All were verified by read-back. T1/T2 are absent and there is no Purpose field. Probe create/read/update/delete passed and was cleaned up. See docs/setup/AIRTABLE-MANIFEST.md. The runtime token scoped to the base is still a manual step.

Runtime Anthropic API verification: PENDING

## Next action

Finish remaining Trello REST verification and runtime Anthropic API check.

This document may be updated during setup.
