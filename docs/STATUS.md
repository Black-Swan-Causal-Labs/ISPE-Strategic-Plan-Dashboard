# ISPE Strategic Plan Dashboard — Status / Handoff

_Cold-start snapshot. Read this first, then `DECISIONS.md` for the "why". Last updated: 2026-07-27._

## Start here (cold start)

```bash
# Look at it / edit it. The helper is what makes Save and Publish real git actions.
python3 admin-server.py          # → http://127.0.0.1:8800/admin.html  (editor)
                                 # → http://127.0.0.1:8800/index.html  (public view)

# Just viewing, no editing:
python3 -m http.server 8000      # → http://localhost:8000/index.html
```

**Both branches are in sync and pushed as of 2026-07-27.** Nothing is half-finished in the repo.

| | state |
|---|---|
| `main` | current — all work through 2026-07-27 |
| `public-deploy` | current — synced from `main`, `admin.html` correctly absent |
| BSCL Pages | serving **`main`** (so `admin.html` is publicly reachable — see Live URLs) |
| ISPE fork | **does not exist yet** (404 as of 2026-07-27) |

**Three things are waiting on a human, not on code** — see the sections below for detail:
1. Flip BSCL Pages to serve `public-deploy` (one dropdown; un-publishes `admin.html`).
2. Confirm the footer copyright holder — it currently names ISPE, which was an assumption.
3. Decide how ISPE will get updates (fork + sync, vs. iframe BSCL directly, vs. push access).

## What this is
A static, client-side dashboard tracking progress on the ISPE Strategic Plan (2024–2029).
99 tactics across 8 objectives/goals. Served via GitHub Pages and intended to be embedded on the
ISPE website as an `<iframe>`. No backend — everything runs in the browser.

## Repo layout (branch model)
- **`main`** — the working repo. Contains:
  - `index.html` — the **public** dashboard (no admin controls, no at-risk panel, no search box)
  - `admin.html` — the **admin/editor** (at-risk panel, Admin Control Panel, search box, As-of date picker)
  - `data.json` — the data the dashboards fetch at runtime (committee-level only, **no PII**)
  - `csv_to_dashboard_json.py` — converts an Alchemer survey CSV → `data.json`
  - `admin-server.py` — **local** helper: serves the dashboard and turns admin's Save/Publish into
    real git commits/pushes. Run `python3 admin-server.py`, then open http://127.0.0.1:8800/admin.html
  - `fonts/` — self-hosted Source Serif 4 (woff2 + SIL OFL licence)
  - `docs/` — this documentation
  - `.gitignore` — allowlist (only tracks the files above + images); **the raw survey CSV is intentionally NOT tracked (it contains names/emails/IPs)**
- **`public-deploy`** — the deploy branch: **public dashboard only** (`index.html`, `data.json`, `fonts/`,
  images, `README.md`). `admin.html`, `admin-server.py`, and the CSV script are deliberately excluded so they
  can never be published to the public site. This is the branch GitHub Pages *should* serve.
  - It has its **own separate allowlist `.gitignore`** — different from `main`'s. Anything new that
    `index.html` depends on must be allowlisted there too, or it silently won't ship. `fonts/` was added
    on 2026-07-27 for exactly this reason.
  - The branch is maintained by **copying `index.html` from `main`**, not by merging. As of 2026-07-27 the
    two are in sync.

## Live URLs & deployment state (verified 2026-07-27)
- **Black Swan (live now):** https://black-swan-causal-labs.github.io/ISPE-Strategic-Plan-Dashboard/
  - **BSCL Pages is configured to serve `main`, not `public-deploy`.** That is why
    `.../admin.html` is publicly reachable. It contradicts the intent recorded in this file.
  - **Pending, one-click, no code change:** switch the Pages source branch to `public-deploy` in repo
    Settings → Pages. That un-publishes `admin.html` immediately. `public-deploy` is current, so there is
    no downside to flipping it. *(Left to the owner — it is a GitHub settings change.)*
- **ISPE (not yet created):** `github.com/ispe-sp/ISPE-Strategic-Plan-Dashboard` returned **404** as of
  2026-07-27 — **ISPE has not forked yet.** Nothing downstream is stale; there is a clean window to get
  `public-deploy` right before they fork, which is already done.
  - When they fork: **uncheck "Copy the main branch only"** or `public-deploy` won't come across and
    there will be nothing to point Pages at.
  - They then enable Pages on `public-deploy`, giving
    https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/ ← the iframe `src`.
- **⚠️ Forks do not auto-update.** Every `data.json` refresh needs someone at ISPE to click **"Sync fork."**
  That puts the party least able to act quickly on the critical path, and the failure mode is a public
  dashboard quietly showing last quarter's numbers. Two ways out, both easier to arrange *before* they fork:
  (a) ISPE iframes the BSCL Pages URL directly — no fork, no sync, updates land on push; or
  (b) ISPE forks but grants push access, so BSCL syncs it. Not yet raised with them.

