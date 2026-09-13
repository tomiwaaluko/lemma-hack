# Recall Desk — 2-minute demo

Target spoken length: **105–115 seconds**. Closing line lands before 2:00.

Label the take `LIVE`. Reset and show `check-fixtures ✓ PASS` before recording.

## Exact command sequence

Run from the repo root. Credentials must already be in the environment. Do not skip reset.

```powershell
python -m recall_desk.cli reset
python -m recall_desk.cli check-fixtures
```

Expect `reset PASS`, then `check-fixtures ✓ PASS`. If fixtures fail, stop. Do not record.

Keep these open in the browser before you start:

1. Airtable → Permission Changes → **REQ-001** (Amara's request text)
2. Notion → **Volunteer With Us** (N1 hero) and **2024 Spring Workshop Recap** (N2)
3. Trello → **Oct Volunteer Drive: Instagram carousel** (T1) and **Workshop anniversary throwback** (T2)

Then run:

```powershell
python -m recall_desk.cli run REQ-001 --approve
```

Current CLI: `--approve` is a flag, not an interactive `y` prompt.

After the run:

1. Notion: N1 image block archived on Volunteer With Us; N2 recap still visible
2. Trello: T1 in **Rights Hold** with the Rights hold label and same-request comment; T2 unchanged
3. Terminal / `runs/{run_id}.md`: counts and `Final result: NEEDS_FOLLOW_UP`

Optional after the take:

```powershell
python -m recall_desk.cli reset
```

## Script (~110 seconds)

### 0:00–0:15 — problem + pitch

**On screen:** title card, then Airtable REQ-001.

**Say:**
> Permissions are scoped. Takedowns usually aren't. If someone says "stop using my photo for this, but keep that," most teams either delete everything or miss a copy. Recall Desk enforces the scoped change — and only that change.

### 0:15–0:30 — Amara / Airtable

**On screen:** REQ-001 request text. Airtable is the rights registry.

**Say:**
> Amara asked Riverbend to stop using her photo for volunteer recruitment, and to keep the 2024 Spring Workshop Recap. Airtable is what they're allowed to do.

### 0:30–0:45 — Notion and Trello before the run

**On screen:** Notion Volunteer With Us (live N1) and the recap page (N2). Trello T1 in the planned list; T2 anniversary card still there.

**Say:**
> Notion is what's live: the recruitment hero, and the recap she asked to keep. Trello is what's about to go live: a volunteer carousel, and an anniversary post whose last slide isn't decided.

### 0:45–1:15 — run Recall Desk

**On screen:** terminal.

```text
python -m recall_desk.cli reset
python -m recall_desk.cli check-fixtures
python -m recall_desk.cli run REQ-001 --approve
```

Show `check-fixtures ✓ PASS`, then the run. Leave the action-to-result sequence uncut.

**Say:**
> Reset to the known fixtures. Check they match. Then Recall Desk runs. The model looks at meaning. Code matches exact registered files, journals each write before it hits the API, and verifies what actually changed.

### 1:15–1:35 — after: Notion archive + Trello hold

**On screen:** Notion Volunteer With Us with N1 gone; recap page unchanged. Trello T1 in Rights Hold.

**Say:**
> The recruitment image is archived. The recap stays. The planned carousel is in Rights Hold — moved, labeled, and marked to this request — so a rerun won't hold it twice.

### 1:35–1:50 — summary

**On screen:** terminal counts or `runs/{run_id}.md`.

**Say:**
> One removed, one held, two preserved. One uncertain — the anniversary slide. One manual — the printed flyer. Zero failed. Needs follow-up. Code computed that; the model doesn't get to call it done.

### 1:50–2:00 — reliability close

**On screen:** title card, or a journal / report line if it is already on screen. Do not show invented eval numbers.

**Say:**
> If a write comes back unknown, it records SENT, reads the live object, and reconciles — it doesn't blindly retry. Permissions are scoped. Recall Desk makes enforcement scoped, too.

## Timing notes

- If the live run overruns 0:45–1:15, shorten the 0:30–0:45 tour, not the close.
- Do not narrate metrics from `eval/report.md` unless that file is frozen in git for this commit.
- Do not present sim UI as live footage.
