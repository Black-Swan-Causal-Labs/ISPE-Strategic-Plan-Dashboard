#!/usr/bin/env python3
"""Build the public data.json from the working one, with internal fields removed.

The admin panel and the public dashboard read the same data.json. The survey's
free-text notes are internal: committees write things like "on hold because the
initiative was paused" that ISPE does not intend to publish. Removing the Notes
column from index.html does NOT make them private - data.json is served over
HTTP and can be read directly, which is how 18 notes were publicly readable at
the dashboard's own /data.json until 2026-08-09.

So the notes have to be absent from the file that ships, not merely unrendered.

Usage:
    python3 build_public_payload.py                  # -> public/data.json
    python3 build_public_payload.py -o some/data.json
    python3 build_public_payload.py --check FILE     # exit 1 if FILE leaks

--check is the mode the publish workflow calls: it is an assertion about what is
about to reach the internet, so it fails rather than warns.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "data.json"
DEFAULT_OUT = HERE / "public" / "data.json"

# Per-tactic keys stripped from the public payload. Anything a committee typed
# for internal consumption belongs here; anything the dashboard renders to the
# public (description, status, completion/revision dates) does not.
INTERNAL_TACTIC_KEYS = ("notes",)


def iter_tactics(data):
    for obj in data.get("objectives", []):
        for goal in obj.get("goals", []):
            for tactic in goal.get("tactics", []):
                yield tactic


def redact(data):
    """Strip internal keys in place. Returns the number of values removed."""
    removed = 0
    for tactic in iter_tactics(data):
        for key in INTERNAL_TACTIC_KEYS:
            # Count only keys carrying an actual value: an empty string is not a
            # disclosure, and counting it would make the report meaningless.
            if str(tactic.get(key) or "").strip():
                removed += 1
            tactic.pop(key, None)
    return removed


def leaks(data):
    """Internal keys still carrying a value. Empty list means the file is clean."""
    found = []
    for tactic in iter_tactics(data):
        for key in INTERNAL_TACTIC_KEYS:
            if str(tactic.get(key) or "").strip():
                found.append((tactic.get("tactic_id", "?"), key))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", metavar="FILE",
                    help="verify FILE carries no internal fields; exit 1 if it does")
    ap.add_argument("-o", "--out", default=str(DEFAULT_OUT),
                    help=f"output path (default: {DEFAULT_OUT})")
    ap.add_argument("-s", "--source", default=str(SOURCE),
                    help=f"source data.json (default: {SOURCE})")
    args = ap.parse_args()

    if args.check:
        path = Path(args.check)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            sys.exit(f"FAIL: could not read {path}: {e}")
        found = leaks(data)
        if found:
            print(f"FAIL: {path} carries {len(found)} internal value(s) "
                  f"that must not be published:")
            for tid, key in found[:20]:
                print(f"    {tid}.{key}")
            if len(found) > 20:
                print(f"    ... and {len(found) - 20} more")
            sys.exit(1)
        print(f"OK: {path} carries no internal fields "
              f"({', '.join(INTERNAL_TACTIC_KEYS)})")
        return

    src = Path(args.source)
    if not src.exists():
        sys.exit(f"source not found: {src}")
    data = json.loads(src.read_text(encoding="utf-8"))

    total = sum(1 for _ in iter_tactics(data))
    removed = redact(data)

    remaining = leaks(data)
    if remaining:  # belt and braces; redact() should make this unreachable
        sys.exit(f"FAIL: {len(remaining)} internal value(s) survived redaction")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Read  {src}  ({total} tactics)")
    print(f"Wrote {out}")
    print(f"  stripped {removed} internal value(s): {', '.join(INTERNAL_TACTIC_KEYS)}")
    print(f"  verified: no internal fields remain")


if __name__ == "__main__":
    main()
