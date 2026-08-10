# The reviewer site — what it is, and how to put it up

A password-protected copy of the dashboard where ISPE reviewers can **comment,
flag and approve**, and where **everyone who can open the site sees everyone
else's** comments, flags and approvals. Read-only otherwise: reviewers cannot
change a status, edit a rationale, or publish. You keep doing that locally with
`admin-server.py`.

The thing that makes it work is that review state lives in a **database**, not
in the browser. `review-panel-mock.html` kept state in `localStorage`, which
would have given each reviewer a private copy of their own checkmarks that
nobody else could ever see, and that vanished on a different device.

```
review-site/
  build_review_site.py     generates dist/ from the repo's index.html
  src/                     the review layer (css, markup, js) that gets injected
  functions/api/           the API: auth middleware + review endpoints
  lib/email.js             builds and sends the completion summary
  (at-risk panel)          extracted from ../admin.html at build time, not copied
  schema.sql               comments, flags, approvals, submissions
  wrangler.toml            Pages + D1 binding
  dist/                    GENERATED. Never edit; never commit.
```

**Cost: nothing.** Cloudflare Pages, Access (up to 50 users) and D1 all have
free tiers far above what a handful of reviewers touching a 99-tactic plan
four times a year will use.

---

## What reviewers get

- A **general comment box at the top** for anything miscellaneous about the cycle.
- **💬 and ⚑ on every tactic, goal and objective**, plus on the three summary
  panels (status overview, revisions, completed).
- **✓ approve, per objective.** Approvals are recorded **per reviewer**, so the
  button shows *how many* people approved and hovering names them. This is
  deliberate: with one shared checkbox you cannot tell "nobody has approved this
  yet" from "someone approved it and someone else unticked it", and you cannot
  tell who signed off — which is the entire content of an approval.
- A **"Complete review & email summary"** button. This is how you find out they
  are done: pressing it emails you everything that reviewer raised, grouped by
  tactic/goal/objective, plus which objectives they did and did **not** approve.
  It asks for confirmation first (email cannot be unsent), and afterwards the
  row shows when it was sent. If they comment again later, it prompts them to
  send an updated summary so the afterthought is not stranded.
- The **At Risk panel** — the 31 tactics reporting Not Started or Delayed,
  grouped by objective, with the provenance markers that say which statuses were
  reconfirmed this cycle and which were carried forward. It is admin-only and
  must never appear on the public dashboard, but it is precisely what a reviewer
  needs before signing anything off, and this site is behind Access. It is
  extracted from `admin.html` at build time, not copied, and can be commented on
  and flagged like anything else. It needs no committee notes, so it does not
  reopen the payload decision below.
- An **activity feed** at the top listing everything outstanding, unresolved
  first. Clicking an entry jumps to it (and clears any active filter first, so
  the link never lands on a hidden row).
- Comments can be **resolved by anyone** (it is a shared workflow) but
  **deleted only by their author** — deleting someone else's would erase review
  history with no trace it existed.

