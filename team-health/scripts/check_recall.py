#!/usr/bin/env python3
"""Pillar 1 check — MemChorus recall verification (team-health).

Verifies that MemChorus recall content ACTUALLY LANDED in recent turn
prompts. Per GH-#312, a doctor-green / probe-green signal is NOT a valid
health signal: on_grok the doctor passed while recall injection was off
because the gateway interpreter cannot import memchorus and
on_pre_llm_call returns None silently.

Evidence source
---------------
Turn evidence = ``request_dump_*.json`` under ``<HERMES_HOME>/sessions/``.
These dumps contain the FULL request body (system + user messages) exactly
as sent to the LLM — the only on-disk copy of a turn's real prompt content.
Caveat (documented on the pillar card): dumps are written on API-failure
paths, so healthy turns are not always captured; absence of a block in a
captured turn is therefore read as "no recall landed in that turn", while
absence of dumps is read as "unverifiable" — never as "recall is dead".

Markers (memchorus/hooks.py injection contract)
-----------------------------------------------
- CONTENT marker (recall actually landed, context_items non-empty):
    ``[MemChorus injected context]``  or  ``<!-- memchorus:recalled -->``
- WRAPPER marker (block present, may contain only guard/balance lines —
  recall did NOT land):
    ``[MemChorus Memory Recall]``
A wrapper-only block is the exact #312 false-positive class: "MemChorus is
active" signal with no recall content inside.

Probe (contrast only, NEVER the verdict)
----------------------------------------
Runs ``memchorus-doctor`` with the profile's HERMES_HOME and parses the
printed probe table (NOT the exit code — doctor has returned exit 0 with a
failed probe). The ``inprocess_interpreter`` probe is the #312 root-cause
probe.

Verdict semantics (content-first)
---------------------------------
- GREEN  : a CONTENT marker is present in >=1 of the last N captured turns
           (probe status recorded as contrast; a red probe is flagged as a
           probe false-positive, not a verdict).
- YELLOW : (a) no content in the last N turns, but the doctor probe reports
           green (zero failed probes) — the #312 signature: green probe,
           no landing. Or (b) recall landed but the newest landing is older
           than the freshness window (--max-landing-age-hours, default 72h) —
           stale evidence cannot verify the CURRENT recall state.
- RED    : no content in the last N turns AND the doctor probe is red or
           unknown (failed probes present, or doctor could not run).

Read-only: never modifies MemChorus config, skills, or data.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCOPE = "memory-context"          # team-health/health-rules.json pillar scope
CHECK = "memchorus-recall"       # pillar id
CONTENT_MARKERS = ("[MemChorus injected context]", "<!-- memchorus:recalled -->")
WRAPPER_MARKER = "[MemChorus Memory Recall]"
HERMES_ROOT = Path(os.environ.get("HERMES_ROOT", "~/.hermes")).expanduser()


def home_for(profile: str) -> Path:
    return HERMES_ROOT if profile == "default" else HERMES_ROOT / "profiles" / profile


def _message_text(content) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    try:
        return json.dumps(content)
    except (TypeError, ValueError):
        return str(content)


def inspect_dump(path: Path) -> dict:
    """Parse one request dump and classify its turn's MemChorus block."""
    out = {
        "file": path.name,
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
        "turn_ts": None,
        "reason": None,
        "has_block": False,
        "has_content": False,
        "block_positions": [],
        "error": None,
    }
    try:
        data = json.loads(path.read_text(errors="replace"))
    except Exception as exc:  # malformed dump — record, keep going
        out["error"] = f"unparseable dump: {exc.__class__.__name__}"
        return out
    request = data.get("request") or {}
    body = request.get("body") or {}
    out["turn_ts"] = data.get("timestamp")
    out["reason"] = data.get("reason")
    messages = body.get("messages") or []
    for idx, msg in enumerate(messages):
        text = _message_text((msg or {}).get("content"))
        if not text:
            continue
        block_at = text.find(WRAPPER_MARKER)
        content_at = max(text.find(m) for m in CONTENT_MARKERS)
        if block_at != -1:
            out["has_block"] = True
            out["block_positions"].append(f"messages[{idx}]@{block_at}")
        if content_at != -1:
            out["has_content"] = True
            out["block_positions"].append(f"messages[{idx}]:content@{content_at}")
    return out


