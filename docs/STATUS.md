# ISPE Strategic Plan Dashboard — Status / Handoff

_Cold-start snapshot. Read this first, then `DECISIONS.md` for the "why". Last updated: 2026-07-22._

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
  - `docs/` — this documentation
  - `.gitignore` — allowlist (only tracks the files above + images); **the raw survey CSV is intentionally NOT tracked (it contains names/emails/IPs)**
- **`public-deploy`** — the deploy branch: **public dashboard only** (`index.html`, `data.json`, images, `README.md`). `admin.html` and the script are deliberately excluded so they can never be published to the public site. This is the branch GitHub Pages should serve.

## Live URLs
- **Black Swan (current):**
  - Public: https://black-swan-causal-labs.github.io/ISPE-Strategic-Plan-Dashboard/
  - Admin: https://black-swan-causal-labs.github.io/ISPE-Strategic-Plan-Dashboard/admin.html
  - (BSCL Pages serves `main`, so both files are live there.)
- **ISPE (planned):** ISPE forks the repo into **`github.com/ispe-sp`** (a personal user account, works fine), enables Pages on the **`public-deploy`** branch, giving:
  - https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/  ← the iframe `src`
  - When forking, **uncheck "Copy the main branch only"** so `public-deploy` is included.

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
- **Revised / New = 13** (11 revised + 2 survey-submitted new) — an *overlay* tag, not a status (see note below).
- **At Risk = 37** (30 Not Started + 7 Delayed) — **admin view only**.
- Header "As of …" date comes from `data.json` → `metadata.as_of_date` (set via the admin "As-of date" picker).

## Key UI components
- **Summary cards** — the 4 status cards partition all 99; **"Revised / New*"** is a separate overlay tag
  (a revised tactic still has one of the 4 statuses), explained in the footnote under the cards.
- **Changes & New Tactics** — collapsible, List/Timeline toggle.
- **Completed Tactics** — collapsible, grouped by objective (no timeline: there's no true completion date;
  the only date is the survey-report date, which clusters into ~2 months — see DECISIONS).
- **At Risk** — admin-only; tactics reporting Not Started or Delayed, grouped by objective with short themes.
- **Footer** — "Questions about the content? Email info@pharmacoepi.org".

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
- **Mobile not yet verified on a real device** — responsive CSS is in place but was never screenshot at true
  phone width. Spot-check on a phone.
- **Editing two copies of the plan:** `DEFAULT_DATA` exists in both `index.html` and `admin.html`. Any
  structural plan change (add/remove a tactic, reset flags) must be made in both, and reflected in `data.json`.
  The script only reads/writes via `index.html` + `data.json`.

## Updating the data (current best-understanding workflow)
1. Get the new Alchemer CSV (keep it out of git — it has PII).
2. Run `python3 csv_to_dashboard_json.py` (it reads `index.html`'s `DEFAULT_DATA` + the CSV → writes `data.json`).
3. Review the diff on `data.json`.
4. Commit `data.json` to `public-deploy` (public site) and/or `main`. Pages redeploys in ~1 min.
5. If any tactics were added/removed or revised/new flags should change, edit `DEFAULT_DATA` in both HTML files too.
