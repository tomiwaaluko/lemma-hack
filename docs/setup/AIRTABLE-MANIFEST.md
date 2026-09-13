# Airtable Fixture Manifest

Base "Riverbend Media Rights", created 2026-09-13 through the connected Airtable MCP. All values below were returned by Airtable and confirmed by read-back. No secrets are recorded here.

```
BASE_ID=appsqq3PhBdyQiJDP
BASE_URL=https://airtable.com/appsqq3PhBdyQiJDP

ASSETS_TABLE_ID=tblRiMsGTasv1IF3e
VARIANTS_TABLE_ID=tblqd0yaBTfinuDlS
OCCURRENCES_TABLE_ID=tblh1DzuYpGwlSvRx
PERMISSION_CHANGES_TABLE_ID=tblQeA7OXN29IxiWt

AST_001_RECORD_ID=recNdmA95A8rA3bjB

VAR_001_A_RECORD_ID=recu6KEKt9dRlJT4c
VAR_001_B_RECORD_ID=recHojWrmDvFb8zye
VAR_001_C_RECORD_ID=recs02Vob9yp8rRJl

N1_OCCURRENCE_RECORD_ID=recRdwYVqoRIxjWJa
N2_OCCURRENCE_RECORD_ID=recK1BGLyXPiPmbQB
N3_OCCURRENCE_RECORD_ID=recLlloGw1415QDoN
FLYER_OCCURRENCE_RECORD_ID=recqFnBss7EBBUBoU

REQ_001_RECORD_ID=recLskGQpZc9XNvqr

REGISTERED_OCCURRENCE_COUNT=4
T1_PREEXISTS=no
T2_PREEXISTS=no
PURPOSE_FIELD_EXISTS=no
REQUEST_TEXT_EXACT=yes
SETUP_WRITE_VERIFICATION=pass
```

## Field IDs

### Assets (`tblRiMsGTasv1IF3e`)

| Field | ID | Type |
|---|---|---|
| Asset ID (primary) | fldI8CogyakzUeMtF | singleLineText |
| Title | fldEV16dNFTyrck89 | singleLineText |
| Subject name | fldaI5JHHxnGxIdja | singleLineText |
| Consent date | fldIKlumc7pnBn6ug | date (ISO) |
| Consent terms | fldYkKOLUgu70ncKh | multilineText |
| Restrictions | fld4HnC3gjGnLVIkv | multilineText |
| Variants | fldfuQ5B4uPVcZT9U | link → Variants (inverse of Variants.Asset) |
| Permission Changes | fld6oSJcEQHpHDUPm | link → Permission Changes (auto-created inverse of Permission Changes.Asset) |

### Variants (`tblqd0yaBTfinuDlS`)

| Field | ID | Type |
|---|---|---|
| Variant ID (primary) | flda7VWT1DDGVGZCY | singleLineText |
| Asset | fldXegpegygXJiY6q | link → Assets |
| Filename | fld4VPNkcINzRONmf | singleLineText |
| Canonical URL | fldOOb8KD7T5XtyGe | url |
| Derivation | fldUGhkeau6f3KVWX | singleSelect: Original / Square crop / Banner composite |
| Preview | fldRMh2FcH1WqtMle | multipleAttachments (empty) |
| Occurrences | fldK8pEBiQmwiHH5E | link → Occurrences (auto-created inverse of Occurrences.Variant) |

### Occurrences (`tblh1DzuYpGwlSvRx`)

| Field | ID | Type |
|---|---|---|
| Occurrence key (primary) | fldsj3AxAB3Z8oRmD | singleLineText |
| Variant | fld8gwGm13EcAXye5 | link → Variants |
| System | fldD4SPvMfjCyjKYG | singleSelect: Notion / Trello / External |
| Location label | fldU0V8ddrP8ZDbAe | singleLineText |
| Location URL | fldtvEfYBxXNidIaV | url |
| Source | fldupfTenxSBNCTon | singleSelect: Registered / Discovered |
| Verdict | fld5Kkp6AC68ryKKF | singleSelect: REMOVE / PRESERVE / UNCERTAIN |
| Outcome | fld0vvo0kjSeilLD3 | singleSelect: the 12 outcome values from spec §2.2 (en dash `–`) |
| Rationale | fldZEfDmFWMz4GDMV | multilineText |
| Evidence quotes | fldHP3BhBR5hQvuYr | multilineText |
| Missing or conflicting evidence | fldNPOvbXeWztWnt6 | multilineText |
| Last run ID | fld1COK9neoYhsUgY | singleLineText |
| Last verified at | fldjCY9mfY8XIUhsI | dateTime (ISO, 24h, utc) |

No Purpose field exists.

