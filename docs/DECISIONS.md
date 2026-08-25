# ISPE Strategic Plan Dashboard — Decision Log

_Why the dashboard is built the way it is. Newest context at the bottom. See `STATUS.md` for the current snapshot._

## Ownership & hosting
> ⚠️ **The fork-and-host plan below was superseded on 2026-08-03** — it cannot be assembled once the working
> repo is private. See "Private working repo, push-to-publish" at the bottom of this file, and
> `MIGRATION-private-repo.md` for the replacement. The rest of this section is kept as the record of what was
> intended and why. **Nothing has been executed yet**, so the live site still follows the old model.

- **Repo moved to the `Black-Swan-Causal-Labs` GitHub org** (transferred from a personal account; old URL redirects).
- **Deployment plan: ISPE forks, ISPE hosts.** ISPE's GitHub is `github.com/ispe-sp` (a personal *user*
  account — works for forking + Pages; an Org would be tidier for an official multi-maintainer presence, but
  not required). ISPE forks the BSCL repo and enables Pages on `public-deploy`; the ISPE website embeds that
  Pages URL as an iframe. Chosen over transferring ownership so BSCL keeps the canonical/maintenance copy and
  ISPE controls their own deployment. Updates propagate via GitHub's "Sync fork".
- **Public/admin split by file, not by auth.** GitHub Pages on a public repo has no login, so "admin-only"
  means "not published," not "access-controlled." The `public-deploy` branch omits `admin.html` entirely so
  the public site can only ever serve the public dashboard.

## Public vs. admin dashboard
- **`index.html` = public build; `admin.html` = editor.** The public page has the admin control panel, the
  at-risk panel, and the keyword search removed; the admin page keeps them.
- **At-risk panel is admin-only.** It was briefly on the public page, then moved to admin only — ISPE
  leadership didn't want the "at risk" framing surfaced by default on the public site. (Underlying data is
  public regardless, since it's in the page source / `data.json`; this is about default presentation.)
- **Search box removed from the public view, kept in admin.** With status-filter buttons + collapsible
  objectives, search added little on the public embed; a maintainer may still want it in admin.
- **"As-of date" picker moved into the Admin Control Panel.** It sets the header's "As of [month]"; it was
  awkwardly sitting in the filter box. Admin-only; never on the public page.
- **Prototype banner removed** from `admin.html` (the red "Prototype — In Development" bar).

## "At risk" definition (set with ISPE leadership)
- A tactic is **at risk** if its reported status is **Not Started** or **In Progress – Delayed**, regardless
  of the narrative in its notes. (Replaced an earlier "goals below 50%" heuristic.)
- Rendered grouped by objective, Delayed first, with short objective **themes** in the sub-headers.

## Data corrections
- **Removed duplicate tactic 6.1.9** (a repeat of 5.1.6, inadvertently added to goal 6.1). Plan went from
  100 → **99 tactics**. Fixed in `data.json` and both embedded `DEFAULT_DATA` copies.
- **Fixed garbled descriptions on 6.1.6 and 6.1.7** (stray "Revised tactic …" text had been concatenated in;
  also corrected an obvious "the of implementation" typo on 6.1.7).

## Summary cards / "Revised / New"
- The **four status cards partition all 99** (Not Started + On Track + Delayed + Completed = Total).
  *(Since 2026-08-03 they partition the **active** tactics — 95 of 99, with four retired. See below.)*
- **"Revised / New" is a separate overlay tag**, not a status — a revised tactic still has one of the four
  statuses and is *also* counted here, plus survey-submitted new tactics — so it is not part of the total.
  Marked with a `*` and an explanatory footnote so the numbers "not adding up" is understood, not confusing.
- **Em dashes removed** from that footnote and the at-risk header (style preference).

## Completed Tactics section
- Added a **collapsible "Completed Tactics"** panel (styled like Changes & New Tactics), grouped by objective
  with counts, on both views.
- **No List/Timeline toggle** (unlike Changes). Reason: completed tactics have **no true completion date** —
  the only date is `last_reported_at` (survey-report date), which clusters into just ~2 months and would
  misrepresent survey dates as completion dates. A real completion timeline would require capturing a
  "completed on" date per tactic (future enhancement).

## Build / pipeline
- **`csv_to_dashboard_json.py` repointed to `index.html`.** It previously read the plan structure from
  `ISPE_Strategic_Plan_Dashboard.html`, which had been renamed to `admin.html`, so the script was broken.
  `index.html`'s `DEFAULT_DATA` is now the authoritative plan structure it reads.
- **`data.json` + the script are tracked; the raw survey CSV is not** (allowlist `.gitignore`). The CSV holds
  respondent PII (names, emails, IPs) and must stay out of the (public) repo. `data.json` is committee-level
  only and was PII-scanned clean.
- **Recurring updates are still unproven** — see STATUS.md "Open questions." Decision pending on whether to
  make "Revised / New" auto-refresh from the survey's "Changed" responses vs. keep it a manual plan-structure
  edit each cycle. Deferred at ISPE's request until the first real re-upload shows how the update behaves.
  *(Resolved 2026-08-03: the re-upload arrived in a different format and "Revised / New" now refreshes from
  the survey. See the 2026-08-03 section at the bottom.)*

## Mobile
- Responsive CSS extended (stack search/summary, wrap at-risk rows, reflow summary note, tighten collapsible
  padding). **Not yet verified at true phone width** — the dev environment couldn't screenshot below ~500px.

---

# 2026-07-26 — Visual & correctness overhaul

## Status palette rebuilt (accessibility)
- The old palette was **measurably broken**, not merely dated. On Track `#c6c611` vs Delayed `#ffbf00`
  measured **ΔE 0.8 under protanopia** — indistinguishable — and **8.6 for normal vision**, below the
  ΔE 15 floor. All four colours sat **under 3:1 contrast** on white.
- Root cause was semantic: *On Track* was painted caution-yellow when it means **good**, which is why it
  collided with *Delayed*. New mapping is the conventional one:

  | Status | Was | Now | Meaning |
  |---|---|---|---|
  | Not Started | `#0f9ed4` blue | `#64748b` slate | null state, deliberately neutral |
  | On Track | `#c6c611` olive | `#0284c7` blue | in progress, healthy |
  | Delayed | `#ffbf00` amber | `#d97706` amber | at risk |
  | Completed | `#4da72d` green | `#16a34a` green | done |

- Validated: worst adjacent pair now **ΔE 16.8 protan**, all four **≥ 3:1**. Green↔amber sits at ΔE 6.2,
  which is only permissible **with a non-colour channel** — hence the glyphs below.
- **Do not re-hue these without re-running a CVD validator.** The ordering is a safety mechanism, not taste.
- **Secondary encoding added:** every status badge carries a glyph (`○` `▶` `!` `✓`), so status survives
  greyscale printing, colourblind vision, and `forced-colors` mode.
- **Ring/donut draw order is deliberately non-semantic** — `Completed, On Track, Delayed, Not Started` —
  because it keeps the green and amber segments from ever touching, the one adjacency that fails CVD.
- Text vs marks are separated: filter pills and small white-on-colour badges use **darker steps**
  (`#036ba1`, `#b45309`, `#15803d`) because text needs 4.5:1 while graphical marks need only 3:1.

## Progress is a count, not a rescaled percentage
- Goal progress previously showed `x/10` derived from `round(pct/100 * 10)`. Goal 3.1 (2 of 7 complete)
  displayed **"3/10"** — a numerator matching no actual tactic. Now shows **`2/7`** plus the percentage.
- Objective rings likewise show the composite fraction (objective 3 = **4/13**). The underlying ring
  percentage was already computed this way; only the label changed. *(Both denominators now exclude retired
  tactics: goal 3.1 reads 3/3 and objective 3 reads 5/9 as of 2026-08-03.)*
- **The stored `progress_score` / `progress_max` fields in `data.json` are deliberately unused.** All 17
  goals' stored scores disagree with the computed values (some wildly: goal 2.2 stored 6, computes 0).
  Progress is derived from tactic statuses so it always reconciles with the rows beneath it. Revisit only
  if committees' self-reported judgement should override the tactic counts — a governance decision.
- Progress bars use a single neutral slate (`--progress`), never the status hues. Previously percentage
  bands mapped onto status colours, so a goal at 72% was painted the same green as "Completed".

