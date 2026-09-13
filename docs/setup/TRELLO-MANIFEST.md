# Trello Fixture Manifest — Riverbend Content Calendar

Created 2026-09-13 through the connected Trello MCP (workspace "Hackathons", `6aa6c2ec45072daf117af234`).
IDs below are Trello object IDs. The MCP addresses objects by ARI:
`ari:cloud:trello::<type>/workspace/6aa6c2ec45072daf117af234/<objectId>`.

No credentials or tokens are stored in this file.

BOARD_ID=6aa6f706da9b20af34821101
BOARD_URL=https://trello.com/b/pKGVbDbn/riverbend-content-calendar

LIST_ID_IDEAS=6aa6f7232ef473a406e41d7a
LIST_ID_IN_PRODUCTION=6aa6f729bd56ec9218932d83
LIST_ID_SCHEDULED=6aa6f7329f47ad4f0543640f
LIST_ID_PUBLISHED=6aa6f7393b77252f03d70434
LIST_ID_RIGHTS_HOLD=6aa6f742cf8902339a999830

RIGHTS_HOLD_LABEL_ID=PENDING — see "Remaining manual steps" (candidate: 6aa6f706da9b20af3482110a, red, currently unnamed)

T1_CARD_ID=6aa6f75b30a189362e5fd0b8
T1_CARD_URL=https://trello.com/c/axmsBWk6/1-oct-volunteer-drive-instagram-carousel
T1_ATTACHMENT_ID=PENDING — manual upload required
T1_ATTACHMENT_FILENAME=PENDING (target: volunteer-drive-banner-2025.jpg)

T2_CARD_ID=6aa6f763644e485160dab57c
T2_CARD_URL=https://trello.com/c/kDWip8yl/2-workshop-anniversary-throwback
T2_ATTACHMENT_ID=PENDING — manual upload required
T2_ATTACHMENT_FILENAME=PENDING (target: amara-okafor-portrait.jpg)

T3_CARD_ID=6aa6f769404ab3b7949589a6
T3_CARD_URL=https://trello.com/c/Ne4AKKLB/3-mentor-spotlight-jordan
T3_ATTACHMENT_ID=PENDING — manual upload required
T3_ATTACHMENT_FILENAME=PENDING (target: jordan-mentor.jpg)

T4_CARD_ID=6aa6f76ff6b70e5b14f587de
T5_CARD_ID=6aa6f77593a9798864f64c8c
T6_CARD_ID=6aa6f77cbb41c345ddba5d70
T7_CARD_ID=6aa6f782a084227b07bb6435
T8_CARD_ID=6aa6f788bd4df552b11baeb2
T9_CARD_ID=6aa6f78e328c137666a77398
T10_CARD_ID=6aa6f794329ea8db38de888e
T11_CARD_ID=6aa6f79a9a57c3db422f4077
T12_CARD_ID=6aa6f7a0481d33cae4a49889

MOVE_TEST=pass
LABEL_ADD_TEST=pass (mechanics verified with the unnamed red label 6aa6f706da9b20af3482110a; named "Rights hold" label not yet present)
LABEL_REMOVE_TEST=pass (same label)
COMMENT_ADD_TEST=not-supported
COMMENT_READ_TEST=not-supported
COMMENT_DELETE_TEST=not-supported
PROBE_CLEANUP=pass

## Cards (verified by MCP read-back)

| Card | Title | List | Due | Labels | Description |
|---|---|---|---|---|---|
| T1 | Oct Volunteer Drive: Instagram carousel | Scheduled | 2026-10-01T13:00:00.000Z (Oct 1, 09:00 EDT) | none | empty |
| T2 | Workshop anniversary throwback | In Production | none | none | exact spec text (two lines, `TBD` preserved) |
| T3 | Mentor spotlight: Jordan | Scheduled | none | none | Jordan volunteer-recruitment copy |
| T4 | STEM Book Recommendations | Ideas | none | none | filler |
| T5 | Tool Safety Tuesday | Ideas | none | none | filler |
| T6 | September Robotics Lab Highlights | In Production | none | none | filler |
| T7 | Donor Thank-You Graphic | In Production | none | none | filler |
| T8 | Open Lab Hours Reminder | Scheduled | none | none | filler |
| T9 | Family Maker Night | Scheduled | none | none | filler |
| T10 | Summer Camp Highlights | Published | none | none | filler |
| T11 | Equipment Upgrade Announcement | Published | none | none | filler |
| T12 | August Newsletter | Published | none | none | filler |

- Rights Hold list: empty (no open cards).
- No card has any comment; no Recall Desk marker anywhere.
- No filler card has an attachment or mentions any registered Amara filename/URL.
- All 12 titles are unique.

## Setup probe

`[Recall Desk setup probe]` (card 6aa6f7a6702df88dae9b78ee) was created in Ideas, moved to Rights Hold and read back (list changed), label attached and read back (present), label detached and read back (absent), then archived (`closed: true`). It does not appear in open-card enumeration.
The comment step was attempted: the MCP rejected `add_comment` (`trelloWriteCard` action enum is create/update/move/archive/mark_done/attach_label/detach_label). No comment was created.

## MCP limitations (connected Trello MCP, 2026-09-13)

- No label create/rename tool → "Rights hold" label cannot be created/named.
- No attachment tool, and card reads do not return attachments → T1/T2/T3 attachments cannot be added or verified.
- No comment add/read/delete → hold marker comments cannot be verified.
- No Trello API key/token is available locally for a REST fallback.

## Remaining manual steps

1. In the board UI, rename the red label `6aa6f706da9b20af3482110a` to `Rights hold` (keeps the ID) and record it as RIGHTS_HOLD_LABEL_ID. Do not apply it to any card.
2. Upload (as files, not URL links) under the registered filenames:
   - T1 ← `volunteer-drive-banner-2025.jpg` (https://tomiwaaluko.github.io/riverbend-assets/images/volunteer-drive-banner-2025.jpg)
   - T2 ← `amara-okafor-portrait.jpg` (https://tomiwaaluko.github.io/riverbend-assets/images/amara-okafor-portrait.jpg)
   - T3 ← `jordan-mentor.jpg` (https://tomiwaaluko.github.io/riverbend-assets/images/jordan-mentor.jpg)
3. With a Trello key/token (REST), capture attachment IDs/names and verify comment add/read/delete on a throwaway card.
