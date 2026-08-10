#!/usr/bin/env python3
"""
csv_to_dashboard_json.py

Reads an ISPE strategic-plan survey report CSV plus the plan structure
embedded (as DEFAULT_DATA) in index.html, and produces a data.json file
that the dashboard can fetch.

Usage:
    python3 csv_to_dashboard_json.py [path/to/report.csv] [--no-merge]

With no path, the newest "SP Reports*.csv" in this directory is used.

CSV format (changed 2026-07-30)
-------------------------------
The export is now a *report* export, not the raw Alchemer response dump:
- Committee is column 0. There is NO Response ID / Time Started / Date
  Submitted / Status block, so responses carry no timestamp at all.
- Headers are riddled with non-breaking spaces (U+00A0), including between
  "Tactic" and the number, so all header text is normalized before matching.
- "New tactics" is now a structured repeating group per goal
  (Description / Budget Needed / Timeline / Community Involvement) behind a
  "Have you added new tactic(s) to goal X.Y?" yes/no gate.
Each cycle is expected to be PARTIAL (only some committees report), so the
old format is not supported for input any more.

Aggregation rules
-----------------
- For each tactic / goal-score, the value used is the submission from the
  committee that owns that goal (per the plan's responsible_committee).
- If the owning committee has not responded, fall back to any committee that
  answered that question.
- Because the report carries no submission dates, ties are broken by file
  order rather than recency. Provenance is committee-based; last_reported_at
  is therefore null for values sourced from this format.
- Status enums are normalized to 4 values:
    Not Started, In Progress - On Track, In Progress - Delayed, Completed
- "Changed" is tracked as a SEPARATE flag (is_revised), not a status. A tactic
  reported as "Changed" gets status = "In Progress - On Track" + is_revised=True
  + revised_description from the paired Explain Changes column.
- New tactic descriptions are listed per-goal under new_tactics (also surfaced
  in the Changed section in the UI).
- Committee names in the dashboard refer to committees only; individual
  respondent names/emails are NOT written to data.json.

Merge (default)
---------------
A cycle only covers the committees that reported. Values are resolved per
tactic in this order:
    1. this CSV            2. existing data.json            3. plan default
so tactics nobody reported on keep their current published value instead of
silently reverting to the plan's baked-in March 2026 status. Pass --no-merge
to rebuild from the plan alone (what the script used to do).
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
# Plan structure (DEFAULT_DATA) is the fetch-failure fallback baked into the
# dashboard page; index.html is the authoritative source for it.
HTML_PATH = HERE / "index.html"
OUT_PATH = HERE / "data.json"


# Filename conventions seen so far, newest-by-mtime wins across all of them.
# 'SP Plan-SurveyExport.csv' is deliberately NOT matched: it is the retired
# April format with a different column count, and picking it up by accident
# would mis-attribute every answer rather than fail.
CSV_GLOBS = ("SP Reports*.csv", "[0-9]*-SurveyExport.csv")


def resolve_csv_path(argv):
    """CSV path from argv, else the newest recognized export beside this script."""
    args = [a for a in argv[1:] if not a.startswith("--")]
    if args:
        p = Path(args[0])
        if not p.is_absolute():
            p = HERE / p
        if not p.exists():
            sys.exit(f"CSV not found: {p}")
        return p
    candidates = sorted(
        (p for pat in CSV_GLOBS for p in HERE.glob(pat)),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        sys.exit(
            f"No CSV given and nothing matching {' or '.join(CSV_GLOBS)} found in "
            f"{HERE}.\nUsage: python3 csv_to_dashboard_json.py <report.csv>"
        )
    return candidates[-1]


NBSP_CHARS = "\xa0\u2007\u202f\u2009\u200a\u200b\ufeff"


def clean_header(h):
    """Normalize a header cell: strip nbsp/zero-width, collapse whitespace.

    The 2026-07-30 export writes 'Tactic\\xa05.3.5:' with a non-breaking space,
    which silently defeated the tactic regex and dropped that tactic entirely.
    """
    if not h:
        return ""
    for ch in NBSP_CHARS:
        h = h.replace(ch, " ")
    h = h.replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", h).strip()


# ---------- helpers ----------

def load_plan_structure():
    """Extract DEFAULT_DATA = {...}; from the dashboard HTML."""
    text = HTML_PATH.read_text(encoding="utf-8")
    m = re.search(r"const\s+DEFAULT_DATA\s*=\s*(\{.*?\});", text, re.DOTALL)
    if not m:
        sys.exit("Could not find DEFAULT_DATA in HTML.")
    return json.loads(m.group(1))


def norm_committee(s):
    """Loose normalization for committee-name comparison."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def committee_matches(respondent, owner):
    """True if respondent's committee plausibly equals the owning committee."""
    r, o = norm_committee(respondent), norm_committee(owner)
    if not r or not o:
        return False
    if r == o:
        return True
    # owner can be 'Executive/Impact' or 'Global Development / Strategic Planning'
    owner_parts = [norm_committee(p) for p in re.split(r"[/&]", owner)]
    if r in owner_parts:
        return True
    # substring either way (e.g. 'Global Development/Strategic Planning' vs 'Strategic Planning')
    if r in o or o in r:
        return True
    return False


