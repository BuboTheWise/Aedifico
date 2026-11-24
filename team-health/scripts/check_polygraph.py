#!/usr/bin/env python3
"""Pillar 2 check - Polygraph CLI health (team-health).

Pillar scope (team-health/health-rules.json): tooling / "polygraph-health".

What this check answers
-----------------------
"Is the Polygraph CLI usable right now, and are there P0/P1 blockers on the
Polygraph repo?" Two independent probes, combined into one verdict:

  1. CLI usability - actually run `python3 scripts/run_polygraph.py --help`
     inside the Polygraph repo and capture the real exit code.
       * exit != 0 (missing dependency / entrypoint crash) -> RED
       * exit == 0                                          -> pass

  2. Blocker scan - list OPEN issues on the GitHub repo and classify each by
     how much it blocks or degrades CLI usage:
       P0 (blocker)      : CLI cannot start/parse - import/startup failures,
                           entrypoint crash (e.g. a missing local package).
       P1 (degraded)     : CLI runs but the result is wrong/unusable-in-context
                           - tests a hardcoded model instead of the agent's
                           active model, OPSEC / portability (hardcoded home
                           paths so the skill cannot run from any location).
       P2 (non-blocking) : everything else (feature, CI, docs, hygiene).
     `critical_issues` = count of P0 + P1 open issues.

Verdict (matches health-rules.json "polygraph-health")
-------------------------------------------------------
  RED    CLI --help exit != 0                     (CLI not usable at all)
  YELLOW CLI exit == 0 AND critical_issues > 0    (tooling partially blocked)
  GREEN  CLI exit == 0 AND critical_issues == 0   (tooling healthy)

Documented misses (phase-gate, see evidence + health-rules.json)
----------------------------------------------------------------
  * FALSE POSITIVE (green-but-broken): `--help` exit 0 only proves importability
    + arg-parsing. A real run against a dead model endpoint still fails
    ("1A ERROR - All connection attempts failed", Overall Grade FAIL, exit 1).
    So "CLI usable" (from --help) is necessary but NOT sufficient for the tool
    to actually produce a verified result.
  * FALSE NEGATIVE (yellow-but-fine): the blocker scan counts an OPEN P0 issue
    (CLI import failure) as blocking -> yellow, but the current code no longer
    triggers that import and --help returns exit 0 from every context, so that
    specific failure no longer reproduces. A stale open issue therefore
    over-penalises a tool that actually works. The check records
    `reproduces: false` on such P0 issues (cross-referenced against the live
    --help probe) so the false negative is visible in evidence.

Evidence schema (identical to team-health/health-rules.json):
  { profile, scope, check, result: { status, details, metrics }, time }
  metrics: { exit_code, critical_issues, ... }   (required keys first)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCOPE = "tooling"
CHECK = "polygraph-health"

# Severity classification patterns (title, case-insensitive).
# NB: the missing-package error is matched via "module\s*not\s*found" (covers both
# "module not found" and the exception name) rather than spelling the full name.
P0_RE = re.compile(
    r"module\s*not\s*found|importerror|no module named|cannot import|fails with|"
    r"traceback|exits? non-?zero|segmentation|segfault|crash(es)? on (start|launch|invoke)|"
    r"cannot run|cannot start", re.I)
P1_RE = re.compile(
    r"must test|not a hardcoded|hardcoded.{0,20}(model|path|url)|wrong model|"
    r"active model|leaks? .{0,24}(username|home|path)|any install location|portability", re.I)


def _tail(text: str, n: int = 400) -> str:
    text = (text or "").strip()
    return text[-n:]


def run_cli_probe(polygraph_repo: Path, timeout_s: int) -> dict:
    """Run `python3 scripts/run_polygraph.py --help`; capture the real exit code."""
    script = polygraph_repo / "scripts" / "run_polygraph.py"
    probe = {
        "command": f"python3 {script.name} --help",
        "script_path": str(script),
        "script_exists": script.is_file(),
        "ran": False,
        "exit_code": None,
        "import_error": False,
        "stdout_tail": "",
        "stderr_tail": "",
        "error": None,
    }
    if not probe["script_exists"]:
        probe["error"] = f"runner script not found: {script}"
        return probe
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=str(polygraph_repo),
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        probe["error"] = f"--help timed out after {timeout_s}s"
        return probe
    except Exception as exc:  # noqa: BLE001
        probe["error"] = f"{exc.__class__.__name__}: {exc}"
        return probe
    probe["ran"] = True
    probe["exit_code"] = proc.returncode
    probe["stdout_tail"] = _tail(proc.stdout)
    probe["stderr_tail"] = _tail(proc.stderr)
    if re.search(r"No module named|ImportError|Traceback",
                 (proc.stderr or "") + (proc.stdout or "")):
        probe["import_error"] = True
    return probe


def resolve_token(profile: str | None) -> str | None:
    """GH_TOKEN / GITHUB_TOKEN env first, then candidate .env files."""
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        val = os.environ.get(var, "").strip()
        if val:
            return val
    home = Path.home()
    candidates = []
    if profile:
        candidates.append(home / ".hermes" / "profiles" / profile / ".env")
    candidates.append(home / ".hermes" / ".env")
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("GITHUB_TOKEN=") or line.startswith("GH_TOKEN="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val
    return None


def fetch_open_issues(repo: str, token: str | None) -> tuple[list[dict], str]:
    """List open issues. Prefer gh CLI, fall back to GitHub REST. Returns (issues, method)."""
    if token:
        os.environ.setdefault("GH_TOKEN", token)
        os.environ.setdefault("GITHUB_TOKEN", token)
    try:
        proc = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", "open",
             "--limit", "200", "--json", "number,title,labels"],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            return data, "gh-cli"
    except Exception:  # noqa: BLE001
        pass
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    issues = [{"number": i.get("number"), "title": i.get("title"),
               "labels": [{"name": l.get("name")} for l in i.get("labels", [])]}
              for i in data if "pull_request" not in i]
    return issues, "gh-rest"


def classify(issues: list[dict], cli_probe: dict) -> dict:
    """Classify open issues P0/P1/P2 and cross-reference P0 import failures."""
    groups = {"P0": [], "P1": [], "P2": []}
    for iss in issues:
        title = iss.get("title") or ""
        label_names = [l.get("name", "") for l in (iss.get("labels") or [])]
        is_bug = any(l.lower() in {"bug", "p0", "p1", "critical", "blocker"} for l in label_names)
        if P0_RE.search(title):
            sev = "P0"
        elif is_bug and P1_RE.search(title):
            sev = "P1"
        else:
            sev = "P2"
        entry = {
            "number": iss.get("number"),
            "title": title,
            "labels": label_names,
            "severity": sev,
            "blocking": sev in ("P0", "P1"),
        }
        # Cross-reference P0 import/startup failures against the live CLI probe:
        # if the failure the issue describes no longer reproduces, flag it.
        if sev == "P0" and cli_probe.get("ran") and not cli_probe.get("import_error"):
            entry["reproduces"] = False
            entry["note"] = ("issue describes an import/startup failure, but the live "
                             "--help probe returned exit 0 with no import error - "
                             "failure no longer reproduces (stale open issue).")
        groups[sev].append(entry)
    return groups


def build_evidence(profile: str, polygraph_repo: Path, cli_probe: dict,
                   groups: dict, issue_method: str, repo: str, now: str) -> dict:
    critical = len(groups["P0"]) + len(groups["P1"])
    exit_code = cli_probe.get("exit_code")
    if exit_code is None or exit_code != 0:
        status = "red"
        details = (f"CLI usability check FAILED: '{cli_probe.get('command')}' "
                   f"exit {exit_code}. {cli_probe.get('error') or cli_probe.get('stderr_tail') or ''}")
    elif critical > 0:
        status = "yellow"
        detail_issues = ([f"#{i['number']}" for i in groups["P0"]]
                         + [f"#{i['number']}" for i in groups["P1"]])
        details = (f"CLI importable & runs (--help exit 0), but {critical} P0/P1 open issue(s) "
                   f"block/degrade tool usage: {', '.join(detail_issues)}. Tooling partially blocked.")
    else:
        status = "green"
        details = ("CLI importable & runs (--help exit 0) and no P0/P1 open issues block tool "
                   "usage. Polygraph tooling healthy.")
    metrics = {
        "exit_code": exit_code if exit_code is not None else -1,
        "critical_issues": critical,
        "p0_issues": len(groups["P0"]),
        "p1_issues": len(groups["P1"]),
        "p2_issues": len(groups["P2"]),
        "cli_import_error": bool(cli_probe.get("import_error")),
        "issue_source": issue_method,
    }
    return {
        "profile": profile,
        "scope": SCOPE,
        "check": CHECK,
        "result": {"status": status, "details": details, "metrics": metrics},
        "time": now,
        "_evidence": {
            "polygraph_repo": str(polygraph_repo),
            "github_repo": repo,
            "cli_probe": cli_probe,
            "issues": {"P0": groups["P0"], "P1": groups["P1"], "P2": groups["P2"]},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Pillar 2 - Polygraph CLI health check")
    ap.add_argument("--polygraph-repo", default=os.path.expanduser("~/Projects/Polygraph"),
                    help="Path to the Polygraph repo (default: ~/Projects/Polygraph)")
    ap.add_argument("--github-repo", default="BuboTheWise/Polygraph",
                    help="GitHub repo for the blocker scan (default: BuboTheWise/Polygraph)")
    ap.add_argument("--profile", default=os.environ.get("HERMES_PROFILE", "cthugha"),
                    help="Agent profile name for the evidence record")
    ap.add_argument("--evidence-out", default=None,
                    help="Write evidence JSON to this path (default: <team-health>/evidence/polygraph-run-<date>.json)")
    ap.add_argument("--timeout", type=int, default=30, help="--help timeout seconds (default 30)")
    args = ap.parse_args()

    polygraph_repo = Path(args.polygraph_repo).expanduser()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    cli_probe = run_cli_probe(polygraph_repo, args.timeout)
    token = resolve_token(args.profile)
    issues, issue_method = fetch_open_issues(args.github_repo, token)
    groups = classify(issues, cli_probe)
    evidence = build_evidence(args.profile, polygraph_repo, cli_probe,
                              groups, issue_method, args.github_repo, now)

    if args.evidence_out:
        out = Path(args.evidence_out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        team_health = Path(__file__).resolve().parent.parent
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        out = team_health / "evidence" / f"polygraph-run-{day}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"[evidence] wrote {out}", file=sys.stderr)

    canonical = {k: v for k, v in evidence.items() if k != "_evidence"}
    print(json.dumps(canonical, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
