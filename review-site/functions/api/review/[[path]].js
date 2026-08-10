// The review API. Every route below runs only after functions/api/_middleware.js
// has verified an Access token, so `data.email` is always a real, verified
// address — never something the browser told us it was.
//
// Routes:
//   GET    /api/review/state?cycle=<label>
//   POST   /api/review/comments            {cycle, target, body}
//   PATCH  /api/review/comments/<id>       {resolved: bool}
//   DELETE /api/review/comments/<id>
//   POST   /api/review/flags               {cycle, target, flagged: bool}
//   POST   /api/review/approvals           {cycle, scope, approved: bool}
//   POST   /api/review/complete            {cycle}   -> emails the summary

import { buildSummary, deliver } from '../../../lib/email.js';

const MAX_BODY = 4000;
const MAX_CYCLE = 64;

// Anything a comment can hang off. A whitelist rather than free text: the target
// is stored verbatim and echoed back into the page, and an unbounded key space
// would also let a stray client fill the table with rows nothing can ever
// display or clean up.
const TARGET_RE = /^(?:general|panel:[a-z][a-z0-9-]{0,31}|objective:\d{1,3}|goal:\d{1,3}\.\d{1,3}|tactic:\d{1,3}\.\d{1,3}\.\d{1,3})$/;
const SCOPE_RE = /^(?:review|objective:\d{1,3})$/;

function json(status, obj) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

function bad(message) {
  return json(400, { error: message });
}

