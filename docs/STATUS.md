# ISPE Strategic Plan Dashboard — Status / Handoff

_Cold-start snapshot. Read this first, then `DECISIONS.md` for the "why". Last updated: 2026-08-03._

> **Next session starts here:** `MIGRATION-private-repo.md` — take the working repo private, replace ISPE's
> fork with a push-to-publish Action, and move review into a Codespace. Planned in full, **nothing executed.**
> Read its "Decisions needed before starting" section first; three questions gate the work.

## Start here (cold start)

```bash
# Look at it / edit it. The helper is what makes Save and Publish real git actions.
python3 admin-server.py          # → http://127.0.0.1:8800/admin.html  (editor)
                                 # → http://127.0.0.1:8800/index.html  (public view)

# Just viewing, no editing:
python3 -m http.server 8000      # → http://localhost:8000/index.html

# Ingest a new survey cycle (defaults to the newest "SP Reports*.csv" here):
git checkout main -- data.json   # always start from the published version
python3 csv_to_dashboard_json.py
```

| | state |
|---|---|
| `main` | current through 2026-08-03, includes the 7.30 cycle; pushed |
| `new-csv-format-intake` | **merged into `main`** (2026-08-03, merge `faa9a3d`). Kept as a record; no longer the working branch |
| `public-deploy` | **synced 2026-08-03** — the July cycle is live |
| BSCL Pages | serving **`public-deploy`** — `admin.html` is **no longer public** (404 verified) |
| ISPE fork | **does not exist yet** (404 re-verified 2026-08-03) — and per the migration plan it never will |
| BSCL repo | **public**, Team plan, 0 forks / 0 stars / 0 watchers. Going private retracts nothing |

**Uncommitted / unpushed as of the end of the 2026-08-03 session:**
- `main` is **1 commit ahead of origin** — `8d587e6`, the at-risk provenance markers. Admin-only, so the
  public site is unaffected either way. Push it or don't; nothing depends on it.

**Open items** (as of 2026-08-03):
0. **Migrate to a private working repo with push-to-publish** — the plan is written
   (`MIGRATION-private-repo.md`) and is the intended next session. Supersedes item 7 below.
1. ~~Flip BSCL Pages to `public-deploy`~~ — **done.** `admin.html` now returns 404 publicly.
2. ~~Confirm the footer copyright holder~~ — **confirmed: ISPE owns it.** The footer was already correct.
3. ~~Absorb the new CSV format~~ — **done**, merged to `main`. See "The 7.30 cycle" below.
4. ~~Set `as_of_date` before publishing~~ — **done.** It reads **July 2026**. It stays curated in the admin
   panel on purpose and cannot be derived from a file that carries no dates, so **it will need setting again
   next cycle.**
5. ~~Review and merge `new-csv-format-intake`, then sync `public-deploy`~~ — **done 2026-08-03.** Both
   branches pushed; the July cycle is live on the BSCL Pages site.
6. **The rest of the cycle is outstanding** — only 6 committees reported; the user is waiting on the others.
   When they arrive, follow "Updating the data" below — and note that step 2 (reset `data.json` first)
   matters more than usual now, because a second partial cycle merges onto this one.
7. ~~How ISPE receives updates~~ — **answered 2026-08-03, see item 0.** The fork model is abandoned: forks
   inherit visibility, a private fork cannot be made public, and `ISPE-SP` is a personal *user* account whose
   Pages serves public repos only. Publishing becomes a push into a separate public repo, which also deletes
   the "Sync fork" click that put ISPE on the critical path. **Still requires ISPE's cooperation once** — to
   create the public repo and add a deploy key — but never again after that.

## The 7.30 cycle (what just happened)

`SP Reports 7.30.2026.csv` arrived on 2026-07-31 and is **a different export format, permanently** — a
report export rather than the raw Alchemer dump. Committee is column 0, the whole `Response ID` /
`Time Started` / `Date Submitted` / `Status` block is gone, headers are full of non-breaking spaces, and the
new-tactic question became a structured repeating group. Run unchanged, the old script would not have
crashed — it would have mis-attributed every answer. `DECISIONS.md` has the full account.

What that produced, and what is now true of the pipeline:
- **Cycles are partial.** The script **merges** by default: CSV → existing `data.json` → plan default. Never
  run it twice in a row without resetting `data.json` first; the second run merges onto the first run's
  output and masks any correction in between. The script warns when it detects this.
