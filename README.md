# ISPE Strategic Plan Dashboard — public deploy

This branch (`public-deploy`) contains **only** the public-facing dashboard, ready to be
served by GitHub Pages and embedded on the ISPE website as an `<iframe>`.

## What's on this branch
- `index.html` — the public dashboard (self-contained: reads `data.json`, with an embedded fallback copy)
- `data.json` — plan progress data (committee-level only; **no personal/respondent data**)
- `newlogo.jpg`, `banner picture.jpg`, `ISPE Logo.jpg` — image assets

The admin editor (`admin.html`) and the data-generation script are intentionally **not** on this
branch, so they are never published to the public site. They live on `main`.

## Deploy with GitHub Pages
Repo → **Settings → Pages → Build and deployment**:
- **Source:** Deploy from a branch
- **Branch:** `public-deploy` — folder `/ (root)` → **Save**

The site publishes at `https://<account>.github.io/<repo>/` (for this account/repo:
`https://ispe-sp.github.io/ISPE-Strategic-Plan-Dashboard/`). First build takes ~1 minute.

## Embed on the ISPE website
Paste the responsive iframe snippet from the handoff notes into the page where the dashboard
should appear, pointing `src` at the Pages URL above.

## Updating the data
The dashboard reads `data.json`. To update it:
1. On `main`, open `admin.html` locally, load the current data, make edits, and **Export JSON**.
2. Commit the new `data.json` to this `public-deploy` branch.
3. GitHub Pages redeploys automatically within a minute.
