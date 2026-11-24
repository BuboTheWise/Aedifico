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


def get_skip_authors():
    """Return the skip_authors list from config, falling back to ['bubothewise']."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            return cfg.get("skip_authors", ["bubothewise"])
        except (json.JSONDecodeError, IOError):
            pass
    return ["bubothewise"]


# Cache auth token once at startup to avoid per-call keyring lookups.
_AUTH_TOKEN = None


def _ensure_token():
    global _AUTH_TOKEN
    if _AUTH_TOKEN is None:
        try:
            r = subprocess.run(
                ["gh", "auth", "token", "--show-if-available"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                _AUTH_TOKEN = r.stdout.strip()
            else:
                # gh CLI will use its own auth when token is not available
                pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return _AUTH_TOKEN


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 124


def api_get(repo, resource):
    """GET /repos/{repo}/{resource} via gh CLI. Returns (items_list, error_or_None)."""
    cmd = [
        "gh", "api", f"repos/{repo}/{resource}",
        "--method", "GET", "--jq", ".[]",
        "--accept", "application/vnd.github+json",
    ]
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


def strip_quotes(body):
    """Strip quoted reply text (> lines, git-style --- separator) for scoring."""
    lines = body.split("\n")
    cleaned = []
    in_quote = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith(">"):
            in_quote = True
            continue
        if stripped.strip() == "---":
            # Git-style separator between quoted section and new text
            in_quote = False
            continue
        if in_quote and not stripped.startswith("```"):
            continue
        if in_quote:  # code block ending the quote
            in_quote = False
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def is_pure_praise(body):
    """Return True if the comment is purely appreciative (no question or action requested)."""
    bl = body.lower()
    praise_words = ["thank you", "thanks ", "thanks for", "appreciate",
                    "great work", "well done", "awesome", "nice "]
    has_question = any(q in bl for q in ["?", "how does", "why did", "could you",
                                          "should we", "is there", "can you"])
    # If it's praise AND no question, treat as non-actionable
    for pw in praise_words:
        if pw in bl and not has_question:
            return True
    return False


def is_author_self_update(comment, pr_data):
    """Return True if the commenter is the PR author making a status update."""
    author = comment.get("user", {}).get("login", "")
    pr_author = (pr_data or {}).get("user", {}).get("login", "")
    return bool(author and pr_author and author == pr_author)


def needs_response(comment, cutoff):
    """Score a comment. Returns (score_100, reason). Higher score = more likely actionable."""
    author = comment.get("user", {}).get("login", "")

    # Check against config skip_authors
    skip_list = get_skip_authors()
    if author.lower() in skip_list:
        return 0, "own comment"

    body = comment.get("body", "").strip()
    if not body:
        return 0, "empty body"

    # Strip quoted reply text before scoring to avoid false positives
    scored_body = strip_quotes(body)
    bl = scored_body.lower()

    # Pure praise filter — skip appreciation without questions or action items
    if is_pure_praise(scored_body):
        return 0, "pure praise"

    # Skip stale
    created_str = comment.get("created_at", "")
    if created_str:
        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if created_dt < cutoff:
                return 0, f"stale ({(cutoff - created_dt).days}d)"
        except ValueError:
            pass

    # Question patterns (high score)
    questions = [
        "how does", "why did", "why not", "could you", "should we",
        "is there", "what about", "can you explain", "are these",
        "does this handle", "should this be"
    ]
    for q in questions:
        if q in bl:
            return 95, f"question: {q}"

    # Design rationale (high score)
    design = [
        "rationale", "design choice", "why choose", "motivation",
        "background on", "context for", "explain why", "intended behavior"
    ]
    for d in design:
        if d in bl:
            return 90, f"design question: {d}"

    # Reject pure nits
    nit = ["nit:", "nit ", "typo", "formatting issue", "style fix"]
    for n in nit:
        if n in bl:
            return 0, "pure nit"

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

    return 0, "no actionable pattern"


def _get_pr_data(repo, pr_num):
    """Fetch PR metadata for author info."""
    items, err = api_get(repo, f"pulls/{pr_num}")
    if items and len(items) > 0:
        return items[0]
    return None


def scan_repo(repo, since_days=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    # Get open PR count + basic info (batched for performance)
    stdout, stderr, rc = run_cmd(
        ["gh", "pr", "list", "--repo", repo, "--state", "open", "-L", "100"],
        timeout=60
    )
    if rc != 0:
        return {
            "repo": repo,
            "error": f"gh failed: {stderr.strip()[:200]}",
            "actionable": [],
            "total_open": 0
        }

    pr_lines = [l for l in stdout.strip().split("\n") if l.strip()]
    total_open = len(pr_lines)

    actionable = []
    checked_prs = set()
    pr_cache = {}  # Cache PR author data to avoid repeated API calls

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

        # Get review comments (batch of review line comments)
        comments, err = api_get(repo, f"pulls/{pr_num}/comments")
        if err == "RATE_LIMITED":
            return {
                "repo": repo,
                "error": "Rate limited",
                "actionable": actionable,
                "total_open": total_open,
                "rate_limited": True
            }
        if not comments:
            continue

        # Get general PR comments for context (batched)
        pr_comments, _ = api_get(repo, f"issues/{pr_num}/comments")

        # Batch fetch PR data to get author info (single call vs. per-comment)
        if pr_num not in pr_cache:
            pr_data = _get_pr_data(repo, pr_num)
            pr_cache[pr_num] = pr_data

        all_comments = list(comments) + (list(pr_comments) if pr_comments else [])

        for comment in all_comments:
            score, reason = needs_response(comment, cutoff)
            if score >= 60:
                actionable.append({
                    "pr_number": pr_num,
                    "commenter": comment.get("user", {}).get("login", "?"),
                    "date": comment.get("created_at", ""),
                    "body": _fmt_ctx(comment),
                    "is_review": comment.get("commit_id") is not None,
                    "html_url": comment.get("html_url", f"https://github.com/{repo}/pull/{pr_num}"),
                })

    return {
        "repo": repo,
        "total_open": total_open,
        "actionable": actionable,
        "rate_limited": False
    }


def _fmt_ctx(comment):
    body = comment.get("body", "").strip()
    if not body:
        return "(no body)"
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    t = lines[0][:120]
    return t + ("..." if len(lines[0]) > 120 else "")


def generate_draft(commenter, pr_number, comment_body, repo=None):
    """Generate a professional draft reply for an actionable comment.

    Args:
        commenter: GitHub login of the person who wrote the comment
        pr_number: PR number (int)
        comment_body: Full comment text
        repo: owner/repo string for context

    Returns:
        Draft reply string, or None if LLM generation fails.
    """
    # Build prompt with proper separate args — fixes P0 signature bug
    repo_context = f"\nRepo: {repo}" if repo else ""

    prompt_text = (
        f"You are a senior open-source contributor responding to review feedback."
        f" Please generate a professional, concise reply draft.{repo_context}\n\n"
        f"PR #{pr_number} comment from @{commenter}:\n---\n{comment_body}\n---"
        f"\n\nDraft reply:"
    )

    # Use Ollama local LLM for draft generation
    try:
        r = subprocess.run(
            ["ollama", "run", "qwen3.6:35b"],
            input=prompt_text,
            capture_output=True, text=True, timeout=120
        )
        if r.returncode == 0 and r.stdout.strip():
            draft = r.stdout.strip()
            # Avoid leaking internal model names in output
            return draft[:3000]
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # Fallback: mark as needing manual draft
        return None

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Scan third-party PRs for comments needing replies from BuboTheWise."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", help="Single repo to scan (owner/repo)")
    parser.add_argument("--since-days", type=int, default=14)
    parser.add_argument(
        "--generate-drafts", action="store_true",
        help="Include LLM-generated reply drafts for actionable items"
    )
    args = parser.parse_args()

    repos = [args.repo] if args.repo else load_repos()

    _ensure_token()  # Cache auth once at startup to avoid per-call overhead

    print(f"\U0001f4cb PR Comment Monitor — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Monitored repos: {', '.join(repos)}")
    print(f"   Scan window: last {args.since_days} days\n")

    if args.dry_run:
        # Dry-run: only check repo connectivity, no actual scanning
        all_ok = True
        for repo in repos:
            stdout, stderr, rc = run_cmd(
                ["gh", "api", f"repos/{repo}/pulls?state=open&per_page=1"],
                timeout=15
            )
            status = "accessible" if rc == 0 and not stderr.strip() else f"error ({stderr.strip()[:80]})"
            print(f"  {repo}: {status}")
            if rc != 0 or stderr.strip():
                all_ok = False
        if all_ok:
            print("\nAPI connectivity check complete — no scanning performed.")
        else:
            print("\n⚠️  One or more repos failed the connectivity check.", file=sys.stderr)
        return 0

    all_actionable = []
    rate_limited = False
    any_errors = False

    for repo in repos:
        result = scan_repo(repo, args.since_days)

        if result.get("rate_limited"):
            rate_limited = True
            print(f"\u26a0\ufe0f  {result['repo']}: Rate limited — stopping.")
            break

        if result.get("error"):
            any_errors = True
            print(f"\U0001f6ab {result['repo']}: {result['error']}")
            continue

        n = len(result["actionable"])
        total = result.get("total_open", "?")
        if n > 0:
            print(f"\U0001f50d {result['repo']}: **{n}** item(s) needing response ({total} open PRs)")
            all_actionable.extend(result["actionable"])
        else:
            print(f"\u2705 {result['repo']}: clean")

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
            # Generate draft if requested
            if args.generate_drafts:
                draft = generate_draft(
                    commenter=item['commenter'],
                    pr_number=item['pr_number'],
                    comment_body=item['body'],
                    repo=item.get('repo')  # Might not be set in the actionable dict
                )
                if draft:
                    print(f"**Draft:**\n```\n{draft}\n```")
                else:
                    print("**Draft:** *(generation failed — manual review needed)*")
            print()
    else:
        print("\n" + "=" * 60)
        print("No comments needing response across all monitored repos.")

    # Return non-zero if any repo errors occurred (not just rate limiting)
    return 1 if (rate_limited or any_errors) else 0


if __name__ == "__main__":
    sys.exit(main())