### Permission Changes (`tblQeA7OXN29IxiWt`)

| Field | ID | Type |
|---|---|---|
| Request ID (primary) | fldPHAb17tpW0wRCa | singleLineText |
| Asset | fldMrBa9fv89U1kCA | link → Assets |
| Received at | flduLExjLUm1sIeoO | dateTime (ISO, 24h, utc) |
| Request text | fldQfDx3kgutVT7QV | multilineText |
| Interpreted scope | fldRqtQZ5O26Vi74L | multilineText |
| Scope approved | fldMaJaaAVTxsVaue | checkbox |
| Approved by | fldLCIyqOJZPat5RC | singleLineText |
| Approved at | fld7U0bIJ7kmASS7M | dateTime (ISO, 24h, utc) |
| Execution state | fldjI3RduRztHZ5PU | singleSelect: RUNNING / INTERRUPTED / FINISHED |
| Final result | fldEJUfbvNvHYVtL7 | singleSelect: FAILED_SAFE / PARTIAL / NEEDS_FOLLOW_UP / COMPLETE |
| Removed | fldEEQy6vD1duovqt | number (0 dp) |
| Held | fld05Vu51b3m2EZxn | number (0 dp) |
| Preserved | fldaqUn8ckewYseMy | number (0 dp) |
| Uncertain | fldg4FueNhP3gkYn0 | number (0 dp) |
| Manual | fld2hQggOtbGPTPti | number (0 dp) |
| Other follow-up | fld7nuwqVfEsNmA85 | number (0 dp) |
| Failed | flduBW7PFWgttsYN8 | number (0 dp) |
| Report summary | fldnhs3qchCLRNWxJ | multilineText |
| Last run ID | fldlBLODPPElRSaV6 | singleLineText |

## Fixture records (verified by read-back)

| Row | Record ID | Key values |
|---|---|---|
| AST-001 | recNdmA95A8rA3bjB | Amara Okafor Photo Set; Amara Okafor; 2023-01-15; consent terms verbatim; Restrictions blank; links VAR-001-A/B/C and REQ-001 |
| VAR-001-A | recu6KEKt9dRlJT4c | amara-okafor-portrait.jpg; Original; → AST-001 |
| VAR-001-B | recHojWrmDvFb8zye | amara-portrait-square.jpg; Square crop; → AST-001 |
| VAR-001-C | recs02Vob9yp8rRJl | volunteer-drive-banner-2025.jpg; Banner composite; → AST-001 |
| N1 | recRdwYVqoRIxjWJa | notion:block:c6fd67e0-87d5-40fb-a27e-75de6df3dac4; VAR-001-B; Notion; Volunteer With Us; Registered |
| N2 | recK1BGLyXPiPmbQB | notion:block:fa07d443-94fb-4c46-afd2-2ee388f28f5c; VAR-001-A; Notion; 2024 Spring Workshop Recap; Registered |
| N3 | recLlloGw1415QDoN | notion:block:f4884441-b313-4084-9e2f-aa3acbb3d8de; VAR-001-A; Notion; Annual Impact Report 2024; Registered |
| Flyer | recqFnBss7EBBUBoU | external:fall-2024-flyer; VAR-001-A; External; Printed recruitment flyer, 500 copies distributed; Location URL blank; Registered |
| REQ-001 | recLskGQpZc9XNvqr | → AST-001; Received at 2026-09-13T00:00:00.000Z; request text verbatim; all output fields blank |

Canonical URLs are `https://tomiwaaluko.github.io/riverbend-assets/images/<filename>` for each variant, verified exact on read-back.

Verdict, Outcome, Rationale, Evidence quotes, Missing or conflicting evidence, Last run ID and Last verified at are blank on all four occurrence rows. No Trello (T1/T2) occurrence rows exist; Recall Desk must discover them.

## Write verification

A temporary Occurrences row (`setup-probe:temporary-delete-me`, record recKhgr5sPcAYeqUX) was created, read, updated (`probe v1` → `probe v2`), read back, and deleted. A follow-up table read returned exactly the four fixture rows. Fixture records were not touched.

## Notes

- No pre-existing base named "Riverbend Media Rights" existed; the base was newly created. The workspace also contains an unrelated "Untitled Base", left untouched.
- Airtable automatically adds inverse link fields. Beyond the spec's own Assets.Variants link, this created **Assets.Permission Changes** and **Variants.Occurrences**. They're harmless and link-only; the runtime shouldn't depend on them.
- `Received at` has no time in the spec, so it's stored as midnight UTC on 2026-09-13.
- The runtime token must be a personal access token scoped to this base only (records read/write, schema read). Create it manually; it is not recorded here.