STATUS_MAP = {
    "not started": "Not Started",
    "in progress - on track": "In Progress - On Track",
    "in progress on track": "In Progress - On Track",
    "in progress - delayed": "In Progress - Delayed",
    "in progress delayed": "In Progress - Delayed",
    "completed": "Completed",
}


def normalize_status(raw):
    """Return (status, is_revised). Status is None if value unrecognized/empty."""
    if not raw:
        return None, False
    v = raw.strip()
    if not v:
        return None, False
    if v.lower() == "changed":
        # "Changed" says the tactic was revised; it says nothing about how far
        # along it is. It used to default the status to On Track, which read as
        # progress the committee never reported - four tactics being retired
        # into 3.1.8 all showed as On Track. Status is now left alone (the
        # previous value carries forward) and only is_revised is set.
        return None, True
    key = re.sub(r"[^a-z ]", " ", v.lower())
    key = re.sub(r"\s+", " ", key).strip()
    return STATUS_MAP.get(key), False


def is_changed_value(v):
    """True if a status cell reports the tactic as revised rather than a status."""
    return bool(v) and v.strip().lower() == "changed"


# Tactics retired by a later revision. The survey has no structured "retired"
# field - the Executive Committee said so in free text ("overcome and included
# in the new tactic 3.1.8") - so this stays a curated list rather than
# something inferred from prose. Retired tactics remain visible in their goal
# but are excluded from every progress count.
RETIRED = {
    "3.1.4": {"as_of": "July 2026", "superseded_by": "3.1.8"},
    "3.1.5": {"as_of": "July 2026", "superseded_by": "3.1.8"},
    "3.1.6": {"as_of": "July 2026", "superseded_by": "3.1.8"},
    "3.1.7": {"as_of": "July 2026", "superseded_by": "3.1.8"},
}

# When each completed tactic was completed. The export records what a status is
# but never when it changed, so - like RETIRED - these dates are curated and
# live here rather than in data.json, where a regeneration would drop them.
# Applied only to tactics the survey still reports as Completed; a tactic listed
# here that comes back as anything else is a conflict and is reported, not
# silently dated.
COMPLETED_AT = {
    "3.1.1": "October 2025",
    "3.2.1": "October 2025",
    "3.2.6": "October 2025",
    "4.2.1": "October 2025",
    "6.2.2": "October 2025",
    "6.2.4": "October 2025",
    "6.2.5": "October 2025",
    "8.2.6": "October 2025",
    "1.2.1": "February 2026",
    "2.1.1": "February 2026",
    "3.1.2": "February 2026",
    "5.3.4": "February 2026",
    "6.1.1": "February 2026",
    "6.2.3": "February 2026",
    "7.1.1": "February 2026",
    "7.1.3": "February 2026",
    "8.2.1": "February 2026",
    "8.2.7": "February 2026",
    # These six were already Completed before the August cycle — carried from the
    # plan baseline, with last_reported_at None, so no survey ever reported them
    # and no earlier completion date exists for them. Dated to August 2026 as the
    # cycle they were recorded in, not the cycle they were finished in.
    "2.1.2": "August 2026",
    "2.1.3": "August 2026",
    "2.1.6": "August 2026",
    "3.1.3": "August 2026",
    "6.1.2": "August 2026",
    "7.1.2": "August 2026",
}

