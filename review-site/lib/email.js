// Review-completion summary: composition and delivery.
//
// Lives outside functions/ on purpose. Every file inside functions/ becomes a
// route; a helper module there would publish itself as an endpoint.
//
// Delivery is provider-agnostic and configured entirely by environment
// variables, because the right answer depends on infrastructure this code
// cannot see. Note for this project specifically: blackswancausallabs.com is on
// Cloudflare nameservers BUT its MX points at Google Workspace, so Cloudflare's
// native Email Routing sender is a poor fit — turning it on wants the MX
// records, which is how you break real email to save four notifications a year.
// An outbound HTTPS API needs no MX change at all.

const MAX_QUOTE = 600; // per comment, in the email body

function esc(v) {
  if (v === null || v === undefined) return '';
  return String(v).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function clip(text) {
  const s = String(text == null ? '' : text);
  return s.length > MAX_QUOTE ? s.slice(0, MAX_QUOTE) + '…' : s;
}

// 'tactic:3.1.2' -> 'Tactic 3.1.2'. Sorting key keeps numeric segments in
// numeric order so 3.1.10 lands after 3.1.9 rather than after 3.1.1.
function label(target) {
  if (target === 'general') return 'Overall comment on this cycle';
  const kind = target.split(':')[0];
  const id = target.slice(kind.length + 1);
  if (kind === 'panel') return `Panel: ${id.replace(/-/g, ' ')}`;
  return kind.charAt(0).toUpperCase() + kind.slice(1) + ' ' + id;
}

function sortKey(target) {
  if (target === 'general') return [0];
  const kind = target.split(':')[0];
  const rank = { panel: 1, objective: 2, goal: 3, tactic: 4 }[kind] || 5;
  const nums = (target.slice(kind.length + 1).match(/\d+/g) || []).map(Number);
  return [rank, ...nums];
}

function compareTargets(a, b) {
  const ka = sortKey(a);
  const kb = sortKey(b);
  for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
    const x = ka[i] === undefined ? -1 : ka[i];
    const y = kb[i] === undefined ? -1 : kb[i];
    if (x !== y) return x - y;
  }
  return 0;
}

function boardLine(board) {
  const people = `reviewer${board.reviewers === 1 ? '' : 's'}`;
  const verb = board.completed === 1 ? 'has' : 'have';
  return `${board.completed} of ${board.reviewers} ${people} ${verb} completed`;
}

