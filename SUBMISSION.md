# Recall Desk — hackathon submission copy

Paste-ready. Fill the two placeholders before submit. Do not invent eval numbers.

---

## 1. One-line project description

Recall Desk enforces a scoped media-permission change across Airtable, Notion, and Trello — removing one use without wiping the rest.

---

## 2. Project summary (~75 words)

Recall Desk enforces a scoped media-permission change across Airtable, Notion, and Trello. A person can withdraw one use of a photo without deleting every copy. Amara asks Riverbend Youth Makerspace to stop using her picture for volunteer recruitment and keep the 2024 Spring Workshop Recap. The desk archives the live recruitment image, holds the planned carousel, leaves the recap, and reports what it cannot decide or reach. Code computes the final result: needs follow-up.

---

## 3. Project summary (~150 words)

Permissions are scoped. Takedowns usually are not. Small teams keep rights in one app, live pages in another, and the editorial calendar in a third, so a consent change either wipes everything or misses a copy about to go live.

Recall Desk takes one approved permission change for one asset across Airtable, Notion, and Trello. A person approves the scope, not individual clicks. Code finds uses by exact registered URL or unique filename, not face matching. A language model investigates purpose from read-only evidence and returns REMOVE, PRESERVE, or UNCERTAIN. Code validates those verdicts, journals SENT before every external write, executes only permitted removals, and reconciles unknown outcomes by reading the live object. UNCERTAIN never authorizes content mutation.

In the Riverbend demo: one archived Notion image, one Trello Rights Hold, two preserved uses, one uncertain planned post, one manual printed flyer, and a computed result of needs follow-up.

---

## 4. Problem

A volunteer can say: stop using my photo for recruitment, but keep the workshop recap. That is a scoped permission change. Most teams cannot enforce it.

Rights live in a register. Published pages live in a CMS. The next post lives on an editorial board. Someone fixes the page they remember and misses the carousel about to ship — or they delete every copy, including the use the person asked to keep. Mentions of a name, printed flyers, and unclear planned posts get lumped in with exact image uses.

The failure is not “we need more AI.” The failure is unscoped enforcement.

---

## 5. Solution

Recall Desk is a bounded agent that enforces one approved, scoped media-permission change.

- **Airtable** is what the organization is allowed to do.
- **Notion** is what is live.
- **Trello** is what is planned.

Code matches exact registered asset identifiers, not faces. The model investigates whether each matched use falls inside the approved scope. Code decides the permitted action, records the write in a durable journal, performs the API call, and verifies the live object.

Validated REMOVE archives a Notion image block or holds a Trello card (move, label, same-request marker). PRESERVE and UNCERTAIN do not mutate content. Uses outside connected systems are listed as manual follow-up. The final result is computed by code. Needs follow-up is an honest outcome, not a failed run.

---

## 6. How Recall Desk uses AI

The model is an investigator, not an API client. It has no tools that archive Notion blocks, move Trello cards, or write the run result.

It is used to:

1. Interpret a natural-language permission request into a scope a person approves once.
2. Investigate each matched occurrence against that scope, using a starter evidence packet and a small budget of read-only tools.
3. Return REMOVE, PRESERVE, or UNCERTAIN with rationale and evidence quotes.

Code then:

- matches identifiers
- validates evidence (rules only move a decision toward UNCERTAIN)
- maps verdicts to permitted actions
- journals SENT before each external write
- reconciles unknown outcomes by reading
- verifies results and computes the final status

If evidence is missing or conflicting, the verdict is UNCERTAIN and the content object is left unchanged.

---

## 7. Apps integrated

**Airtable — Riverbend Media Rights.** Source of the permission-change request, asset variants (canonical URL and filename), and occurrence registry. Recall Desk reads coverage from here and writes run bookkeeping (execution state, final result, counts). It is what the organization is allowed to do.

**Notion — Riverbend Website.** Live content. Registered image blocks are matched by exact URL. A REMOVE archives the image block on the page (restorable by an admin). Retained pages, including the 2024 Spring Workshop Recap, are verified unchanged.

Public site: https://positive-canvas-c11.notion.site/Riverbend-Website-3daf279e86cf81bb90a4e9589d691df6

**Trello — Riverbend Content Calendar.** Planned editorial content. A REMOVE is a composite hold: move to Rights Hold, add the Rights hold label, add a same-request marker comment. Partial holds are not rolled back. A later run that sees the same-request marker does not duplicate the hold.

---

## 8. Reliability approach

Reliability is a split of labor, not a vibe.

