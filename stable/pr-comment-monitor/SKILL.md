---
name: pr-comment-monitor
description: 'Monitor open third-party PRs for comments needing professional replies from BuboTheWise.'
version: 0.1.0
author: nyarlathotep
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, github, pr-management]
---

# PR Comment Monitor

Scan third-party open-source repositories for review comments that need a professional reply from BuboTheWise. Helps maintain responsiveness without embarrassing auto-replies.

## When to use

- Before daily standup to know what PR feedback needs attention
- As the daily 04:00 PST cron job (see cron config below)
- Any time you want a quick status of pending PR interactions

## Usage

```bash
# Full scan (all configured repos, last 14 days)
python3 stable/pr-comment-monitor/scripts/pr_monitor.py

# Dry run — shows what would be found without generating drafts
python3 stable/pr-comment-monitor/scripts/pr_monitor.py --dry-run

# Scan specific repo only
python3 stable/pr-comment-monitor/scripts/pr_monitor.py --repo ollama/ollama

# Change scan window (default 14 days)
python3 stable/pr-comment-monitor/scripts/pr_monitor.py --since-days 7
```

## Configuration

Edit `config/repos.json` to add/remove repos. Only add repos where you actively contribute and have review comments to track.

```json
{
  "repos": [
    "ollama/ollama",
    "huggingface/transformers"
  ],
  "_note": "Add more repos as needed. Keep only repos where we have active PRs."
}
```

## Scan behavior

- **Monitors:** Open PRs in configured third-party repos
- **Looks for:** Questions, design rationale requests, change suggestions, and action items directed at us
- **Skips:** Our own comments, pure nits/typos, stale comments (>14 days), merge conflict notices, CI failures unrelated to code changes
- **Does NOT auto-post:** All output is drafted for human review only

## Cron job setup (04:00 PST daily)

Add a cron job via the hermes agent:

```yaml
name: pr-comment-monitor-daily
schedule: "0 4 * * *"
timezone: America/Los_Angeles
skills: [pr-comment-monitor, github]
command: python3 stable/pr-comment-monitor/scripts/pr_monitor.py
output: deliver_to_origin_chat
```

The cron output will be structured markdown with actionable items per repo. Review drafts and manually post responses when appropriate.

## Safety constraints

- **Never auto-post comments.** Always present drafts for human review.
- **Respect API rate limits.** Skip repos that hit rate limits, report in output.
- **No code modification.** This skill only reads PRs and generates reply drafts.
- **OPSEC-clean.** Config contains org/repo pairs only — no credentials, handles, or private identifiers.

## Architecture

```
stable/pr-comment-monitor/
  SKILL.md                  # This file
  scripts/
    pr_monitor.py           # Core scanning logic (Python)
  config/
    repos.json              # Configurable repo list
```

The Python script uses the `gh` CLI exclusively — no direct API calls that could expose credentials. All operations run under existing BuboTheWise GitHub auth.