def collect_turns(profile: str, n: int) -> tuple[list[dict], int]:
    """Return the newest N captured turns for a profile + total dump count."""
    home = home_for(profile)
    sess_dir = home / "sessions"
    if not sess_dir.is_dir():
        return [], 0
    dumps = sorted(
        sess_dir.glob("request_dump_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [inspect_dump(p) for p in dumps[:n]], len(dumps)


def run_doctor(profile: str, timeout_s: int) -> dict:
    """Run memchorus-doctor for the profile; parse the probe table.

    The exit code is recorded but never trusted (doctor has exited 0 with a
    failed probe — GH-#312). Probe states are parsed from the printed table.
    """
    home = home_for(profile)
    doctor_bin = HERMES_ROOT / "bin" / "memchorus-doctor"
    probe = {
        "ran": False,
        "exit_code": None,
        "status": "unknown",
        "passed": None,
        "warnings": None,
        "failed": None,
        "failed_probes": [],
        "inprocess_interpreter": "unknown",
        "error": None,
    }
    if not doctor_bin.exists():
        probe["error"] = f"doctor binary not found: {doctor_bin}"
        return probe
    env = dict(os.environ, HERMES_HOME=str(home))
    try:
        proc = subprocess.run(
            [str(doctor_bin)],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        probe["error"] = f"doctor timed out after {timeout_s}s"
        return probe
    except Exception as exc:  # doctor crashed — record, keep going
        probe["error"] = f"{exc.__class__.__name__}: {exc}"
        return probe
    probe["ran"] = True
    probe["exit_code"] = proc.returncode
    text = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"Summary:\s*(\d+)\s*passed,\s*(\d+)\s*warnings?,\s*(\d+)\s*failed", text)
    if m:
        probe["passed"], probe["warnings"], probe["failed"] = (int(g) for g in m.groups())
        probe["status"] = "green" if probe["failed"] == 0 else "red"
    for line in text.splitlines():
        if "🔴" in line and ":" in line:
            name = line.strip().split(":", 1)[0].strip()
            if name and name not in probe["failed_probes"]:
                probe["failed_probes"].append(name)
            if name.startswith("inprocess_interpreter"):
                probe["inprocess_interpreter"] = "red"
        elif "inprocess_interpreter:" in line:
            probe["inprocess_interpreter"] = "green" if "✅" in line else "red"
    if probe["status"] not in ("green", "red"):
        probe["error"] = probe["error"] or "could not parse doctor Summary line"
    return probe


def check_profile(profile: str, turns_n: int, doctor_timeout_s: int,
                  max_landing_age_h: float) -> dict:
    turns, total_dumps = collect_turns(profile, turns_n)
    probe = run_doctor(profile, doctor_timeout_s)

    with_block = [t for t in turns if t["has_block"]]
    with_content = [t for t in turns if t["has_content"]]
    recall_landed = bool(with_content)

    # Staleness: a landing older than the freshness window cannot verify the
    # CURRENT recall state — green is downgraded to yellow (documented miss:
    # 'default' went green on 19-day-old evidence).
    now = datetime.now(tz=timezone.utc)
    newest_landing = None
    landing_age_h = None
    if with_content:
        newest_landing = max(t["mtime"] for t in with_content)  # ISO-8601 UTC
        landing_age_h = round(
            (now - datetime.fromisoformat(newest_landing)).total_seconds() / 3600, 1
        )
    evidence_stale = landing_age_h is not None and landing_age_h > max_landing_age_h

    if recall_landed and not evidence_stale:
        status = "green"
    elif recall_landed and evidence_stale:
        status = "yellow"
    elif probe["status"] == "green":
        status = "yellow"  # #312 signature: probe green, no content landing
    else:
        status = "red"     # no content, probe red/unknown

    # ---- details (human-readable, evidence-first) -------------------------
    parts = []
    if recall_landed:
        parts.append(
            f"recall content LANDED in {len(with_content)}/{len(turns)} of the last "
            f"{len(turns)} captured turns (newest landing {newest_landing}, "
            f"{landing_age_h}h old); content markers: {list(CONTENT_MARKERS)}"
        )
        if evidence_stale:
            parts.append(
                f"GREEN DOWNGRADED TO YELLOW: newest landing is {landing_age_h}h old "
                f"(> {max_landing_age_h:g}h freshness window) — stale evidence cannot "
                "verify the CURRENT recall state"
            )
        elif probe["status"] == "red":
            parts.append(
                f"probe reports red ({', '.join(probe['failed_probes'])}) yet content "
                "landed — probe false-positive, content verdict stands (per #312: "
                "content is the valid signal)"
            )
    else:
        parts.append(
            f"no recall content marker in any of the last {len(turns)} captured turns"
            + (f" ({len(with_block)} had a wrapper-only block — the #312 false-positive class)"
               if with_block else "")
            + " in request dumps"
        )
    if not turns:
        parts.append(
            "NO captured turns at all (request dumps only record API-failure paths) — "
            "recall landing is unverifiable, not proven dead"
        )
    if probe["ran"]:
        parts.append(
            f"doctor probe: {probe['passed']} passed / {probe['warnings']} warnings / "
            f"{probe['failed']} failed (exit {probe['exit_code']}); "
            f"inprocess_interpreter={probe['inprocess_interpreter']}"
        )
        if probe["status"] == "green" and not recall_landed:
            parts.append(
                "GREEN PROBE WITH NO LANDING = the #312 mismatch (doctor-green is not "
                "a valid health signal)"
            )
    elif probe["error"]:
        parts.append(f"doctor probe unavailable: {probe['error']}")
    if turns:
        parts.append(
            f"newest captured turn {max(t['mtime'] for t in turns)} "
            f"({len(turns)}/{total_dumps} dumps inspected)"
        )

    return {
        "profile": profile,
        "scope": SCOPE,
        "check": CHECK,
        "result": {
            "status": status,
            "details": " | ".join(parts),
            "metrics": {
                "recall_landed": recall_landed,
                "turns_inspected": len(turns),
                "total_dumps_on_disk": total_dumps,
                "turns_with_block": len(with_block),
                "turns_with_content": len(with_content),
                "evidence_source": "request_dump_*.json (API-failure captured turns)",
                "content_markers": list(CONTENT_MARKERS),
                "newest_turn": max((t["mtime"] for t in turns), default=None),
                "newest_landing": newest_landing,
                "newest_landing_age_h": landing_age_h,
                "evidence_stale": evidence_stale,
                "probe_status": probe["status"],
                "probe_failed_probes": probe["failed_probes"],
                "inprocess_interpreter": probe["inprocess_interpreter"],
                "doctor_exit_code": probe["exit_code"],
            },
        },
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Pillar 1: verify MemChorus recall content landed in recent turns "
        "(actual content, not probe status — GH-#312)."
    )
    prof = ap.add_mutually_exclusive_group()
    prof.add_argument("--profile", action="append", default=None,
                      help="profile name (repeatable); default profile = 'default'")
    prof.add_argument("--all", action="store_true",
                      help="check every profile found under ~/.hermes (plus 'default')")
    ap.add_argument("--turns", type=int, default=3,
                    help="how many newest captured turns to inspect (default 3)")
    ap.add_argument("--doctor-timeout", type=int, default=90,
                    help="doctor subprocess timeout in seconds (default 90)")
    ap.add_argument("--max-landing-age-hours", type=float, default=72,
                    help="freshness window: green requires a landing newer than "
                    "this (default 72h); older landings downgrade green to yellow")
    ap.add_argument("--out", default=None, help="write JSON result to this file")
    ap.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = ap.parse_args(argv)

    profiles: list[str] = []
    if args.all:
        prof_dir = HERMES_ROOT / "profiles"
        if prof_dir.is_dir():
            profiles += sorted(
                p.name for p in prof_dir.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            )
        profiles.append("default")
    elif args.profile:
        profiles = args.profile
    else:
        profiles = ["default"]

    results = [
        check_profile(p, args.turns, args.doctor_timeout, args.max_landing_age_hours)
        for p in profiles
    ]
    out = results if len(results) > 1 else results[0]
    text = json.dumps(out, indent=2 if args.pretty else None)
    print(text)
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(text + "\n")

    statuses = [r["result"]["status"] for r in results]
    if any(s == "red" for s in statuses):
        return 2
    if any(s == "yellow" for s in statuses):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
