#!/usr/bin/env python3
"""pr_monitor.py — Scan third-party open PRs for comments needing professional replies from BuboTheWise.

Usage:
    python pr_monitor.py              # Full scan
    python pr_monitor.py --dry-run   # Check repo connectivity only
    python pr_monitor.py --repo org/repo  # Single repo
    python pr_monitor.py --since-days 7     # Shorter window
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config" / "repos.json"
DEFAULT_REPOS = ["ollama/ollama", "huggingface/transformers"]


def load_repos():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f).get("repos", DEFAULT_REPOS)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: could not load {CONFIG_PATH}: {e}", file=sys.stderr)
    return DEFAULT_REPOS


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 124


def api_get(repo, resource):
    """GET /repos/{repo}/{resource} via gh CLI. Returns (items_list, error_or_None)."""
    cmd = ["gh", "api", f"repos/{repo}/{resource}", "--jq", ".[]"]
    stdout, stderr, rc = run_cmd(cmd)
    if rc != 0:
        msg = stderr.strip()
        if "rate limit" in msg.lower() or "403" in msg:
            return None, "RATE_LIMITED"
        return None, msg[:200]
    items = []
    for line in stdout.strip().split("\n"):
        if line.strip():
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return items, None


def needs_response(comment, cutoff):
    """Score a comment. Returns (score_100, reason). Higher score = more likely actionable."""
    author = comment.get("user", {}).get("login", "")
    
    # Check against config skip_authors (with fallback for older configs)
    local_config_path = os.path.join(os.path.dirname(__file__), "..", "config", "repos.local.json")
    if os.path.exists(local_config_path):
        with open(local_config_path) as f:
            try:
                local_cfg = json.load(f)
                skip_list = local_cfg.get("skip_authors", ["bubothewise"])
            except (json.JSONDecodeError, KeyError):
                skip_list = ["bubothewise"]
    else:
        # Fallback to public default for configs without skip_authors
        skip_list = ["bubothewise"]
    
    if author.lower() in skip_list:
        return 0, "own comment"

    body = comment.get("body", "").strip()
    if not body:
        return 0, "empty body"

    # Skip stale
    created_str = comment.get("created_at", "")
    if created_str:
        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if created_dt < cutoff:
                return 0, f"stale ({(cutoff - created_dt).days}d)"
        except ValueError:
            pass

    bl = body.lower()

    # Question patterns (high score)
    questions = ["how does", "why did", "why not", "could you", "should we",
                 "is there", "what about", "can you explain", "are these",
                 "does this handle", "should this be"]
    for q in questions:
        if q in bl:
            return 95, f"question: {q}"

    # Design rationale (high score)
    design = ["rationale", "design choice", "why choose", "motivation",
              "background on", "context for", "explain why", "intended behavior"]
    for d in design:
        if d in bl:
            return 90, f"design question: {d}"

    # Scoring suggestions (medium-high score)
    suggestion_items = [
        ("change ", 3), ("update ", 3), ("fix ", 3), ("add ", 2),
        ("remove ", 3), ("rename ", 2), ("move ", 2), ("consider ", 3),
        ("instead of ", 4), ("could also", 2), ("would be better", 4),
        ("might want", 2), ("you might", 2), ("i think you", 2),
        ("please add", 5), ("please fix", 5),
    ]
    score = 0
    for pattern, weight in suggestion_items:
        if pattern in bl:
            score += weight

    if score >= 3:
        return min(score * 10, 95), f"suggestion (score: {score})"

    # Reject pure nits
    nit = ["nit:", "nit ", "typo", "formatting issue", "style fix"]
    for n in nit:
        if n in bl:
            return 0, "pure nit"

    return 0, "no actionable pattern"


def scan_repo(repo, since_days=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    # Get open PR count + basic info
    stdout, stderr, rc = run_cmd(["gh", "pr", "list", "--repo", repo, "--state", "open", "-L", "100"], timeout=30)
    if rc != 0:
        return {"repo": repo, "error": f"gh failed: {stderr.strip()[:200]}", "actionable": [], "total_open": 0}

    pr_lines = [l for l in stdout.strip().split("\n") if l.strip()]
    total_open = len(pr_lines)

    actionable = []
    checked_prs = set()

    for line in pr_lines[:100]:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            pr_num = int(parts[0])
        except ValueError:
            continue
        if pr_num in checked_prs:
            continue
        checked_prs.add(pr_num)

        # Get review comments
        comments, err = api_get(repo, f"pulls/{pr_num}/comments")
        if err == "RATE_LIMITED":
            return {"repo": repo, "error": "Rate limited", "actionable": actionable,
                    "total_open": total_open, "rate_limited": True}
        if not comments:
            continue

        # Get general PR comments for context
        pr_comments, _ = api_get(repo, f"issues/{pr_num}/comments")

        all_comments = list(comments) + (list(pr_comments) if pr_comments else [])

        for comment in all_comments:
            score, reason = needs_response(comment, cutoff)
            if score >= 60:  # Threshold for actionable
                actionable.append({
                    "pr_number": pr_num,
                    "commenter": comment.get("user", {}).get("login", "?"),
                    "date": comment.get("created_at", ""),
                    "body": _fmt_ctx(comment),
                    "is_review": comment.get("commit_id") is not None,
                    "html_url": comment.get("html_url", f"https://github.com/{repo}/pull/{pr_num}"),
                })

    return {"repo": repo, "total_open": total_open, "actionable": actionable, "rate_limited": False}


def _fmt_ctx(comment):
    body = comment.get("body", "").strip()
    if not body:
        return "(no body)"
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    t = lines[0][:120]
    return t + ("..." if len(lines[0]) > 120 else "")


def main():
    parser = argparse.ArgumentParser(description="Scan third-party PRs for comments needing replies from BuboTheWise.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", help="Single repo to scan (owner/repo)")
    parser.add_argument("--since-days", type=int, default=14)
    args = parser.parse_args()

    repos = [args.repo] if args.repo else load_repos()

    print(f"📋 PR Comment Monitor — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Monitored repos: {', '.join(repos)}")
    print(f"   Scan window: last {args.since_days} days\n")

    all_actionable = []
    rate_limited = False

    for repo in repos:
        if args.dry_run:
            stdout, stderr, rc = run_cmd(
                ["gh", "api", f"repos/{repo}/pulls?state=open&per_page=1"], timeout=15)
            status = "accessible" if rc == 0 and not stderr.strip() else f"error ({stderr.strip()[:80]})"
            print(f"  {repo}: {status}")
            continue

        result = scan_repo(repo, args.since_days)

        if result.get("rate_limited"):
            rate_limited = True
            print(f"⚠️  {result['repo']}: Rate limited — stopping.")
            break

        if result.get("error"):
            print(f"❌ {result['repo']}: {result['error']}")
            continue

        n = len(result["actionable"])
        total = result.get("total_open", "?")
        if n > 0:
            print(f"🔍 {result['repo']}: **{n}** item(s) needing response ({total} open PRs)")
            all_actionable.extend(result["actionable"])
        else:
            print(f"✅ {result['repo']}: clean")

    if all_actionable:
        print("\n" + "=" * 60)
        print("ACTIONABLE ITEMS\n")
        for i, item in enumerate(all_actionable, 1):
            print(f"--- #{i} ---")
            print(f"**Repo:** {item['repo']} PR #{item['pr_number']}")
            print(f"**Commenter:** @{item['commenter']} ({item['date'][:10]})")
            print(f"**Link:** {item['html_url']}")
            print(f"**Context:** {item['body']}")
            if item.get('is_review'):
                print("**Type:** Review comment (code feedback)")
            print()
            print("*Run with --generate-drafts to produce AI reply drafts.*")
            print()
    else:
        print("\n" + "=" * 60)
        print("✅ No comments needing response across all monitored repos.")

    return 1 if rate_limited else 0


if __name__ == "__main__":
    sys.exit(main())