- **The CSV has no dates.** The cycle date is derived from the **filename**. Everything dated "July 2026"
  traces back to `SP Reports 7.30.2026.csv`, not to anything in the file.
- **Revised / New now refreshes from the survey**, which the older notes listed as an open question.

## What this is
A static, client-side dashboard tracking progress on the ISPE Strategic Plan (2024–2029).
99 tactics across 8 objectives/goals, of which **95 are active and 4 retired**. Served via GitHub Pages and
intended to be embedded on the ISPE website as an `<iframe>`. No backend — everything runs in the browser.

## Repo layout (branch model)
- **`main`** — the working repo. Contains:
  - `index.html` — the **public** dashboard (no admin controls, no at-risk panel, no search box)
  - `admin.html` — the **admin/editor** (at-risk panel, Admin Control Panel, search box, As-of date picker)
  - `data.json` — the data the dashboards fetch at runtime (committee-level only, **no PII**)
  - `csv_to_dashboard_json.py` — merges a survey report CSV into `data.json` (see "Updating the data")
  - `admin-server.py` — **local** helper: serves the dashboard and turns admin's Save/Publish into
    real git commits/pushes. Run `python3 admin-server.py`, then open http://127.0.0.1:8800/admin.html
  - `fonts/` — self-hosted Source Serif 4 (woff2 + SIL OFL licence)
  - `docs/` — this documentation: `STATUS.md` (here), `DECISIONS.md` (the why),
    `MIGRATION-private-repo.md` (the planned next phase)
  - `.gitignore` — allowlist (only tracks the files above + images); **the raw survey CSV is intentionally NOT tracked (it contains names/emails/IPs)**
- **`public-deploy`** — the deploy branch: **public dashboard only** (`index.html`, `data.json`, `fonts/`,
  images, `README.md`). `admin.html`, `admin-server.py`, and the CSV script are deliberately excluded so they
  can never be published to the public site. This is the branch GitHub Pages *should* serve.
  - It has its **own separate allowlist `.gitignore`** — different from `main`'s. Anything new that
    `index.html` depends on must be allowlisted there too, or it silently won't ship. `fonts/` was added
    on 2026-07-27 for exactly this reason.
  - The branch is maintained by **copying `index.html` from `main`**, not by merging. **Synced 2026-08-03**
    (`e13de00`): `index.html` and `data.json` were copied verbatim from `main` and verified identical to it.
    Sync it again after every `data.json` regeneration, or the public site keeps showing the last cycle.

## Live URLs & deployment state (Pages verified 2026-07-27; fork re-checked 2026-08-03)
- **Black Swan (live now):** https://black-swan-causal-labs.github.io/ISPE-Strategic-Plan-Dashboard/
  - **Pages serves `public-deploy`** (switched 2026-07-27). Verified live: `index.html` 200,
    `admin.html` **404**, `fonts/` 200. The admin panel is no longer reachable from the internet — it is a
    local tool, run via `python3 admin-server.py`.
  - This is "not published", not "access-controlled". If admin ever needs to be shared with ISPE leaders,
    that is a separate problem (GitHub Pages on a public repo has no auth) — see DECISIONS.
- **ISPE (not yet created):** `github.com/ispe-sp/ISPE-Strategic-Plan-Dashboard` still returned **404** when
  re-checked on **2026-08-03** — **ISPE has not forked yet**, and per the user they will not until the format
  work is absorbed and the new data ingested. Nothing downstream is stale, and the window to settle the
  sync question before a fork exists is still open.
  - When they fork: **uncheck "Copy the main branch only"** or `public-deploy` won't come across and
    there will be nothing to point Pages at.
  - They then enable Pages on `public-deploy`, giving
    https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/ ← the iframe `src`.
- **⚠️ Forks do not auto-update** — every refresh would need someone at ISPE to click **"Sync fork,"** putting
  the party least able to act quickly on the critical path, failing silently as a public dashboard showing
  last quarter's numbers. **This is why the fork model was abandoned on 2026-08-03.** The replacement is a
  push into a separate public repo — see `MIGRATION-private-repo.md`. Still true, and still the reason,
  until that migration runs.