function when(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return String(iso || '');
  return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

/**
 * Builds the summary of ONE reviewer's work on ONE cycle.
 *
 * `board` carries everyone's activity, used only for the short context footer —
 * knowing that 2 of 3 reviewers have finished is what tells the recipient
 * whether to act now or wait.
 */
export function buildSummary({ cycle, reviewer, mine, board, objectiveNumbers, siteUrl }) {
  const flaggedTargets = new Set(mine.flags.map((f) => f.target));

  // Group this reviewer's comments by what they are about.
  const byTarget = new Map();
  for (const c of mine.comments) {
    if (!byTarget.has(c.target)) byTarget.set(c.target, []);
    byTarget.get(c.target).push(c);
  }
  // A flag with no comment still needs to appear, or "3 flagged" in the header
  // describes items the email never lists.
  for (const t of flaggedTargets) if (!byTarget.has(t)) byTarget.set(t, []);

  const targets = [...byTarget.keys()].sort(compareTargets);

  const approvedObjectives = mine.approvals
    .filter((a) => a.scope.startsWith('objective:'))
    .map((a) => Number(a.scope.split(':')[1]))
    .sort((a, b) => a - b);

  const allObjectives = (objectiveNumbers && objectiveNumbers.length)
    ? objectiveNumbers.slice().sort((a, b) => a - b)
    : null;
  const notApproved = allObjectives
    ? allObjectives.filter((n) => !approvedObjectives.includes(n))
    : null;

  const stats = {
    comments: mine.comments.length,
    flags: mine.flags.length,
    approved: approvedObjectives.length,
    objectives: allObjectives ? allObjectives.length : null,
  };

  const headline = [
    `${stats.comments} comment${stats.comments === 1 ? '' : 's'}`,
    `${stats.flags} flagged`,
    allObjectives
      ? `${stats.approved} of ${stats.objectives} objectives approved`
      : `${stats.approved} objectives approved`,
  ].join(' · ');

  const subject = `ISPE review complete — ${reviewer} — ${cycle}`;

  // ---------------------------------------------------------------- plain text
  const lines = [];
  lines.push(`${reviewer} has completed their review of ${cycle}.`);
  lines.push('');
  lines.push(headline);
  lines.push('');

  if (targets.length === 0) {
    lines.push('They left no comments and raised no flags.');
    lines.push('');
  } else {
    lines.push('WHAT THEY RAISED');
    lines.push('');
    for (const t of targets) {
      lines.push(`${flaggedTargets.has(t) ? '[FLAGGED] ' : ''}${label(t)}`);
      const items = byTarget.get(t);
      if (items.length === 0) {
        lines.push('    (flagged, no comment)');
      }
      for (const c of items) {
        lines.push(`    "${clip(c.body)}"`);
        if (c.resolved_at) lines.push(`    — later resolved by ${c.resolved_by}`);
      }
      lines.push('');
    }
  }

  lines.push('APPROVALS');
  lines.push(approvedObjectives.length
    ? `  Approved: objectives ${approvedObjectives.join(', ')}`
    : '  Approved: none');
  if (notApproved) {
    lines.push(notApproved.length
      ? `  Not approved: objectives ${notApproved.join(', ')}`
      : '  Not approved: none — every objective approved');
  }
  lines.push('');

  if (board) {
    lines.push('WHERE THE REVIEW STANDS');
    lines.push(`  ${boardLine(board)}`);
    lines.push(`  ${board.openComments} open comment${board.openComments === 1 ? '' : 's'}` +
      ` · ${board.flags} flagged, across everyone`);
    lines.push('');
  }

  if (siteUrl) {
    lines.push(`Open the review board: ${siteUrl}`);
    lines.push('');
  }
  lines.push('Nothing has been published. This is a notification only.');

  const text = lines.join('\n');

  // ---------------------------------------------------------------------- html
  const rows = targets.map((t) => {
    const items = byTarget.get(t);
    const flagged = flaggedTargets.has(t);
    const body = items.length
      ? items.map((c) =>
          `<div style="margin:6px 0 0;padding:8px 11px;background:#fff;border:1px solid #e1e8ef;border-radius:6px;white-space:pre-wrap;">${esc(clip(c.body))}` +
          (c.resolved_at ? `<div style="margin-top:5px;font-size:12px;color:#6b7c93;">later resolved by ${esc(c.resolved_by)}</div>` : '') +
          `</div>`).join('')
      : `<div style="margin:6px 0 0;font-size:13px;color:#6b7c93;font-style:italic;">Flagged, no comment.</div>`;
    return `<div style="margin:0 0 16px;">
      <div style="font:700 13px -apple-system,Segoe UI,Roboto,sans-serif;color:${flagged ? '#b91c1c' : '#2c3e50'};">
        ${flagged ? '&#9873; ' : ''}${esc(label(t))}
      </div>${body}</div>`;
  }).join('');

  const html = `<div style="font:15px/1.55 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#2c3e50;max-width:640px;">
  <div style="background:#1a2a3a;color:#fff;padding:14px 18px;border-radius:8px 8px 0 0;">
    <div style="font-size:16px;font-weight:700;">Review complete — ${esc(cycle)}</div>
    <div style="font-size:13px;opacity:0.85;margin-top:2px;">${esc(reviewer)}</div>
  </div>
  <div style="border:1px solid #e1e8ef;border-top:0;border-radius:0 0 8px 8px;padding:18px;background:#fafbfc;">
    <div style="font:700 13px -apple-system,Segoe UI,Roboto,sans-serif;color:#0f766e;margin-bottom:16px;">${esc(headline)}</div>
    ${targets.length ? rows : '<div style="color:#6b7c93;font-style:italic;">They left no comments and raised no flags.</div>'}
    <div style="margin-top:18px;padding-top:14px;border-top:1px solid #e1e8ef;font-size:14px;">
      <div><b>Approved:</b> ${approvedObjectives.length ? 'objectives ' + approvedObjectives.join(', ') : 'none'}</div>
      ${notApproved ? `<div style="margin-top:3px;"><b>Not approved:</b> ${notApproved.length ? 'objectives ' + notApproved.join(', ') : 'none — every objective approved'}</div>` : ''}
      ${board ? `<div style="margin-top:10px;color:#6b7c93;font-size:13px;">${esc(boardLine(board))} · ${board.openComments} open comment${board.openComments === 1 ? '' : 's'} · ${board.flags} flagged, across everyone</div>` : ''}
    </div>
    ${siteUrl ? `<div style="margin-top:18px;"><a href="${esc(siteUrl)}" style="display:inline-block;background:#0f766e;color:#fff;text-decoration:none;padding:9px 16px;border-radius:6px;font-weight:700;font-size:14px;">Open the review board</a></div>` : ''}
    <div style="margin-top:16px;font-size:12px;color:#6b7c93;">Nothing has been published. This is a notification only.</div>
  </div>
</div>`;

  return { subject, text, html, stats };
}

/**
 * Sends it. Never throws — returns an outcome the caller records and shows.
 * A completion is a fact about the reviewer's work; it must not be rolled back
 * because an API key expired.
 */
export async function deliver(env, message) {
  const provider = String(env.EMAIL_PROVIDER || '').trim().toLowerCase();
  const to = String(env.REVIEW_NOTIFY_TO || '').trim();

  if (!provider) return { ok: false, status: 'not-configured', to: null, reason: 'EMAIL_PROVIDER is not set' };

  try {
    if (provider === 'resend') {
      const key = String(env.EMAIL_API_KEY || '').trim();
      const from = String(env.EMAIL_FROM || '').trim();
      if (!key || !from || !to) {
        return {
          ok: false, status: 'not-configured', to: to || null,
          reason: 'EMAIL_PROVIDER=resend needs EMAIL_API_KEY, EMAIL_FROM and REVIEW_NOTIFY_TO',
        };
      }
      const resp = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
        body: JSON.stringify({
          from,
          to: to.split(/[,\s]+/).filter(Boolean),
          subject: message.subject,
          text: message.text,
          html: message.html,
        }),
      });
      if (!resp.ok) {
        const detail = (await resp.text().catch(() => '')).slice(0, 300);
        return { ok: false, status: `failed: HTTP ${resp.status}`, to, reason: detail || `HTTP ${resp.status}` };
      }
      return { ok: true, status: 'sent', to, reason: null };
    }

    // Generic JSON POST. Covers Slack/Teams incoming webhooks, Zapier, or any
    // relay, without this file having to know which.
    if (provider === 'webhook') {
      const url = String(env.EMAIL_WEBHOOK_URL || '').trim();
      if (!url) {
        return { ok: false, status: 'not-configured', to: null, reason: 'EMAIL_PROVIDER=webhook needs EMAIL_WEBHOOK_URL' };
      }
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          subject: message.subject,
          text: message.text,
          html: message.html,
          // Slack and Teams both render a top-level `text` field, so the same
          // payload is usable as-is by either.
          summary: message.stats,
        }),
      });
      if (!resp.ok) {
        const detail = (await resp.text().catch(() => '')).slice(0, 300);
        return { ok: false, status: `failed: HTTP ${resp.status}`, to: url, reason: detail || `HTTP ${resp.status}` };
      }
      return { ok: true, status: 'sent', to: url, reason: null };
    }

    return { ok: false, status: 'not-configured', to: null, reason: `unknown EMAIL_PROVIDER: ${provider}` };
  } catch (err) {
    return { ok: false, status: 'failed: network', to: to || null, reason: String(err && err.message ? err.message : err) };
  }
}
