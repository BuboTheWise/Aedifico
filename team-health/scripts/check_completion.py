#!/usr/bin/env python3
"""Pillar 3 check - Task completion rate (team-health).

Pillar scope (team-health/health-rules.json): workflow-efficiency / "task-completion-rate".

What this check answers
-----------------------
"What percentage of the last N completed kanban tasks (default N=20) reached
the completion gate WITHOUT blockers or rework?"

Definition of a CLEAN completion (per task, from board evidence):
  * NO `blocked` events in the task's event history
    (a `blocked` event covers every block kind the kernel supports —
     dependency / needs_input / capability / transient — and is the board's
     record of a `blocked` or `needs_input` status change), AND
  * NO rework runs: every row in task_runs must have a successful outcome.
    Successful outcomes: `completed`, `review_requested` (review handoff is
    the normal flow for tasks with review children, not a blocker).
    Non-successful (rework): blocked, crashed, timed_out, spawn_failed,
    gave_up, reclaimed, changes_requested.

Evidence source: the shared kanban SQLite store (~/.hermes/kanban.db) — the
same rows the kanban_list / kanban_show tools read. Read-only connection
(`mode=ro`); this check NEVER writes to the board (task-data is read-only
input; auto-correction for low-rate trends = comment/new card, not an edit).

Verdict (matches health-rules.json "task-completion-rate")
----------------------------------------------------------
  YELLOW  fewer than --min-tasks (default 10) tasks in window — insufficient data
  GREEN   completion rate > 80%
  YELLOW  completion rate 60-80% (inclusive)
  RED     completion rate < 60%

Documented misses (phase-gate, see evidence + health-rules.json)
----------------------------------------------------------------
  * FALSE POSITIVE (clean/green but work failed later): t_caa89f9b
    ("wing_isolation: accept {PROFILE}_{CATEGORY} as NATIVE") shows ONE
    `completed` run and zero blocked events — a clean completion by this
    measure — yet the same issue #304 required two later [FIX] tasks
    (t_f360c2e8, t_468a6223) because the delivered code still flagged
    owning-profile wings as foreign. A clean run history does not prove the
    DELIVERED WORK was right.
  * FALSE NEGATIVE (penalised but work succeeded): t_c4232521
    ("memchorus-recall retrieve: flat-file fallback") ran 3x crashed
    ("owner admission settled failed" x2, worker exited without a lifecycle
    call x1) before one successful `completed` run. This check counts it as
    rework (correct — the blocker cost is real), but the deliverable landed
    and the work succeeded; the verdict is a delayed-success penalty, not a
    failed task. t_fd00e142 (blocked on a behavioral guard, then completed)
    is the same class.

Evidence schema (identical to team-health/health-rules.json):
  { profile, scope, check, result: { status, details, metrics }, time }
  metrics: { completion_rate, total_tasks, clean_tasks, blocked_tasks, rework_tasks }

Exit codes: 0 = check ran and produced a verdict (verdict lives in the JSON,
matching sibling checks); 1 = check could not run (DB missing/unreadable).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SCOPE = "workflow-efficiency"
CHECK = "task-completion-rate"

# Outcomes that count as a normal, successful run (not rework).
SUCCESS_OUTCOMES = {"completed", "review_requested"}
# Outcomes that count as rework if they appear anywhere in the task's runs.
REWORK_OUTCOMES = {"blocked", "crashed", "timed_out", "spawn_failed",
                   "gave_up", "reclaimed", "changes_requested"}


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the kanban store READ-ONLY (check never mutates task data)."""
    if not db_path.is_file():
        raise FileNotFoundError(f"kanban DB not found: {db_path}")
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def fetch_window(con: sqlite3.Connection, limit: int) -> list[dict]:
    """Last N completed (status='done') tasks, most recent first."""
    tasks = []
    for r in con.execute(
        "SELECT id, title, assignee, completed_at FROM tasks "
        "WHERE status='done' AND completed_at IS NOT NULL "
        "ORDER BY completed_at DESC, id DESC LIMIT ?", (limit,)
    ):
        tasks.append({
            "id": r["id"],
            "title": r["title"],
            "assignee": r["assignee"],
            "completed_at": r["completed_at"],
        })
    return tasks


