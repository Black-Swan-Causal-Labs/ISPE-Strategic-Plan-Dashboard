#!/usr/bin/env python3
"""
csv_to_dashboard_json.py

Reads a Alchemer survey export (SP Plan-SurveyExport.csv) plus the plan
structure embedded (as DEFAULT_DATA) in index.html, and produces a
data.json file that the dashboard can fetch.

Aggregation rules (agreed with user):
- For each tactic / goal-score, the value used is the MOST RECENT submission
  from the committee that owns that goal (per the plan's responsible_committee).
- If the owning committee has not responded, fall back to the most recent
  submission from any committee that answered that question.
- Status enums are normalized to 4 values:
    Not Started, In Progress - On Track, In Progress - Delayed, Completed
- "Changed" is tracked as a SEPARATE flag (is_revised), not a status. A tactic
  reported as "Changed" gets status = "In Progress - On Track" + is_revised=True
  + revised_description from the paired Explain Changes column.
- New tactics submitted via the "new tactics added" columns are listed
  per-goal under new_tactics (also surfaced in the Changed section in the UI).
- Committee names in the dashboard refer to committees only; individual
  respondent names/emails are NOT written to data.json.
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
CSV_PATH = HERE / "SP Plan-SurveyExport.csv"
# Plan structure (DEFAULT_DATA) is the fetch-failure fallback baked into the
# dashboard page; index.html is the authoritative source for it.
HTML_PATH = HERE / "index.html"
OUT_PATH = HERE / "data.json"


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
        # Per user: track separately, default the *real* status to On Track.
        return "In Progress - On Track", True
    key = re.sub(r"[^a-z ]", " ", v.lower())
    key = re.sub(r"\s+", " ", key).strip()
    return STATUS_MAP.get(key), False


def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%b %d, %Y %I:%M:%S %p", "%b %d, %Y %I:%M:%S%p"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---------- header parsing ----------

def classify_header(h):
    h = h.replace("\n", " ").strip()
    m = re.match(r"Tactic (\d+\.\d+\.\d+)", h)
    if m:
        return ("TACTIC", m.group(1))
    if "at risk" in h.lower():
        return ("ATRISK", None)
    if "Explain changes" in h and "tactic" in h.lower():
        return ("TACTIC_EXPLAIN", None)
    if "new tactics" in h.lower():
        return ("NEWTAC", None)
    hl = h.lower()
    if "based on the answers" in hl and "progress" in hl:
        return ("GOAL_SCORE", None)
    return ("OTHER", None)


def build_column_map(header):
    """
    Walk the header row in order. Each tactic column establishes a 'current
    goal' (e.g. tactic 3.2.4 -> goal 3.2). Following ATRISK/EXPLAIN columns
    pair to the most recent tactic; NEWTAC and GOAL_SCORE pair to the
    current goal.

    Returns a dict:
      tactic_status[tactic_id]   -> col index
      tactic_atrisk[tactic_id]   -> col index
      tactic_explain[tactic_id]  -> col index
      goal_new_tactics[goal_id]  -> [col index, ...]
      goal_score[goal_id]        -> col index   (first one wins)
    """
    out = {
        "tactic_status": {},
        "tactic_atrisk": {},
        "tactic_explain": {},
        "goal_new_tactics": {},
        "goal_score": {},
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
        elif kind == "NEWTAC" and current_goal:
            out["goal_new_tactics"].setdefault(current_goal, []).append(i)
        elif kind == "GOAL_SCORE" and current_goal:
            out["goal_score"].setdefault(current_goal, i)
    return out


# ---------- aggregation ----------

def pick_value(rows, col_idx, owner_committee, value_filter=lambda v: bool(v and v.strip())):
    """
    From all responses, pick the most recent value at col_idx where:
      1. respondent committee matches owner_committee, OR
      2. (fallback) any committee whose value passes value_filter.
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

