# Migration plan — private working repo, push-to-publish

_Status: **planned, not started.** Written 2026-08-03. Nothing in this document has been executed._
_Read `STATUS.md` for where the project actually is, and `DECISIONS.md` for why the current build looks
the way it does. This file supersedes the "ISPE forks, ISPE hosts" plan recorded in DECISIONS._

## What this changes, in one line

The working repo becomes **private**, the ISPE reviewer is added as a collaborator, and publishing becomes
an **Action that pushes** the built public dashboard into a separate public repo — instead of ISPE forking
and clicking "Sync fork."

## Why

Three problems with the current model, in order of severity:

1. **Forks do not auto-update.** Every `data.json` refresh needs someone at ISPE to click "Sync fork." That
   puts the party least able to act quickly on the critical path, and the failure mode is silent: a public
   dashboard showing last quarter's numbers with no error anywhere.
2. **`admin.html` is protected by not being published, not by auth.** It works, but it is one careless
   branch change away from being public, and it means the admin dashboard cannot be reviewed anywhere except
   a machine with Python and the repo checked out.
3. **The public payload is defined by a second allowlist `.gitignore`** on `public-deploy`, which drifts.
   `fonts/` had to be added on 2026-07-27 after the font silently fell back to Georgia.

## The constraint that rules out "fork"

The natural reading of "private repo, ISPE forks it" does not assemble:

- **Forks inherit the parent's visibility.** A fork of a private repo is private.
- **A private fork cannot be flipped to public.** GitHub's documented workaround is to *duplicate* the repo,
  which is not a fork and has no "Sync fork" button — so the propagation mechanism disappears anyway.
- **`ISPE-SP` is a personal *user* account, not an organization** (confirmed via the API, 2026-08-03). On a
  free personal account Pages serves **public repos only**, so a private fork could not be served regardless.

**Verify the first two at execution time** before relying on them — they are GitHub policy, and policy moves.

Replacing the fork with a push removes the constraint *and* problem 1 above, because publishing then lands
on the live site directly with no action required at ISPE, ever, after setup.

## Target architecture

```
Black-Swan-Causal-Labs/ISPE-Strategic-Plan-Dashboard   [PRIVATE]   the working repo
  admin.html, admin-server.py, csv_to_dashboard_json.py,
  index.html, data.json, docs/, fonts/, images, SP Reports*.csv
  reviewer added as a collaborator (write)
        |
        |  Action: build public payload, push over SSH deploy key
        v
ISPE-SP/<public repo name>                             [PUBLIC]    deploy target only
  index.html, data.json, fonts/, newlogo.jpg, banner picture.jpg, README.md
  Pages enabled on the default branch
        |
        v
https://ispe-sp.github.io/<repo>/   ->  the iframe src ISPE IT embeds, once, forever
```

**`public-deploy` goes away.** The Action builds the payload from an explicit file list, which is auditable
in the workflow and fails loudly when a dependency is missing — unlike an allowlist in a second `.gitignore`
on a branch nobody looks at.

**Review happens in a Codespace.** The reviewer opens the private repo in a browser Codespace, runs
`python3 admin-server.py`, and gets the real admin dashboard on a port private to their GitHub account. This
is the only option found that gives a visual admin review without either a local Python setup or publishing
`admin.html`. It works precisely because a Codespace *has a backend* — Save and Publish keep functioning as
built. The Team plan includes Codespaces core-hours.

## Decisions needed before starting

These change the work; do not start Phase 1 without them.

1. **Who owns the public deploy repo?**
   - *ISPE-SP owns it* — URL reads `ispe-sp.github.io`, which is what an ISPE-branded page wants. Costs one
     setup task on their side: create the repo, add a deploy key, enable Pages.
   - *BSCL owns it* — zero dependency on ISPE, but the URL says `black-swan-causal-labs.github.io`.
2. **Should `ISPE-SP` become an organization?** As a personal account, access runs through one human; if they
   leave ISPE, recovery is awkward. An org with multiple owners is more durable for something ISPE intends to
   keep. Worth raising with them at the same time, since it is far cheaper to do before the repo exists.
3. **Who is the reviewer**, and do they get write access to the private repo (can merge/publish) or read
   access (reviews, someone at BSCL merges)?

## Migration steps

Ordered so the live site never goes dark and every step is reversible until Phase 5.

### Phase 1 — stand up the public deploy repo (current site stays live)
- Create the public repo under the chosen owner.
- Seed it with the current public payload: `index.html`, `data.json`, `fonts/`, `newlogo.jpg`,
  `banner picture.jpg`, `README.md`.
- Enable Pages on its default branch. Confirm the site renders and `admin.html` 404s.
- **Do not point ISPE IT at it yet.**

### Phase 2 — deploy key
- Generate an SSH keypair. Public half → the **public** repo as a deploy key **with write access**.
  Private half → the **working** repo as an Actions secret.
- A deploy key is preferred over a PAT: scoped to exactly one repo, tied to no human account, no expiry.