## Embed
```html
<div style="max-width:1200px; margin:0 auto;">
  <iframe src="https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/"
    title="ISPE Strategic Plan Progress Dashboard" loading="lazy"
    style="width:100%; height:1800px; border:0; border-radius:8px;" referrerpolicy="no-referrer"></iframe>
</div>
```
Paste into a "Custom HTML" block. GitHub Pages allows external iframing. The page detects
framing itself and un-pins its sticky chrome, so the host page needs to add nothing.

**On the height.** Measured collapsed content, 2026-08-10: 1742px at 1200px wide, 1927 at 900,
1986 at 760, 1988 at 600, 2708 at 414, 2910 at 380. The old value of 1400px was shorter than
the desktop view and scrolled inside the frame — the nested-scroll problem the embedded mode
exists to avoid. 1800px clears the desktop collapsed view. **No fixed height fits every case**:
phones and any expanded objective will still scroll within the frame. Only a postMessage
resizer fixes that exactly, and it requires the host page to cooperate.

## Data pipeline (how the dashboard gets its numbers)
1. **Plan structure** (the list of objectives/goals/tactics, plus `is_revised` / `is_new_in_plan` flags)
   is the source of truth and lives as `const DEFAULT_DATA = {...}` embedded in **`index.html`**.
2. `csv_to_dashboard_json.py` reads that plan structure **+** the survey report CSV **+ the existing
   `data.json`** and writes a new `data.json`. Each tactic resolves **CSV → existing `data.json` → plan
   default**, so a cycle that only covers some committees does not roll the rest back to March 2026.
   `--no-merge` restores the old rebuild-from-plan behaviour.
3. Both `index.html` and `admin.html` **fetch `data.json`** at load. If the fetch fails they fall back to
   their own embedded `DEFAULT_DATA`. So on the live site, `data.json` (when present) is what's displayed.
4. To update the live site, commit the new `data.json` to the deployed branch(es).

The script prints a report every run: value sources, status counts, who reported, column coverage, columns
recognized but deliberately not consumed, and any status cell that matched no known value. **Read it.** It is
the only thing standing between a malformed cycle and a plausible-looking wrong dashboard.

## Current state (as of this handoff, on `main` — and live on `public-deploy`)
- **99 tactics, of which 95 are active and 4 are retired.** Active split: 43 On Track, 21 Not Started,
  24 Completed, 7 Delayed.
- **Retired = 3.1.4, 3.1.5, 3.1.6, 3.1.7**, superseded by a proposed tactic 3.1.8 that **does not exist in
  the plan yet**. They stay listed in goal 3.1 with a `RETIRED` badge and a dagger, and are excluded from
  every progress count — rings, goal `n/m`, objective totals, all the summary cards, mini pills, at-risk.
- **Revised / New = 17** on the card; the **Revisions section badge reads 21**. They differ on purpose: the
  card excludes retired tactics so every card describes the same 95, the section includes them because being
  retired *is* the revision. See DECISIONS if this looks like a bug.
- **Goal/objective progress is a plain count over active tactics** — goal 3.1 reads `3/3`, objective 3 reads
  `5/9`. The old `x/10` scale is gone. Stored `progress_score` fields are intentionally unused.
- **At Risk = 28** (21 Not Started + 7 Delayed, retired excluded) — **admin view only**. Of those, only
  **3 were reconfirmed in the July cycle**; **24 are carried forward** from Feb/Mar 2026 and **1 (5.3.5) has
  never been reported at all**. Down from 37 in April, but 4 of that drop is the retirement of 3.1.4–3.1.7
  rather than progress. The panel now marks this per row — see "At Risk" under Key UI components.
- Header "As of …" comes from `metadata.as_of_date` (admin picker) and reads **July 2026**. The line under
  it — "Survey data through July 2026 · 6 committee responses this cycle" — comes from
  `metadata.cycle_label` / `cycle_committees`. Both are correct and agree.

## Key UI components
- **Summary cards** — the 4 status cards partition the **95 active** tactics; **"Revised / New*"** is a
  separate overlay tag (a revised tactic still has one of the 4 statuses), explained in the footnote under
  the cards, which also states how many tactics are retired and excluded.
- **Revisions & New Tactics** (renamed from "Changes & New Tactics" on 2026-08-03) — collapsible,
  List/Timeline toggle. Each revised tactic shows the committee's own explanation and its date; dates come
  from `revised_at` per tactic, falling back to `metadata.tracker_label`, and are no longer hardcoded.