## Revised / New counting — three bugs fixed
- **Statusless suggestions leaked into every filter.** Entries in `new_tactics` are free-text survey
  submissions with **no `status` field**; they were counted unconditionally, inflating every filtered view
  by +2. Filtering to Delayed showed 2 when the true answer is **0**.
- **`is_new_in_plan` was ignored** by the summary, which counted only `is_revised` — dropping 5 tactics.
- **The Changes badge double-counted.** Tactics **1.2.4 and 1.2.5 carry both flags**, so
  `revised.length + added.length` counted them twice: 18 reported for **16** actual changed items.
- Net: the summary said 13 and the Changes card said 18, they disagreed, and neither was right. Both now
  report **16**. The four statuses sum exactly to Total in every view.
- The "Revised / New" filter pill also matched only `is_revised`, hiding new-but-not-revised tactics from a
  filter whose label promised them. Now matches both flags.

## Typography
- **Source Serif 4, self-hosted** (SIL OFL 1.1, `fonts/`), for the whole page. Chosen over a system stack
  because *any* system stack resolves to the face already in use — `system-ui` is SF Pro on macOS, so a
  reorder alone changes nothing visible. A visible change requires a real webfont.
- **Self-hosted, not CDN,** for two reasons: the page is opened over `file://` as well as HTTP (a CDN font
  fails there), and a third-party font request on behalf of EU members is a GDPR liability.
- `unicode-range` splits latin / latin-ext, so the 98 KB extended file is **never fetched** for current
  ASCII-only content but covers accented names automatically if they appear. 119 KB transfers.
- Root size lifted to **17px** (16px on mobile) and the heading ramp widened from a compressed 1.55/1.0 to
  **2.05 / 1.4 / 1.2 / 1.06**. A uniform bump alone would have scaled the flatness too.
- The canvas donut needs a **font-load redraw** — canvas gets no reflow when a webfont arrives, so it would
  otherwise permanently bake in the Georgia fallback.

## Embedded (iframe) layout
- `index.html` detects framing (`window.self !== window.top`, set inline in `<head>` before the stylesheet)
  and **drops `position: sticky`** on the header and filter row.
- Reason: inside an iframe, sticky pins to the **iframe's** viewport. The header + filter row are ~335px of
  permanently-frozen chrome. At the documented 1400px embed that is 24%; at a 600px embed it is **56%**,
  leaving room for roughly three objective rows. Unstuck, the chrome scrolls away and the host page's own
  scrollbar does the work.
- True iframe auto-height needs `postMessage` and a script on the ISPE page — **not** done, since it
  requires cooperation from the ISPE side.

## Save / Publish are now git operations
- Added **`admin-server.py`**: a local server exposing `/api/save` (write `data.json` + commit) and
  `/api/publish` (+ push). Bound to `127.0.0.1` only — it can commit to the repository.
- **Why local rather than the GitHub API:** `admin.html` was publicly reachable when this was decided, so
  any embedded token would have been world-readable. *(Pages was switched to `public-deploy` on 2026-07-27
  and admin now 404s — but the reasoning still holds: a fork republishes whatever is on the branch it
  serves, and Pages on a public repo has no auth.)* A runtime-entered token in `localStorage` is also unsafe here while survey free-text is
  still interpolated into `innerHTML` unescaped.
- `admin.html` **degrades gracefully** — with no helper it falls back to the previous download behaviour, so
  the public copy is unaffected.
- The server writes with the **exact formatting `csv_to_dashboard_json.py` uses** (`indent=2`, default
  `ensure_ascii`, trailing newline) and skips the write entirely when the parsed content is unchanged.
  Without both, formatting drift alone produced empty commits.

## Branch & deployment (2026-07-27)
- **`public-deploy` is maintained by copying `index.html` from `main`, not by merging.** Verified before
  updating it: `public-deploy`'s `index.html` was **byte-identical** (SHA-256) to `main`'s pre-session
  version, and its five "divergent" commits were all manual sync commits plus a README tweak. So this is a
  clean overwrite, not a merge — and merging would risk dragging `admin.html` onto the branch that exists
  specifically to exclude it.
- **`public-deploy` has its own separate allowlist `.gitignore`.** `fonts/` had to be allowlisted there
  independently; without it the font files are untrackable on that branch and the live ISPE-facing site
  silently falls back to Georgia. **Any future file `index.html` depends on must be added to both
  allowlists.**
- **BSCL Pages was switched from `main` to `public-deploy` on 2026-07-27**, matching the intent recorded
  here from the start. Verified live: `index.html` 200, `admin.html` **404**, `fonts/` 200. `admin.html` is
  now a local tool only, run through `admin-server.py`. This is "not published", **not** access control —
  Pages on a public repo has no auth, and a fork republishes whatever branch it serves.
- **Copyright holder confirmed as ISPE** (2026-07-27), so the footer was already correct. It had been an
  assumption; it is now stated fact.
- **ISPE had not forked as of 2026-07-27** (`ispe-sp/...` → 404), so `public-deploy` was brought current
  *before* any fork exists. That is the cheap ordering; fixing it after a fork means asking ISPE to re-sync.
- **Fork sync is a standing dependency on ISPE.** GitHub forks do not auto-update; someone there must click
  "Sync fork" for every `data.json` refresh. Given how slow that channel has been, two alternatives were
  raised and are **still undecided**: ISPE iframes the BSCL Pages URL directly (removes them from the
  critical path entirely), or ISPE grants push access so BSCL syncs the fork itself.

## Escaping & mobile (2026-07-27)
- **`esc()` added and applied to every data-derived interpolation** — 30 sites in `index.html`, 41 in
  `admin.html` (the latter includes the string-concatenation form inside `publishReadOnly`, so the published
  export is covered too). Survey free-text reaches these pages from respondent input via
  `csv_to_dashboard_json.py` and is rendered with `innerHTML`; without escaping a crafted survey answer
  executes as markup.
- **Verified by controlled test, not by inspection.** A payload was injected into `data.json` and both
  builds were loaded: on the pre-fix build (`3d0f94e`) the `onerror` handler **fired** and an element was
  injected into the DOM; on the fixed build nothing fired, no elements were injected, and the cell contained
  74 characters of text with **zero child elements**. `data.json` was restored byte-identical afterwards.
- **Any new interpolation of survey-sourced text must use `esc()`.** The helper escapes `& < > " '` so it is
  safe in attribute contexts as well as element content.
- **Mobile verified at 390 / 360 / 320 px.** Tested via iframe viewports, which is what the media queries
  actually respond to (direct window resizing did not take effect in this environment). No horizontal
  overflow at any width, zero elements past the right edge, root font drops to 16px, summary grid reflows
  2→1 columns, and the tactics table stacks into cards with 13.6px body text. The serif holds at small
  sizes — the concern raised when the typeface changed is resolved. A real-handset check is still worth
  doing for touch-target feel, but the layout question is settled.

## Import / Export JSON — hardened, then removed (2026-07-27)
- Import was first **hardened**: it had replaced the whole dataset with no shape check, no confirmation, and
  persisted *before* rendering, so a malformed-but-parseable file (`JSON.parse` accepts `{}`, `[]`,
  `"hello"`) was written to `localStorage` before anything discovered it was broken.
- Then **both buttons were removed entirely**, on the reasoning that once Save commits to git, they are
  redundant with git and Import was the most destructive control in the tool:
  - **Export** was the only real save before `admin-server.py`. Git now provides history, backups, diffs
    and sharing.
  - **Import** was never in the pipeline's path — `csv_to_dashboard_json.py` writes `data.json` directly
    and both pages fetch it on load, so a new cycle is "regenerate, reload". Restoring an old version is
    `git checkout <sha> -- data.json`, which has history and cannot be aimed at the wrong file.
- Recorded rather than quietly deleted because hardening-then-removing looks like churn otherwise. The
  hardening was correct while the feature existed; "is it safe?" and "should it exist?" are separate
  questions and were answered in that order.
- **`validate_payload()` stays in `admin-server.py`.** Save/Publish is now the only path that overwrites
  `data.json`, so that check still guards every write. Its browser-side mirror went with the import UI.

## Other
- **Side-tab accent borders removed** (4px coloured left slabs on the Changes / Completed / at-risk cards)
  in favour of hairline borders — the headers already carried the colour three ways.