async function readJson(request) {
  try {
    const parsed = await request.json();
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

// Cycle labels are human text ("August 2026"), so spaces are expected and
// only control characters are rejected.
function cleanCycle(value) {
  const s = String(value == null ? '' : value).trim();
  if (!s || s.length > MAX_CYCLE) return null;
  if (/[\u0000-\u001f\u007f]/.test(s)) return null;
  return s;
}

function nowIso() {
  return new Date().toISOString();
}

// The objective list is read from the site's own data.json rather than trusted
// from the browser, so "3 of 8 approved" in the email cannot be shaped by the
// client that triggered it.
async function readObjectiveNumbers(env, request) {
  try {
    if (!env.ASSETS) return null;
    const resp = await env.ASSETS.fetch(new Request(new URL('/data.json', request.url).toString()));
    if (!resp.ok) return null;
    const data = await resp.json();
    const numbers = (data.objectives || [])
      .map((o) => Number(o.objective_number))
      .filter((n) => Number.isFinite(n));
    return numbers.length ? numbers : null;
  } catch {
    return null;
  }
}

async function getState(db, cycle, me, isOwner) {
  const [comments, flags, approvals, submissions] = await db.batch([
    db
      .prepare(
        `SELECT id, target, body, author, created_at, resolved_at, resolved_by
           FROM comments WHERE cycle = ? ORDER BY created_at ASC`,
      )
      .bind(cycle),
    db.prepare(`SELECT target, raised_by, raised_at FROM flags WHERE cycle = ?`).bind(cycle),
    db
      .prepare(`SELECT scope, reviewer, approved_at FROM approvals WHERE cycle = ? ORDER BY approved_at ASC`)
      .bind(cycle),
    db
      .prepare(
        `SELECT reviewer, submitted_at, comments, flags, approved, delivery
           FROM submissions WHERE cycle = ? ORDER BY submitted_at ASC`,
      )
      .bind(cycle),
  ]);

  return {
    me,
    isOwner,
    cycle,
    comments: comments.results || [],
    flags: flags.results || [],
    approvals: approvals.results || [],
    submissions: submissions.results || [],
  };
}

export async function onRequest(context) {
  const { request, env, params, data } = context;

  if (!env.DB) {
    return json(503, {
      error: 'The review database is not connected, so nothing can be saved.',
      detail: 'No D1 binding named DB. See DEPLOY.md, step 2.',
    });
  }

  const segments = (params.path || []).filter(Boolean);
  const route = segments[0] || '';
  const method = request.method.toUpperCase();
  const me = data.email;
  const isOwner = !!data.isOwner;

  try {
    // ---- who am I -------------------------------------------------------
    if (route === 'whoami' && method === 'GET') {
      return json(200, { me, isOwner });
    }

    // ---- the whole board ------------------------------------------------
    if (route === 'state' && method === 'GET') {
      const cycle = cleanCycle(new URL(request.url).searchParams.get('cycle'));
      if (!cycle) return bad('A cycle label is required.');
      return json(200, await getState(env.DB, cycle, me, isOwner));
    }

    // ---- comments -------------------------------------------------------
    if (route === 'comments') {
      if (method === 'POST') {
        const payload = await readJson(request);
        if (!payload) return bad('Expected a JSON body.');

        const cycle = cleanCycle(payload.cycle);
        if (!cycle) return bad('A cycle label is required.');

        const target = String(payload.target || '').trim();
        if (!TARGET_RE.test(target)) return bad(`Not something that can be commented on: ${target}`);

        const body = String(payload.body == null ? '' : payload.body).trim();
        if (!body) return bad('A comment cannot be empty.');
        if (body.length > MAX_BODY) return bad(`A comment cannot be longer than ${MAX_BODY} characters.`);

        const row = {
          id: crypto.randomUUID(),
          target,
          body,
          author: me,
          created_at: nowIso(),
          resolved_at: null,
          resolved_by: null,
        };
        await env.DB.prepare(
          `INSERT INTO comments (id, cycle, target, body, author, created_at) VALUES (?, ?, ?, ?, ?, ?)`,
        )
          .bind(row.id, cycle, row.target, row.body, row.author, row.created_at)
          .run();

        return json(201, { comment: row });
      }

      const id = segments[1];
      if (!id) return bad('Which comment?');

      if (method === 'PATCH') {
        const payload = await readJson(request);
        if (!payload) return bad('Expected a JSON body.');
        const resolved = !!payload.resolved;

        // Resolving is a shared workflow action — any reviewer may resolve any
        // comment, including someone else's. Deleting is not; see below.
        const result = await env.DB.prepare(
          `UPDATE comments SET resolved_at = ?, resolved_by = ? WHERE id = ?`,
        )
          .bind(resolved ? nowIso() : null, resolved ? me : null, id)
          .run();

        if (!result.meta || result.meta.changes === 0) return json(404, { error: 'That comment no longer exists.' });
        return json(200, { ok: true });
      }

      if (method === 'DELETE') {
        // Author-only (owners excepted). Deleting someone else's comment would
        // remove review history with no trace that it ever existed.
        const existing = await env.DB.prepare(`SELECT author FROM comments WHERE id = ?`).bind(id).first();
        if (!existing) return json(404, { error: 'That comment no longer exists.' });
        if (existing.author !== me && !isOwner) {
          return json(403, { error: 'Only the person who wrote a comment can delete it. You can resolve it instead.' });
        }
        await env.DB.prepare(`DELETE FROM comments WHERE id = ?`).bind(id).run();
        return json(200, { ok: true });
      }

      return json(405, { error: `${method} is not allowed here.` });
    }

    // ---- flags ----------------------------------------------------------
    if (route === 'flags' && method === 'POST') {
      const payload = await readJson(request);
      if (!payload) return bad('Expected a JSON body.');

      const cycle = cleanCycle(payload.cycle);
      if (!cycle) return bad('A cycle label is required.');

      const target = String(payload.target || '').trim();
      if (!TARGET_RE.test(target)) return bad(`Not something that can be flagged: ${target}`);

      if (payload.flagged) {
        await env.DB.prepare(
          `INSERT INTO flags (cycle, target, raised_by, raised_at) VALUES (?, ?, ?, ?)
             ON CONFLICT (cycle, target) DO NOTHING`,
        )
          .bind(cycle, target, me, nowIso())
          .run();
      } else {
        await env.DB.prepare(`DELETE FROM flags WHERE cycle = ? AND target = ?`).bind(cycle, target).run();
      }
      return json(200, { ok: true });
    }

    // ---- approvals ------------------------------------------------------
    if (route === 'approvals' && method === 'POST') {
      const payload = await readJson(request);
      if (!payload) return bad('Expected a JSON body.');

      const cycle = cleanCycle(payload.cycle);
      if (!cycle) return bad('A cycle label is required.');

      const scope = String(payload.scope || '').trim();
      if (!SCOPE_RE.test(scope)) return bad(`Not something that can be approved: ${scope}`);

      // Keyed by reviewer, so one person un-approving cannot erase another
      // person's sign-off.
      if (payload.approved) {
        await env.DB.prepare(
          `INSERT INTO approvals (cycle, scope, reviewer, approved_at) VALUES (?, ?, ?, ?)
             ON CONFLICT (cycle, scope, reviewer) DO UPDATE SET approved_at = excluded.approved_at`,
        )
          .bind(cycle, scope, me, nowIso())
          .run();
      } else {
        await env.DB.prepare(`DELETE FROM approvals WHERE cycle = ? AND scope = ? AND reviewer = ?`)
          .bind(cycle, scope, me)
          .run();
      }
      return json(200, { ok: true });
    }

    // ---- complete review, and email the summary -------------------------
    if (route === 'complete' && method === 'POST') {
      const payload = await readJson(request);
      if (!payload) return bad('Expected a JSON body.');

      const cycle = cleanCycle(payload.cycle);
      if (!cycle) return bad('A cycle label is required.');

      const [mineComments, mineFlags, mineApprovals, openCount, flagCount, doneCount, peopleCount] =
        await env.DB.batch([
          env.DB.prepare(
            `SELECT target, body, created_at, resolved_at, resolved_by
               FROM comments WHERE cycle = ? AND author = ? ORDER BY created_at ASC`,
          ).bind(cycle, me),
          env.DB.prepare(`SELECT target FROM flags WHERE cycle = ? AND raised_by = ?`).bind(cycle, me),
          env.DB.prepare(`SELECT scope FROM approvals WHERE cycle = ? AND reviewer = ?`).bind(cycle, me),
          env.DB.prepare(`SELECT COUNT(*) AS n FROM comments WHERE cycle = ? AND resolved_at IS NULL`).bind(cycle),
          env.DB.prepare(`SELECT COUNT(*) AS n FROM flags WHERE cycle = ?`).bind(cycle),
          // Excludes me: I am completing right now and am added below. Counting
          // myself here would double-count a reviewer who is resubmitting.
          env.DB.prepare(
            `SELECT COUNT(DISTINCT reviewer) AS n FROM submissions WHERE cycle = ? AND reviewer != ?`,
          ).bind(cycle, me),
          env.DB.prepare(
            `SELECT COUNT(*) AS n FROM (
               SELECT author AS r FROM comments WHERE cycle = ?
               UNION SELECT raised_by FROM flags WHERE cycle = ?
               UNION SELECT reviewer FROM approvals WHERE cycle = ?)`,
          ).bind(cycle, cycle, cycle),
        ]);

      const first = (result) => ((result.results || [])[0] || { n: 0 }).n || 0;

      const summary = buildSummary({
        cycle,
        reviewer: me,
        mine: {
          comments: mineComments.results || [],
          flags: mineFlags.results || [],
          approvals: mineApprovals.results || [],
        },
        board: {
          reviewers: first(peopleCount),
          completed: first(doneCount) + 1, // everyone else, plus me, completing now
          openComments: first(openCount),
          flags: first(flagCount),
        },
        objectiveNumbers: await readObjectiveNumbers(env, request),
        siteUrl: new URL('/', request.url).toString(),
      });

      // Send first, then record what happened to it. The completion is recorded
      // either way: a reviewer who finished has finished, and rolling that back
      // because an API key expired would be a lie told by the software.
      const result = await deliver(env, summary);

      await env.DB.batch([
        env.DB.prepare(
          `INSERT INTO submissions (id, cycle, reviewer, submitted_at, comments, flags, approved, delivery, delivered_to)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        ).bind(
          crypto.randomUUID(), cycle, me, nowIso(),
          summary.stats.comments, summary.stats.flags, summary.stats.approved,
          result.status, result.to,
        ),
        env.DB.prepare(
          `INSERT INTO approvals (cycle, scope, reviewer, approved_at) VALUES (?, 'review', ?, ?)
             ON CONFLICT (cycle, scope, reviewer) DO UPDATE SET approved_at = excluded.approved_at`,
        ).bind(cycle, me, nowIso()),
      ]);

      return json(200, {
        ok: true,
        delivery: result.status,
        deliveredTo: result.to,
        reason: result.reason,
        stats: summary.stats,
      });
    }

    return json(404, { error: `No such endpoint: /api/review/${segments.join('/')}` });
  } catch (err) {
    // Surfaced to the page, which shows it in a banner rather than failing
    // silently — a review tool that quietly stops saving is worse than one
    // that is plainly broken.
    return json(500, { error: 'The review database rejected that.', detail: String(err && err.message ? err.message : err) });
  }
}
