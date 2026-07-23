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