def main():
    plan = load_plan_structure()

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows_raw = list(reader)
    header = rows_raw[0]
    colmap = build_column_map(header)

    DATE_COL = 2          # "Date Submitted"
    COMMITTEE_COL = 21    # "Your Committee"

    responses = []
    for row in rows_raw[1:]:
        responses.append({
            "row": row,
            "date": parse_date(row[DATE_COL]),
            "committee": row[COMMITTEE_COL].strip() if len(row) > COMMITTEE_COL else "",
        })

    # Build new schema by enriching the plan structure.
    out = {
        "metadata": {
            **plan["metadata"],
            "as_of_date": datetime.now().strftime("%B %Y"),
            "source": "alchemer-csv",
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

                # Pick status from owner committee, fall back to anyone with a recognized value.
                def is_known_status(v):
                    s, _ = normalize_status(v)
                    return s is not None or (v and v.strip().lower() == "changed")

                status_raw, status_who, status_when = pick_value(
                    responses, status_col, owner, value_filter=is_known_status,
                )
                # is_revised / is_new_in_plan come from the plan structure
                # (the March 2026 xlsx tracker baked into DEFAULT_DATA), and
                # are preserved regardless of what the survey says.
                plan_revised = bool(tac.get("is_revised"))
                plan_new = bool(tac.get("is_new_in_plan"))
                # is_revised is taken ONLY from the plan structure (xlsx
                # March 2026). Survey "Changed" responses do not retroactively
                # mark a tactic as revised — the xlsx tracker is authoritative.
                is_revised = plan_revised
                if status_raw is not None:
                    status, _ = normalize_status(status_raw)
                    if status_who:
                        responders.add(status_who)
                else:
                    status = tac.get("status")
                    if status == "Changed":
                        status = "In Progress - On Track"

                # Notes from "at risk" explanation
                notes_raw, notes_who, _ = pick_value(
                    responses, atrisk_col, owner,
                    value_filter=lambda v: v and v.strip() and v.strip().lower() not in {"no", "no.", "none", "not at risk", "n/a"},
                )

                # Revised description (only meaningful if is_revised)
                rev_desc = None
                rev_who = None
                rev_when = None
                if is_revised:
                    rev_desc, rev_who, rev_when = pick_value(
                        responses, explain_col, owner,
                        value_filter=lambda v: v and v.strip(),
                    )
                    if rev_when is None:
                        # Fall back to the status submission date.
                        rev_when = status_when
                    if rev_who:
                        responders.add(rev_who)

                new_goal["tactics"].append({
                    "tactic_id": tid,
                    "description": tac["description"],
                    "status": status,
                    "is_revised": bool(is_revised),
                    "is_new_in_plan": plan_new,
                    "notes": notes_raw or "",
                    "last_reported_by": status_who,
                    "last_reported_at": status_when,
                })

            # New tactics added (from any committee, but prefer owner)
            for col in colmap["goal_new_tactics"].get(gid, []):
                for r in sorted(responses, key=lambda x: x["date"] or datetime.min, reverse=True):
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
                    if True:
                        new_tactics_list.append({
                            "description": v.strip(),
                            "submitted_by": r["committee"],
                            "submitted_at": r["date"].isoformat() if r["date"] else None,
                        })
                        responders.add(r["committee"])
                        break  # one entry per column

            new_goal["responding_committees"] = sorted(responders)
            new_obj["goals"].append(new_goal)
        out["objectives"].append(new_obj)

    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")

    # Quick summary
    n_tactics = sum(len(g["tactics"]) for o in out["objectives"] for g in o["goals"])
    n_revised = sum(1 for o in out["objectives"] for g in o["goals"] for t in g["tactics"] if t["is_revised"])
    n_new = sum(len(g["new_tactics"]) for o in out["objectives"] for g in o["goals"])
    print(f"  {n_tactics} tactics, {n_revised} revised, {n_new} new tactics submitted")


if __name__ == "__main__":
    main()