- Footer now carries a **2026 copyright** and credits Black Swan Causal Labs for the dashboard; the personal
  byline was removed at the author's request. **The copyright holder is an assumption** (ISPE, as content
  owner) — confirm before this is treated as a legal notice.
- The contact line moved out of the footer to sit under the last objective.
- Design-detector waivers live in `.impeccable/config.json` (not tracked — the allowlist excludes it), each
  with a recorded reason.

---

# 2026-08-03 — New CSV format, partial cycles, retirement

The trial re-upload the earlier notes were waiting on arrived as `SP Reports 7.30.2026.csv`. It did not
behave like a refresh; it behaved like a different instrument. Everything below follows from that.

## The export changed shape, and the old shape is not coming back
- It is now a **report export, not the raw Alchemer response dump**. Committee is column 0; the entire
  `Response ID` / `Time Started` / `Date Submitted` / `Status` block is gone. 540 columns against 404, and
  6 responses against 13.
- Confirmed with the user that **this is the format going forward**, so the script targets it rather than
  treating it as an exception.
- **Run unchanged it would not have crashed — it would have been silently wrong.** `DATE_COL = 2` pointed at
  a goal answer and `COMMITTEE_COL = 21` at an at-risk text box, so every answer failed committee matching,
  fell through to the "any committee" pool, and was attributed by file order. Plausible-looking garbage.
  Columns are now located by header name, which also keeps the old format parsing.
- **Headers are full of non-breaking spaces.** `Tactic\xa05.3.5:` defeated `^Tactic (\d+\.\d+\.\d+)` and
  dropped that tactic from every run. All header text is normalized before matching; coverage went 98 → 99.
- **New tactics were being discarded entirely.** The gate now reads `new tactic(s)`, which the old
  `"new tactics"` test missed, so `NEWTAC` matched **0 of 18** columns. One real proposal was disappearing.
- Incidental: the report export appears to carry **no PII** (no names, emails or IPs). The allowlist
  `.gitignore` still keeps it untracked; that is not worth relaxing for one file's convenience.

## Merge, not rebuild
- **Each cycle is partial.** Six committees reported here and the user confirmed the rest are still
  outstanding. The script previously rebuilt from `DEFAULT_DATA` every run, so an unreported tactic fell back
  to the plan's baked-in **March 2026** status — a partial CSV would have rolled 63 tactics backwards.
- Values now resolve **CSV → existing `data.json` → plan default**, with `--no-merge` for the old behaviour.
- Worth recording because merge looked like a no-op on this cycle: statuses came out identical either way,
  since the unreported tactics happened to already sit at their plan defaults. It was not a no-op — a rebuild
  would have wiped **15 notes, 61 provenance records, 2 previously submitted new tactics**, and reset
  `as_of_date`. It will matter for statuses too once more committees report.
- **`as_of_date` is preserved, not regenerated.** It is curated in the admin panel and cannot be derived from
  a file with no dates. It was being stamped with `datetime.now()`, which silently overwrote the curated value.
- **Re-running a cycle merges it onto its own output**, so a correction made between runs is masked by the
  previous run's values carried forward. This bit during development. The script now detects it
  (`metadata.source_file` matches the input) and tells you to `git checkout main -- data.json` first.

## "Changed" means revised, not on track
- A `Changed` answer used to set the status to **In Progress - On Track**. That turned four tactics being
  *retired* into four tactics reported as progressing — 3.1.4 through 3.1.7 all moved Not Started → On Track
  on the first ingest, and the cycle looked like 17 status changes when only 12 were real.
- **`Changed` now sets `is_revised` and leaves the status alone**, so the previous value carries forward.
  It answers "did this change?", not "how far along is it?", and inventing a status from it overstates
  progress in exactly the cases where work is being abandoned.

## Revisions come from the tactic question, not the goal question
- `is_revised` had been sourced **only** from the March 2026 xlsx tracker, so five tactics reported as
  `Changed` in this cycle showed as revised nowhere. It now comes from the tracker **or** a survey `Changed`.
- The new format also has a goal-level **"Have you revised Strategic Goal X.Y?"**. It is deliberately
  **not** wired in. It asks whether the *goal's own wording* changed, which is a different question:
  Executive answered **No** for goal 3.1 while marking four of its tactics `Changed`. Driving a tactic-level
  overlay from a goal-level question would have contradicted the committee's own answers.

## Retired tactics leave every progress count
- The Executive Committee's new tactic **replaces 3.1.4–3.1.7** ("overcome and included in the new tactic
  3.1.8"). Neither the plan nor the dashboard had any concept of a superseded tactic, so those four kept
  diluting goal 3.1's denominator while representing work that will never be done.
- **Retired tactics are excluded from everything that describes progress**: rings, goal `n/m`, objective
  totals, all four status cards, the Revised/New card, the mini pills, and the admin at-risk panel. Goal 3.1
  reads **3/3** and objective 3 **5/9**. Confirmed with the user that the cards move too, so every figure on
  the page describes the same 95 active tactics rather than the cards and the rings disagreeing.
- They **stay listed** in their goal with a `RETIRED` badge and a dagger pointing at a note under the
  tracker. Removing them would erase the record of a decision; the point is that they are visible *and*
  uncounted. The admin status select is disabled for them.
- **Retirement is a curated list** (`RETIRED` in `csv_to_dashboard_json.py`), not inferred. The survey has no
  structured retirement field — the committee said it in free text — and guessing retirement from prose
  would be the kind of silent wrongness this whole section exists to avoid. Future retirements mean editing
  that dict, which is a reason to ask ISPE for a real field if this recurs.
- Known asymmetry, chosen deliberately: the **Revised/New card reads 17** (retired excluded, so all cards
  describe the same population) while the **section badge reads 21** (retired included, because being
  retired *is* the revision being documented). They will not match.

## Dates are data, not markup
- The Revisions section had `when: 'March 2026'` **hardcoded as a string literal** in both pages. No data
  file could ever move it. It now reads `revised_at` per tactic and falls back to `metadata.tracker_label`.
- **The export carries no dates at all**, so the cycle date is derived from the **filename**
  (`SP Reports 7.30.2026.csv` → July 2026). It is the only evidence of when a cycle was collected. This
  cycle's revisions and new tactic are stamped July 2026 and sort to the top of the timeline.
- **The header stamp was getting staler with every fresh ingest.** "Survey data through …" took the max of
  `last_reported_at`; since nothing from the new format carries a date, the only dates left were
  carried-forward March ones. It now reads `metadata.cycle_label`, plus `cycle_committees` for a
  this-cycle-only response count rather than the cumulative one.
- Ask ISPE to **restore a submission date to the export**. Without it there is no way to order two responses
  from the same committee, and provenance is committee-based rather than recency-based.

## Section renamed
- **"Changes & New Tactics" → "Revisions & New Tactics."** "Changes" was vague and the section only ever
  contained revisions and new tactics.

## Still open
- **Blank ≠ Not Started.** `Not started` appears **zero** times in the new export against 29 in the old one;
  unreported tactics are simply blank. Blank now means one of three things — not started, not reported this
  cycle, or not this committee's goal — and the file does not distinguish them.
- **No mapping rule for junk status values.** Three `N/A` cells and two respondents typing a sentence into a
  status dropdown are reported by the script rather than dropped in silence, but nothing maps them. All five
  happened to carry forward correctly this cycle; that was luck.
