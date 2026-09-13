# Trello Fixture Manifest — Riverbend Content Calendar

Created 2026-09-13 through the connected Trello MCP (workspace "Hackathons", `6aa6c2ec45072daf117af234`).
IDs below are Trello object IDs. The MCP addresses objects by ARI:
`ari:cloud:trello::<type>/workspace/6aa6c2ec45072daf117af234/<objectId>`.

REST verification completed 2026-09-13. No credentials or tokens are stored in this file.

BOARD_ID=6aa6f706da9b20af34821101
BOARD_URL=https://trello.com/b/pKGVbDbn/riverbend-content-calendar

LIST_ID_IDEAS=6aa6f7232ef473a406e41d7a
LIST_ID_IN_PRODUCTION=6aa6f729bd56ec9218932d83
LIST_ID_SCHEDULED=6aa6f7329f47ad4f0543640f
LIST_ID_PUBLISHED=6aa6f7393b77252f03d70434
LIST_ID_RIGHTS_HOLD=6aa6f742cf8902339a999830

RIGHTS_HOLD_LABEL_ID=6aa6f706da9b20af3482110a
RIGHTS_HOLD_LABEL_NAME=Rights hold
RIGHTS_HOLD_LABEL_COLOR=red

T1_CARD_ID=6aa6f75b30a189362e5fd0b8
T1_CARD_URL=https://trello.com/c/axmsBWk6/1-oct-volunteer-drive-instagram-carousel
T1_ATTACHMENT_ID=6aa6fcb1b05037b02ada0f06
T1_ATTACHMENT_FILENAME=volunteer-drive-banner-2025.jpg

T2_CARD_ID=6aa6f763644e485160dab57c
T2_CARD_URL=https://trello.com/c/kDWip8yl/2-workshop-anniversary-throwback
T2_ATTACHMENT_ID=6aa6fcd52c37fb7b903e6e60
T2_ATTACHMENT_FILENAME=amara-okafor-portrait.jpg

T3_CARD_ID=6aa6f769404ab3b7949589a6
T3_CARD_URL=https://trello.com/c/Ne4AKKLB/3-mentor-spotlight-jordan
T3_ATTACHMENT_ID=6aa6fcf2ed707d3daa8b436e
T3_ATTACHMENT_FILENAME=jordan-mentor.jpg

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
LABEL_ADD_TEST=pass
LABEL_REMOVE_TEST=pass
COMMENT_ADD_REST_TEST=pass
COMMENT_READ_REST_TEST=pass
COMMENT_DELETE_REST_TEST=pass
PROBE_CLEANUP=pass

T1_REST_STATE_VALID=yes
T2_REST_STATE_VALID=yes
T3_REST_STATE_VALID=yes
RIGHTS_HOLD_EMPTY=yes

TRELLO_API_KEY_AVAILABLE=yes
TRELLO_TOKEN_AVAILABLE=yes
FRESH_PROCESS_CAN_SEE_BOTH=yes

SECRETS_EXPOSED=no
SECRETS_COMMITTED=no

## Cards (verified by MCP + REST read-back)

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
- Rights hold label exists (red, named), applied to no cards.
- T1/T2/T3 each have one file attachment under the registered filename; REST state valid.
- No card has any comment; no Recall Desk marker anywhere.
- No filler card has an attachment or mentions any registered Amara filename/URL.
- All 12 titles are unique.

## Setup probe

`[Recall Desk setup probe]` (card 6aa6f7a6702df88dae9b78ee) was created in Ideas, moved to Rights Hold and read back (list changed), label attached and read back (present), label detached and read back (absent), then archived (`closed: true`). It does not appear in open-card enumeration.
Comment add/read/delete were verified via Trello REST on a throwaway probe and cleaned up (`COMMENT_*_REST_TEST=pass`, `PROBE_CLEANUP=pass`).

## MCP vs REST notes (2026-09-13)

- Connected Trello MCP: no label create/rename, no attachment tool, no comment add/read/delete.
- REST fallback used for label naming confirmation, attachment ID/filename capture, and comment add/read/delete verification.
- API key and token are available to a fresh process; values are not stored in this repo.
