-- Review state for the ISPE Strategic Plan dashboard.
--
-- Everything here is scoped by `cycle` (the dashboard's as-of label, e.g.
-- "August 2026"). That scoping is load-bearing, not bookkeeping: an approval
-- must never carry silently onto a cycle whose numbers nobody has looked at.
-- Old cycles are kept rather than deleted, so last cycle's review is still
-- readable after the data moves on.
--
-- Apply with:
--   wrangler d1 execute ispe-sp-review --remote --file=schema.sql
--   wrangler d1 execute ispe-sp-review --local  --file=schema.sql   (for dev)

-- Append-only. Rows are never rewritten in place, so two reviewers commenting
-- at the same moment cannot clobber each other — the failure mode a single
-- read-modify-write JSON blob in KV would have had, silently.
CREATE TABLE IF NOT EXISTS comments (
  id           TEXT PRIMARY KEY,        -- uuid, minted server-side
  cycle        TEXT NOT NULL,
  target       TEXT NOT NULL,           -- 'general' | 'panel:x' | 'objective:1' | 'goal:1.1' | 'tactic:1.1.1'
  body         TEXT NOT NULL,
  author       TEXT NOT NULL,           -- verified email from the Access JWT; never self-declared
  created_at   TEXT NOT NULL,           -- ISO 8601 UTC
  resolved_at  TEXT,
  resolved_by  TEXT
);
CREATE INDEX IF NOT EXISTS comments_cycle_target  ON comments (cycle, target);
CREATE INDEX IF NOT EXISTS comments_cycle_created ON comments (cycle, created_at);

-- A flag is shared, not per-reviewer: it means "this needs attention", and
-- anyone can raise or clear it. We keep who raised it so the feed can say so.
-- Presence of the row IS the flag; clearing deletes it.
CREATE TABLE IF NOT EXISTS flags (
  cycle      TEXT NOT NULL,
  target     TEXT NOT NULL,
  raised_by  TEXT NOT NULL,
  raised_at  TEXT NOT NULL,
  PRIMARY KEY (cycle, target)
);

-- Approvals ARE per-reviewer, deliberately. With one shared checkbox you
-- cannot tell "nobody approved this yet" from "someone approved it and someone
-- else unticked it", and you cannot tell who signed off — which is the entire
-- content of an approval. scope is 'objective:<n>' or 'review' (overall sign-off).
CREATE TABLE IF NOT EXISTS approvals (
  cycle        TEXT NOT NULL,
  scope        TEXT NOT NULL,
  reviewer     TEXT NOT NULL,
  approved_at  TEXT NOT NULL,
  PRIMARY KEY (cycle, scope, reviewer)
);
CREATE INDEX IF NOT EXISTS approvals_cycle ON approvals (cycle);

-- One row each time a reviewer presses "Complete review". Resubmissions are
-- allowed and append, so the history of "I thought I was done, then found more"
-- is preserved rather than overwritten.
--
-- `delivery` records what happened to the email IN THE SAME transaction-ish
-- moment as the completion. Completion is never blocked on the mail going out:
-- a reviewer who finished has finished, and telling them otherwise because an
-- API key expired would be a lie. The UI reads this field and says plainly when
-- the summary was recorded but not delivered.
CREATE TABLE IF NOT EXISTS submissions (
  id            TEXT PRIMARY KEY,
  cycle         TEXT NOT NULL,
  reviewer      TEXT NOT NULL,
  submitted_at  TEXT NOT NULL,
  comments      INTEGER NOT NULL DEFAULT 0,
  flags         INTEGER NOT NULL DEFAULT 0,
  approved      INTEGER NOT NULL DEFAULT 0,
  delivery      TEXT NOT NULL,   -- 'sent' | 'not-configured' | 'failed: <reason>'
  delivered_to  TEXT
);
CREATE INDEX IF NOT EXISTS submissions_cycle ON submissions (cycle, submitted_at);