- **Goal ownership is now declared in the survey** (17 "please select the strategic goal(s) your committee is
  leading" columns) and is better data than `committee_matches()`'s fuzzy string comparison. Not adopted.
- **At-risk is no longer strictly per-tactic** — 81 columns for 99 tactics, some goals asking once for a
  block of three. The parser pairs a follow-up to the most recent tactic, so a block answer lands on the last
  tactic and the earlier ones read empty. Also, the at-risk text is now mostly *negations* ("The tactic is
  not at risk…"), so non-empty must never be read as "at risk".
- **New-tactic Budget / Timeline / Community Involvement have no home in `data.json`.** Budget in particular
  should probably never render on a public dashboard. The columns are recognized and reported, not consumed.
- **Tactic 3.1.8 does not exist yet.** It is referenced as the successor to four retired tactics but is not
  in the plan; goal 3.1 still runs .1 to .7. Adding it means editing `DEFAULT_DATA` in both HTML files.

## At-risk provenance is per tactic, not per committee (2026-08-03)
Only 6 of ~13 committees reported on 7.30, so the at-risk panel was presenting 28 tactics as one list of
equally-current problems when most were last-known status from February or March. Each row now carries an
*as of Mmm YYYY* marker, or **never reported**, with a header line giving the split: **3 confirmed this
cycle, 24 carried forward, 1 never reported.**
- **Committee-level attribution was tried first and is wrong.** A committee filing a report does not mean
  every tactic it owns got an answer: Executive reported in July and still left 8.2.3 and 8.2.5 blank. Owner
  matching mislabelled **7 of 28 rows** as current (8.2.3, 8.2.5, 6.1.8, 7.1.7, 4.2.2, 4.2.3, and 5.3.5 in
  the other direction). Freshness is therefore read per tactic.
- **The signal is `last_reported_at`.** This export carries no submission date, so a value from the current
  cycle lands `null` while a carried-forward one keeps the timestamp of the cycle it came from.
  `tacticFreshness()` falls back to comparing against `metadata.cycle_date`, so the rule survives ISPE
  restoring a date column.
- **`COMMITTEE_ALIASES` folds `Executive/Impact` → `Executive`** (same committee, per the user). It affects
  only the hover text, which separates "reported but left this blank" from "has not reported at all" — both
  stale, but only the second is worth chasing.
- **Not a coloured pill.** The row already carries one, and the CVD-validated palette owns amber for Delayed,
  so a second chip would read as a status. Muted italic text with a dotted underline reads as an annotation,
  and the wording carries the meaning without depending on colour.
- The header line is suppressed when provenance is uniform, so a fully-reported cycle carries no caveat it
  has not earned.

## Private working repo, push-to-publish (2026-08-03) — planned, not executed
Replaces "ISPE forks, ISPE hosts" at the top of this file. Full plan in `MIGRATION-private-repo.md`.
- **The working repo goes private**, the ISPE reviewer is added as a collaborator, and publishing becomes an
  Action that **pushes** the built public payload into a separate public repo. ISPE's fork disappears from
  the design.
- **Why the fork model had to go:** forks inherit visibility, a private fork cannot be flipped to public
  (GitHub's workaround is to duplicate, which is not a fork and has no "Sync fork"), and `ISPE-SP` is a
  personal *user* account, so Pages there serves public repos only. Confirmed against the API 2026-08-03.
- **The bigger win is not privacy, it is the removal of "Sync fork."** Forks do not auto-update, so every
  refresh needed a click from the party least able to act quickly, failing silently as a stale public
  dashboard. A push lands on the live site with no ISPE action required after setup.
- **`public-deploy` is retired.** The Action builds from an explicit file list, which is auditable and fails
  loudly; the second allowlist `.gitignore` on that branch drifted at least once (`fonts/`, 2026-07-27).
- **Review moves to a Codespace** running `admin-server.py` — the only option that gives a visual admin
  review without a local Python setup and without publishing `admin.html`. It works because a Codespace has a
  backend, so Save/Publish keep functioning. A private repo's Pages site is still *publicly visible* on the
  Team plan (private Pages is Enterprise Cloud only), so serving admin from there was never an option.
- **The CSV can now live in git.** The 7.30 export carries no PII — verified: no Name / Email / Contact ID /
  IP / geo columns and zero email or IP patterns in cell contents, against 13 emails and 24 IPs in the old
  export. This is a property of the current format, **not a guarantee**, so the ingest Action must scan every
  upload and fail closed rather than trust it.
- **BSCL is on the Team plan** (Pages on private repos, Actions, Codespaces all available). The repo has 0
  forks / 0 stars / 0 watchers, so going private retracts nothing.

# 2026-08-09/10 — August cycle, notes off the public site, the emblem

## The filename convention changed; the format did not
`20260804134803-SurveyExport.csv` arrived as a third naming convention. The *columns* were byte-identical to
the 7.30 export, so no parser work was needed — but two things would have failed silently:
- **`cycle_date_from_filename` matched only `M.D.YYYY`** and returned `(None, None)`, which would have dated
  the entire cycle `null`. An undated cycle renders as a clean page with the dates merely absent; nothing
  looks wrong. It now reads a leading `YYYYMMDD` stamp as well.
- **The default glob was `SP Reports*.csv`**, which does not match the new name, so running the documented
  no-argument command would have re-ingested **July** while appearing to work. `CSV_GLOBS` now covers both
  conventions and deliberately excludes `SP Plan-SurveyExport.csv`, the retired 404-column April format.

## The August file supersedes July rather than merging onto it
All six July committee rows appear **byte-identical** in the August export, plus six more. Executive answered
twice: the two rows are complementary, not contradictory — 16 columns filled only by the first, 22 only by
the second, **zero where both are filled and disagree** — so `pick_value` assembles them correctly with no
rule needed. 11 committees reported; **Executive/Impact, Finance and Global Development / Strategic Planning
did not**, and their tactics carried forward.

## Completion dates: curated for history, self-dating from here
The export records what a status *is*, never when it changed. So `COMPLETED_AT` in
`csv_to_dashboard_json.py` holds the dates — beside `RETIRED`, and for the same reason: **in the script, not
in `data.json`, so a regeneration cannot quietly drop them.**
- Tactics that **transition** to Completed during a cycle are stamped with that cycle automatically. This is
  the mechanism going forward; the dict should not need maintaining again.
- A tactic listed in `COMPLETED_AT` that comes back as anything other than Completed is **reported, not
  silently dated**.
- **Six dates record when the tactic was logged, not when it was finished.** 2.1.2, 2.1.3, 2.1.6, 3.1.3,
  6.1.2 and 7.1.2 were already Completed before August, with `last_reported_at` `null` — no survey ever
  reported them and no earlier date exists. They are dated August 2026 at the user's direction. **The
  dashboard shows all nine August dates identically**, so a reader will take all nine as work finished this
  cycle. If that distinction ever matters, the honest options are a footnote or leaving those six blank.

## Notes are internal — stripped from the payload, not hidden in the page
Committee notes are written for internal reporting ("not started due to the expected completion date…"), and
ISPE does not publish them. **Removing the Notes column would not have made them private:** `index.html`
fetches `data.json` over HTTP, so the file is readable directly — and 28 notes were sitting at the live
site's own `/data.json` until this was fixed.
- `build_public_payload.py` strips them from the file that ships and **refuses to emit a file that still
  contains them**. Its `--check` mode is the assertion the publish step runs; verified in both directions
  (fails on the working `data.json`, passes on the generated payload).
- **The public payload is a build artifact under `public/`, rebuilt every publish, never committed.** The
  previous model — copy `data.json` across from `main` — is now the single action that would put the notes
  back on the public site. The `public-deploy` README says so explicitly.
- The notes remain readable in `main`'s `data.json`, which is a public repo. The user reviewed all 28 and
  judged them benign; git history keeps them regardless. Going private closes this, not the build step.

## Revision rationale is published, so it is edited rather than stripped
`revised_description` is the same raw survey free text as notes, but it reaches the public **Revisions & New
Tactics** panel, which is a deliberate feature. It was publishing unedited answers — *"the ISPE Manuscript
Initiative was on hold the precious year"*, a fragment reading *"overcome and included in the new tactic
3.1.8"*, and one entry that is literally the answer to a yes/no question, beginning *"Yes."*. This is a
presentation problem, not a disclosure one, so the fix was to make it **editable in the admin panel** on
every revised tactic (not only those that already have text), with a placeholder stating the text is
published. Clearing the field deletes the key rather than storing `""`, so the payload carries no empty
fields the dashboard would render as an empty quotation.

## A failed data load must announce itself
When `data.json` cannot be read, both pages fall back to the inline `DEFAULT_DATA` — a complete, plausible
and **wrong** dashboard: February 2026, 18 Completed against the 27 that are real, no retirements. The only
signal was a `console.warn` nobody opens. Anyone downloading `admin.html` from the public repo and opening it
got exactly this. Both pages now render a sticky banner above everything, naming the cause (`file://` vs an
HTTP status) and the snapshot's own date, **read from `DEFAULT_DATA`** so it stays honest if that snapshot is
ever refreshed. Verified by serving both pages from a directory with no `data.json`.

## The as-of field was write-only
`dateInput` was never populated on load — written on change, never read back — so the admin panel never
displayed the date it was about to publish. **That is the mechanism behind `as_of_date` sitting on April
while the data said July.** It now renders the current value; the month-name list is shared rather than
duplicated between the setter and the parser.

## The emblem came from the pptx, not the jpg
The supplied `coffee stain logo.jpg` looked like a plain logo with a faint smudge — 608 tinted pixels, 7%
luminance difference. That was **JPEG flattening**, not the artwork: the PNG inside `coffee stain logo.pptx`
is RGBA (50.5% fully transparent, 49.5% partial alpha, three pixels opaque) and the "stain" is a **bold white
brushed ring**. Exported to JPEG it became white-on-white and vanished.
- The asset is cropped to its artwork (the source carried ~35px of empty pixels top and bottom, so uncropped
  the *image* would meet the header edge while the ring floated inside it), sized for a 180px slot and
  palette-quantised: **146 KB → 16.5 KB**, with no pixel differing by more than 16/255 at render size.
- **The header has no vertical padding**, so the emblem sets its height and the ring meets both edges. The
  white chip the old logo sat on is gone — it would have put a white rectangle behind a transparent ring.
- Steps 180 → 140px below 900px; at 640px the header wraps, the emblem stops defining the height, and
  vertical padding returns at 88px. Checked at 1200 / 860 / 600 / 380.
- The **read-only export inlines the emblem as a data URI**. That document is emailed as a single file, so a
  relative `src` rendered as a broken image the moment it left the folder.
- `newlogo.jpg` and `ISPE Logo.jpg` are retired — byte-identical duplicates of each other, `index.html` used
  one and `admin.html` the other.

## `public-deploy`'s allowlist is a live hazard, not paperwork
That branch ignores everything by default, so an asset that is not allowlisted is **absent from the deploy
and 404s on the live site with nothing failing anywhere**. `banner picture.jpg` was in exactly that state —
tracked from before the allowlist tightened, but never allowlisted, so it would not have survived being
untracked once. Both it and `ispe-emblem.png` are named explicitly now. This is the same failure that lost
`fonts/` on 2026-07-27.

## The documented embed height was shorter than the page
The snippet specified `height:1400px`; the collapsed page measures **1742px at 1200px wide** (1927 at 900,
1986 at 760, 1988 at 600, 2708 at 414, 2910 at 380). It was scrolling *inside* the frame — the nested-scroll
problem `is-embedded` exists to avoid — and the header had grown 120 → 180px with the emblem. Now 1800px.
**No fixed height fits every case**: phones and any expanded objective scroll within the frame regardless.
Only a postMessage resizer fixes that exactly, and it needs the host page to cooperate, which this design
deliberately avoids requiring.

## The fork is back — as an acknowledged stopgap, not a reversal
The 2026-08-03 reasoning stands: forks do not auto-update, and "Sync fork" puts the slowest-moving party on
the critical path with a silent failure mode. But the migration has not run, the repo is **still public**, and
ISPE wants a branded URL now — and a fork of a *public* repo is public and Pages-servable on a free personal
account. So ISPE-SP forks, enables Pages on `public-deploy`, and IT embeds `ispe-sp.github.io`.
- **Verified 2026-08-10: no fork exists.** `forks_count` and `network_count` are both 0, the forks list is
  empty, and ISPE-SP has 0 public repos. An earlier belief that they had forked "last week" was mistaken.
- **This unwinds at migration.** Confirmed against the docs: making a public repo private **detaches existing
  public forks into a new network**, so theirs permanently loses the ability to sync. The fork is a thing to
  tear down, not a foundation to build on.
- **The failure mode to watch is Pages on `main`**, which would publish `admin.html` and the notes under
  ISPE's own URL. The handoff note therefore makes "confirm `/admin.html` returns 404" an explicit step and
  tells them not to share the address if it does not.

## The hosted reviewer site was chosen and built (2026-08-10)
**Decided and built.** `review-site/` is a Cloudflare Pages project behind Access, with a Pages Function and
a D1 database. It supersedes the Phase-6 Codespace step in `MIGRATION-private-repo.md`. Setup and the
verification checklist are in `review-site/DEPLOY.md`. What the decision actually settled:

- **Review-only, not a hosted admin.** Reviewers comment, flag and approve; they cannot change a status, edit
  a rationale or publish. Hosting the *editor* would have meant turning Save/Publish into authenticated
  server-side git operations and giving every reviewer the ability to alter the published plan. Editing stays
  local, where `admin-server.py` already makes Save and Publish real git actions.
- **Access with one-time PIN, not a shared password.** A shared password cannot tell reviewers apart, so
  every comment would carry a self-declared, unverifiable name, and revoking one person would mean changing
  it for everyone. Access verifies the email and the API reads the identity from the signed token, so
  attribution is a property of the system rather than a request to be honest.
- **D1, not a KV blob.** Review state as one JSON document per cycle is a read-modify-write: two reviewers
  commenting in the same moment silently lose one comment. Comments are an append-only table instead, so
  concurrent writes cannot clobber each other.
- **Approvals are per reviewer, not one shared checkbox.** A shared tick cannot distinguish "nobody approved
  yet" from "someone approved and someone else unticked it", and records nobody's name — which is the entire
  content of an approval. The button shows the count and names the approvers.
- **The site serves the notes-stripped public payload.** Reviewers are checking what is about to be
  published, so that is the artifact to look at; it also keeps the committee notes off an internet-facing
  host rather than leaving Access as the only thing in front of them. This is the one point where the build
  departs from the "feed it working data" note below — it departs because the page is review-only and never
  rendered the notes anyway.
- **The page is generated from `index.html`, not copied.** STATUS already records that the render code exists
  twice and "every fix lands twice"; a hand-maintained third copy would be the one nobody updates.
  `build_review_site.py` patches the dashboard at build time and **asserts the match count of every patch**,
  so drift in `index.html` fails the build instead of silently producing a review site with no comment buttons.
- **Notification is one email per reviewer per cycle, triggered by them.** Not a daily digest (this site
  changes twice a year, so a schedule is noise) and not per comment (a reviewer working through 99 tactics
  would send dozens). Pressing **Complete review** mails the owner that reviewer's comments in full, grouped
  by target, plus which objectives they did and did **not** approve — the second list being the more useful
  signal. It is a button, not a checkbox, because a tick that silently emails somebody is a nasty surprise,
  and it confirms first because email cannot be unsent.
- **A completed review is recorded even when the email fails.** Delivery status is stored per attempt and
  shown on the row. A reviewer who finished has finished; rolling that back because an API key expired would
  be the software lying, and "it looked like it worked" is this project's characteristic failure.
- **Mail goes out over HTTPS, not Cloudflare Email Routing.** `blackswancausallabs.com` is on Cloudflare
  nameservers, which makes Email Routing look free and obvious — but its MX points at Google Workspace, and
  enabling Email Routing wants those records. Breaking real email to save four notifications a year is a bad
  trade. An outbound API call touches no DNS.
- **The API fails closed.** With the Access variables unset it returns 503 and serves nothing, rather than
  treating "no auth configured" as "allow". Verified, along with rejection of a forged token carrying a
  correct audience, issuer and expiry.

The original assessment that led here, kept for the reasoning:
- **Most of the panel already works unhosted** — the code was written for it (`admin.html`, "everything falls
  back to the previous download-a-file behaviour"). Render, editing, Change Log, and **Publish** (which falls
  back to downloading the self-contained export) all function. **Save is the trap**: it reports "Saved in this
  browser only", but `ispe_sp_data` is written and never read back, so the edits are gone on reload. That
  message must be made honest before anyone else uses a hosted copy.
- **It beats the Codespaces plan on every axis** for review: no GitHub account needed (Access does email
  OTP), no cost (Team orgs get *zero* free Codespaces quota), always current if Pages auto-deploys from the
  repo, and no local Python. If this is built, the Codespace step in `MIGRATION-private-repo.md` — which
  exists solely to give a reviewer a visual admin — becomes unnecessary.
- **Whatever hosts admin must be fed working data, so the auth becomes the only thing protecting the notes.**
- **Reviewer feedback needs shared server-side state**, not localStorage and not an emailed file, because the
  requirement is "go in and see it". A Function backed by KV, keyed by cycle, with the commenter's identity
  read from the Access JWT — which gives attribution for free. A mock of the review panel exists at
  `review-panel-mock.html` (untracked): comment and flag on any tactic/goal/objective/panel, per-objective
  reviewed checkboxes, an aggregated feed, and review state that **resets when the cycle label changes** so
  an approval cannot silently carry onto data nobody saw.

## Setting Access up has two traps that fail in opposite directions (2026-08-10)
Both were hit on the real deployment and neither announces itself.

- **One-time PIN is the default login method only while NO identity provider exists.** This account already
  had a "Cloudflare" provider, so the login page offered *only* "Sign in with Cloudflare" — an option
  requiring a Cloudflare account, which no external reviewer has. The site looked correctly protected and
  would simply have refused everyone invited. One-time PIN has to be added explicitly under
  **Integrations → Identity providers**. Verify the login page shows an **Email** box before sharing a URL.
- **The login page prints a team name that is not necessarily the live team domain.** It showed
  `wandering-firefly-0501.cloudflareaccess.com` while the working one is `ispe-sp.cloudflareaccess.com`.
  Configuring `ACCESS_TEAM_DOMAIN` from the page would have failed the issuer check on every valid token.
  The authoritative test is which host serves `/cdn-cgi/access/certs` — the real one returns 200, the other
  404. Both the team domain and the AUD tag can be read straight out of the redirect the site returns to an
  unauthenticated request, which is faster and does not depend on dashboard layout.

## `@ispe.org` is a different society — the access rule nearly went to the wrong one (2026-08-10)
The requested reviewer rule was "anyone `@ispe.org`". That domain belongs to the **International Society for
Pharmaceutical Engineering**: separate registrar, separate nameservers, separate Microsoft tenant. The
pharmacoepidemiology society is **`@pharmacoepi.org`**, which is what the dashboard's own contact address
uses. The rule as requested would have admitted thousands of members of an unrelated organisation to a board
carrying committee comments and the at-risk list, *and* refused every actual ISPE address. The acronym
collision is easy to make and will recur — check the domain, not the initials.

## Reviewer feedback, first cycle (2026-08-10)
- **"Efforts" → "tactics".** The donut's centre label was *believed* to be the last place the old word
  survived. It was not — see the 2026-08-20 entry below; three more UI strings were found and fixed.
- **"Revised / New" came off the summary row.** It sat beside four mutually exclusive statuses and read as a
  fifth category. It is an overlay tag — a revised tactic also carries one of the four — and only the
  footnote said so. Removing it makes the remaining figures visibly sum to the total with nothing to
  reconcile, and the Revisions & New Tactics section below already carries the detail plus a timeline. The
  **filter button of the same name was kept**: the objection was to a row of counts that looked like
  categories, and a filter is a tool for narrowing the view rather than a claim about them.

## Tactic numbering: 3.1.8 stands unless Executive agrees otherwise (2026-08-10)
Proposed: number the tactic replacing 3.1.4–3.1.7 as **3.1.4**, matching the convention of keeping new
numbers aligned with active ones. Not adopted, pending the committee. Three reasons, in order of weight:

1. **Executive named it 3.1.8 in writing** in their August survey response ("…overcome and included in the
   new tactic 3.1.8"). That is the responsible committee's own identifier, not ours to reassign.
2. **It is already published** — 8 fields on the live site (4 × `superseded_by`, 4 × rationale text).
3. **`csv_to_dashboard_json.py` merges keyed on `tactic_id`.** Reusing 3.1.4 for different work means the
   old 3.1.4's status and provenance carry silently onto a tactic its committee has never seen — the
   plausible-but-wrong output this pipeline produces whenever an identity is ambiguous.

If ISPE does renumber, the retired rows must move out of the goal listing in the same change, or two rows
share an ID. Either way the replacement's text already exists: Executive supplied it in August and it sits
unused in `data.json` as a `new_tactics` entry under goal 3.1.

## Tactic numbering: 3.1.4, revised in place (2026-08-20) — supersedes the entry above
ISPE settled it: **Daniela asked for 3.1.4, and confirmed with Ursula** ("designating the new tactic as
3.1.4 to keep the numbering and indicating this as a revision (also listing the retired tactics under
'Revisions and New tactics')"). The 2026-08-10 entry above is superseded — its reasoning stands as the
record of *why the question was worth asking*, not as the outcome.

**What was adopted is narrower than "renumber 3.1.8 to 3.1.4".** There were two ways to give ISPE the
number they asked for, and only one of them works:

- **A separate new 3.1.4, with the old 3.1.4 still retired beside it.** This is what the 2026-08-10 entry
  warned about, and re-checking confirmed it: three separate things are keyed on `tactic_id` and would each
  break. `csv_to_dashboard_json.py:631` (`existing_tactics.get(tid)`) would carry the retired tactic's
  status and provenance onto the new one; `RETIRED["3.1.4"]` would stamp the new tactic retired and
  superseded by itself; and the survey instrument **still ships a "Tactic 3.1.4: Identify gaps…" column**
  (col 177 of the August export), so next cycle's answer to the old question would land on the new tactic.
- **3.1.4 revised in place, with 3.1.5–3.1.7 retired into it.** Adopted. One `tactic_id`, one continuous
  history, nothing to re-key. Ursula's own words — "indicating this as a revision" — describe exactly this,
  and it is what makes reusing the number *honest* rather than a collision: 3.1.4 is not a different tactic
  wearing an old number, it is the same line item rewritten.

Result: Goal 3.1 reads **3/4** instead of the old 3/3 that implied the goal was finished, Objective 3 reads
**5/10**, and active tactics move **95 → 96** with retired **4 → 3**. Verified in the browser, not just in
the data: 3.1.4 renders active with a REV badge, 3.1.5–3.1.7 render retired, and the string "3.1.8" appears
nowhere on the rendered page.

**Two curated overrides were needed, because the survey re-supplies its answers on every ingest.**
- `REVISION_RATIONALE` — the rationale is published prose, and the explain column wins over `data.json` on
  every run (`rev_desc`, ~:683). Executive wrote "overcome and included in the new tactic 3.1.8" in four
  cells; without the override, every re-ingest quietly restores the old number. **Their wording is kept and
  only the number moves** — editing a committee's own published words is authorised here by Daniela and
  Ursula, and is not something to do silently on our own initiative.
- `ADOPTED_NEW_TACTICS` — Executive's free-text submission is the *source* of the new wording. Once it is
  carried as a numbered tactic it must stop appearing as an open suggestion, or "Revisions & New Tactics"
  lists the same thing twice: once as the suggestion, once as the tactic it became.

**The one judgment call: provenance was carried, not cleared.** 3.1.4 keeps `last_reported_by: Executive`
/ `last_reported_at: 2026-02-27`. The 2026-08-10 plan said to clear it so the tactic read "never reported" —
but that was written for 3.1.8, a genuinely new row with no history. Under revised-in-place the lineage is
the whole justification for the number, so erasing it would contradict the model, and it would need a
mechanism that exists for exactly one row. The carried date is also what correctly flags 3.1.4 as
**unreconfirmed this cycle** in the at-risk panel — which is true: Executive proposed the revision in August
but reported no status against it. `revised_at: 2026-08-04` and the rationale carry the "this changed in
August" signal.

**Left open deliberately: the survey instrument still asks the old question.** Its 3.1.4 column reads
"Identify gaps (gaps and prioritization analysis)…". The ingest is correct — that column maps to 3.1.4,
which is the right tactic — but a committee answering it next cycle is answering about wording that no
longer exists. This needed fixing under *either* numbering (3.1.8 had no column at all, which the coverage
check at :780 would have reported), and it is an instrument edit, not a code change.

## "Efforts" → "tactics": our chrome only, never the plan's prose (2026-08-20)
Daniela's first fix was applied twice: once on 2026-08-10 (the donut label), and properly on 2026-08-20,
when "throughout" turned up three UI strings the first pass missed — `Filter Strategic Efforts` in **both**
`index.html` and `admin.html`, and `Total Strategic Efforts` in `admin.html`'s `publishReadOnly()` export.
The 08-10 note claiming the donut was "the last place the old word survived" was wrong, and is corrected in
place above so a cold start does not trust it.

**The word is now gone from everything we author. It deliberately remains in 16 strings that other people
wrote — 15 plan descriptions (3 goal, 12 tactic) and 1 committee submission — and those must not be
touched.** In the 15, "strategic efforts" is the **ISPE Strategic Plan's own language**, quoted from `ISPE_Strat_Plan_2029_-_FINAL.pdf` — "continue transparent calls for leaders and
members to engage in strategic efforts" (Goal 1.1), "lead strategic efforts through a transparent
solicitation" (1.1.1), and 14 more. Rewriting those would not be relabelling our UI; it would be editing the
plan the dashboard exists to report on, and several read as nonsense with the word swapped ("lead strategic
tactics").

The distinction is **who wrote the string**, not which file it lives in:
- **Ours → "tactics".** Headings, filter labels, summary cards, the donut, section titles.
- **The plan's / a committee's → leave verbatim.** Everything inside `DEFAULT_DATA` descriptions, plus
  survey-sourced `notes`, `revised_description`, and `new_tactics`. A blanket find-and-replace across these
  files is therefore **always wrong**. Audited 2026-08-20: of the 16 remaining matches in `data.json`, 15
  are plan `description` fields and the 16th is Education's own new-tactic submission under goal 1.2 (the
  one that begins *"Yes."*). None are in notes or revision rationales.

**Still inconsistent, deliberately left:** `publishReadOnly()` also carries a **"Revised / New" summary
card**, which is the *other* half of Daniela's feedback ("stop listing Revised / New as a status", shipped
in `8d4cb42`). That fix landed in `renderSummary()` and missed this export path. Removing a card from a
published artifact is a wider change than a relabel, so it was flagged rather than done. Worth closing next
time this file is open.

## The embed's lonely donut: keep the two cards side by side to 600px (2026-08-20)
On the ISPE page the dashboard sits in an iframe about **760px** wide. That fell under the old **900px**
breakpoint, so `.chart-filter-row` collapsed from `170px 1fr` to a single column, the Status Overview card
went full-width, and a **140px donut sat alone in a 760px box** with roughly 150px of dead space around it.
It looked broken in the embed while looking correct on a desktop browser, which is why it survived so long —
**nobody who tested it at desktop width could see it.**

Fixed by moving the collapse point to **600px**, which is where 170px plus the filter buttons genuinely stop
fitting, rather than where the desktop layout happens to stop being comfortable. Two supporting rules apply
only in the 600–900px range:
- `.chart-card canvas { margin: auto }` — the donut centres in whatever height the filter card sets, instead
  of hanging at the top of a stretched grid cell.
- `.filter-row .filter-btn { flex: 0 1 auto }` — buttons are `flex: 1 1 auto` by default so a full row
  divides evenly. At this width they wrap, and a **lone wrapped button stretches across an entire row on its
  own**, which reads as a banner rather than a filter. Sizing to text fixes it.

Verified at three widths: 420px still stacks (phone, unchanged), 760px sits side by side (the embed),
above 900px is untouched. Saves ~150px of vertical space in the embed.

**A merged single card was considered and not taken.** Putting the donut and filters in one pill solves the
same problem, but it restructures markup that `review-site/build_review_site.py` patches by
match-count-asserted selector, and it changes the desktop layout to fix a defect that only exists below
900px. The breakpoint move is three rules and touches nothing above 900px.

**The general trap:** this dashboard is **embedded**, so the width that matters is the host page's content
column, not the browser window. Anything responsive must be checked at ~760px, not just full-screen.

## 6.2.1 is not completed — the survey was wrong, and the file said so itself (2026-08-21)

Daniela, on the email chain: *"can we remove Tactic 6.2.1 from the list of completed tactics based on the
communication with Anne? This is not completed yet and it's an important document, so I don't want anyone to
look up for an updated version."*

**The correction was never in the export.** `Export 8.20.2026.csv` still carries `Membership -> 'Completed'`
in column 387. Laura's edit did not reach Alchemer, so no re-ingest could ever have picked it up.

**The file contradicted itself, which is the part worth remembering.** The same work is tracked twice:

| tactic | reported by | August answer |
|---|---|---|
| 6.1.5 | Strategic Planning | `In progress- on track` |
| 6.2.1 | Membership | `Completed` |

The survey header for 6.1.5 says so outright — *"…\*also a tactic under goal 6.2"*. The plan baseline in
`index.html`'s `DEFAULT_DATA` also carries 6.2.1 as In Progress. So Membership's answer was the lone outlier,
and Daniela's correction agreed with two independent sources already in the repo. **When two committees own
one piece of work, the export can disagree with itself and nothing flags it** — the ingest has no
cross-tactic consistency check, and a duplicate-tracked tactic is exactly where one would pay off.

**Fixed by editing `data.json`, not the script.** 6.2.1's `completed_at: "August 2026"` was *derived* — it is
not in `COMPLETED_AT`; `csv_to_dashboard_json.py:753-762` stamps the cycle label when a tactic flips to
Completed during a cycle. So clearing the status clears the date on its own, and there was no curated
override to unwind. Status set to `In Progress - On Track` to match 6.1.5. Goal 6.2 went `5/6 → 4/6`,
plan-wide Completed `27 → 26`, On Track `37 → 38`. Published as `main 881e3e4` / `public-deploy 5ca8cbc`.

⚠️ **This correction is not durable against a re-ingest.** The August CSV still says `Completed`, so anyone
following the documented ingest recipe in `STATUS.md` (`git checkout main -- data.json` then run the script)
**silently reverts it**. There is no `STATUS_OVERRIDE` map today — `RETIRED`, `REVISION_RATIONALE` and
`COMPLETED_AT` cover the other "the survey is wrong and we know better" cases, but not status. If August is
genuinely the last ingest of this cycle the edit is safe; if the file is ever re-run, check 6.2.1 first.

## The Aug 20 "new ingest" was the Aug 4 export again (2026-08-21)

`Export 8.20.2026.csv` is **byte-identical** to `20260804134803-SurveyExport.csv` — same MD5
(`447c3ce04c61924bfbbcb74bc3e61668`), already the source of `data.json`. Same 12 responses, same 11
committees. No late returns arrived between Aug 4 and Aug 20.

**Ingesting it would have corrupted data while changing nothing.** A dry run moved 11 of 1041 leaf fields:
three metadata, and **eight `revised_at` dates pushed `2026-08-04 → 2026-08-20`** (2.2.1, 2.2.2, 2.2.5,
3.1.4, 3.1.5, 3.1.6, 3.1.7, 7.1.7). Cause: `rev_when = rev_explained_at or cycle_date` at line 719, where
`cycle_date` comes from the **filename**. Correct for a real cycle; it back-dates a revision that never
happened for a re-ingest. Zero statuses, progress values or narratives changed.

**Two intake gaps this exposed:**
1. `CSV_GLOBS` matches `SP Reports*.csv` and `[0-9]*-SurveyExport.csv` — **neither matches
   `Export 8.20.2026.csv`**. A bare `python3 csv_to_dashboard_json.py` would have skipped the new file,
   re-ingested the August one, and printed a confident success. The filename convention is now three deep
   and the glob is the only thing standing between a renamed export and a silently stale publish.
2. Nothing compares CSV **content** to what is already ingested. `metadata.source_file` records a name, not
   a hash, so a re-download under a new name looks like a new cycle.

**Suggested guards (not built):** store a `source_hash` in `metadata` and refuse to ingest when it matches;
warn loudly on any unrecognized `*.csv` sitting in the folder rather than ignoring it in silence. **Until
then: `md5` the CSV against `metadata.source_file` before every ingest.** Identical means do not ingest.

## The survey stamp is gone from the public header (2026-08-21)

Removed in two steps, both from Daniela with Ursula agreeing. The header line under the title used to read
`Survey data through August 2026 · 11 committee responses this cycle`. Neither half survived.

**The count went first.** *"I think adding the '11 committee responses this cycle' note creates confusion, as
Ursula also indicated. Not sure we need that information included."* She was right, and for a specific
reason: **11 of 14 committees reported**, and one of the 12 rows was a **second Executive submission**. So
"11 committee responses" was a completeness figure with its denominator missing — it read as *everyone
reported* when three committees had not. A number that invites the wrong inference is worse than no number.

**Then the date.** *"it just seems redundant"* — and it was, verbatim: the line above already says
`2024-2029 | As of August 2026`. Both come from the same cycle. Nothing was lost by deleting the restatement.

**What that removed in code.** Both branches of the count (the `cycle_committees` length *and* an older
fallback derived from `responding_committees` — leaving that one would have brought the note back on any
cycle where `cycle_committees` was empty, with no obvious cause), the `committees` Set, the `#surveyStamp`
element, and the whole `latest` pass over every tactic, which existed solely to date this stamp. The As-of
line uses `metadata.as_of_date` and needs none of it.

**`admin.html` keeps its stamp.** Internally, "how much of the cycle is actually in" is the question you are
asking, so the count earns its place. The two headers now differ by one line on purpose — if they are ever
reconciled, reconcile *toward* admin keeping it, not toward the public page getting it back.

**Collapsed desktop height after the change: 1742px**, so the documented 1800px embed still clears it. See
"The documented embed height was shorter than the page".

**A process note worth keeping.** The STATUS.md bullet describing this header was wrong when checked — it
claimed a "Revised / New = 18" card that had been deleted the day before, and a revisions badge of 21 that
actually renders 23. A verification pass had marked it correct, because it compared the docs against
`data.json` rather than against **the rendered page**. 21 is the right answer from the data; 23 is what the
badge shows, because it adds the 2 `new_tactics` submitted this cycle. **Check UI claims by loading the
page.** Data-derived agreement is not evidence about what a user sees.

## Reviewer round 2: 6.2.1 flips back, and revised tactics leave At Risk (2026-08-24)

Five comments from the reviewing admin on the Cloudflare site. **Two changed something; three were already
true.** Worth reading as a set, because the pattern is that most reviewer comments are confirmations and the
job is separating those from the ones that are not.

**6.2.1 → Completed. This reverses the 2026-08-21 entry above, and it was contested.** Daniela had asked for
in-progress, sourced ("communication with Anne") and reasoned (nobody should find a non-final document). The
admin asked for `Completed` with no stated reason. **The contradiction was surfaced rather than applied**;
John chose the admin's reading. Objective 6 → 7/14, Goal 6.2 → 5/6, plan-wide Completed → 27.

What this restores is **what the export actually said** — Membership reported `Completed` in the August
cycle. What it does *not* resolve is the underlying disagreement: **6.1.5 tracks the same work under goal 6.1
and still reads `In progress- on track`**. Two committees, one document, opposite answers, and the dashboard
now shows both. ⚠️ **6.2.1 has been flipped twice in four days. Do not change it a third time without asking
who is deciding** — and if it comes up again, the fix is probably to reconcile 6.1.5 and 6.2.1 rather than
to keep flipping one of them.

**At Risk now excludes revised tactics** (3.1.4, 7.1.7 drop out; 30 total, 9 delayed, 21 not started, 29
confirmed / 1 carried). The rationale: a revised tactic's status is carried forward from *before* the
rewrite, so it describes work that no longer exists rather than work at risk.

**The admin's own numbers are what identified the rule**, and this is the useful trick: "Total delayed = 9"
and "Total = 21" only both hold if **revised** tactics are excluded while **new** ones stay. Excluding
revised *and* new would have given 19 not started, not 21. Two quoted totals were enough to pin down an
intent that the prose left ambiguous — when a reviewer quotes numbers, solve for the rule before asking.

⚠️ **Accepted trade-off: 7.1.7 is genuinely `In Progress - Delayed` and now appears in no risk view at
all.** The panel exists to surface what needs attention before publishing, and this hides one item from it.
Flagged before the change, accepted. It also sits close to the "Revised / New is not a status" decision of
2026-08-20 — it does not reintroduce a status, but it does let *revised* override a real status in one view.

**Implemented as a filter in `renderAtRisk()` in `admin.html`, not as a data change.** At Risk is admin-only
— `index.html` carries a stray `.at-risk-item` CSS rule and nothing else — so the public dashboard moved only
via `data.json`. The reviewer site inherits the filter because `build_review_site.py` lifts the whole region
between `const AT_RISK_STATUSES = [` and the SUMMARY comment out of `admin.html`; the edit sits inside that
region and touches neither anchor, so the build's match assertions still pass.

**The three no-ops.** All six tactics listed under "revisions" already carried the exact status quoted —
3.2.2, 3.2.5, 6.1.4, 6.1.5, 6.1.7 on track and 4.2.4 not started. Note 3.2.5 and 6.1.5 are **not** flagged
revised, so they do not appear in the Revisions panel at all; if the admin expected them there, that is a
separate question nobody has asked yet.

## 7.1.7: a status taken from the committee's own words (2026-08-24)

Set to `In Progress - On Track` by hand. It had read `Delayed` since March, carried forward because Meetings
Oversight reported it `Changed` in August and "Changed" supplies no status.

Their revision text in the same submission settles it: *"The is tactic is in progress as we have started
working on it. The timeline for tactic 7.1.7. which was planned to be completed in December 2025 has been
changed and is now December 2027 (in line with Gulf regional meeting planning)."* It was Delayed for missing
December 2025 — a deadline that no longer exists. **The status is read out of the committee's own prose, not
inferred from the absence of one.** Plan-wide Delayed 10 → 9, On Track 37 → 38.

**3.1.4 was deliberately NOT changed**, though it is stale in exactly the same way — `Not Started` carried
from February 2026, describing the tactic *before* it absorbed 3.1.5-3.1.7. The difference is evidence:
7.1.7's committee wrote down its progress, 3.1.4's did not, and `Not Started` is plausibly correct for a
newly consolidated tactic. **Guessing is what made 6.2.1 flip twice in four days.** Laura confirmed on a call
(week of 2026-08-17) that 3.1.4 is the combination of 3.1.4-3.1.7, which confirms the revision, not a status.

⚠️ **Neither correction survives a re-ingest.** The August export says `Changed` for both, which carries no
status, so 7.1.7 would revert to Delayed. This is the third hand-correction now living only in `data.json`
(with 6.2.1), and the second that a re-run would silently undo. The `STATUS_OVERRIDE` map keeps earning its
place — see 2026-08-21.

**A note on "Changed" as an option.** It sits in the same single-select as the four progress values, so a
committee picking it cannot also report progress — 8 tactics did so this cycle. Mapping `Changed → On Track`
would reproduce the reviewer's exact figures (9 delayed, 21 not started), but that behaviour existed once and
was removed on purpose: it showed progress nobody had reported, precisely for the 3.1.4-3.1.7 family. Per
tactic, from evidence, is the right granularity. A blanket rule is not.

## 6.2.1 / 6.1.5: settled — both In Progress (2026-08-25)

**This supersedes both earlier 6.2.1 entries and should be the last word.** Daniela, asked directly and
answering both tactics together:

> "Those two tactics refer to the update of the opportunities pathway. This has not been completed, but it is
> in progress as there are ongoing activities that will support the update (e.g., FISPE engagement, the
> benefits survey). I would say to mark as 'in progress' for both tactics."

Both now read `In Progress - On Track`; 6.2.1 lost its August 2026 date. 6.1.5 was already correct.

**The full history, because the shape of it is the lesson:**

| when | 6.2.1 | who, and on what basis |
|---|---|---|
| August ingest | Completed | Membership's survey answer |
| 2026-08-21 | In Progress | Daniela, via Anne — sourced, but only about 6.2.1 |
| 2026-08-24 | Completed | reviewing admin, no reason given |
| 2026-08-25 | **In Progress** | **Daniela, with a reason, covering both tactics** |

Three flips in five days on one tactic. What ended it was not a better argument but a **better-scoped
question**: asking about *both* tactics at once, of the person who owns the work. Each earlier round asked
about 6.2.1 alone, so each answer left the other half of the same document contradicting it, and the
contradiction kept regenerating the dispute.

**The root cause was never a data-entry error — it is that one deliverable is tracked as two tactics under
two goals, owned by two committees.** Membership said Completed for 6.2.1; Strategic Planning said in-progress
for 6.1.5. Both answered honestly about the same document. The ingest has no cross-tactic consistency check
and cannot have a useful one, because neither answer is malformed. ⚠️ **If a third cycle produces the same
split, fix the instrument — merge them or cross-reference them in the survey — rather than adjudicating the
answers again.**

**Two things worth remembering.** A reviewer comment is not automatically authoritative: the admin's
`Completed` was applied, published to three surfaces, and then reversed a day later by the person who owns
the work. And the survey answer was wrong the whole time — Membership reported `Completed` in August, so
**any re-ingest of the August export puts the wrong value back**. That is now the third hand-correction with
that property.