# Where the baked-in is_revised / is_new_in_plan flags came from. Rendered as
# the date on those items, which was previously hardcoded in the page markup.
TRACKER_LABEL = "March 2026"


def cycle_date_from_filename(path):
    """('2026-08-04', 'August 2026') from the filename, else (None, None).

    The export carries no dates at all, so the filename is the only evidence of
    when a cycle was collected. Two conventions have arrived so far:
        'SP Reports 7.30.2026.csv'         M.D.YYYY
        '20260804134803-SurveyExport.csv'  a YYYYMMDDHHMMSS export stamp
    The second returned no match until 2026-08-09, which would have dated the
    whole August cycle as None - and an undated cycle renders as a clean page
    with the dates simply missing, so nothing would have looked wrong.
    """
    stamp = re.match(r"(20\d{2})(\d{2})(\d{2})\d*(?:\D|$)", path.name)
    if stamp:
        year, month, day = (int(x) for x in stamp.groups())
        try:
            d = datetime(year, month, day)
        except ValueError:
            return None, None
        return d.date().isoformat(), d.strftime("%B %Y")
    m = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d{2})", path.name)
    if not m:
        return None, None
    month, day, year = (int(x) for x in m.groups())
    try:
        d = datetime(year, month, day)
    except ValueError:
        return None, None
    return d.date().isoformat(), d.strftime("%B %Y")


def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%b %d, %Y %I:%M:%S %p", "%b %d, %Y %I:%M:%S%p"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---------- header parsing ----------

# One repeating-group field of the new-tactic block, e.g.
#   "2:Tactic Description:New Tactic(s) for Goal 2.1"
#   "Executive Committee:1:Community Involvement:New Tactic(s) for Goal 3.1"
NEWTAC_FIELD_RE = re.compile(
    r"^(?:(?P<who>.*?):)?(?P<slot>\d+):"
    r"(?P<field>Tactic Description|Budget Needed|Timeline|Community Involvement):"
    r"New Tactic\(s\) for Goal (?P<goal>\d+\.\d+)",
    re.IGNORECASE,
)
NEWTAC_FIELD_KIND = {
    "tactic description": "NEWTAC_DESC",
    "budget needed": "NEWTAC_BUDGET",
    "timeline": "NEWTAC_TIMELINE",
    "community involvement": "NEWTAC_COMMUNITY",
}

# Kinds recognized so they can be reported, but deliberately NOT consumed yet:
# survey-driven Revised/New (goal-level) and the extra new-tactic fields have
# no home in data.json until that call is made. Reported by print_report().
DEFERRED_KINDS = {
    "GOAL_REVISED", "GOAL_EXPLAIN", "GOAL_LEAD",
    "NEWTAC_GATE", "NEWTAC_BUDGET", "NEWTAC_TIMELINE", "NEWTAC_COMMUNITY",
}


def classify_header(h):
    h = clean_header(h)
    m = re.match(r"Tactic\s+(\d+\.\d+\.\d+)", h)
    if m:
        return ("TACTIC", m.group(1))

    m = NEWTAC_FIELD_RE.match(h)
    if m:
        return (NEWTAC_FIELD_KIND[m.group("field").lower()], m.group("goal"))

    hl = h.lower()
    m = re.search(r"have you added new tactic\(s\) to goal (\d+\.\d+)", hl)
    if m:
        return ("NEWTAC_GATE", m.group(1))
    m = re.search(r"have you revised strategic goal (\d+\.\d+)", hl)
    if m:
        return ("GOAL_REVISED", m.group(1))
    m = re.match(r"strategic goal (\d+\.\d+): explain changes", hl)
    if m:
        return ("GOAL_EXPLAIN", m.group(1))

    if "at risk" in hl:
        return ("ATRISK", None)
    if "explain changes" in hl and "tactic" in hl:
        return ("TACTIC_EXPLAIN", None)
    if "please select the strategic goal" in hl:
        return ("GOAL_LEAD", None)
    if "new tactics" in hl:
        # Legacy free-text column from the pre-2026-07-30 export.
        return ("NEWTAC", None)
    if "based on the answers" in hl and "progress" in hl:
        return ("GOAL_SCORE", None)
    return ("OTHER", None)


