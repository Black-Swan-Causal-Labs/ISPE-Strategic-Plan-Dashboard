#!/usr/bin/env python3
"""Build the reviewer site into review-site/dist/.

The page is GENERATED from the repo's index.html, never hand-copied. That is
deliberate. STATUS.md already records that renderChanges/renderSummary/
computeGoalProgress exist in both index.html and admin.html and that "every fix
lands twice"; a hand-maintained third copy for reviewers would make it three,
and the third would be the one nobody remembers to update. Here the dashboard
is patched at build time instead, so index.html stays the single source of the
render code.

Every patch asserts its match count. If index.html drifts so that an anchor no
longer matches exactly once, this script FAILS rather than quietly emitting a
review site with, say, no comment buttons on tactics.

The data it ships is the notes-stripped public payload, not the working
data.json. A reviewer is checking what is about to be published, so that is the
artifact they should be looking at — and it keeps the committee notes off an
internet-reachable host, rather than leaving Access as the only thing between
them and the world. To review the notes too, change PAYLOAD_SOURCE below and
say so in DEPLOY.md, because it changes what a leak would cost.

Usage:
    python3 build_review_site.py
    python3 build_review_site.py --check     # build, verify, then report only
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC = HERE / "src"
DIST = HERE / "dist"

DASHBOARD = REPO / "index.html"
PAYLOAD_BUILDER = REPO / "build_public_payload.py"

TITLE = "Review — ISPE Strategic Plan Progress Tracker"


class BuildError(RuntimeError):
    pass


def patch(html, anchor, replacement, *, what, expected=1):
    """Replace `anchor` exactly `expected` times, or raise.

    The count assertion is the point. A silently-skipped patch produces a review
    site that renders perfectly and cannot be reviewed with.
    """
    found = html.count(anchor)
    if found != expected:
        raise BuildError(
            f"{what}: expected {expected} match(es) in index.html, found {found}.\n"
            f"  Anchor: {anchor[:120]!r}\n"
            f"  index.html has drifted. Re-read the anchor and update this script;\n"
            f"  do not relax the assertion."
        )
    return html.replace(anchor, replacement)


def read(path):
    if not path.exists():
        raise BuildError(f"missing source file: {path}")
    return path.read_text(encoding="utf-8")


def build_html():
    html = read(DASHBOARD)

    # --- 1. a fourth column on the tactics table, for the review marks -------
    html = patch(
        html,
        '          <th style="width:180px">Status</th>\n        </tr></thead>',
        '          <th style="width:180px">Status</th>\n'
        '          <th class="rv-col">Review</th>\n        </tr></thead>',
        what="tactics table header",
    )

    # --- 2. tactic rows: identity + the cell the marks mount into ------------
    html = patch(
        html,
        '" data-tactic>',
        '" data-tactic data-review-target="tactic:${esc(t.tactic_id)}">',
        what="tactic row identity",
    )
    html = patch(
        html,
        '    <td data-label="Status">${statusCell}</td>\n  </tr>',
        '    <td data-label="Status">${statusCell}</td>\n'
        '    <td class="rv-cell" data-label="Review"></td>\n  </tr>',
        what="tactic row review cell",
    )

    # --- 3. goal and objective identity -------------------------------------
    html = patch(
        html,
        'data-goal="${gi}" id="goal-${esc(goal.goal_id)}">',
        'data-goal="${gi}" id="goal-${esc(goal.goal_id)}"'
        ' data-review-target="goal:${esc(goal.goal_id)}">',
        what="goal identity",
    )
    html = patch(
        html,
        '<div class="objective ${hasVisible ? \'\' : \'hidden\'}" data-obj="${oi}">',
        '<div class="objective ${hasVisible ? \'\' : \'hidden\'}" data-obj="${oi}"'
        ' data-review-target="objective:${esc(obj.objective_number)}">',
        what="objective identity",
    )

    # --- 4. title, so a stray tab is never mistaken for the live site --------
    html = patch(
        html,
        "<title>ISPE Strategic Plan Progress Tracker</title>",
        f"<title>{TITLE}</title>",
        what="page title",
    )

    # --- 5. the review layer itself -----------------------------------------
    html = patch(
        html,
        "</style>",
        "\n/* ==== review layer (review-site/src/review-layer.css) ==== */\n"
        + read(SRC / "review-layer.css")
        + "\n</style>",
        what="review stylesheet injection",
    )
    html = patch(
        html,
        "<body>",
        "<body>\n" + read(SRC / "review-bar.html"),
        what="review bar injection",
    )
    html = patch(
        html,
        '<div class="container">',
        '<div class="container">\n' + read(SRC / "review-panels.html"),
        what="review panels injection",
    )
    # A separate <script> after the dashboard's own, so its functions are already
    # defined and can be wrapped rather than edited.
    html = patch(
        html,
        "</body>",
        "<script>\n" + read(SRC / "review-layer.js") + "\n</script>\n</body>",
        what="review script injection",
    )

    return html


# Local files the built page actually asks the browser for. Parsed out of the
# HTML rather than listed by hand: `fonts/` was lost from public-deploy exactly
# once by a hand-maintained list, and the live site 404'd with nothing failing
# anywhere. One of these filenames contains a space, which is why this is a
# regex over the markup and not a shell loop.
ASSET_PATTERNS = (
    re.compile(r'(?:src|href)\s*=\s*"([^"]+)"'),
    re.compile(r"url\(\s*'([^']+)'\s*\)"),
    re.compile(r'url\(\s*"([^"]+)"\s*\)'),
)


def referenced_assets(html):
    found = set()
    for pattern in ASSET_PATTERNS:
        for raw in pattern.findall(html):
            ref = raw.strip()
            if not ref or ref.startswith(("http://", "https://", "//", "#", "mailto:", "data:")):
                continue
            if ref.startswith("/"):
                continue  # same-origin API routes, served by Functions
            found.add(ref.split("?", 1)[0].split("#", 1)[0])
    return sorted(found)


def build_payload():
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / "data.json"
    run = subprocess.run(
        [sys.executable, str(PAYLOAD_BUILDER), "-o", str(out)],
        capture_output=True, text=True, cwd=str(REPO),
    )
    if run.returncode != 0:
        raise BuildError(f"build_public_payload.py failed:\n{run.stdout}\n{run.stderr}")

    # The same assertion the publish workflow makes. If it ever fails, the
    # reviewer site was about to serve committee notes over the internet.
    check = subprocess.run(
        [sys.executable, str(PAYLOAD_BUILDER), "--check", str(out)],
        capture_output=True, text=True, cwd=str(REPO),
    )
    if check.returncode != 0:
        raise BuildError(
            "the generated payload still carries internal fields — refusing to build:\n"
            f"{check.stdout}\n{check.stderr}"
        )
    return out, run.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="build and verify, then print the report (same work, clearer intent)")
    args = ap.parse_args()

    try:
        html = build_html()

        DIST.mkdir(parents=True, exist_ok=True)
        (DIST / "index.html").write_text(html, encoding="utf-8")

        payload_path, payload_report = build_payload()

        assets = referenced_assets(html)
        copied, missing = [], []
        for ref in assets:
            if ref == "data.json":
                continue  # generated above, not copied
            source = REPO / ref
            if not source.exists():
                missing.append(ref)
                continue
            destination = DIST / ref
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(ref)

        if missing:
            raise BuildError(
                "the page references files that do not exist in the repo:\n  "
                + "\n  ".join(missing)
                + "\nThey would 404 on the live site with nothing failing anywhere."
            )

        # Post-build assertions on what is actually in dist/.
        built = (DIST / "index.html").read_text(encoding="utf-8")
        problems = []
        for marker, why in (
            ('id="rvGeneralBody"', "general comment box"),
            ('data-review-target="tactic:', "tactic review targets"),
            ('data-review-target="goal:', "goal review targets"),
            ('data-review-target="objective:', "objective review targets"),
            ('class="rv-cell"', "tactic review cells"),
            ("/api/review", "review API calls"),
        ):
            if marker not in built:
                problems.append(f"{why} missing from the built page ({marker})")
        # The reviewer site is read-only by design; admin editing lives locally.
        for banned, why in (
            ("Admin Control Panel", "admin editing controls"),
            ("publishReadOnly", "publish control"),
        ):
            if banned in built:
                problems.append(f"{why} leaked into the reviewer build ({banned})")
        if problems:
            raise BuildError("post-build checks failed:\n  " + "\n  ".join(problems))

        tactics = built.count('data-review-target="tactic:')
        print("Review site built into", DIST)
        print(f"  index.html      {len(built):,} bytes")
        print(f"  data.json       {payload_path.stat().st_size:,} bytes (notes stripped, --check passed)")
        print(f"  assets copied   {len(copied)}: " + ", ".join(copied))
        print(f"  review targets  tactic template x{tactics}, plus goals, objectives and 3 panels")
        if payload_report:
            print("\n" + payload_report)
        print("\nNext: cd review-site && npx wrangler pages dev dist   (see DEPLOY.md)")

    except BuildError as err:
        print("BUILD FAILED\n", err, sep="", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