- **Exact match only.** Canonical URL, or a filename that maps to exactly one variant. No vision, face match, or fuzzy match. Ambiguous identifiers are not sent to the model and are not mutated.
- **Human checkpoint.** A person approves the permission scope once before content mutation.
- **No model writes.** The model cannot mutate Notion or Trello.
- **Plan validation.** Content writes target only the validated REMOVE set.
- **SENT before send.** The journal commits SENT to SQLite before the HTTP call.
- **Reconcile, don’t guess.** If a write’s result is unknown, read the live object. Retry only if the effect is absent and retry remains safe. No blind resend.
- **Composite Trello hold.** Move + label + marker; no rollback of a partial hold; idempotent on rerun.
- **Fail-safe UNCERTAIN.** Missing or conflicting purpose → no content mutation, manual follow-up with the evidence gap.
- **Honest finale.** Code computes FAILED_SAFE, PARTIAL, NEEDS_FOLLOW_UP, or COMPLETE. The model cannot override it.
- **Coverage boundary.** Connected systems plus the registry. Everything else is listed, not guessed.

Measured eval numbers, when frozen, come only from `eval/report.md`. They are not hand-edited and are not claimed here.

---

## 9. What makes it original

Most “AI + three apps” demos let the model click around until something looks done. Recall Desk treats a permission change as a scoped enforcement problem.

Original pieces:

- **Scoped takedown, not blanket delete.** Keep the recap; remove recruitment; hold planned reuse.
- **Three-app split that matches how the work actually lives:** allowed / live / planned.
- **Identity is code; meaning is the model.** Exact files vs. purpose. The model never decides which bytes are Amara’s photo.
- **UNCERTAIN is a product behavior.** The anniversary post’s last slide is undecided, so nothing changes, and the report says why.
- **Writes are journaled and verified.** SENT-before-write and read-back reconciliation, including a composite Trello hold that will not duplicate itself.
- **The run can refuse to call itself done.** Needs follow-up is the correct result when something remains human.

---

## 10. Demo walkthrough

**Setup (not in the cut):** `python -m recall_desk.cli reset` then `python -m recall_desk.cli check-fixtures`. Record only if fixtures pass.

**On screen, in order:**

1. Airtable REQ-001: Amara’s request — stop volunteer-recruitment use; keep the 2024 Spring Workshop Recap.
2. Notion before: recruitment hero present; recap page present.
3. Trello before: Oct Volunteer Drive carousel in a planned list; anniversary throwback still there.
4. Terminal: `python -m recall_desk.cli run REQ-001 --approve`.
5. Notion after: recruitment image archived; recap unchanged.
6. Trello after: carousel in Rights Hold with label and marker; anniversary card unchanged.
7. Summary: 1 removed, 1 held, 2 preserved, 1 uncertain, 1 manual, 0 failed. Final: NEEDS_FOLLOW_UP.

**Closing line:** Permissions are scoped. Recall Desk makes enforcement scoped, too.

Full timed script: `DEMO.md`.

---

## 11. Tech stack

- Python 3.12
- Anthropic API (investigative model; read-only tools)
- Live REST adapters: Airtable, Notion, Trello (`httpx`)
- Pydantic domain types
- SQLite durable journal (`SENT` before write)
- pytest
- CLI entry: `python -m recall_desk.cli`

Demo content is fictional (Riverbend Youth Makerspace / Amara Okafor). Images are hosted as registered files, not identified by vision.

---

## 12. Known limitations

- No legal or policy judgments. A person approves the permission scope; the agent only classifies connected occurrences against that scope.
- No guessing. Unclear uses are left unchanged and listed for a person.
- “Removed” means the Notion image block is archived. It does not wipe caches, screenshots, or email already sent.
- “Held” flags a Trello card in the team’s workflow. It does not technically prevent someone from publishing.
- Coverage is the connected Airtable base, Notion site, and Trello board, plus registry rows. Printed matter and other apps are manual follow-up.
- Only uses of the registered image count. Name mentions in text are out of scope.
- One request, one asset, one run. No webhooks, scheduled re-checks, or a fourth app.

---

## 13. Repository

https://github.com/tomiwaaluko/lemma-hack

*(Confirm this is the public URL before paste.)*

---

## 14. Demo video

[DEMO VIDEO URL]

---

## 15. Public demo Notion site

https://positive-canvas-c11.notion.site/Riverbend-Website-3daf279e86cf81bb90a4e9589d691df6

---

## Fallback: 30-second demo script

Use only if the two-minute take will not land. Label `LIVE`. Reset and show `check-fixtures ✓ PASS` first.

**0:00–0:08** Airtable REQ-001.
> Amara asked us to stop using her photo to recruit volunteers, but keep the workshop recap. Deleting everything is wrong. Missing a copy is worse.

**0:08–0:18** Terminal run, then Notion archive + Trello Rights Hold.
> Recall Desk finds the exact files. It archives the live recruitment image, holds the planned carousel, and leaves the recap.

**0:18–0:30** Counts / title card.
> One removed, one held, two preserved, one uncertain, one manual. Needs follow-up — not “done.” Permissions are scoped. Recall Desk makes enforcement scoped, too.
