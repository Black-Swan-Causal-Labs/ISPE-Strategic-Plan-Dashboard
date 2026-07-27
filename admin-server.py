#!/usr/bin/env python3
"""
Local admin server for the ISPE Strategic Plan Dashboard.

Serves the dashboard on localhost and gives admin.html two endpoints that a
browser cannot reach on its own:

    POST /api/save      write data.json, stage it, commit
    POST /api/publish   write data.json, stage it, commit, push to origin
    GET  /api/status    branch, dirty state, unpushed count, last commit

Run it from the project directory:

    python3 admin-server.py            # then open the printed URL

Design notes
------------
* Binds to 127.0.0.1 only. This process can commit to your repository, so it
  must never be reachable from the network.
* Uses your existing git credentials. No tokens, nothing secret on disk, and
  nothing added to the public repo.
* Writes only data.json, and only after the payload is shape-checked. A bad
  request cannot cause an arbitrary file write.
* admin.html degrades gracefully when this server is not running: the buttons
  fall back to their old download-a-file behaviour.
"""

import http.server
import json
import socketserver
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PORT = 8800
ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"
TRACKED = "data.json"


def git(*args, check=True):
    """Run a git command in the project directory."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def require_git_repo():
    try:
        inside = git("rev-parse", "--is-inside-work-tree")
    except (RuntimeError, FileNotFoundError):
        sys.exit(f"error: {ROOT} is not a git repository (or git is unavailable).")
    if inside != "true":
        sys.exit(f"error: {ROOT} is not a git repository.")


def validate_payload(payload):
    """
    Reject anything that is not recognisably the dashboard dataset.

    The admin page has no confirmation step, so this is the last line of
    defence against overwriting data.json with something malformed.
    """
    if not isinstance(payload, dict):
        return "payload is not a JSON object"
    if "objectives" not in payload or not isinstance(payload["objectives"], list):
        return "missing 'objectives' array"
    if not payload["objectives"]:
        return "'objectives' is empty - refusing to overwrite data.json"
    for obj in payload["objectives"]:
        if not isinstance(obj, dict) or "goals" not in obj:
            return "an objective is missing 'goals'"
        if not isinstance(obj["goals"], list):
            return "'goals' is not an array"
        for goal in obj["goals"]:
            if not isinstance(goal, dict) or not isinstance(goal.get("tactics"), list):
                return f"goal {goal.get('goal_id', '?')} has no 'tactics' array"
    if "metadata" not in payload:
        return "missing 'metadata'"
    return None


def summarise(payload):
    """One-line description of the dataset, used in the commit message."""
    total = completed = delayed = 0
    for obj in payload["objectives"]:
        for goal in obj["goals"]:
            for tactic in goal["tactics"]:
                total += 1
                status = tactic.get("status")
                if status == "Completed":
                    completed += 1
                elif status == "In Progress - Delayed":
                    delayed += 1
    as_of = (payload.get("metadata") or {}).get("as_of_date", "unknown date")
    return as_of, f"{total} tactics, {completed} completed, {delayed} delayed"


def git_status():
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(git("status", "--porcelain", "--", TRACKED))
    try:
        unpushed = git("rev-list", "--count", f"origin/{branch}..{branch}")
    except RuntimeError:
        unpushed = "?"
    last = git("log", "-1", "--pretty=%h %s (%cr)", check=False) or "(no commits)"
    return {
        "branch": branch,
        "dataJsonDirty": dirty,
        "unpushedCommits": unpushed,
        "lastCommit": last,
    }


def write_and_commit(payload, push):
    problem = validate_payload(payload)
    if problem:
        return 400, {"ok": False, "error": f"Rejected: {problem}"}

    as_of, summary = summarise(payload)

    # Byte-for-byte the same shape csv_to_dashboard_json.py produces
    # (indent=2, ensure_ascii default, trailing newline). Writing a different
    # encoding turns every save into a diff even when nothing changed.
    serialised = json.dumps(payload, indent=2) + "\n"

    # Semantic no-op guard: if the data is unchanged, do not touch the file at
    # all. Without this, formatting drift alone produces empty commits.
    if DATA_FILE.exists():
        try:
            if json.loads(DATA_FILE.read_text(encoding="utf-8")) == payload:
                result = {"ok": True, "committed": False,
                          "message": "No changes — data.json already matches."}
                if push:
                    git("push", "origin", "HEAD")
                    result["pushed"] = True
                    result["message"] = "No data changes; pushed any pending commits."
                result["git"] = git_status()
                return 200, result
        except (json.JSONDecodeError, OSError):
            pass  # unreadable existing file: fall through and overwrite

    DATA_FILE.write_text(serialised, encoding="utf-8")

    git("add", "--", TRACKED)
    if not git("status", "--porcelain", "--", TRACKED):
        # Nothing changed - still a success from the caller's point of view.
        result = {"ok": True, "committed": False,
                  "message": "No changes to data.json - nothing to commit."}
        if push:
            git("push", "origin", "HEAD")
            result["pushed"] = True
            result["message"] = "No data changes; pushed any pending commits."
        result["git"] = git_status()
        return 200, result

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"data: update progress as of {as_of}\n\n{summary}\nSaved from admin panel at {stamp}."
    git("commit", "-m", message)
    committed = git("rev-parse", "--short", "HEAD")

    result = {"ok": True, "committed": True, "commit": committed,
              "message": f"Committed {committed} - {summary}"}
    if push:
        git("push", "origin", "HEAD")
        result["pushed"] = True
        result["message"] = (f"Committed {committed} and pushed. "
                             "GitHub Pages usually redeploys within a minute.")
    result["git"] = git_status()
    return 200, result


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        if "/api/" in (self.path or ""):
            sys.stderr.write(f"  {self.command} {self.path}\n")

    def _send_json(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/status":
            try:
                self._send_json(200, {"ok": True, "git": git_status()})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
            return
        super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/save", "/api/publish"):
            self._send_json(404, {"ok": False, "error": "unknown endpoint"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 25_000_000:
                self._send_json(400, {"ok": False, "error": "missing or oversized body"})
                return
            payload = json.loads(self.rfile.read(length))
            status, body = write_and_commit(payload, push=self.path.endswith("publish"))
            self._send_json(status, body)
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"invalid JSON: {exc}"})
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})


def main():
    require_git_repo()
    if not DATA_FILE.exists():
        print(f"warning: {DATA_FILE.name} not found in {ROOT}", file=sys.stderr)

    status = git_status()
    socketserver.TCPServer.allow_reuse_address = True
    # 127.0.0.1, never 0.0.0.0 - this process can commit to your repository.
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("ISPE dashboard admin server")
        print(f"  admin   http://127.0.0.1:{PORT}/admin.html")
        print(f"  public  http://127.0.0.1:{PORT}/index.html")
        print(f"  branch  {status['branch']}  |  unpushed: {status['unpushedCommits']}")
        print("  Save -> commit    Publish -> commit + push")
        print("  Ctrl-C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped.")


if __name__ == "__main__":
    main()