def build_column_map(header):
    """
    Walk the header row in order. Each tactic column establishes a 'current
    goal' (e.g. tactic 3.2.4 -> goal 3.2). Following ATRISK/EXPLAIN columns
    pair to the most recent tactic; NEWTAC and GOAL_SCORE pair to the
    current goal.

    New-tactic description columns carry their goal in the header itself
    ("...:New Tactic(s) for Goal 3.1"), so they are keyed off that rather
    than off whatever tactic happened to precede them.

    Returns a dict:
      tactic_status[tactic_id]   -> col index
      tactic_atrisk[tactic_id]   -> col index
      tactic_explain[tactic_id]  -> col index
      goal_new_tactics[goal_id]  -> [col index, ...]
      goal_score[goal_id]        -> col index   (first one wins)
      deferred[kind]             -> [col index, ...]   (recognized, not consumed)
      unclassified               -> [col index, ...]
    """
    out = {
        "tactic_status": {},
        "tactic_atrisk": {},
        "tactic_explain": {},
        "goal_new_tactics": {},
        "goal_score": {},
        "deferred": {},
        "unclassified": [],
    }
    current_tactic = None
    current_goal = None
    for i, h in enumerate(header):
        kind, val = classify_header(h)
        if kind == "TACTIC":
            current_tactic = val
            current_goal = ".".join(val.split(".")[:2])
            out["tactic_status"][val] = i
        elif kind == "ATRISK" and current_tactic:
            out["tactic_atrisk"][current_tactic] = i
        elif kind == "TACTIC_EXPLAIN" and current_tactic:
            out["tactic_explain"][current_tactic] = i
        elif kind == "NEWTAC_DESC" and val:
            out["goal_new_tactics"].setdefault(val, []).append(i)
        elif kind == "NEWTAC" and current_goal:
            # Legacy free-text column (pre-2026-07-30 export).
            out["goal_new_tactics"].setdefault(current_goal, []).append(i)
        elif kind == "GOAL_SCORE" and current_goal:
            out["goal_score"].setdefault(current_goal, i)
        elif kind in DEFERRED_KINDS:
            out["deferred"].setdefault(kind, []).append(i)
        elif kind == "OTHER":
            out["unclassified"].append(i)
    return out


# ---------- aggregation ----------

def pick_value(rows, col_idx, owner_committee, value_filter=lambda v: bool(v and v.strip())):
    """
    From all responses, pick the value at col_idx where:
      1. respondent committee matches owner_committee, OR
      2. (fallback) any committee whose value passes value_filter.
    Within a pool, the most recent submission wins. The current report export
    carries no dates, so every date is None and the stable sort leaves file
    order intact — ownership, not recency, is what actually disambiguates.
    Returns (value, respondent_committee, date_str) or (None, None, None).
    """
    if col_idx is None:
        return None, None, None
    owned = []
    other = []
    for r in rows:
        v = r["row"][col_idx] if col_idx < len(r["row"]) else ""
        if not value_filter(v):
            continue
        if committee_matches(r["committee"], owner_committee):
            owned.append((r["date"], v, r["committee"]))
        else:
            other.append((r["date"], v, r["committee"]))
    pool = owned or other
    if not pool:
        return None, None, None
    pool.sort(key=lambda t: t[0] or datetime.min, reverse=True)
    date, val, who = pool[0]
    return val, who, (date.isoformat() if date else None)


# ---------- main ----------

def find_column(header, *wanted):
    """Index of the first header matching any of `wanted` (case-insensitive)."""
    targets = {w.lower() for w in wanted}
    for i, h in enumerate(header):
        if clean_header(h).lower() in targets:
            return i
    return None