## Embed
```html
<div style="max-width:1200px; margin:0 auto;">
  <iframe src="https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/"
    title="ISPE Strategic Plan Progress Dashboard" loading="lazy"
    style="width:100%; height:1400px; border:0; border-radius:8px;" referrerpolicy="no-referrer"></iframe>
</div>
```
Paste into a "Custom HTML" block. GitHub Pages allows external iframing.

## Data pipeline (how the dashboard gets its numbers)
1. **Plan structure** (the list of objectives/goals/tactics, plus `is_revised` / `is_new_in_plan` flags)
   is the source of truth and lives as `const DEFAULT_DATA = {...}` embedded in **`index.html`**.
2. `csv_to_dashboard_json.py` reads that plan structure **+** the Alchemer CSV and writes **`data.json`**
   (fills in each tactic's status/notes from the most recent response by the owning committee).
3. Both `index.html` and `admin.html` **fetch `data.json`** at load. If the fetch fails they fall back to
   their own embedded `DEFAULT_DATA`. So on the live site, `data.json` (when present) is what's displayed.
4. To update the live site, commit the new `data.json` to the deployed branch(es).

## Current state (as of this handoff)
- **99 tactics**: 44 On Track, 30 Not Started, 18 Completed, 7 Delayed.
- **Revised / New = 16** (14 distinct revised-or-new tactics + 2 survey-submitted suggestions) — an *overlay*
  tag, not a status. **This was 13 and the Changes card said 18; both were wrong** — see DECISIONS
  "Revised / New counting". Under a status filter it now reports only that status's share (Delayed → 0).
- **Goal/objective progress is a plain count** — goal 3.1 reads `2/7`, objective 3 reads `4/13`. The old
  `x/10` scale is gone. Stored `progress_score` fields are intentionally unused.
- **At Risk = 37** (30 Not Started + 7 Delayed) — **admin view only**.
- Header "As of …" date comes from `data.json` → `metadata.as_of_date` (set via the admin "As-of date" picker).

## Key UI components
- **Summary cards** — the 4 status cards partition all 99; **"Revised / New*"** is a separate overlay tag
  (a revised tactic still has one of the 4 statuses), explained in the footnote under the cards.
- **Changes & New Tactics** — collapsible, List/Timeline toggle.
- **Completed Tactics** — collapsible, grouped by objective (no timeline: there's no true completion date;
  the only date is the survey-report date, which clusters into ~2 months — see DECISIONS).
- **At Risk** — admin-only; tactics reporting Not Started or Delayed, grouped by objective with short themes.
- **Footer** — 2026 copyright + "Dashboard designed and built by Black Swan Causal Labs, LLC".
  The contact line ("Questions about the content? Email info@pharmacoepi.org") now sits in its own card
  between the last objective and the footer.
- **Status encoding** — colour **plus a glyph** (`○` `▶` `!` `✓`) on every badge. The palette is
  CVD-validated; see DECISIONS before changing any status colour.

## ⚠️ Open questions / watch-outs for the next survey cycle
- **The recurring-update path is unproven.** The next Alchemer upload is a trial run. It may turn out that
  each cycle is effectively a **new-ish build** rather than a clean automatic refresh. Treat the pipeline
  below as "best current understanding," not a guarantee.
- **"Revised / New" does NOT reset from a new CSV.** Those flags are baked into the plan structure
  (`DEFAULT_DATA` in `index.html`), from the March 2026 tracker — the script does *not* derive them from the
  survey. So a new CSV updates status/notes but keeps the current revised/new list. The only CSV-driven "new"
  is the survey's free-text "new tactics added" columns. To make revised/new refresh each cycle we'd need to
  either (a) manually reset the flags in the plan structure, or (b) change the script to drive "Revised" from
  the survey's own "Changed" responses (recommended; not yet done).
- **The script is not automatic** — someone must run `csv_to_dashboard_json.py` with the new CSV, then commit
  `data.json`. `admin.html`'s "Import JSON" imports a `data.json`, not a raw CSV.
- **`admin.html` is publicly reachable** wherever it's deployed (GitHub Pages on a public repo has no auth).
  It's kept off `public-deploy` for exactly this reason; on `main`/BSCL it's reachable by URL.
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

## Updating the data (current best-understanding workflow)
1. Get the new Alchemer CSV (keep it out of git — it has PII).
2. Run `python3 csv_to_dashboard_json.py` (it reads `index.html`'s `DEFAULT_DATA` + the CSV → writes `data.json`).
3. Review the diff on `data.json`.
4. Commit `data.json` to `public-deploy` (public site) and/or `main`. Pages redeploys in ~1 min.
   **Or** run `python3 admin-server.py`, edit in the admin panel, and press **Save** (commits) or
   **Publish** (commits + pushes). Note that without the helper running, admin edits live only in the
   browser and **do not survive a reload** — `localStorage` is written but never read back.
5. If any tactics were added/removed or revised/new flags should change, edit `DEFAULT_DATA` in both HTML files too.