- **Retirement note** — sits between the last objective and the contact card, explains the dagger on retired
  rows, and states the active total. Rendered by `renderRetiredNote()`; empty when nothing is retired.
- **Completed Tactics** — collapsible, grouped by objective (no timeline: there's no true completion date;
  the only date is the survey-report date, which clusters into ~2 months — see DECISIONS).
- **At Risk** — admin-only; **active** tactics reporting Not Started or Delayed, grouped by objective with
  short themes. Retired tactics are excluded: flagging superseded work would send leadership chasing it.
  - **Provenance markers (added 2026-08-03).** Each row whose status was not reconfirmed this cycle carries
    an *as of Mmm YYYY* marker, or **never reported** when no committee has ever answered for it. A header
    line gives the split. Freshness is judged **per tactic, not per committee**: a committee can file a
    report and still leave individual tactics blank — Executive reported in July and left 8.2.3 and 8.2.5
    blank — so committee-level attribution would have marked those current when they are five months stale.
  - The signal is `last_reported_at`: the current export carries no submission date, so a value from this
    cycle lands `null` while a carried-forward value keeps the timestamp of the cycle it came from. If a
    date column is ever restored, `tacticFreshness()` falls back to comparing against `metadata.cycle_date`.
  - `COMMITTEE_ALIASES` folds **`Executive/Impact` → `Executive`** (same committee). It only affects the
    hover text, which distinguishes "reported but left this blank" from "has not reported at all".
- **Footer** — 2026 copyright + "Dashboard designed and built by Black Swan Causal Labs, LLC".
  The contact line ("Questions about the content? Email info@pharmacoepi.org") now sits in its own card
  between the last objective and the footer.
- **Status encoding** — colour **plus a glyph** (`○` `▶` `!` `✓`) on every badge. The palette is
  CVD-validated; see DECISIONS before changing any status colour.

## ⚠️ Open questions / watch-outs for the next survey cycle
- ~~The recurring-update path is unproven~~ — **resolved 2026-08-03, and it broke.** The re-upload was a
  different export format, not a refresh. See "The 7.30 cycle" above and `DECISIONS.md`. Treat the *next*
  cycle with the same suspicion: read the script's run report before trusting the output.
- ~~"Revised / New" does NOT reset from a new CSV~~ — **fixed 2026-08-03.** A survey `Changed` answer now
  sets `is_revised`, on top of the flags baked into `DEFAULT_DATA` from the March 2026 tracker. Note the
  goal-level "Have you revised Strategic Goal X.Y?" question is **deliberately not used** — it asks about the
  goal's own wording, and Executive answered No for goal 3.1 while marking four of its tactics `Changed`.
- **Blank no longer means Not Started.** `Not started` appears **zero** times in the new export (29 in the
  old one); unreported tactics are blank. Blank now means not started, or not reported this cycle, or not
  this committee's goal, and nothing in the file distinguishes them. **Unresolved.**
- **Junk in status cells is reported, not mapped.** Three `N/A` cells and two respondents typing a sentence
  into a status dropdown appear in the run report. They carried forward correctly this cycle by luck. No
  mapping rule exists yet.
- **At-risk columns are no longer strictly one-per-tactic** (81 for 99; some goals ask once for a block of
  three). A block answer is attributed to the *last* tactic in the block. Also, at-risk text is now mostly
  *negations* — "The tactic is not at risk…" — so never treat a non-empty at-risk cell as "at risk".
- **The script is not automatic** — someone must run `csv_to_dashboard_json.py` with the new CSV, then commit
  `data.json`. **Import/Export JSON were removed on 2026-07-27** — see below.
- **Never run the script twice without resetting `data.json` first.** The second run merges the cycle onto
  its own output, so anything you corrected in between is masked by carried-forward values. The script
  detects and warns about this, but the warning does not stop the write.
- **Retirement is a curated list** in `csv_to_dashboard_json.py` (`RETIRED`), because the survey has no
  structured retirement field. Future retirements mean editing that dict — and are worth raising with ISPE
  as a survey change if it keeps happening.
- **`admin.html` is publicly reachable on any branch a Pages site serves** (GitHub Pages on a public repo
  has no auth). It is kept off `public-deploy` for exactly this reason. **On BSCL this is now resolved** —
  Pages was switched to `public-deploy` on 2026-07-27 and admin returns 404. The warning still applies to
  ISPE's fork: whatever branch they serve is public.
