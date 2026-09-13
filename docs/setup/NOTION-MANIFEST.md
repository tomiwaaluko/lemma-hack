# Notion Fixture Manifest — Riverbend Website

Generated during T00 setup. Page IDs were returned by the Notion MCP
(`notion-create-pages` / `notion-fetch`); image block IDs were confirmed by
the real Notion REST API. No IDs are guessed.

## Connector capability note (read first)

The Notion MCP available in this session (`da36f022-...`) is a page/markdown-level
connector: `notion-search`, `notion-fetch`, `notion-create-pages`, `notion-update-page`,
`notion-move-pages`, plus comment/attachment/database helpers. It exposes **no
block-level API** — there is no get-block, archive-block, restore-block, or
publish-page tool anywhere in its tool surface. `notion-fetch` returns page
content as flattened Markdown; individual blocks (e.g. an image block) are not
addressable by ID through this connector.

Consequences, stated plainly:
- **Image block IDs cannot be captured.** Only page-level IDs are obtainable.
- **Archive / direct-archived-read / restore behavior cannot be tested** through
  this connector — those are Notion REST API operations (`blocks.retrieve`,
  `blocks.update{archived}`), not exposed here.
- **Public web publishing cannot be triggered or verified** through this
  connector — no publish tool exists in its surface.

These three verifications require either (a) the real Notion REST API with an
integration token (as the actual Recall Desk `adapters.live` will use via
`httpx`, per §4.7 of the design spec), driven from an interactive Notion
session, or (b) manual steps in the Notion UI. They are **not a limitation of
the fixture content**, which is complete and verified below.

## Root page

```
ROOT_PAGE_ID=3daf279e-86cf-81bb-90a4-e9589d691df6
ROOT_PAGE_URL=https://app.notion.com/p/3daf279e86cf81bb90a4e9589d691df6
ROOT_PUBLIC_URL=NOT_AVAILABLE (no publish tool exposed by this MCP; publish manually in Notion UI: Share > Publish to web)
```

## N1 · Volunteer With Us (expected verdict: REMOVE, VAR-001-B)

```
N1_PAGE_ID=ec0b1ee3-2c92-4c82-b816-7c59112abd95
N1_PAGE_URL=https://app.notion.com/p/ec0b1ee32c924c82b8167c59112abd95
N1_IMAGE_BLOCK_ID=c6fd67e0-87d5-40fb-a27e-75de6df3dac4
N1_IMAGE_URL=https://tomiwaaluko.github.io/riverbend-assets/images/amara-portrait-square.jpg
```

Verified content (via notion-fetch and direct REST read): heading "Mentors make Riverbend work";
image with caption "Amara, volunteer mentor since 2023"; text "Apply by
October 15, no experience needed"; link "Apply to volunteer".

## N2 · 2024 Spring Workshop Recap (expected verdict: PRESERVE, VAR-001-A)

```
N2_PAGE_ID=1e920a50-8af9-4712-b072-39265437da13
N2_PAGE_URL=https://app.notion.com/p/1e920a508af94712b07239265437da13
N2_IMAGE_BLOCK_ID=fa07d443-94fb-4c46-afd2-2ee388f28f5c
N2_IMAGE_URL=https://tomiwaaluko.github.io/riverbend-assets/images/amara-okafor-portrait.jpg
```

Verified content (via direct REST read): historical workshop narrative; image with caption "Amara
leading the robotics table on day two"; a second, unrelated
workshop-participant image (`workshop-participant.jpg`); no recruitment CTA.

## N3 · Annual Impact Report 2024 (expected verdict: PRESERVE, VAR-001-A)

```
N3_PAGE_ID=a983a11c-ad44-4525-9a12-7ffb313f580e
N3_PAGE_URL=https://app.notion.com/p/a983a11cad4445259a127ffb313f580e
N3_IMAGE_BLOCK_ID=f4884441-b313-4084-9e2f-aa3acbb3d8de
N3_IMAGE_URL=https://tomiwaaluko.github.io/riverbend-assets/images/amara-okafor-portrait.jpg
```

Verified content (via direct REST read): donor-facing text containing "Your gifts funded 38
workshops"; image with caption "Volunteers like Amara gave 2,100 hours"; no
call to action.

## N4–N9 · filler (must not use a registered Amara asset identifier)

```
N4_PAGE_ID=7e7bb0bf-09ae-4ced-9b40-f024c8858147   (About Us — uses Jordan decoy image)
N5_PAGE_ID=cb454015-f225-4d9d-ba70-362a846b77b8   (Programs — no image)
N6_PAGE_ID=ac4cfc74-adf6-48df-a4ca-5afaa6451563   (FAQ — no image)
N7_PAGE_ID=b749a774-7821-431f-bca9-b8dbdced864f   (Donate — no image)
N8_PAGE_ID=adcd6115-a566-4e76-9b85-201b8373e661   (Contact — no image)
N9_PAGE_ID=9219a32c-f3a2-406a-a358-278636cdfdd3   (Newsletter Archive — no image)
```

Confirmed: none of N4–N9 reference `amara-okafor-portrait.jpg`,
`amara-portrait-square.jpg`, or `volunteer-drive-banner-2025.jpg`. All nine
page titles (N1–N9) are unique.

## External image URLs — verified live (HTTP 200, image/jpeg)

```
amara-okafor-portrait.jpg   -> 200 image/jpeg 308222 bytes
amara-portrait-square.jpg   -> 200 image/jpeg 277530 bytes
jordan-mentor.jpg           -> 200 image/jpeg 304486 bytes
workshop-participant.jpg    -> 200 image/jpeg 291502 bytes
```

## REST API-behavior verification

```
ARCHIVE_TEST=pass (temporary test block archived through PATCH /v1/blocks/{test-id})
DIRECT_ARCHIVED_BLOCK_READ=pass (GET /v1/blocks/{test-id} returned archived=true)
ARCHIVED_VISIBLE_IN_CHILD_LIST=no (GET /v1/blocks/{root-id}/children omitted the archived test block)
RESTORE_TEST=pass (PATCH /v1/blocks/{test-id} restored it; direct read returned archived=false)
CLEANUP_TEST_BLOCK_ARCHIVED=yes (the temporary test block was archived again)
PUBLICATION_VERIFIED=no (blocked: no publish tool; manual step required)
```

The archive/read/restore sequence used a newly created temporary paragraph
under the Riverbend Website root. N1, N2, and N3 image blocks were read and
matched by their exact registered external image URLs but were not modified.

## Manual steps remaining

1. Publish "Riverbend Website" to web (Notion UI: Share → Publish to web),
   then record the public URL here.