### Phase 3 — publish workflow
- Add the publish workflow to the working repo (shape below). Trigger it manually first.
- Verify: the public repo receives only the intended files, Pages redeploys, and the admin-surface assertion
  passes.

### Phase 4 — cut over
- Give ISPE IT the new iframe snippet. Confirm the embed renders on their page.
- Keep the old BSCL Pages site live until they confirm.

### Phase 5 — make the working repo private
- **Last, and only after Phase 4 is confirmed.** Safe to do: the repo has **0 forks, 0 stars, 0 watchers**
  (checked 2026-08-03), so nothing is retracted and no one loses access.
- Add the reviewer as a collaborator.
- Allowlist `SP Reports*.csv` in `.gitignore` — see the PII guard before doing this.
- Note: Actions minutes are **billed on private repos** (free on public). The Team plan's monthly allowance
  is far above what this workflow uses, but it is no longer free-by-default.

### Phase 6 — ingest automation
- Workflow: upload `SP Reports <M.D.YYYY>.csv` to the working repo → Action runs `csv_to_dashboard_json.py`
  → commits `data.json` → opens a PR carrying the script's run report.
- Review the PR (and/or the Codespace dashboard), then publish.

### Phase 7 — retire the old path
- Delete the `public-deploy` branch and disable Pages on the working repo.
- Update `STATUS.md` and `DECISIONS.md`.

## The publish workflow (shape, not final code)

```
on: workflow_dispatch            # publishing stays a deliberate human act
steps:
  1. checkout working repo
  2. assert the payload is public-safe:
       - no admin.html / admin-server.py / csv_to_dashboard_json.py / docs/ in the file list
       - grep index.html for "Admin Control Panel", "publishReadOnly", "atRisk", search box -> must be 0
       - data.json parses; tactic count and active/retired split reported in the job summary
  3. copy the explicit payload file list into a clean directory
  4. push that directory to the public repo over the deploy key
  5. print the resulting Pages URL
```

Step 2 is the point of the whole thing. It is the assertion that stops the admin editor reaching the
internet, and it must fail the job rather than warn.

## Guards that must exist before Phase 6

Automation here fails *silently* — a bad cycle renders as a plausible wrong dashboard, not an error. Each of
these has already bitten or nearly bitten:

1. **PII guard, failing closed.** The 7.30 export carries no PII — verified 2026-08-03: no Name / Email /
   Contact ID / IP / geo columns, zero email addresses, zero IPs in cell contents. The *old* export had all
   of it (13 emails, 24 IPs). That is a property of the current export, **not a guarantee**, and the repo the
   CSV lands in is one visibility change away from public. The Action must scan every uploaded CSV for those
   column names and for email/IP patterns in cells, and **refuse to commit** on a hit.
2. **Double-run guard.** Re-uploading the same CSV merges a cycle onto its own output, masking any correction
   made in between. The script detects this and warns; in CI it must be a **hard failure**.
3. **As-of date.** Curated in the admin panel, and not derivable from a file that carries no dates. In an
   automated flow it must become a workflow input or be derived from the filename — never silently inherited,
   which is how it sat on "April 2026" while the data said July.
4. **Retirement is a hardcoded dict** (`RETIRED` in `csv_to_dashboard_json.py`). A cycle that retires a tactic
   needs a code edit, so that one case can never be "just drop the CSV." Worth raising with ISPE as a survey
   change if it recurs.
5. **Partial cycles are the norm.** 6 of ~13 committees reported on 7.30. The merge behaviour is correct and
   must not be "fixed" into a rebuild.

## What ISPE receives

One `<iframe>` snippet, pasted into a Custom HTML block, pointing at the public Pages URL:

```html
<div style="max-width:1200px; margin:0 auto;">
  <iframe src="https://ispe-sp.github.io/<repo>/"
    title="ISPE Strategic Plan Progress Dashboard" loading="lazy"
    style="width:100%; height:1400px; border:0; border-radius:8px;" referrerpolicy="no-referrer"></iframe>
</div>
```

It never changes again regardless of how often the data updates. That property is the point of the migration.

## Rollback

- **Phases 1–4** are additive; abandoning them costs a deleted repo.
- **Phase 5** is reversible — a private repo can be made public again — but note that going private and back
  does not restore stars/watchers. There are none today, so this is currently free.
- **Phase 7** is the first irreversible step. Do not delete `public-deploy` until the new path has survived a
  real cycle.

## What this does NOT solve

- **Blank ≠ Not Started.** Unreported tactics are indistinguishable from genuinely unstarted ones in the new
  export. Automation does not fix this; it makes it more urgent, because nobody is reading the CSV by hand.
  The at-risk provenance markers added 2026-08-03 mitigate the symptom, not the cause.
- **Junk status values** still have no mapping rule.
- **Tactic 3.1.8** still does not exist in the plan.
- **A hosted admin dashboard for people without GitHub accounts.** Codespaces requires a GitHub login. If ISPE
  ever wants a link-and-password admin page, that is a different project: an authenticated host (Cloudflare
  Pages or Netlify) plus a serverless function holding the token.
