# ISPE Strategic Plan Dashboard — Decision Log

_Why the dashboard is built the way it is. Newest context at the bottom. See `STATUS.md` for the current snapshot._

## Ownership & hosting
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
  percentage was already computed this way; only the label changed.
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
- **Why local rather than the GitHub API:** `admin.html` is publicly reachable, so any embedded token would
  be world-readable. A runtime-entered token in `localStorage` is also unsafe here while survey free-text is
  still interpolated into `innerHTML` unescaped.
- `admin.html` **degrades gracefully** — with no helper it falls back to the previous download behaviour, so
  the public copy is unaffected.
- The server writes with the **exact formatting `csv_to_dashboard_json.py` uses** (`indent=2`, default
  `ensure_ascii`, trailing newline) and skips the write entirely when the parsed content is unchanged.
  Without both, formatting drift alone produced empty commits.

## Other
- **Side-tab accent borders removed** (4px coloured left slabs on the Changes / Completed / at-risk cards)
  in favour of hairline borders — the headers already carried the colour three ways.
- Footer now carries a **2026 copyright** and credits Black Swan Causal Labs for the dashboard; the personal
  byline was removed at the author's request. **The copyright holder is an assumption** (ISPE, as content
  owner) — confirm before this is treated as a legal notice.
- The contact line moved out of the footer to sit under the last objective.
- Design-detector waivers live in `.impeccable/config.json` (not tracked — the allowlist excludes it), each
  with a recorded reason.