def load_existing():
    """Current published data.json, indexed for merge. Empty if absent/unreadable."""
    if not OUT_PATH.exists():
        return {}, {}, None
    try:
        doc = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ! could not read existing {OUT_PATH.name} ({e}); not merging")
        return {}, {}, None
    tactics, goals = {}, {}
    for o in doc.get("objectives", []):
        for g in o.get("goals", []):
            goals[g.get("goal_id")] = g
            for t in g.get("tactics", []):
                tactics[t.get("tactic_id")] = t
    return tactics, goals, doc.get("metadata", {})


def main():
    csv_path = resolve_csv_path(sys.argv)
    merge = "--no-merge" not in sys.argv
    plan = load_plan_structure()

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows_raw = list(reader)
    header = rows_raw[0]
    colmap = build_column_map(header)

    print(f"Reading {csv_path.name}  ({len(rows_raw) - 1} responses, {len(header)} columns)")

    # The 2026-07-30 report export puts committee in column 0 and drops the
    # Alchemer metadata block entirely, so neither position is assumed.
    committee_col = find_column(header, "Your Committee")
    if committee_col is None:
        sys.exit("No 'Your Committee' column found; cannot attribute responses.")
    # No date column in the current format. Kept so provenance comes back
    # automatically if ISPE restores a submission date to the export.
    date_col = find_column(header, "Date Submitted", "Time Started")

    responses = []
    for row in rows_raw[1:]:
        if not any(c.strip() for c in row):
            continue
        responses.append({
            "row": row,
            "date": parse_date(row[date_col]) if date_col is not None and date_col < len(row) else None,
            "committee": row[committee_col].strip() if len(row) > committee_col else "",
        })

    if date_col is None:
        print("  ! no submission-date column: ties break on file order, not recency")

    existing_tactics, existing_goals, existing_meta = load_existing() if merge else ({}, {}, None)
    if merge and (existing_meta or {}).get("source_file") == csv_path.name:
        # Merging a cycle onto its own previous output compounds whatever that
        # run got wrong - its results become this run's carried-forward base.
        print(f"\n  !! data.json was already generated from {csv_path.name}.")
        print("     Re-running merges this cycle onto its own output, so any")
        print("     correction you just made will be masked by the old values.")
        print("     Reset to the last published version first:")
        print("         git checkout main -- data.json\n")
    if merge and existing_tactics:
        print(f"  merging onto existing data.json ({len(existing_tactics)} tactics)")
    elif merge:
        print("  no existing data.json to merge onto; building from plan")
    else:
        print("  --no-merge: rebuilding from plan structure only")

    # Counters for the end-of-run report.
    stats = {"from_csv": 0, "carried_forward": 0, "from_plan": 0}
    unmapped = []          # status cells that matched no known value
    completion_conflicts = []   # curated completion date vs. a non-Completed status
    responders_all = set()

    # The as-of date is curated in the admin panel and cannot be derived from a
    # file with no dates in it, so an existing value is preserved.
    as_of = (existing_meta or {}).get("as_of_date") or datetime.now().strftime("%B %Y")

    cycle_date, cycle_label = cycle_date_from_filename(csv_path)
    if cycle_label:
        print(f"  cycle date from filename: {cycle_label} ({cycle_date})")
    else:
        print("  ! no date in the CSV filename; this cycle's items will be undated")

    # Build new schema by enriching the plan structure.
    out = {
        "metadata": {
            **plan["metadata"],
            "as_of_date": as_of,
            "source": "alchemer-csv",
            "source_file": csv_path.name,
            "cycle_date": cycle_date,
            "cycle_label": cycle_label,
            "tracker_label": TRACKER_LABEL,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "status_colors": {
            "Not Started": "#0f9ed4",
            "In Progress - On Track": "#c6c611",
            "In Progress - Delayed": "#ffbf00",
            "Completed": "#4da72d",
        },
        "changed_color": "#a02a93",
        "objectives": [],
    }

    for obj in plan["objectives"]:
        new_obj = {
            "objective_number": obj["objective_number"],
            "title": obj["title"],
            "description": obj["description"],
            "goals": [],
        }
        for goal in obj["goals"]:
            gid = goal["goal_id"]
            owner = goal["responsible_committee"]

            # Goal score
            score_raw, score_who, score_when = pick_value(
                responses, colmap["goal_score"].get(gid), owner,
                value_filter=lambda v: v and v.strip().isdigit(),
            )
            try:
                progress_score = int(score_raw) if score_raw is not None else goal["progress_score"]
            except ValueError:
                progress_score = goal["progress_score"]

            # Per-goal "responding committees" audit (names of committees that
            # answered any tactic for this goal)
            responders = set()

            new_tactics_list = []
            new_goal = {
                "goal_id": gid,
                "description": goal["description"],
                "responsible_committee": owner,
                "progress_score": progress_score,
                "progress_max": goal.get("progress_max", 10),
                "last_updated": score_when,
                "last_reported_by": score_who,
                "tactics": [],
                "new_tactics": new_tactics_list,  # filled below
            }

            for tac in goal["tactics"]:
                tid = tac["tactic_id"]
                status_col = colmap["tactic_status"].get(tid)
                explain_col = colmap["tactic_explain"].get(tid)
                atrisk_col = colmap["tactic_atrisk"].get(tid)

                # Pick status from owner committee, fall back to anyone with a
                # recognized value. "Changed" is deliberately NOT a status
                # value here - it is picked up separately below so it can set
                # is_revised without disturbing the status.
                def is_known_status(v):
                    s, _ = normalize_status(v)
                    return s is not None

                status_raw, status_who, status_when = pick_value(
                    responses, status_col, owner, value_filter=is_known_status,
                )
                changed_raw, changed_who, _ = pick_value(
                    responses, status_col, owner, value_filter=is_changed_value,
                )
                # Record status cells that were filled in but matched nothing,
                # so unrecognized answers surface instead of vanishing.
                if status_col is not None:
                    for r in responses:
                        v = r["row"][status_col] if status_col < len(r["row"]) else ""
                        if v and v.strip() and not is_known_status(v) and not is_changed_value(v):
                            unmapped.append((tid, r["committee"], v.strip()))

                # is_revised / is_new_in_plan come from the plan structure
                # (the March 2026 xlsx tracker baked into DEFAULT_DATA), and
                # are preserved regardless of what the survey says.
                plan_revised = bool(tac.get("is_revised"))
                plan_new = bool(tac.get("is_new_in_plan"))
                # is_revised now comes from the plan structure OR from a
                # "Changed" answer in this cycle. The goal-level "Have you
                # revised Strategic Goal X.Y?" question is deliberately not
                # used: it asks whether the goal's own wording changed, which
                # is a different thing from a tactic being revised.
                survey_changed = changed_raw is not None
                is_revised = plan_revised or survey_changed
                if survey_changed and changed_who:
                    responders.add(changed_who)
                    responders_all.add(changed_who)

                prev = existing_tactics.get(tid) if merge else None
                if status_raw is not None:
                    # 1. Reported in this cycle.
                    status, _ = normalize_status(status_raw)
                    stats["from_csv"] += 1
                    if status_who:
                        responders.add(status_who)
                        responders_all.add(status_who)
                elif prev and prev.get("status"):
                    # 2. Not reported this cycle: keep the published value
                    #    rather than reverting to the plan's March 2026 status.
                    status = prev["status"]
                    status_who = prev.get("last_reported_by")
                    status_when = prev.get("last_reported_at")
                    stats["carried_forward"] += 1
                else:
                    # 3. Never reported: plan default.
                    status = tac.get("status")
                    if status == "Changed":
                        status = "In Progress - On Track"
                    stats["from_plan"] += 1

                # Notes from "at risk" explanation
                notes_raw, notes_who, _ = pick_value(
                    responses, atrisk_col, owner,
                    value_filter=lambda v: v and v.strip() and v.strip().lower() not in {"no", "no.", "none", "not at risk", "n/a"},
                )
                if notes_raw is None and prev:
                    # Carry forward the published note when this cycle is silent.
                    notes_raw = prev.get("notes") or None

                # Revised description (only meaningful if is_revised)
                rev_desc = None
                rev_who = None
                rev_when = None
                if is_revised:
                    rev_desc, rev_who, rev_explained_at = pick_value(
                        responses, explain_col, owner,
                        value_filter=lambda v: v and v.strip(),
                    )
                    if rev_who:
                        responders.add(rev_who)
                    if survey_changed:
                        # Revised in THIS cycle, so it is dated to this cycle.
                        # Not status_when: that is a carried-forward date from
                        # whenever the tactic was last reported, which for a
                        # tactic revised today is months stale.
                        rev_when = rev_explained_at or cycle_date
                    else:
                        # Flag came from the tracker, not from this survey.
                        rev_when = rev_explained_at or status_when
                if survey_changed:
                    rev_desc = rev_desc or (prev or {}).get("revised_description")
                elif prev:
                    rev_desc = rev_desc or prev.get("revised_description")
                    rev_when = rev_when or prev.get("revised_at")

                tactic_out = {
                    "tactic_id": tid,
                    "description": tac["description"],
                    "status": status,
                    "is_revised": bool(is_revised),
                    "is_new_in_plan": plan_new,
                    "notes": notes_raw or "",
                    "last_reported_by": status_who,
                    "last_reported_at": status_when,
                }
                if rev_desc:
                    tactic_out["revised_description"] = rev_desc
                if rev_when:
                    tactic_out["revised_at"] = rev_when
                if tid in COMPLETED_AT:
                    if status == "Completed":
                        tactic_out["completed_at"] = COMPLETED_AT[tid]
                    else:
                        completion_conflicts.append((tid, COMPLETED_AT[tid], status))
                elif status == "Completed":
                    # Not curated, so derive it: keep a date already established,
                    # otherwise stamp this cycle if the tactic became Completed
                    # during it. A tactic that was already Completed and already
                    # undated stays undated — inventing a date is worse than a
                    # blank, and this is how completions after the curated set
                    # date themselves without anyone maintaining COMPLETED_AT.
                    carried = (prev or {}).get("completed_at")
                    if carried:
                        tactic_out["completed_at"] = carried
                    elif prev and prev.get("status") not in (None, "", "Completed") and cycle_label:
                        tactic_out["completed_at"] = cycle_label
                if tid in RETIRED:
                    tactic_out["is_retired"] = True
                    tactic_out["retired_as_of"] = RETIRED[tid]["as_of"]
                    tactic_out["superseded_by"] = RETIRED[tid]["superseded_by"]
                new_goal["tactics"].append(tactic_out)

            # New tactics added. The current format gives one Description
            # column per repeat slot per goal, so every non-empty slot is a
            # distinct submission rather than one-per-column.
            # This cycle's submissions are collected FIRST so that when the same
            # submission also exists in the published file, the version with
            # this cycle's date wins over the older undated copy.
            seen_new = set()
            for col in colmap["goal_new_tactics"].get(gid, []):
                for r in responses:
                    v = r["row"][col] if col < len(r["row"]) else ""
                    vs = (v or "").strip()
                    vsl = vs.lower()
                    # Skip empties and common "no new tactics" answers (substring match).
                    if not vs or vsl in {"none", "n/a", "no", "no."}:
                        continue
                    if any(p in vsl for p in (
                        "no new tactic", "no tactics were added",
                        "no additional tactic", "none have been added",
                        "no new tactics have been added",
                    )):
                        continue
                    key = (vs, r["committee"])
                    if key in seen_new:
                        continue
                    seen_new.add(key)
                    new_tactics_list.append({
                        "description": vs,
                        "submitted_by": r["committee"],
                        # No dates in the export; fall back to the cycle date so
                        # this cycle's submissions are not rendered undated.
                        "submitted_at": r["date"].isoformat() if r["date"] else cycle_date,
                    })
                    responders.add(r["committee"])
                    responders_all.add(r["committee"])

            if merge:
                for nt in (existing_goals.get(gid) or {}).get("new_tactics", []) or []:
                    key = (nt.get("description", "").strip(), nt.get("submitted_by") or "")
                    if key[0] and key not in seen_new:
                        seen_new.add(key)
                        new_tactics_list.append(nt)

            if merge:
                # Keep committees credited on goals they reported in past cycles.
                responders |= set((existing_goals.get(gid) or {}).get("responding_committees", []) or [])
            new_goal["responding_committees"] = sorted(responders)
            new_obj["goals"].append(new_goal)
        out["objectives"].append(new_obj)

    # Committees that reported in THIS cycle, as distinct from the cumulative
    # per-goal responding_committees, which carry forward across cycles.
    out["metadata"]["cycle_committees"] = sorted(responders_all)

    # ---- coverage checks before writing ----
    plan_ids = [t["tactic_id"] for o in plan["objectives"] for g in o["goals"] for t in g["tactics"]]
    missing = [t for t in plan_ids if t not in colmap["tactic_status"]]

    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")

    # ---- summary ----
    n_tactics = sum(len(g["tactics"]) for o in out["objectives"] for g in o["goals"])
    n_revised = sum(1 for o in out["objectives"] for g in o["goals"] for t in g["tactics"] if t["is_revised"])
    n_new = sum(len(g["new_tactics"]) for o in out["objectives"] for g in o["goals"])
    counts = {}
    n_retired = 0
    for o in out["objectives"]:
        for g in o["goals"]:
            for t in g["tactics"]:
                if t.get("is_retired"):
                    n_retired += 1
                    continue
                counts[t["status"]] = counts.get(t["status"], 0) + 1
    revised_now = [t["tactic_id"] for o in out["objectives"] for g in o["goals"]
                   for t in g["tactics"] if t.get("revised_at") == cycle_date]

    print(f"  {n_tactics} tactics ({n_tactics - n_retired} active, {n_retired} retired), "
          f"{n_revised} revised, {n_new} new tactics submitted")
    if revised_now:
        print(f"  revised this cycle ({len(revised_now)}): {', '.join(sorted(revised_now))}")
    print(f"  sources: {stats['from_csv']} from this CSV, "
          f"{stats['carried_forward']} carried forward, {stats['from_plan']} from plan default")
    print("  statuses: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda kv: str(kv[0]))))
    if responders_all:
        print(f"  reported this cycle ({len(responders_all)}): {', '.join(sorted(responders_all))}")

    print(f"  tactic columns matched: {len(colmap['tactic_status'])}/{len(plan_ids)}"
          + (f"   MISSING: {', '.join(missing)}" if missing else ""))
    if colmap["deferred"]:
        parts = ", ".join(f"{k}={len(v)}" for k, v in sorted(colmap["deferred"].items()))
        print(f"  recognized but NOT consumed (pending decisions): {parts}")
    if colmap["unclassified"]:
        print(f"  unclassified columns: {len(colmap['unclassified'])}")
    if unmapped:
        print(f"  ! {len(unmapped)} status cell(s) matched no known value — review these:")
        for tid, who, v in unmapped:
            print(f"      {tid}  [{who}]  {v[:90]!r}")

    # Completion dates are curated, so drift between them and the survey is the
    # thing worth surfacing: a tactic completed on paper but reported otherwise,
    # and completed tactics nobody has dated yet.
    every_tactic = [t for o in out["objectives"] for g in o["goals"] for t in g["tactics"]]
    dated = sorted(t["tactic_id"] for t in every_tactic if t.get("completed_at"))
    undated = sorted(t["tactic_id"] for t in every_tactic
                     if t.get("status") == "Completed" and not t.get("completed_at")
                     and not t.get("is_retired"))
    print(f"  completion dates: {len(dated)} dated, {len(undated)} completed without one")
    if undated:
        print(f"      no completion date: {', '.join(undated)}")
    if completion_conflicts:
        print(f"  ! {len(completion_conflicts)} tactic(s) have a curated completion date but "
              f"did not come back Completed — date withheld, review COMPLETED_AT:")
        for tid, when, status in completion_conflicts:
            print(f"      {tid}  dated {when}  but reported {status!r}")


if __name__ == "__main__":
    main()