def analyze_task(con: sqlite3.Connection, task: dict) -> dict:
    """Classify one task: clean / blocked / rework, with evidence."""
    runs = con.execute(
        "SELECT outcome, error FROM task_runs WHERE task_id=? ORDER BY started_at",
        (task["id"],),
    ).fetchall()
    blocked_events = con.execute(
        "SELECT payload, created_at FROM task_events "
        "WHERE task_id=? AND kind='blocked' ORDER BY created_at",
        (task["id"],),
    ).fetchall()

    run_outcomes = [r["outcome"] for r in runs]
    rework_runs = [
        {"outcome": r["outcome"], "error_tail": (r["error"] or "").strip()[-160:]}
        for r in runs if r["outcome"] not in SUCCESS_OUTCOMES
    ]
    blocked_details = []
    for ev in blocked_events:
        try:
            payload = json.loads(ev["payload"] or "{}")
        except (json.JSONDecodeError, TypeError):
            payload = {}
        blocked_details.append({
            "reason": (payload.get("reason") or "")[:200] or None,
            "kind": payload.get("kind"),
            "recurrences": payload.get("recurrences"),
        })

    has_block = len(blocked_events) > 0
    has_rework = len(rework_runs) > 0
    clean = not has_block and not has_rework

    return {
        **task,
        "clean": clean,
        "blocked_events": len(blocked_events),
        "blocked_details": blocked_details,
        "runs": run_outcomes,
        "rework_runs": rework_runs,
    }


def classify_rate(rate: float, total: int, min_tasks: int) -> tuple[str, str]:
    """Return (status, reason) per the health-rules.json thresholds."""
    if total < min_tasks:
        return "yellow", (f"insufficient data: only {total} completed task(s) "
                          f"in window (need >= {min_tasks})")
    if rate > 80.0:
        return "green", "completion rate > 80%"
    if rate >= 60.0:
        return "yellow", "completion rate in 60-80% band"
    return "red", "completion rate < 60%"


def build_evidence(profile: str, db_path: Path, analyzed: list[dict],
                   limit: int, min_tasks: int, now: str) -> dict:
    total = len(analyzed)
    clean = sum(1 for t in analyzed if t["clean"])
    blocked_tasks = sum(1 for t in analyzed if t["blocked_events"] > 0)
    rework_tasks = sum(1 for t in analyzed if t["rework_runs"])
    rate = round(clean / total * 100.0, 1) if total else 0.0
    status, reason = classify_rate(rate, total, min_tasks)

    if total == 0:
        details = "no completed tasks found in the board window — nothing to measure."
    else:
        details = (
            f"{clean}/{total} of the last {total} completed task(s) reached the "
            f"completion gate without blockers or rework ({rate}%); "
            f"{blocked_tasks} had a blocked/needs_input status change, "
            f"{rework_tasks} had rework runs (crashed/blocked/timed-out). "
            f"Verdict {status.upper()}: {reason}."
        )

    metrics = {
        "completion_rate": rate,
        "total_tasks": total,
        "clean_tasks": clean,
        "blocked_tasks": blocked_tasks,
        "rework_tasks": rework_tasks,
        "window": limit,
    }
    return {
        "profile": profile,
        "scope": SCOPE,
        "check": CHECK,
        "result": {"status": status, "details": details, "metrics": metrics},
        "time": now,
        "_evidence": {
            "kanban_db": str(db_path),
            "window": limit,
            "min_tasks": min_tasks,
            "definition": {
                "clean": "no blocked events AND all task_runs outcomes successful",
                "successful_outcomes": sorted(SUCCESS_OUTCOMES),
                "rework_outcomes": sorted(REWORK_OUTCOMES),
            },
            "tasks": analyzed,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pillar 3 - Task completion rate (kanban board evidence)")
    ap.add_argument("--kanban-db",
                    default=os.environ.get("HERMES_KANBAN_DB",
                                          os.path.expanduser("~/.hermes/kanban.db")),
                    help="Path to the shared kanban SQLite store "
                         "(default: $HERMES_KANBAN_DB or ~/.hermes/kanban.db)")
    ap.add_argument("--limit", type=int, default=20,
                    help="Number of most-recent completed tasks to analyze (default 20)")
    ap.add_argument("--min-tasks", type=int, default=10,
                    help="Below this window size the verdict is YELLOW (insufficient data)")
    ap.add_argument("--profile", default=os.environ.get("HERMES_PROFILE", "cthugha"),
                    help="Agent profile name for the evidence record")
    ap.add_argument("--evidence-out", default=None,
                    help="Write evidence JSON here "
                         "(default: <team-health>/evidence/completion-run-<date>.json)")
    args = ap.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        db_path = Path(args.kanban_db).expanduser()
        con = connect(db_path)
    except (FileNotFoundError, sqlite3.Error) as exc:
        print(f"[check_completion] cannot read kanban DB: {exc}", file=sys.stderr)
        return 1

    try:
        window = fetch_window(con, args.limit)
        analyzed = [analyze_task(con, t) for t in window]
    except sqlite3.Error as exc:
        print(f"[check_completion] query failed: {exc}", file=sys.stderr)
        return 1
    finally:
        con.close()

    evidence = build_evidence(args.profile, db_path, analyzed,
                              args.limit, args.min_tasks, now)

    if args.evidence_out:
        out = Path(args.evidence_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        team_health = Path(__file__).resolve().parent.parent
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        out = team_health / "evidence" / f"completion-run-{day}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"[evidence] wrote {out}", file=sys.stderr)

    canonical = {k: v for k, v in evidence.items() if k != "_evidence"}
    print(json.dumps(canonical, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
