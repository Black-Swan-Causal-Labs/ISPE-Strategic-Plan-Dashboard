// ===========================================================================
// Review layer. Injected as a second <script> into a copy of index.html by
// build_review_site.py — the dashboard's own render code is never edited or
// copied, only decorated after it runs.
//
// State lives in D1 behind /api/review, NOT in localStorage. That is the whole
// difference between this and review-panel-mock.html: every reviewer sees the
// same comments, flags and approvals, from any device, and they survive a
// reload. The mock's localStorage would have given each person a private copy
// of their own checkmarks that nobody else could ever see.
// ===========================================================================
(function () {
  'use strict';

  var API = '/api/review';
  var POLL_MS = 25000;

  // Panels that are not objectives/goals/tactics but still need to be
  // commentable. Each gets a caption strip inserted above the card it names.
  var STRIPS = [
    { target: 'panel:summary', label: 'Status overview & filters', anchor: '.chart-filter-row' },
    { target: 'panel:revisions', label: 'Revisions & new tactics', anchor: '#changesSection' },
    { target: 'panel:completed', label: 'Completed tactics', anchor: '#completedSection' },
  ];

  var state = {
    cycle: null,
    me: null,
    isOwner: false,
    comments: [],
    flags: [],
    approvals: [],
    submissions: [],
    confirming: false,   // two-step guard on the one action that sends mail
    open: {},        // target -> true when its thread is expanded
    drafts: {},      // target -> unsent textarea text, survives a full re-render
    focused: null,   // target whose composer had focus, so we can restore it
    loaded: false,
    busy: 0,
  };

  // -------------------------------------------------------------- utilities
  function esc(v) {
    if (v === null || v === undefined) return '';
    return String(v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function el(id) { return document.getElementById(id); }

  function when(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    });
  }

  // Targets are machine keys ("tactic:3.1.2"); this is what a human reads.
  function targetLabel(target) {
    if (target === 'general') return 'this cycle';
    var kind = target.split(':')[0];
    var id = target.slice(kind.length + 1);
    if (kind === 'tactic') return 'tactic ' + id;
    if (kind === 'goal') return 'goal ' + id;
    if (kind === 'objective') return 'objective ' + id;
    if (kind === 'panel') {
      for (var i = 0; i < STRIPS.length; i++) {
        if (STRIPS[i].target === target) return STRIPS[i].label.toLowerCase();
      }
      return id;
    }
    return target;
  }

  function objectiveCount() {
    return (typeof data !== 'undefined' && data && data.objectives) ? data.objectives.length : 0;
  }

  // ------------------------------------------------------------ status line
  function setStatus(text, kind) {
    var node = el('rvState');
    if (!node) return;
    node.textContent = text;
    node.className = 'rv-state' + (kind ? ' rv-' + kind : '');
  }

  // A save that fails must say so. Everything this dashboard has got wrong
  // historically got wrong quietly, rendering a plausible page over a broken
  // pipeline — so a lost comment gets a red bar, not a console warning.
  function showAlert(message, offerReload, title) {
    var node = el('rvAlert');
    if (!node) return;
    node.innerHTML = '<b>' + esc(title || 'Not saved.') + '</b> ' + esc(message) +
      (offerReload ? ' <button type="button" data-rv-action="reload">Reload</button>' : '');
    node.classList.add('rv-on');
  }

  function clearAlert() {
    var node = el('rvAlert');
    if (node) { node.classList.remove('rv-on'); node.innerHTML = ''; }
  }

  // -------------------------------------------------------------------- api
  async function api(method, path, body) {
    var options = { method: method, headers: {}, cache: 'no-store' };
    if (body !== undefined) {
      options.headers['content-type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    var resp;
    try {
      resp = await fetch(API + path, options);
    } catch (e) {
      throw Object.assign(new Error('the site could not be reached'), { offline: true });
    }
    var payload = null;
    try { payload = await resp.json(); } catch (e) { /* non-JSON error page */ }
    if (!resp.ok) {
      var message = (payload && (payload.error || payload.detail)) || ('the server returned ' + resp.status);
      throw Object.assign(new Error(message), { status: resp.status });
    }
    return payload;
  }

  // `phase` distinguishes "your comment did not save" from "this board never
  // loaded" — the same red bar, but telling the reviewer the wrong one wastes
  // their time hunting for work they never lost.
  function handleFailure(err, phase) {
    var title = phase === 'load' ? 'Review comments could not be loaded.' : 'Not saved.';
    if (err && err.status === 401) {
      showAlert('You have been signed out. Reload to sign in again.', true, title);
    } else if (err && err.offline) {
      showAlert('You appear to be offline. Nothing is queued — it has to be redone once you reconnect.', true, title);
    } else {
      showAlert((err && err.message) || 'Something went wrong.', true, title);
    }
    setStatus(phase === 'load' ? 'not loaded' : 'not saved', 'error');
  }

  // --------------------------------------------------------------- indexing
  function commentsFor(target) {
    return state.comments.filter(function (c) { return c.target === target; });
  }
  function openCountFor(target) {
    return state.comments.filter(function (c) { return c.target === target && !c.resolved_at; }).length;
  }
  function flagFor(target) {
    for (var i = 0; i < state.flags.length; i++) {
      if (state.flags[i].target === target) return state.flags[i];
    }
    return null;
  }
  function approversFor(scope) {
    return state.approvals.filter(function (a) { return a.scope === scope; });
  }
  function iApproved(scope) {
    return approversFor(scope).some(function (a) { return a.reviewer === state.me; });
  }

  // ------------------------------------------------------------------ marks
  function marksHTML(target, opts) {
    opts = opts || {};
    var flag = flagFor(target);
    var count = openCountFor(target);
    var label = targetLabel(target);
    var html = '';

    if (opts.approveScope) {
      var approvers = approversFor(opts.approveScope);
      var mine = iApproved(opts.approveScope);
      var title = approvers.length
        ? 'Approved by ' + approvers.map(function (a) { return a.reviewer; }).join(', ')
        : 'Nobody has approved ' + label + ' yet';
      html += '<button type="button" class="rv-mk rv-ok' + (mine ? ' rv-on' : '') + '"' +
        ' data-rv-action="approve" data-rv-scope="' + esc(opts.approveScope) + '"' +
        ' data-rv-to="' + (mine ? '0' : '1') + '" aria-pressed="' + (mine ? 'true' : 'false') + '"' +
        ' title="' + esc(title) + '" aria-label="' + esc((mine ? 'You approved ' : 'Approve ') + label) + '">' +
        '✓' + (approvers.length ? '<span class="rv-n">' + approvers.length + '</span>' : '') +
        '</button>';
    }

    html += '<button type="button" class="rv-mk rv-flag' + (flag ? ' rv-on' : '') + '"' +
      ' data-rv-action="flag" data-rv-target="' + esc(target) + '"' +
      ' data-rv-to="' + (flag ? '0' : '1') + '" aria-pressed="' + (flag ? 'true' : 'false') + '"' +
      ' title="' + esc(flag ? 'Flagged by ' + flag.raised_by + ' — click to clear' : 'Flag ' + label + ' for attention') + '"' +
      ' aria-label="' + esc((flag ? 'Clear flag on ' : 'Flag ') + label) + '">⚑</button>';

    html += '<button type="button" class="rv-mk rv-cmt' + (count ? ' rv-has' : '') + '"' +
      ' data-rv-action="thread" data-rv-target="' + esc(target) + '"' +
      ' aria-expanded="' + (state.open[target] ? 'true' : 'false') + '"' +
      ' title="' + esc('Comment on ' + label) + '"' +
      ' aria-label="' + esc('Comment on ' + label) + '">\u{1F4AC}' +
      (count ? '<span class="rv-n">' + count + '</span>' : '') + '</button>';

    return html;
  }

  function mountMarks(host, target, opts) {
    if (!host) return;
    var box = host.querySelector(':scope > .rv-marks');
    if (!box) {
      box = document.createElement('span');
      box.className = 'rv-marks';
      host.appendChild(box);
    }
    box.innerHTML = marksHTML(target, opts);
  }

  // --------------------------------------------------------------- comments
  function commentHTML(c) {
    var canDelete = (c.author === state.me) || state.isOwner;
    return '<div class="rv-comment' + (c.resolved_at ? ' rv-resolved' : '') + '">' +
      '<div class="rv-c-meta"><b>' + esc(c.author) + '</b> ' + esc(when(c.created_at)) +
      (c.resolved_at ? ' <span>&middot; resolved by ' + esc(c.resolved_by) + '</span>' : '') +
      '<span class="rv-c-actions">' +
      '<button type="button" data-rv-action="resolve" data-rv-id="' + esc(c.id) + '"' +
      ' data-rv-to="' + (c.resolved_at ? '0' : '1') + '">' + (c.resolved_at ? 'Reopen' : 'Resolve') + '</button>' +
      (canDelete
        ? '<button type="button" data-rv-action="delete" data-rv-id="' + esc(c.id) + '">Delete</button>'
        : '') +
      '</span></div>' +
      '<div class="rv-c-text">' + esc(c.body) + '</div>' +
      '</div>';
  }

  function composerHTML(target) {
    var label = targetLabel(target);
    return '<div class="rv-composer">' +
      '<textarea data-rv-draft="' + esc(target) + '" rows="2"' +
      ' aria-label="' + esc('Comment on ' + label) + '"' +
      ' placeholder="' + esc('Comment on ' + label + '…') + '">' + esc(state.drafts[target] || '') + '</textarea>' +
      '<button type="button" data-rv-action="post" data-rv-target="' + esc(target) + '">Comment</button>' +
      '</div>' +
      '<div class="rv-hint">Everyone who can open this site sees this, signed with your email. ' +
      '⌘/Ctrl + Enter to post.</div>';
  }

  // Updates a thread container in place. The composer is only built when it is
  // missing, so a background refresh mid-sentence cannot wipe what someone is
  // still typing.
  function paintThread(container, target) {
    var list = container.querySelector(':scope > .rv-list');
    if (!list) {
      list = document.createElement('div');
      list.className = 'rv-list';
      container.appendChild(list);
    }
    var comments = commentsFor(target);
    list.innerHTML = comments.length
      ? comments.map(commentHTML).join('')
      : '<div class="rv-feed-empty" style="margin-bottom:10px">No comments here yet.</div>';

    if (!container.querySelector(':scope > .rv-composer')) {
      container.insertAdjacentHTML('beforeend', composerHTML(target));
    }
  }

  // Creates (or removes) the thread element that belongs to a target.
  function syncThread(parent, after, target, asTableRow, colspan) {
    var existing = parent.querySelector(':scope > [data-rv-thread="' + CSS.escape(target) + '"]');

    if (!state.open[target]) {
      if (existing) existing.remove();
      return;
    }
    if (!existing) {
      if (asTableRow) {
        existing = document.createElement('tr');
        existing.className = 'rv-thread-row';
        existing.setAttribute('data-rv-thread', target);
        var cell = document.createElement('td');
        cell.colSpan = colspan || 4;
        var inner = document.createElement('div');
        inner.className = 'rv-thread';
        cell.appendChild(inner);
        existing.appendChild(cell);
      } else {
        existing = document.createElement('div');
        existing.className = 'rv-thread';
        existing.setAttribute('data-rv-thread', target);
      }
      after.parentNode.insertBefore(existing, after.nextSibling);
    }
    paintThread(asTableRow ? existing.querySelector('.rv-thread') : existing, target);
  }

  // ------------------------------------------------------------ panel strips
  function installStrips() {
    STRIPS.forEach(function (strip) {
      var anchor = document.querySelector(strip.anchor);
      if (!anchor) return;
      var node = document.querySelector('.rv-strip[data-rv-target="' + CSS.escape(strip.target) + '"]');
      if (!node) {
        node = document.createElement('div');
        node.className = 'rv-strip';
        node.setAttribute('data-rv-target', strip.target);
        node.innerHTML = '<div class="rv-strip-row"><span class="rv-strip-label">' +
          esc(strip.label) + '</span></div>';
        anchor.parentNode.insertBefore(node, anchor);
      }
      mountMarks(node.querySelector('.rv-strip-row'), strip.target);
      syncThread(node, node.querySelector('.rv-strip-row'), strip.target, false);
    });
  }

  // ----------------------------------------------------------- decorate pass
  // Runs after every dashboard render. The dashboard replaces whole containers
  // with innerHTML, so anything added here is destroyed and must be rebuilt —
  // which is why open threads and drafts live in `state`, not in the DOM.
  function decorate() {
    if (!state.loaded) return;

    installStrips();

    document.querySelectorAll('.objective[data-review-target]').forEach(function (node) {
      var target = node.getAttribute('data-review-target');
      var header = node.querySelector('.objective-header');
      if (!header) return;
      mountMarks(header, target, { approveScope: target });
      syncThread(node, header, target, false);
    });

    document.querySelectorAll('.goal[data-review-target]').forEach(function (node) {
      var target = node.getAttribute('data-review-target');
      var header = node.querySelector('.goal-header');
      if (!header) return;
      mountMarks(header, target);
      syncThread(node, header, target, false);
    });

    document.querySelectorAll('tr[data-review-target]').forEach(function (row) {
      var target = row.getAttribute('data-review-target');
      var cell = row.querySelector('td.rv-cell');
      if (!cell) return;
      mountMarks(cell, target);
      row.classList.toggle('rv-flagged', !!flagFor(target));
      syncThread(row.parentNode, row, target, true, row.children.length);
    });

    restoreFocus();
  }

  function restoreFocus() {
    if (!state.focused) return;
    var box = document.querySelector('textarea[data-rv-draft="' + CSS.escape(state.focused) + '"]');
    if (box && document.activeElement !== box) {
      box.focus();
      box.selectionStart = box.selectionEnd = box.value.length;
    }
  }

  // -------------------------------------------------------------- the panels
  function paintGeneral() {
    var host = el('rvGeneralBody');
    if (!host) return;
    paintThread(host, 'general');
  }

  function paintSummary() {
    var total = objectiveCount();
    var mine = 0;
    for (var i = 0; i < total; i++) {
      if (iApproved('objective:' + data.objectives[i].objective_number)) mine++;
    }
    var openComments = state.comments.filter(function (c) { return !c.resolved_at; }).length;

    var cycleNode = el('rvCycle');
    if (cycleNode) cycleNode.textContent = state.cycle || '…';

    var prog = el('rvPillProg');
    if (prog) prog.textContent = mine + ' / ' + total + ' objectives approved by you';
    var flagPill = el('rvPillFlag');
    if (flagPill) flagPill.textContent = state.flags.length + ' flagged';
    var openPill = el('rvPillOpen');
    if (openPill) {
      openPill.textContent = openComments + ' open comment' + (openComments === 1 ? '' : 's');
    }
    var bar = el('rvProgBar');
    if (bar) bar.style.transform = 'scaleX(' + (total ? mine / total : 0) + ')';

    paintFeed();
    paintComplete();
  }

  function paintFeed() {
    var host = el('rvFeed');
    if (!host) return;

    var rows = [];
    state.flags.forEach(function (f) {
      rows.push({
        target: f.target, flagged: true, resolved: false,
        text: 'Flagged for attention', who: f.raised_by, at: f.raised_at,
      });
    });
    state.comments.forEach(function (c) {
      rows.push({
        target: c.target, flagged: !!flagFor(c.target), resolved: !!c.resolved_at,
        text: c.body, who: c.author, at: c.created_at,
      });
    });

    // Unresolved first, then newest first: a review feed is a to-do list.
    rows.sort(function (a, b) {
      if (a.resolved !== b.resolved) return a.resolved ? 1 : -1;
      return String(b.at).localeCompare(String(a.at));
    });

    if (!rows.length) {
      host.innerHTML = '<div class="rv-feed-empty">Nothing yet. Use the ' +
        '\u{1F4AC} and ⚑ buttons on any objective, goal or tactic — ' +
        'or the box below for anything general.</div>';
      return;
    }

    host.innerHTML = rows.map(function (r) {
      return '<button type="button" class="rv-feed-item' +
        (r.flagged ? ' rv-f-flag' : '') + (r.resolved ? ' rv-f-done' : '') + '"' +
        ' data-rv-action="jump" data-rv-target="' + esc(r.target) + '">' +
        // ⚑ is the non-colour half of the flagged encoding; the tint is the other.
        '<span class="rv-f-target">' + (r.flagged ? '⚑ ' : '') + esc(targetLabel(r.target)) + '</span>' +
        '<span class="rv-f-body">' + esc(r.text) +
        '<span class="rv-f-meta">' + esc(r.who) + (r.at ? ' · ' + esc(when(r.at)) : '') +
        (r.resolved ? ' · resolved' : '') + '</span></span></button>';
    }).join('');
  }

  // ------------------------------------------------------- complete review
  function mySubmissions() {
    return state.submissions
      .filter(function (s) { return s.reviewer === state.me; })
      .sort(function (a, b) { return String(a.submitted_at).localeCompare(String(b.submitted_at)); });
  }

  function latestSubmission() {
    var mine = mySubmissions();
    return mine.length ? mine[mine.length - 1] : null;
  }

  // Anything this reviewer wrote after they last pressed Complete. Drives the
  // "you have added things since" prompt, so a second thought is not stranded
  // in a board nobody is told to look at again.
  function myActivitySince(iso) {
    return state.comments.filter(function (c) {
      return c.author === state.me && String(c.created_at) > String(iso);
    }).length;
  }

  function myCounts() {
    var total = objectiveCount();
    var approved = 0;
    for (var i = 0; i < total; i++) {
      if (iApproved('objective:' + data.objectives[i].objective_number)) approved++;
    }
    return {
      comments: state.comments.filter(function (c) { return c.author === state.me; }).length,
      flags: state.flags.filter(function (f) { return f.raised_by === state.me; }).length,
      approved: approved,
      objectives: total,
    };
  }

  function deliveryNote(submission) {
    if (!submission) return '';
    var d = String(submission.delivery || '');
    if (d === 'sent') {
      return '<span class="rv-note rv-note-ok">Summary emailed.</span>';
    }
    if (d === 'not-configured') {
      return '<span class="rv-note rv-note-warn">Recorded here, but <b>no email was sent</b> — ' +
        'notification is not set up yet. Tell the dashboard owner directly.</span>';
    }
    return '<span class="rv-note rv-note-bad">Recorded here, but <b>the email did not send</b> (' +
      esc(d) + '). Tell the dashboard owner directly.</span>';
  }

  function paintComplete() {
    var host = el('rvComplete');
    if (!host) return;

    var counts = myCounts();
    var last = latestSubmission();
    var since = last ? myActivitySince(last.submitted_at) : 0;
    var others = state.submissions.filter(function (s) { return s.reviewer !== state.me; });
    var otherNames = [];
    others.forEach(function (s) {
      if (otherNames.indexOf(s.reviewer) === -1) otherNames.push(s.reviewer);
    });

    var summaryLine = 'You have left <b>' + counts.comments + '</b> comment' +
      (counts.comments === 1 ? '' : 's') + ', flagged <b>' + counts.flags + '</b>, ' +
      'and approved <b>' + counts.approved + ' of ' + counts.objectives + '</b> objectives.';

    var html = '';

    if (state.confirming) {
      html =
        '<div class="rv-complete-row">' +
        '<div class="rv-complete-text"><b>Send this to the dashboard owner?</b><br>' +
        summaryLine + ' They will get your comments in full. Nothing is published.</div>' +
        '<div class="rv-complete-actions">' +
        '<button type="button" class="rv-btn rv-btn-ghost" data-rv-action="complete-cancel">Cancel</button>' +
        '<button type="button" class="rv-btn" data-rv-action="complete-confirm">Send summary</button>' +
        '</div></div>';
    } else if (!last) {
      html =
        '<div class="rv-complete-row">' +
        '<div class="rv-complete-text">' + summaryLine + '</div>' +
        '<div class="rv-complete-actions">' +
        '<button type="button" class="rv-btn" data-rv-action="complete">Complete review &amp; email summary</button>' +
        '</div></div>';
    } else {
      html =
        '<div class="rv-complete-row">' +
        '<div class="rv-complete-text"><span class="rv-done">&#10003; You completed this review on ' +
        esc(when(last.submitted_at)) + '.</span> ' + deliveryNote(last) +
        (since
          ? '<div class="rv-since">You have added <b>' + since + '</b> comment' + (since === 1 ? '' : 's') +
            ' since. Send an updated summary so it is not missed.</div>'
          : '') +
        '</div>' +
        '<div class="rv-complete-actions">' +
        '<button type="button" class="rv-btn' + (since ? '' : ' rv-btn-ghost') + '" data-rv-action="complete">' +
        'Send an updated summary</button>' +
        '</div></div>';
    }

    if (otherNames.length) {
      html += '<div class="rv-stamp">Also completed: ' + esc(otherNames.join(', ')) + '</div>';
    }

    host.innerHTML = html;
  }

  function paintAll() {
    decorate();
    paintSummary();
    paintGeneral();
  }

  // ----------------------------------------------------------------- loading
  async function refresh(quiet) {
    if (!state.cycle) return;
    if (!quiet) setStatus('loading…');
    try {
      var payload = await api('GET', '/state?cycle=' + encodeURIComponent(state.cycle));
      state.me = payload.me;
      state.isOwner = payload.isOwner;
      state.comments = payload.comments || [];
      state.flags = payload.flags || [];
      state.approvals = payload.approvals || [];
      state.submissions = payload.submissions || [];
      state.loaded = true;
      var who = el('rvWho');
      if (who) who.textContent = state.me;
      clearAlert();
      setStatus('all changes saved');
      paintAll();
    } catch (err) {
      handleFailure(err, state.loaded ? 'save' : 'load');
    }
  }

  // The cycle label is the dashboard's own as-of date. Review state is keyed to
  // it, so when the data moves to a new cycle the board starts empty rather
  // than carrying last cycle's approvals onto numbers nobody has looked at.
  function ensureCycle() {
    var label = (typeof data !== 'undefined' && data && data.metadata && data.metadata.as_of_date)
      ? String(data.metadata.as_of_date) : null;
    if (!label || label === state.cycle) return;
    state.cycle = label;
    state.open = {};
    state.drafts = {};
    state.confirming = false;
    refresh();
  }

  // --------------------------------------------------------------- mutations
  async function mutate(fn) {
    state.busy++;
    setStatus('saving…', 'saving');
    try {
      await fn();
      await refresh(true);
      clearAlert();
      setStatus('all changes saved');
    } catch (err) {
      handleFailure(err);
      // Pull the truth back so the page never shows an edit the server rejected.
      try { await refresh(true); } catch (e) { /* already reported */ }
    } finally {
      state.busy--;
    }
  }

  function postComment(target) {
    var box = document.querySelector('textarea[data-rv-draft="' + CSS.escape(target) + '"]');
    if (!box) return;
    var body = box.value.trim();
    if (!body) { box.focus(); return; }

    // Clear optimistically so a slow network cannot produce a double-post from
    // an impatient second click; restored below if the save fails.
    box.value = '';
    state.drafts[target] = '';

    mutate(async function () {
      try {
        await api('POST', '/comments', { cycle: state.cycle, target: target, body: body });
      } catch (err) {
        state.drafts[target] = body;
        var again = document.querySelector('textarea[data-rv-draft="' + CSS.escape(target) + '"]');
        if (again) again.value = body;
        throw err;
      }
    });
  }

  async function completeReview() {
    state.confirming = false;
    state.busy++;
    setStatus('sending…', 'saving');
    try {
      var result = await api('POST', '/complete', { cycle: state.cycle });
      await refresh(true);

      if (result.delivery === 'sent') {
        clearAlert();
        setStatus('review sent');
      } else {
        // Recorded, but nobody was told. This is exactly the silent-failure
        // shape this project keeps getting bitten by, so the reviewer is told
        // plainly — and told what to do instead — rather than seeing a tick.
        showAlert(
          result.delivery === 'not-configured'
            ? 'Your review was recorded, but no email went out: notification is not set up on this site yet. ' +
              'Let the dashboard owner know directly that you are done.'
            : 'Your review was recorded, but the summary email failed (' +
              (result.reason || result.delivery) + '). Let the dashboard owner know directly.',
          false,
          'Review recorded — but not delivered.',
        );
        setStatus('recorded, not emailed', 'error');
      }
    } catch (err) {
      handleFailure(err, 'save');
      try { await refresh(true); } catch (e) { /* already reported */ }
    } finally {
      state.busy--;
    }
  }

  // ------------------------------------------------------------------ events
  document.addEventListener('click', function (ev) {
    var button = ev.target.closest('[data-rv-action]');
    if (!button) return;

    var action = button.getAttribute('data-rv-action');
    // Objective and goal headers toggle open/closed on click; a mark inside one
    // must not also collapse the section it sits in.
    ev.preventDefault();
    ev.stopPropagation();

    if (action === 'reload') { location.reload(); return; }

    if (action === 'thread') {
      var target = button.getAttribute('data-rv-target');
      state.open[target] = !state.open[target];
      if (state.open[target]) state.focused = target;
      decorate();
      return;
    }

    if (action === 'flag') {
      var flagTarget = button.getAttribute('data-rv-target');
      var flagged = button.getAttribute('data-rv-to') === '1';
      mutate(function () {
        return api('POST', '/flags', { cycle: state.cycle, target: flagTarget, flagged: flagged });
      });
      return;
    }

    if (action === 'approve') {
      var scope = button.getAttribute('data-rv-scope');
      var approved = button.getAttribute('data-rv-to') === '1';
      mutate(function () {
        return api('POST', '/approvals', { cycle: state.cycle, scope: scope, approved: approved });
      });
      return;
    }

    if (action === 'post') { postComment(button.getAttribute('data-rv-target')); return; }

    if (action === 'resolve') {
      var id = button.getAttribute('data-rv-id');
      var to = button.getAttribute('data-rv-to') === '1';
      mutate(function () { return api('PATCH', '/comments/' + encodeURIComponent(id), { resolved: to }); });
      return;
    }

    if (action === 'delete') {
      var delId = button.getAttribute('data-rv-id');
      // No confirm(): a modal dialog blocks the page and this is recoverable
      // only by retyping, which is a fair trade for not interrupting review.
      mutate(function () { return api('DELETE', '/comments/' + encodeURIComponent(delId)); });
      return;
    }

    if (action === 'complete') { state.confirming = true; paintComplete(); return; }
    if (action === 'complete-cancel') { state.confirming = false; paintComplete(); return; }
    if (action === 'complete-confirm') { completeReview(); return; }

    if (action === 'jump') { jumpTo(button.getAttribute('data-rv-target')); return; }
  }, true);

  document.addEventListener('input', function (ev) {
    var box = ev.target.closest('textarea[data-rv-draft]');
    if (box) state.drafts[box.getAttribute('data-rv-draft')] = box.value;
  });

  document.addEventListener('focusin', function (ev) {
    var box = ev.target.closest('textarea[data-rv-draft]');
    if (box) state.focused = box.getAttribute('data-rv-draft');
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Enter' || !(ev.metaKey || ev.ctrlKey)) return;
    var box = ev.target.closest('textarea[data-rv-draft]');
    if (!box) return;
    ev.preventDefault();
    postComment(box.getAttribute('data-rv-draft'));
  });


  function jumpTo(target) {
    var node = document.querySelector('[data-review-target="' + CSS.escape(target) + '"]') ||
      document.querySelector('.rv-strip[data-rv-target="' + CSS.escape(target) + '"]');

    if (target === 'general') {
      var card = el('rvGeneralCard');
      if (card) card.scrollIntoView({ block: 'center', behavior: 'smooth' });
      return;
    }
    if (!node) return;

    // A status filter or search can hide the row the reviewer just clicked.
    // Scrolling to something invisible reads as a broken link, so clear it.
    if (node.classList.contains('hidden') || node.closest('.hidden')) {
      var allButton = document.querySelector('.filter-btn[data-status="all"]');
      var search = document.querySelector('input[oninput*="searchFilter"], #searchBox');
      if (search && search.value) { search.value = ''; if (typeof searchFilter === 'function') searchFilter(''); }
      if (allButton && typeof setFilter === 'function') setFilter('all', allButton);
      node = document.querySelector('[data-review-target="' + CSS.escape(target) + '"]') || node;
    }

    var objective = node.closest('.objective');
    if (objective) objective.classList.add('open');
    var goal = node.closest('.goal');
    if (goal) goal.classList.add('open');

    state.open[target] = true;
    decorate();

    var again = document.querySelector('[data-review-target="' + CSS.escape(target) + '"]') ||
      document.querySelector('.rv-strip[data-rv-target="' + CSS.escape(target) + '"]');
    if (again) again.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  // ------------------------------------------------------------------- hooks
  // The dashboard's own functions are wrapped rather than edited: index.html
  // stays the single source of the render code, and a drifted function name
  // fails loudly here instead of silently rendering an undecorated page.
  function wrap(name, after) {
    var original = window[name];
    if (typeof original !== 'function') {
      showAlert('This page is built wrong: ' + name + '() is missing, so review controls cannot attach.', false);
      return;
    }
    window[name] = function () {
      var out = original.apply(this, arguments);
      try { after(); } catch (e) { console.error('[review]', e); }
      return out;
    };
  }

  wrap('renderObjectives', decorate);
  wrap('renderAll', function () { ensureCycle(); paintAll(); });

  // Catch-up path, only if the dashboard already rendered before this script
  // ran. Guarded on rendered output rather than firing unconditionally: until
  // init()'s fetch resolves, `data` still holds the inline February snapshot,
  // and reading a cycle label from it would load the wrong cycle's board.
  var rendered = document.getElementById('objectivesContainer');
  if (rendered && rendered.children.length) {
    ensureCycle();
    paintAll();
  }

  // Reviewers work at the same time, so the board has to converge without
  // anyone reloading. Poll while the tab is visible, and immediately on return.
  setInterval(function () {
    if (document.visibilityState === 'visible' && state.cycle && !state.busy) refresh(true);
  }, POLL_MS);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible' && state.cycle && !state.busy) refresh(true);
  });
})();
