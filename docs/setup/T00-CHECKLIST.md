# T00 Setup Checklist

## ASSETS

- [x] fictional media created
- [x] hosted publicly
- [x] filenames finalized
- [x] URLs verified

## NOTION

- [x] Riverbend Website created
- [x] N1–N9 created
- [x] N1 image block ID captured (see docs/setup/NOTION-MANIFEST.md)
- [x] N2 image block ID captured (see docs/setup/NOTION-MANIFEST.md)
- [x] N3 image block ID captured (see docs/setup/NOTION-MANIFEST.md)
- [x] external image URLs verified (HTTP 200, image/jpeg for all four URLs in use)
- [x] archive test verified through the Notion REST API
- [x] direct archived-block read verified through the Notion REST API
- [x] archived test block excluded from normal child enumeration
- [x] restore/unarchive verified through the Notion REST API
- [ ] public publishing checked — blocked: no publish tool exposed; manual step required

## TRELLO

- [x] board created (see docs/setup/TRELLO-MANIFEST.md)
- [x] five lists created
- [x] Rights hold label created (named, red; not applied to any card)
- [x] T1–T12 created (titles, lists, due date, T2 description verified)
- [x] attachment filenames verified (T1/T2/T3 REST IDs and filenames recorded)
- [x] move test verified
- [x] label add/remove verified
- [x] comment add/read/delete verified (REST)

## AIRTABLE

- [x] base created (see docs/setup/AIRTABLE-MANIFEST.md)
- [x] Assets table
- [x] Variants table
- [x] Occurrences table
- [x] Permission Changes table
- [x] AST-001
- [x] VAR-001-A/B/C
- [x] N1/N2/N3 registered after Notion block IDs are known
- [x] external flyer registered
- [x] REQ-001 exact text
- [x] T1/T2 deliberately absent
- [x] no Purpose field
- [x] harmless write/read test verified (create/read/update/read-back/delete on a probe row)
- [ ] runtime personal access token scoped to the base — manual step

## MODEL

- [ ] funded runtime Anthropic API key
- [ ] tool-use / structured response verified

## RULES

- [ ] judge-accessible hosted URL requirement checked
- [ ] any other event-rule constraints checked
