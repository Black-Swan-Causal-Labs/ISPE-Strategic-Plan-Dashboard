# ISPE Strategic Plan Dashboard — Status / Handoff

_Cold-start snapshot. Read this first, then `DECISIONS.md` for the "why". Last updated: 2026-08-21._

> **Next session starts here:** the live thread is #1.
> 1. **The ISPE-SP fork is two publishes stale — chase the sync.** Their `public-deploy` sits at `38fbcea`
>    (verified 2026-08-21), missing `884a501` (Daniela's three fixes + the 3.1.4 renumbering) **and** `5ca8cbc`
>    (6.2.1 is not completed). So the ISPE-hosted site still says "EFFORTS" and still shows **6.2.1 as
>    Completed** — the precise thing Daniela asked us to remove. We cannot push to their fork; someone at
>    ISPE-SP must click **Sync fork → Update branch** *while viewing `public-deploy`*. Send-ready note in
>    "Handing the fork to ISPE-SP" below. Forking itself is **done** (2026-08-10, Pages correctly on
>    `public-deploy`, `admin.html` 404s).
> 2. **Deploy the reviewer site.** The hosted-admin question is **decided and built** (2026-08-10):
>    `review-site/` is a Cloudflare Pages + Access + D1 app where reviewers comment, flag and approve, and
>    everyone sees everyone's. **Complete review** emails you that reviewer's full summary — one mail per
>    reviewer per cycle, which is the right volume for a site that moves twice a year.
>    **It is LIVE, gated and shared-ready:** https://ispe-sp-review.pages.dev — Cloudflare Access, verified
>    end to end 2026-08-10 including a real completion email (`submissions.delivery = 'sent'`). Test rows
>    were cleared, so the August 2026 board is empty. This supersedes the Phase-6 Codespace step in
>    `MIGRATION-private-repo.md`.
> 3. ~~**Daniela's review feedback is applied but not published.**~~ **Published 2026-08-20** as `884a501`
>    — the three fixes plus the 3.1.4 renumbering reached `public-deploy` in a single copy-across, as
>    intended. `review-site` is merged and level with `main`. **On our Pages this is live; on the ISPE fork
>    it is not** — see #1.

## Start here (cold start)

```bash
# Look at it / edit it. The helper is what makes Save and Publish real git actions.
python3 admin-server.py          # → http://127.0.0.1:8800/admin.html  (editor)
                                 # → http://127.0.0.1:8800/index.html  (public view)

# Just viewing, no editing:
python3 -m http.server 8000      # → http://localhost:8000/index.html

# Ingest a new survey cycle (picks the newest recognized export in this folder).
# FIRST: confirm it is actually new. A re-download under a new name is byte-identical
# and re-dates every revision to the new filename's date. See DECISIONS, 2026-08-21.
md5 "<new export>.csv"                            # compare to metadata.source_file's file
git checkout main -- data.json   # always start from the published version
python3 csv_to_dashboard_json.py "<new export>.csv"   # pass it explicitly: the glob only
                                 # matches 'SP Reports*.csv' and '[0-9]*-SurveyExport.csv',
                                 # and silently ignores anything else
# ⚠️ Re-running this against the August export reverts the 6.2.1 correction.

# Build the payload that is safe to publish (strips committee notes):
python3 build_public_payload.py                      # → public/data.json
python3 build_public_payload.py --check public/data.json   # must exit 0
```

| | state |
|---|---|
| `main` | `881e3e4`, level with origin. August 2026 cycle, complete, plus the 6.2.1 correction |
| `public-deploy` | `5ca8cbc`, level with origin. **Live and current** |
| BSCL Pages | serving **`public-deploy`** — `admin.html` 404 verified 2026-08-10 |
| ISPE fork | Exists and is correctly configured (forked 2026-08-10 15:23 UTC; Pages on `public-deploy`, `admin.html` 404) — but its `public-deploy` is **stale at `38fbcea`, two publishes behind** (verified 2026-08-21). **Needs a manual Sync fork; see "Next session starts here" #1** |
| BSCL repo | **public**, Team plan, **1 fork** (ISPE-SP, since 2026-08-10), 0 stars / 0 watchers |
| `review-site` | **merged; level with `main` at `881e3e4`.** Carried the reviewer site, all three of Daniela's fixes, the 3.1.4 renumbering, and the embed layout fix |
| Cloudflare | Pages `ispe-sp-review` + D1 `ispe-sp-review` + Access app "ISPE Strategic Plan Review" |
| `new-csv-format-intake` | merged 2026-08-03 (`faa9a3d`); kept as a record only |

**Working tree clean, all branches pushed.** `review-site` is no longer held back — the numbering question
settled on 2026-08-20, so its `index.html` / `admin.html` changes went to the public site in the single
publish they were being saved for (`884a501`).

**Open items** (as of 2026-08-10):
1. ~~**ISPE-SP forks + Pages on `public-deploy`**~~ — **done by ISPE, verified 2026-08-20.** They took both
   branches (so they did untick "Copy the main branch only"), pointed Pages at **`public-deploy`** and not
   `main`, and their site serves `index.html` 200 with `admin.html`, `admin-server.py` and both scripts all
   **404**. Their `public-deploy` is at `38fbcea`, identical to ours, and their live `data.json` carries
   **0 committee notes**. The handoff note below is kept as the record of what was asked for.
   **What remains is the recurring step:** each cycle, after we push to `public-deploy`, someone at ISPE must
   open the fork, switch to `public-deploy`, and click **Sync fork → Update branch**. Their site is showing
   the pre-feedback dashboard right now — that is **our** unpublished work, not their fork being stale.
2. **Daniela's feedback on the August cycle (2026-08-10).** Three points; the first two are done on
   `review-site` and live on the reviewer site, **not on the public dashboard**:
   - ~~"95 Efforts" -> "95 tactics"~~ done, and **finished properly on 2026-08-20**. The 08-10 pass claimed
     the donut's centre label was the last holdout; it was not. Three UI strings still said it: the filter
     card heading in **both** dashboards ("Filter Strategic Efforts" -> "Filter Tactics") and the summary
     card in `admin.html`'s `publishReadOnly()` export ("Total Strategic Efforts" -> "Total Tactics").
     **"Efforts" now appears nowhere in our own chrome.** What remains is other people's wording - see item 11.
   - ~~"Revised / New" removed from the summary row~~ done. It is an overlay tag, not a fifth status, and
     reading it as mutually exclusive with the other four was exactly the confusion she described. The
     remaining four now visibly sum to the total. The **filter button of the same name was kept** — she
     described the summary row, and a filter is a tool rather than a claim. Worth confirming with her.
   - ~~**Tactic numbering**~~ **settled 2026-08-20 and built.** Daniela asked for **3.1.4**, confirmed with
     Ursula: "designating the new tactic as 3.1.4 to keep the numbering and indicating this as a revision
     (also listing the retired tactics under 'Revisions and New tactics')." Built as **3.1.4 revised in
     place** with 3.1.5–3.1.7 retired into it — *not* as a separate new 3.1.4 beside the retired one, which
     would have put two tactics under one `tactic_id` and broken three things keyed on it. See DECISIONS.
3. ~~**Add the replacement tactic**~~ — **done 2026-08-20, not yet published.** Carried as **3.1.4 revised
   in place**. Active 95 -> 96, retired 4 -> 3, Goal 3.1 -> **3/4** (was 3/3, which implied the goal was
   finished), Objective 3 -> **5/10**. Verified in the browser: 3.1.4 renders active with a REV badge,
   3.1.5-3.1.7 render retired, and "3.1.8" appears nowhere on the page. Provenance was **carried, not
   cleared** — see DECISIONS for why that reverses the note that used to sit here.
4. **Share the reviewer site URL with ISPE.** Ready now. Policy "ISPE reviewers" = `@pharmacoepi.org` +
   4 named addresses; adding a reviewer is one dashboard edit, no redeploy.
   ⚠️ **`@ispe.org` is a different organisation** (International Society for Pharmaceutical Engineering);
   the pharmacoepidemiology society is `@pharmacoepi.org`. Do not "fix" the policy to `@ispe.org`.
   ⚠️ The sender is Resend's shared `onboarding@resend.dev`, which delivers **only** to the Resend account
   owner's address. A second recipient needs a verified sending domain — use a subdomain such as
   `notify.blackswancausallabs.com` so the root domain's Google Workspace records are never touched.
   Raised and dropped 2026-08-10.
5. **The survey instrument still asks the old 3.1.4 question.** Its column reads "Tactic 3.1.4: Identify
   gaps (gaps and prioritization analysis)…", which is wording that no longer exists. The ingest is correct
   (that column maps to 3.1.4, the right tactic) and nothing fails, but a committee answering it next cycle
   is reporting on text that was replaced. **Edit the instrument before the next cycle opens.** This needed
   doing under either numbering — 3.1.8 would have had no column at all.
6. **Tidy the published revision rationales.** Still 8, and most read as raw survey answers — 7.1.7 begins
   *"The is tactic…"*. Four are now clean: 3.1.4-3.1.7 come from `REVISION_RATIONALE` in the ingest script
   as of 2026-08-20, which is also the only way an edit to them survives a re-ingest. The remaining four
   (2.2.1, 2.2.2, 2.2.5, 7.1.7) are still whatever the committee typed, and editing them in the admin panel
   **will be overwritten on the next ingest** unless they are curated the same way. (The rationale that
   begins *"Yes."* is not one of these — it is a new-tactic submission under goal 1.2.)
7. **Six "August 2026" completion dates record when the tactic was logged, not finished** (2.1.2, 2.1.3,
   2.1.6, 3.1.3, 6.1.2, 7.1.2). The dashboard shows all nine August dates identically. Footnote them, blank
   them, or leave as-is — a decision, not a bug.
8. **Three committees have not reported this cycle** — Executive/Impact, Finance, Global Development /
   Strategic Planning. Their tactics carried forward and are flagged at-risk as unreconfirmed.
9. **Test responsive changes at ~760px, not full-screen.** That is the ISPE page's content column, and it
   is the width the embed actually renders at. The donut-alone-in-a-box bug (fixed 2026-08-20) was invisible
   at desktop width for exactly this reason. See DECISIONS.
10. **Make admin's Save message honest.** It says "Saved in this browser only", but `ispe_sp_data` is written
   and never read back, so edits are gone on reload. Less urgent than it was — `review-site/` is read-only and
   never runs admin's Save — but still a live trap for anyone who opens `admin.html` without the helper.
11. **"Efforts" survives in 16 strings other people wrote — leave them.** 15 are plan descriptions (the
   Strategic Plan's own wording, not our label); the 16th is Education's new-tactic submission under goal
   1.2. See DECISIONS; a blanket find-and-replace across `index.html` / `admin.html` / `data.json`
   is always wrong. Related and still open: `publishReadOnly()` in `admin.html` still shows a
   **"Revised / New" summary card**, the one path Daniela's second fix (`8d4cb42`) missed.
12. ~~Absorb the new CSV format~~ / ~~publish the August cycle~~ / ~~keep notes off the public site~~ /
   ~~complete the completion dates~~ / ~~the emblem~~ — **all done 2026-08-09/10 and live.**

## The August cycle (what just happened)

`20260804134803-SurveyExport.csv` is the plan year's **first complete return** — 12 responses, 11 committees.
Two things about it:

- **The format did not change**; the columns are byte-identical to the 7.30 export. Only the **filename
  convention** changed, and that alone would have broken two things silently: the cycle would have been dated
  `null`, and the no-argument command would have re-ingested July. Both fixed — see DECISIONS.
- **It supersedes July rather than merging onto it.** All six July rows appear byte-identical, plus six more.
  Executive answered twice; the rows are complementary with **zero conflicting cells**.

What moved: **Completed 24 → 27**, On Track 43 → 37, Delayed 7 → 10. Nine statuses changed. Worth a look:
4.2.4 and 5.3.2 went **backwards** from On Track to Not Started (actively selected, not blank), and four of
Objective 8's tactics slipped into Delayed at once.

Still true of the pipeline:
- **Cycles may be partial.** The script merges: CSV → existing `data.json` → plan default. Never run it twice
  without resetting `data.json` first; the second run merges onto its own output and masks any correction in
  between. The script warns; the warning does not stop the write.
- **The CSV has no dates.** The cycle date comes from the **filename** — now either `M.D.YYYY` or a leading
  `YYYYMMDD` stamp.

## What this is
A static, client-side dashboard tracking progress on the ISPE Strategic Plan (2024–2029).
99 tactics across 8 objectives/goals, of which **95 are active and 4 retired**. Served via GitHub Pages and
intended to be embedded on the ISPE website as an `<iframe>`. No backend — everything runs in the browser.

## Repo layout (branch model)
- **`main`** — the working repo. Contains:
  - `index.html` — the **public** dashboard (no admin controls, no at-risk panel, no search box)
  - `admin.html` — the **admin/editor** (at-risk panel, Admin Control Panel, search box, As-of date picker)
  - `data.json` — the data the dashboards fetch at runtime (committee-level only, **no PII**)
  - `csv_to_dashboard_json.py` — merges a survey report CSV into `data.json` (see "Updating the data").
    Also holds the two curated dicts the survey cannot supply: `RETIRED` and `COMPLETED_AT`
  - `build_public_payload.py` — **strips committee notes** and writes `public/data.json`. `--check FILE`
    exits non-zero if a file still carries internal fields; that is the publish assertion
  - `admin-server.py` — **local** helper: serves the dashboard and turns admin's Save/Publish into
    real git commits/pushes. Run `python3 admin-server.py`, then open http://127.0.0.1:8800/admin.html
  - `ispe-emblem.png` — the header emblem. **Transparent PNG**; its white brushed ring only reads against
    the dark header and must never be given a white backing. Sourced from `coffee stain logo.pptx`, not
    from the flattened jpg, which erased the ring
  - `fonts/` — self-hosted Source Serif 4 (woff2 + SIL OFL licence)
  - `public/` — **build artifact**, gitignored, rebuilt on every publish. Never commit it
  - `review-site/` — the **reviewer site**: Cloudflare Pages + Access (email one-time PIN) + D1. Reviewers
    comment, flag and approve; state is shared, so everyone sees everyone's. **Complete review** emails the
    owner that reviewer's summary; a failed send is recorded and shown, never swallowed. Read-only otherwise.
    Carries the **at-risk panel**, extracted from `admin.html` at build time — admin-only, still never on the
    public dashboard, but the list a reviewer needs before signing off. Its page is
    **generated from `index.html`** by `build_review_site.py` with match-count-asserted patches, so the
    render code is never hand-copied a third time. `dist/` is generated — never edit or commit it.
    See `review-site/DEPLOY.md`
  - `docs/` — this documentation: `STATUS.md` (here), `DECISIONS.md` (the why),
    `MIGRATION-private-repo.md` (the planned next phase)
  - `.gitignore` — allowlist (only tracks the files above + images). **No survey CSV is tracked.** The old
    April export contains PII (12 emails, 14 IPs — used as the control when scanning). The newer exports
    carry **none** (verified 2026-08-10: 0 of 17 PII columns, 0 emails, 0 IPs), but they do carry free-text
    committee answers that are not published, so they stay out until the repo is private
- **`public-deploy`** — the deploy branch: **public dashboard only** (`index.html`, `data.json`, `fonts/`,
  images, `README.md`). `admin.html`, `admin-server.py`, and the CSV script are deliberately excluded so they
  can never be published to the public site. This is the branch GitHub Pages *should* serve.
  - It has its **own separate allowlist `.gitignore`** — different from `main`'s. Anything new that
    `index.html` depends on must be allowlisted there too, or it is **absent from the deploy and 404s on the
    live site with nothing failing anywhere**. `fonts/` was lost this way on 2026-07-27, and
    `banner picture.jpg` was one untrack away from the same fate until 2026-08-10.
  - `index.html` is maintained by **copying from `main`**, not by merging.
  - ⚠️ **`data.json` here is NOT `main`'s `data.json`.** It is generated by `build_public_payload.py`, which
    strips the committee notes. **Copying `data.json` across from `main` is the single action that puts the
    notes back on the public site.** The branch README says so too.

## Live URLs & deployment state (all verified 2026-08-10)
- **Black Swan (live now):** https://black-swan-causal-labs.github.io/ISPE-Strategic-Plan-Dashboard/
  - Serving `public-deploy`. Verified: `index.html` 200, `ispe-emblem.png` 200, `banner picture.jpg` 200;
    `admin.html`, `admin-server.py`, `csv_to_dashboard_json.py`, `build_public_payload.py` all **404**.
  - Live data: August 2026, 99 tactics (95 active), **27 completed all dated**, **0 notes served**.
  - This is "not published", not "access-controlled". Pages on a public repo has no auth.
- **ISPE (live since 2026-08-10):** https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/ ← the iframe
  `src`. Verified 2026-08-20: Pages source is **`public-deploy` / (root)**, status `built`; `/` 200,
  `data.json` 200 with **0 notes**; `admin.html`, `admin-server.py`, `csv_to_dashboard_json.py`,
  `build_public_payload.py` all **404**. Their `public-deploy` = `38fbcea`, level with ours.
  ⚠️ The fork's **default branch is `main`** — that is fine while Pages points at `public-deploy`, but it
  means anyone browsing their repo lands on the branch that carries `admin.html` and the notes. Do not
  suggest they "fix" Pages to follow the default.

## Handing the fork to ISPE-SP

Someone else owns the ISPE-SP account, so this is a hand-off, not a task. **Four steps, and step 2 is the
one that matters.**

1. **Fork** from https://github.com/Black-Swan-Causal-Labs/ISPE-Strategic-Plan-Dashboard/fork — owner
   `ISPE-SP`, keep the repo name (the URL depends on it), and **untick "Copy the main branch only"**. It is
   ticked by default; leaving it ticked means `public-deploy` never arrives and step 2 has no valid option.
2. **Settings → Pages → Deploy from a branch → `public-deploy` → `/ (root)`.** **Never `main`** — `main`
   carries `admin.html`, the scripts, and the `data.json` with all 28 committee notes.
3. **Verify both:** the site renders, **and `/admin.html` returns 404.** If it does not, Pages is on the
   wrong branch — do not share the address.
4. Send IT the iframe snippet under "Embed".

**Each cycle after that**, someone at ISPE must open the fork, switch to **`public-deploy`**, and click
**Sync fork → Update branch**. Miss it and their site shows the previous cycle indefinitely with no error.

⚠️ **This is a stopgap that unwinds at migration.** Making a public repo private **detaches existing public
forks into a new network** (GitHub docs, confirmed 2026-08-10), so theirs permanently loses the ability to
sync. The fork is a thing to tear down, not to build on — see DECISIONS.

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
   their own embedded `DEFAULT_DATA` — **and now render a loud red banner saying so**, naming the cause and
   the snapshot's date. Before 2026-08-09 that fallback rendered a plausible February 2026 dashboard in
   silence, which is what anyone downloading `admin.html` from the repo saw.
4. `build_public_payload.py` reads `data.json` and writes `public/data.json` with the **notes stripped**.
   That is the file the public branch gets — never `main`'s copy.
5. To update the live site, commit the generated payload to `public-deploy`.

The script prints a report every run: value sources, status counts, who reported, column coverage, columns
recognized but deliberately not consumed, and any status cell that matched no known value. **Read it.** It is
the only thing standing between a malformed cycle and a plausible-looking wrong dashboard.

## Current state (as of this handoff, on `main` — and live on `public-deploy`)
- **99 tactics, of which 96 are active and 3 are retired.** Active split: **38 On Track, 22 Not Started,
  26 Completed, 10 Delayed** (August 2026 cycle).
- **All 26 completed tactics carry a completion date**: 8 October 2025, 10 February 2026, 8 August 2026.
  Of the eight August dates, **only two are genuine August completions** (4.2.2, 8.2.2, dated by the
  transition rule); the other six record when the tactic was *logged*, not finished. See open item 4.
- **11 of 14 committees reported.** Executive/Impact, Finance and Global Development / Strategic Planning
  did not; their tactics carried forward.
- **Retired = 3.1.5, 3.1.6, 3.1.7**, superseded by **3.1.4**, which was **revised in place** rather than
  retired (2026-08-20, Daniela confirmed with Ursula). The earlier plan for a new 3.1.8 was dropped. The three
  stay listed in goal 3.1 with a `RETIRED` badge and a dagger, and are excluded from every progress count —
  rings, goal `n/m`, objective totals, all the summary cards, mini pills, at-risk.
- **There is no "Revised / New" status card any more** — dropped 2026-08-20 on Daniela's feedback that it is
  not a status. It survives only as a *filter button*, which carries no count. The summary row is now just
  **96 Total · 22 Not Started · 38 On Track · 10 Delayed · 26 Completed**, and those four sum to Total.
- **The "Revisions & New Tactics" section badge reads 23**, which is not the 21 flagged tactics. It is
  **21 + 2**: every tactic carrying `is_revised` or `is_new_in_plan` (retired included — being retired *is*
  the revision), **plus the `new_tactics` submitted this cycle** (goals 1.2 and 4.2), which are proposals
  that do not exist in the plan and so are not tactics. `index.html:1256-1260`. The count of revised/new
  among *active* tactics is 18, but **that figure is not displayed anywhere** — do not expect to see it.
- **Goal/objective progress is a plain count over active tactics** — goal 3.1 reads `3/4`, objective 3 reads
  `5/10`. The old `x/10` scale is gone. Stored `progress_score` fields are intentionally unused.
- **At Risk = 32** (22 Not Started + 10 Delayed, retired excluded) — **admin view only**. Up from 28 in July,
  driven by Objective 8: four of its tactics moved into Delayed in one cycle. **29 were reconfirmed this
  cycle; 3 are carried forward** (3.1.4, 6.1.8, 7.1.7). The panel marks this per row — see "At Risk" under
  Key UI components.
- **6.2.1 is corrected, not survey-derived.** Membership reported it `Completed` in August; Daniela confirmed
  with Anne that it is not, and its twin 6.1.5 says `In progress- on track` for the same work. Set by hand in
  `data.json` — **a re-ingest of the August CSV reverts it.** See DECISIONS, 2026-08-21.
- **The public header is two lines and nothing else**: the title, then "2024-2029 | As of **August 2026**"
  from `metadata.as_of_date` (admin picker). The third line under it — the "survey stamp", which read
  "Survey data through August 2026 · 11 committee responses this cycle" — **is gone from `index.html`**
  (Daniela, Ursula agreeing, 2026-08-21): the count read as a completeness claim without its denominator,
  and the date restated the As-of line above it. Element and code both removed, along with the `latest`
  pass that existed only to feed it. **`admin.html` keeps its stamp** — cycle coverage is worth knowing
  internally — so the two headers now differ by that one line, on purpose.

## Key UI components
- **Summary cards** — the 4 status cards partition the **95 active** tactics; **"Revised / New*"** is a
  separate overlay tag (a revised tactic still has one of the 4 statuses), explained in the footnote under
  the cards, which also states how many tactics are retired and excluded.
- **Revisions & New Tactics** (renamed from "Changes & New Tactics" on 2026-08-03) — collapsible,
  List/Timeline toggle. Each revised tactic shows the committee's own explanation and its date; dates come
  from `revised_at` per tactic, falling back to `metadata.tracker_label`, and are no longer hardcoded.
- **Retirement note** — sits between the last objective and the contact card, explains the dagger on retired
  rows, and states the active total. Rendered by `renderRetiredNote()`; empty when nothing is retired.
- **Completed Tactics** — collapsible, grouped by objective. Each entry shows
  `Owner: X · Completed <Month Year>`, from `completed_at`. The date also appears **beneath the status badge**
  in the tactic table, and in the read-only export. It sits *beside* the badge, never inside it: the badge's
  hue, glyph and shape are the validated status encoding and must not take a second job.
- **Header emblem** — `ispe-emblem.png`, flush to the top and bottom of the header band. The header has **no
  vertical padding** by design; the emblem sets its height. No white chip behind it — the ring is the shape.
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
  has no auth). It is kept off `public-deploy` for exactly this reason. **On BSCL this is resolved** — 404
  re-verified 2026-08-10. **It applies in full to ISPE's fork**: whatever branch they serve is public, which
  is why "confirm `/admin.html` 404s" is a step in the handoff note and not an optional check.
- **Mobile verified 2026-07-27** at 390 / 360 / 320 px, and **re-verified 2026-08-10** after the emblem
  change at 1200 / 860 / 600 / 380 px. No horizontal overflow; the emblem steps 180 → 140 → 88px and the
  header reverts to padded layout once it wraps. *Still worth a glance on a real handset* for touch-target
  feel, but the layout question is settled.
- ~~Survey free-text interpolated into `innerHTML` unescaped~~ — **fixed 2026-07-27.** An `esc()` helper now
  wraps all data-derived values (30 sites in `index.html`, 41 in `admin.html`, including the string-concat
  form inside `publishReadOnly`). Verified by injecting a payload into `data.json`: on the pre-fix build the
  `onerror` handler executed and an element was injected; after the fix it renders as inert text.
  **Keep using `esc()` for any new interpolation of survey-sourced text.**
- **Committee notes must never reach the public payload.** `index.html` fetches `data.json` over HTTP, so
  dropping the Notes column does not make notes private — 28 were readable at the live site's own
  `/data.json` until 2026-08-09. Publish only through `build_public_payload.py`. Copying `main`'s
  `data.json` across is the one action that undoes this.
- **Admin's Save is not a save when the helper is not running.** It reports "Saved in this browser only",
  but `ispe_sp_data` is written to `localStorage` and **never read back on load** — so the edits are gone on
  refresh. Harmless locally; a trap the moment `admin.html` is hosted anywhere. Fix the message before that.
- **`public-deploy` needs every asset allowlisted.** It is a separate branch that omits `admin.html`; if `index.html`
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

**Ingest and curate — on `main`**
1. Drop in the new export. Either naming convention works: `SP Reports <M.D.YYYY>.csv` or a leading
   `YYYYMMDD` stamp. **The filename is the only cycle date there is.** Keep it out of git — see the CSV note
   under "Open questions".
2. **Reset first:** `git checkout main -- data.json`. Skipping this merges the cycle onto whatever the last
   run produced and masks any correction you made in between.
3. `python3 csv_to_dashboard_json.py` (no argument picks the newest recognized export; pass a path to choose).
4. **Read the run report.** Source split, status counts, column coverage, unmapped status cells, completion
   dates dated/undated, and any `COMPLETED_AT` conflict. Then review the diff on `data.json`.
5. If tactics retired this cycle, add them to `RETIRED` and re-run from step 2. Same for any completion date
   the transition rule cannot derive — add it to `COMPLETED_AT`.
6. Set the **As-of date** in the admin panel. Not derivable from the CSV; the field now shows its current
   value on load, so a stale date is visible rather than invisible.
7. Tidy the revision rationales in the admin panel — they publish verbatim.
8. Commit `data.json` to `main`. Via `admin-server.py`, **Save** commits and **Publish** commits + pushes.

**Publish — the part that must not be shortcut**
9. `python3 build_public_payload.py` → `public/data.json`, notes stripped.
10. `git checkout public-deploy`, bring `index.html` across from `main` if it changed, copy the **generated**
    payload over `data.json` — **never `main`'s copy**.
11. Assert before pushing. All of these, every time:
    - no `admin.html` / `admin-server.py` / `csv_to_dashboard_json.py` / `build_public_payload.py` tracked
    - no `Admin Control Panel`, `publishReadOnly`, `atRiskPanel`, `notes-input`, `EMBLEM_DATA_URI` in
      `index.html`
    - `python3 build_public_payload.py --check data.json` exits 0
    - `data.json` parses at the expected tactic count
    - **every image and font `index.html` references is tracked on this branch** (parse the filenames — one
      of them contains a space, which a naive shell loop splits)
12. Commit, push, and **verify the live site** rather than assuming Pages redeployed.

**If the plan structure changes** (a tactic added or removed), edit `DEFAULT_DATA` in **both** HTML files and
regenerate. The script only reads `index.html`'s copy.