- **Mobile verified 2026-07-27** at 390 / 360 / 320 px (iframe viewports, which is what the media queries
  respond to). No horizontal overflow at any width, zero elements past the right edge, root correctly drops
  to 16px, summary grid reflows 2→1 columns, tactics table stacks into cards with 13.6px body text. The
  serif holds up at small sizes. *Still worth a glance on a real handset* for touch-target feel, but the
  layout question is settled.
- ~~Survey free-text interpolated into `innerHTML` unescaped~~ — **fixed 2026-07-27.** An `esc()` helper now
  wraps all data-derived values (30 sites in `index.html`, 41 in `admin.html`, including the string-concat
  form inside `publishReadOnly`). Verified by injecting a payload into `data.json`: on the pre-fix build the
  `onerror` handler executed and an element was injected; after the fix it renders as inert text.
  **Keep using `esc()` for any new interpolation of survey-sourced text.**
- **`public-deploy` needs `fonts/` too.** It is a separate branch that omits `admin.html`; if `index.html`
  is updated there without the `fonts/` directory, Source Serif 4 silently falls back to Georgia.
- **Editing two copies of the plan:** `DEFAULT_DATA` exists in both `index.html` and `admin.html`. Any
  structural plan change (add/remove a tactic, reset flags) must be made in both, and reflected in `data.json`.
  The script only reads/writes via `index.html` + `data.json`.
- **The render code is duplicated too.** `renderChanges`, `renderSummary`, `computeGoalProgress`,
  `renderRetiredNote` and the retirement helpers exist in **both** HTML files. Every fix lands twice. When
  patching both, assert the match count per file so a string that has drifted fails loudly instead of
  silently skipping one copy.
- **Tactic 3.1.8 does not exist yet.** Four retired tactics name it as their successor, but goal 3.1 still
  runs .1 to .7. Adding it is a `DEFAULT_DATA` edit in both files plus a `data.json` regeneration.

## Import / Export JSON were removed (2026-07-27)
Both buttons are gone from the Admin Control Panel. Git covers what they did, better:
- **Export** was the only real save before `admin-server.py` existed. Now **Save** commits `data.json`, so
  history, backups, diffs, and sharing all come from git.
- **Import** was never needed by the pipeline: `csv_to_dashboard_json.py` writes `data.json` directly and
  both pages fetch it on load, so a new cycle is "regenerate the file, reload the page". Restoring an older
  version is `git checkout <sha> -- data.json`, which has history and cannot be pointed at the wrong file.
- It was also the most destructive control in the tool — one click replaced the whole plan.

`validate_payload()` **remains in `admin-server.py`** and still guards every write, since Save/Publish is
now the only path that overwrites `data.json`.

## Updating the data (workflow)
1. Get the new survey report CSV. Name it `SP Reports <M.D.YYYY>.csv` — **the date in the filename is the
   only cycle date there is**, since the export carries none. Keep it out of git (the allowlist already
   excludes it; the older raw exports contain PII).
2. **Reset first:** `git checkout main -- data.json`. Skipping this merges the cycle onto whatever the last
   run produced.
3. Run `python3 csv_to_dashboard_json.py` (no argument picks the newest `SP Reports*.csv`; pass a path to
   choose). It reads `index.html`'s `DEFAULT_DATA` + the CSV + the existing `data.json` → writes `data.json`.
4. **Read the run report.** Check the source split, the status counts, the tactic-column coverage, and
   especially any status cell that matched no known value. Then review the diff on `data.json`.
5. If tactics were retired this cycle, add them to `RETIRED` in the script and re-run from step 2.
6. Set the **As-of date** in the admin panel — it is not derived from the CSV.
7. Commit `data.json` to `public-deploy` (public site) and/or `main`. Pages redeploys in ~1 min.
   **Or** run `python3 admin-server.py`, edit in the admin panel, and press **Save** (commits) or
   **Publish** (commits + pushes). Note that without the helper running, admin edits live only in the
   browser and **do not survive a reload** — `localStorage` is written but never read back.
8. If any tactics were added/removed or plan-level flags should change, edit `DEFAULT_DATA` in both HTML
   files too.
