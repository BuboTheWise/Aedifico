#!/usr/bin/env python3
"""Pillar 4 -- Cross-agent communication health (DM delivery success rate).

Measures how reliably inter-agent DMs are actually delivered, by reading the
**sender's own transcript** (each `message_agent` tool result is one DM delivery
record carrying a `delivery_id` + outcome) across every local profile, plus a
live snapshot of the `hermes-dm-*` outbox (DMs not yet settled / dropped).

Why the transcript is the primary source: a DM that delivers normally is
*unlinked* from the scratch outbox when the runner settles it, so the outbox
alone only shows the failed/pending side. The sender's `messages` table keeps
every attempt and its outcome, so it is the only place that can produce a true
success *rate*. The outbox is used as corroborating, real-time "stuck now"
evidence (and its stale entries are cross-referenced against the transcript).

The unit of measurement is one `message_agent` tool CALL (one DM attempt). Each
call may store two tool rows (a "[message_agent] ..." truncated summary plus the
real delivery result), so records are grouped by `tool_call_id` and the
best-classified row wins -- attempts are not double-counted.

Classification of each delivery record (from its tool result JSON):
  delivered  status in {queued,settled,delivered,ok,success} and no error/reason
  failed     `error` present (with or without a delivery_id), or status/reason
             in a known-failure set (e.g. runtime_unavailable "NOT sent",
             ambiguous "admission could not be confirmed", reason "unknown")
  unknown    anything else (counted in the total, lowers the rate conservatively)

Verdict (health-rules.json "agent-communication"):
  green   delivery_rate > 95%
  yellow  80% <= delivery_rate <= 95%
  red     delivery_rate < 80%
  total_dms < 10 in the window   -> yellow (insufficient data)
  no scratch dir / no records    -> yellow (insufficient data)

Read-only: never mutates DM logs, the outbox, or any state.db.
Evidence shape matches team-health/health-rules.json:
  {profile, scope, check, result:{status, details, metrics, _evidence}, time}
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sqlite3
import sys
import time

DEFAULT_PROFILES_DIR = os.path.expanduser("~/.hermes/profiles")
DEFAULT_SCRATCH_DIR = os.path.expanduser("~/.hermes/cache/scratch")
SHARED_DB = os.path.expanduser("~/.hermes/state.db")

DEFAULT_WINDOW_DAYS = 30
GREEN_GT = 95.0
YELLOW_GE = 80.0
MIN_SAMPLES = 10
OUTBOX_STALE_H = 24.0

SUCCESS_STATUSES = {"queued", "settled", "delivered", "ok", "success"}
FAILURE_STATUSES = {
    "ambiguous", "failed", "held", "not_sent", "no_send",
    "error", "conflict", "timeout", "no_owner", "dropped", "rejected",
}
FAILURE_REASONS = {
    "runtime_unavailable", "target_unavailable", "held_not_sent", "no_send",
    "queue_full", "admission_conflict", "no_owner", "timeout", "dropped",
    "rejected", "not_delivered", "owner_offline",
}


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_json_dict(content: str):
    """Return the JSON object from a tool message, or None.

    A `message_agent` tool result is a JSON object (status / delivery_id /
    error / reason / to ...). It is usually the raw tool result, but can be
    wrapped in {"output": "<json string>"} when the harness captured a
    subprocess/tool output. Non-JSON rows (e.g. the "[message_agent] ..."
    truncated summary the harness stores alongside the real result) return
    None and are classified as uncertain.
    """
    c = (content or "").strip()
    if not c:
        return None
    try:
        d = json.loads(c)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    try:
        o = json.loads(c)
        if isinstance(o, dict) and isinstance(o.get("output"), str):
            d2 = json.loads(o["output"])
            if isinstance(d2, dict):
                return d2
    except Exception:
        pass
    return None


def classify_dict(d) -> str:
    """Classify one delivery record: success / failed / uncertain."""
    if not isinstance(d, dict):
        return "uncertain"
    e = d.get("error")
    st = (d.get("status") or "").lower()
    rs = (d.get("reason") or "").lower()
    if e:
        return "failed"
    if st in FAILURE_STATUSES or rs in FAILURE_REASONS:
        return "failed"
    if st in SUCCESS_STATUSES:
        return "success"
    return "uncertain"


def db_paths(profiles_dir: str, include_shared: bool):
    paths = []
    if os.path.isdir(profiles_dir):
        for name in sorted(os.listdir(profiles_dir)):
            db = os.path.join(profiles_dir, name, "state.db")
            if os.path.isfile(db):
                paths.append((name, db))
    if include_shared and os.path.isfile(SHARED_DB):
        paths.append(("default", SHARED_DB))
    return paths


# Per-call precedence: a DM counts as delivered if ANY row for that call was
# accepted (queued/delivered) -- a later successful attempt supersedes an
# earlier failure. If no row indicates success, a failure supersedes uncertain.
_CALL_PREF = {"success": 3, "failed": 2, "uncertain": 1}
_OUTCOME_MAP = {"success": "delivered", "failed": "failed", "uncertain": "unknown"}


def load_dm_records(profiles_dir: str, include_shared: bool):
    """Scan every local profile's state.db (read-only) for DM delivery records.

    The unit of measurement is one `message_agent` tool call (one DM attempt).
    Each call may store two tool rows (a "[message_agent] ..." truncated summary
    plus the real delivery result); we group by `tool_call_id` and take the
    best-classified row, so attempts are not double-counted. Error-only results
    ({"error": ..., "reason": "unknown"}) -- which carry no delivery_id -- are
    real failures and are included.

    Returns (records, scanned) where scanned is the list of (profile, db) pairs
    actually present, for evidence.
    """
    records = []
    scanned = []
    for sender, db in db_paths(profiles_dir, include_shared):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT tool_call_id, content, timestamp FROM messages "
                "WHERE role='tool' AND tool_name='message_agent'"
            ).fetchall()
            con.close()
        except Exception:
            continue
        bycall = {}
        noid = 0
        for r in rows:
            cid = r["tool_call_id"]
            if not cid:
                noid += 1
                cid = f"__noid_{noid}"
            bycall.setdefault(cid, []).append(r)
        n_calls = 0
        for _cid, group in bycall.items():
            best_cls = "uncertain"
            best_d = None
            best_ts = None
            for r in group:
                d = parse_json_dict(r["content"])
                cls = classify_dict(d)
                if _CALL_PREF[cls] > _CALL_PREF[best_cls]:
                    best_cls, best_d, best_ts = cls, d, r["timestamp"]
            n_calls += 1
            rec = {
                "sender": sender,
                "status": (best_d or {}).get("status"),
                "reason": (best_d or {}).get("reason"),
                "error": ((best_d or {}).get("error") or "")[:200],
                "to": (best_d or {}).get("to"),
                "evidence_file": (best_d or {}).get("evidence_file"),
                "delivery_id": ((best_d or {}).get("delivery_id") or "")[:16],
                "ts": best_ts,
                "outcome": _OUTCOME_MAP[best_cls],
            }
            records.append(rec)
        scanned.append({"profile": sender, "db": db, "dm_calls": n_calls})
    return records, scanned


def scan_outbox(scratch_dir: str, stale_h: float):
    """Enumerate the `hermes-dm-*` outbox: DMs not yet settled (in-flight /
    orphaned / no-send). A DM that delivered normally is unlinked, so anything
    still present is the pending-or-failed side."""
    now = time.time()
    items = []
    if not os.path.isdir(scratch_dir):
        return items
    for d in sorted(os.listdir(scratch_dir)):
        if not d.startswith("hermes-dm-"):
            continue
        dp = os.path.join(scratch_dir, d)
        if not os.path.isdir(dp):
            continue
        for f in sorted(os.listdir(dp)):
            if not (f.startswith("dm-") and f.endswith(".txt")):
                continue
            fp = os.path.join(dp, f)
            intent = {}
            lj = fp + ".live.json"
            if os.path.isfile(lj):
                try:
                    with open(lj) as fh:
                        intent = json.load(fh)
                except Exception:
                    intent = {}
            try:
                mtime = os.path.getmtime(fp)
            except OSError:
                mtime = now
            age_h = (now - mtime) / 3600.0
            owner = intent.get("owner") if isinstance(intent, dict) else None
            owner_id = owner.get("id") if isinstance(owner, dict) else owner
            author = intent.get("author") if isinstance(intent, dict) else None
            items.append({
                "dir": d,
                "file": f,
                "owner_id": owner_id,
                "author": author,
                "delivery_id": ((intent.get("delivery_id") if isinstance(intent, dict) else "") or "")[:16],
                "age_h": round(age_h, 1),
                "has_intent": bool(intent),
                "stale": age_h > stale_h,
            })
    return items


def fmt_failures(failures, limit=6):
    if not failures:
        return "no failures"
    parts = []
    for r in failures[:limit]:
        reason = r["reason"] or r["status"] or "unknown"
        parts.append(f"{r['sender']}->{r['to'] or '?'} ({reason})")
    if len(failures) > limit:
        parts.append(f"+{len(failures) - limit} more")
    return "; ".join(parts)


def build_evidence(args) -> dict:
    profile = args.profile or os.environ.get("HERMES_PROFILE") or "cthugha"
    time_now = now_iso()

    records_all, scanned = load_dm_records(args.profiles_dir, not args.no_shared)
    cutoff = time.time() - args.window_days * 86400
    recs = [r for r in records_all if r.get("ts") and r["ts"] >= cutoff]

    delivered = sum(1 for r in recs if r["outcome"] == "delivered")
    failed = sum(1 for r in recs if r["outcome"] == "failed")
    unknown = sum(1 for r in recs if r["outcome"] == "unknown")
    total = len(recs)
    rate = round(delivered / total * 100, 1) if total else 0.0

    outbox = scan_outbox(args.scratch_dir, args.stale_h)
    stuck = len(outbox)
    stale = sum(1 for o in outbox if o["stale"])

    by_sender = {}
    for r in recs:
        s = by_sender.setdefault(r["sender"], {"delivered": 0, "failed": 0, "unknown": 0})
        s[r["outcome"]] += 1

    failures = sorted(
        [r for r in recs if r["outcome"] == "failed"],
        key=lambda r: -(r["ts"] or 0),
    )
    failure_breakdown = collections.Counter(
        (r["reason"] or r["status"] or "unknown") for r in failures
    )
    if failure_breakdown:
        fail_str = "failure modes " + ", ".join(
            f"{k} x{v}" for k, v in sorted(failure_breakdown.items())
        )
    else:
        fail_str = "no failures"

    if total == 0:
        verdict = "yellow"
        details = (
            f"No DM delivery records in the {args.window_days}d window "
            f"(profiles scanned under {args.profiles_dir}). Insufficient data -- "
            f"cannot compute a delivery success rate. Outbox stuck={stuck}, stale={stale}."
        )
    elif total < MIN_SAMPLES:
        verdict = "yellow"
        details = (
            f"Insufficient data: {total} DMs in the {args.window_days}d window "
            f"(min {MIN_SAMPLES}). Delivered {delivered}, failed {failed}, unknown {unknown} "
            f"(rate {rate}% not trusted). {fail_str}; "
            f"failures: {fmt_failures(failures)}. Outbox stuck={stuck}, stale={stale}."
        )
    elif rate > GREEN_GT:
        verdict = "green"
        details = (
            f"{delivered}/{total} DMs delivered in the {args.window_days}d window "
            f"(rate {rate}% > {GREEN_GT}%). Failed {failed}, unknown {unknown}; "
            f"{fail_str}. Outbox stuck={stuck}, stale={stale}."
        )
    elif rate >= YELLOW_GE:
        verdict = "yellow"
        details = (
            f"{delivered}/{total} DMs delivered in the {args.window_days}d window "
            f"(rate {rate}%, in the yellow 80-95 band). Failed {failed}, unknown {unknown}; "
            f"{fail_str}. Failures: {fmt_failures(failures)}. "
            f"Outbox stuck={stuck}, stale={stale}."
        )
    else:
        verdict = "red"
        details = (
            f"Delivery degraded: {delivered}/{total} DMs in the {args.window_days}d window "
            f"(rate {rate}% < {YELLOW_GE}%). Failed {failed}, unknown {unknown}; "
            f"{fail_str}. Failures: {fmt_failures(failures)}. "
            f"Outbox stuck={stuck}, stale={stale}."
        )

    metrics = {
        "delivery_rate": rate,
        "total_dms": total,
        "failed_dms": failed,
        "delivered_dms": delivered,
        "unknown_dms": unknown,
        "outbox_stuck": stuck,
        "outbox_stale": stale,
        "window_days": args.window_days,
        "by_sender": by_sender,
        "failure_modes": dict(failure_breakdown),
    }

    evidence = {
        "dm_records_in_window": total,
        "dm_records_all_time": len(records_all),
        "window_days": args.window_days,
        "min_samples": MIN_SAMPLES,
        "thresholds": {"green_gt": GREEN_GT, "yellow_ge": YELLOW_GE},
        "scanned_profiles": scanned,
        "failures_most_recent": failures[:25],
        "failure_modes": dict(failure_breakdown),
        "outbox_current": outbox,
        "records": recs,
        "classification_note": (
            "Unit of measurement = one `message_agent` tool call (one DM attempt); "
            "rows grouped by tool_call_id so the two-row storage form (truncated "
            "[message_agent] summary + real result) is not double-counted. "
            "delivered = status queued/settled/delivered/ok/success with no "
            "error/reason (accepted by the gateway); failed = error present (with or "
            "without a delivery_id, e.g. reason 'unknown') or status/reason in a "
            "known-failure set (runtime_unavailable 'NOT sent', ambiguous 'admission "
            "could not be confirmed'); unknown = anything else (kept in the total, "
            "lowers the rate conservatively). IMPORTANT: 'delivered' = accepted/"
            "queued by the gateway -- not consumption by the recipient; a queued DM "
            "can still be dropped before the recipient reads it (see phase-gate "
            "false-positive). A normally-delivered DM is unlinked from the outbox on "
            "settle, so the outbox corroborates only the pending/failed side."
        ),
    }

    return {
        "profile": profile,
        "scope": "team-coordination",
        "check": "agent-communication",
        "result": {
            "status": verdict,
            "details": details,
            "metrics": metrics,
        },
        "time": time_now,
        "_evidence": evidence,
    }


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Pillar 4 cross-agent communication health (DM delivery success rate)."
    )
    p.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS,
                   help=f"time window in days (default {DEFAULT_WINDOW_DAYS})")
    p.add_argument("--profiles-dir", default=DEFAULT_PROFILES_DIR,
                   help="directory of profile state.db stores")
    p.add_argument("--scratch-dir", default=DEFAULT_SCRATCH_DIR,
                   help="scratch cache dir holding hermes-dm-* outboxes")
    p.add_argument("--no-shared", action="store_true",
                   help="do not also scan the shared ~/.hermes/state.db")
    p.add_argument("--stale-h", type=float, default=OUTBOX_STALE_H,
                   help=f"outbox age (hours) above which a DM counts as stale (default {OUTBOX_STALE_H})")
    p.add_argument("--profile", default=None,
                   help="profile name to report in evidence (default $HERMES_PROFILE or cthugha)")
    p.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = p.parse_args(argv)

    ev = build_evidence(args)
    if args.pretty:
        print(json.dumps(ev, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(ev, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