Everything is scoped to the **cycle label** (the dashboard's as-of date). When
the data moves to a new cycle the board starts empty rather than carrying last
cycle's approvals onto numbers nobody has looked at. Old cycles are kept, not
deleted.

---

## One-time setup

You need a Cloudflare account and `npx wrangler` (no install needed).
Run everything from `review-site/`.

### 1. Build

```bash
cd review-site
python3 build_review_site.py
```

This regenerates `dist/` from the repo's `index.html`. It **fails loudly** if
`index.html` has drifted so that one of its patch anchors no longer matches
exactly once — better a failed build than a review site with no comment buttons.

### 2. Create the database

```bash
npx wrangler d1 create ispe-sp-review
```

Copy the printed `database_id` into `wrangler.toml`, replacing
`REPLACE_ME_SEE_DEPLOY_MD`. Then create the tables:

```bash
npx wrangler d1 execute ispe-sp-review --remote --file=schema.sql
```

### 3. First deploy

```bash
npx wrangler pages deploy
```

Answer the prompts to create the project (suggested name: `ispe-sp-review`).
It prints a URL like `https://ispe-sp-review.pages.dev`.

**The site is public at this point.** Do not share that URL yet — step 4 is what
makes it private.

### 4. Put Cloudflare Access in front of it

In the Cloudflare dashboard → **Zero Trust** → **Access** → **Applications** →
**Add an application** → **Self-hosted**:

- **Application domain:** your Pages hostname, e.g. `ispe-sp-review.pages.dev`.
- **Add a second domain:** `*.ispe-sp-review.pages.dev` — this covers preview
  deployments. Miss it and every preview build is a public copy of the site.
- **Policy:** Action *Allow*, Include → **Emails** → list each reviewer's
  address. (Or *Emails ending in* `@pharmacoepi.org` if that is the right rule.)
- **Login method:** enable **One-time PIN**. That is the "password": the
  reviewer types their email, gets a 6-digit code, and is in. No account, no
  password to leak, and you can revoke one person without affecting anyone else.

### 5. Tell the API about Access

Zero Trust → Access → Applications → your app → **Overview** → copy the
**Application Audience (AUD) Tag**. Your team domain is on Zero Trust →
**Settings** → it looks like `yourteam.cloudflareaccess.com`.

Cloudflare dashboard → **Workers & Pages** → your project → **Settings** →
**Variables and Secrets**, add for **Production**:

| Name | Value |
|---|---|
| `ACCESS_TEAM_DOMAIN` | `yourteam.cloudflareaccess.com` |
| `ACCESS_AUD` | the AUD tag from above |
| `OWNER_EMAILS` | *(optional)* your address, comma-separated — lets you delete anyone's comment |

Then redeploy so the variables take effect:

```bash
npx wrangler pages deploy
```

### 6. Turn on the completion email

Optional but the point of the thing — without it, reviewers press Complete
review and nobody is told. The site handles that honestly (it says plainly that
no email went out) but you would be back to checking manually.

Add these under the same **Variables and Secrets** screen:

| Name | Value |
|---|---|
| `EMAIL_PROVIDER` | `resend` |
| `EMAIL_API_KEY` | your Resend API key — mark it **Encrypt** |
| `EMAIL_FROM` | the sender, e.g. `ISPE Review <onboarding@resend.dev>` |
| `REVIEW_NOTIFY_TO` | where summaries go — your address |

**Why an HTTP sender and not Cloudflare's own.** `blackswancausallabs.com` is on
Cloudflare nameservers, so Cloudflare Email Routing looks like the obvious
choice — but that domain's MX points at Google Workspace (`smtp.google.com`).
Enabling Email Routing wants those MX records, which is how you break real
email to save four notifications a year. An outbound HTTPS call touches no DNS
at all.

On a free Resend account you can send from `onboarding@resend.dev` to your own
verified address with **no DNS setup whatsoever** — which is all this needs at
four emails a year. Only if you want it to come from your own domain do you add
their DKIM/SPF records, and even then use a subdomain like
`notify.blackswancausallabs.com` so the root domain's existing Google records
are never touched.

**Prefer Slack, Teams, or something else?** Set `EMAIL_PROVIDER=webhook` and
`EMAIL_WEBHOOK_URL` to an incoming webhook instead. The same summary is POSTed
as JSON with `subject`, `text`, `html` and `summary` fields; Slack and Teams
both render the `text` field as-is.

### 7. Verify before sharing the link

Do all four. The first three are the ones that matter.

1. **Open the site in a private window.** You must be stopped by an email
   prompt. If the dashboard renders, Access is not attached to that hostname.
2. **Sign in and confirm the bar reads `Signed in as <your email>`** — not
   blank, not someone else.
3. **Check the API refuses strangers.** From a terminal (no browser session):
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' https://<your-site>/api/review/whoami
   ```
   Must print `302` (Access redirect) or `401`. **If it prints `200`, stop** —
   the API is open and anything anyone writes is world-readable.
4. **Post a test comment, then open the site as a second reviewer** (or a second
   browser profile) and confirm the comment is there. That is the whole feature;
   test it once for real.
5. **Press Complete review once yourself** and check the email arrives. The row
   should then read "Summary emailed." If it instead says the email failed or is
   not configured, that message is accurate — fix step 6 rather than ignoring it.

---

## Every cycle

After you ingest the new survey and set the as-of date (steps 1–8 of "Updating
the data" in `docs/STATUS.md`):

```bash
cd review-site
python3 build_review_site.py     # picks up the new data.json and any index.html changes
npx wrangler pages deploy
```

The review board resets itself, because the cycle label changed. Reviewers see
an empty board against the new numbers. Nothing else to do.

You will get one email per reviewer as each presses **Complete review**. Act on
their comments locally in `admin.html`, then publish to `public-deploy` as
usual. **Publishing is not wired to this site** — completing a review is a
statement by a reviewer, not a trigger. That is deliberate; nothing here can
push to the public dashboard.

---

## Local development

```bash
cd review-site
cp .dev.vars.example .dev.vars          # then edit DEV_REVIEWER_EMAIL
npx wrangler d1 execute ispe-sp-review --local --file=schema.sql
python3 build_review_site.py
npx wrangler pages dev                  # → http://127.0.0.1:8788
```

`.dev.vars` bypasses the sign-in so you can work without Access. It is
deliberately awkward: **both** `ALLOW_DEV_AUTH=1` and `DEV_REVIEWER_EMAIL` must
be set, and the branch only runs when `ACCESS_TEAM_DOMAIN`/`ACCESS_AUD` are
absent — so in production it is unreachable even if the file somehow shipped.
It is gitignored and `wrangler pages dev` reads it; deploys do not.

---

## What this protects, and what it does not

**Verified by test, 2026-08-10:**

- With no auth configured, every API route returns **503 and serves nothing** —
  reads and writes both. It does not fall through to "no auth, so allow".
- A **forged but well-formed token** carrying `attacker@evil.test`, a correct
  audience, a correct issuer and a far-future expiry is **rejected at the
  signature check**. The email claim is never trusted before the signature is.
- The dev bypass **does not win** when Access is configured, even with both set.
- Comment text is escaped: a comment containing `<img src=x onerror=...>`
  renders as inert text and executes nothing.
- A reviewer **cannot delete another reviewer's comment** (403); they can resolve it.
- **A completed review is recorded even when the email fails.** Tested with no
  provider configured and with a provider whose endpoint refuses the connection:
  both recorded the completion, returned the real reason, and showed the reviewer
  a red bar telling them to contact the owner directly. A reviewer who finished
  has finished; rolling that back because an API key expired would be a lie told
  by the software. The `submissions` table keeps the delivery outcome per attempt.

**Worth knowing:**

- The site serves the **notes-stripped public payload**, not the working
  `data.json`. Reviewers are checking what is about to be published, so that is
  the right artifact — and it means the committee notes are not sitting on an
  internet-facing host with Access as the only thing in front of them. If you
  ever want reviewers to see the notes, change `PAYLOAD_SOURCE` handling in
  `build_review_site.py` and update this section, because it changes what a
  misconfigured Access policy would cost.
- Access protects the **static files** (the dashboard HTML and data.json) at the
  edge. The **API** is protected twice: by Access, and by its own JWT check. So
  a hostname missed in the Access policy exposes the already-public dashboard
  data, not the review comments.
- Reviewer identity is whatever Access verified. There is no separate role
  system beyond `OWNER_EMAILS`.

## Not built

- **No notification on individual comments** — by design. One email per reviewer
  per cycle, sent when they press Complete review. With a plan of 99 tactics
  reviewed twice a year, per-comment mail would be noise.
- **No export** of the review board. If you want the comments in a document,
  they have to be copied out, or read from D1:
  `npx wrangler d1 execute ispe-sp-review --remote --command "SELECT * FROM comments"`.
- **No edit-your-own-comment.** Delete and repost.
- **Sign-off does nothing automatic.** See "Every cycle" above.
