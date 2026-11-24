---
name: pr-comment-monitor
description: 'Monitor open third-party PRs for comments needing professional replies from BuboTheWise.'
version: 0.1.0
author: BuboTheWise
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, github, pr-management, cron, third-party]
---

# PR Comment Monitor — Requirements & Architecture

Scan third-party open PRs for review comments needing a professional reply from BuboTheWise. **No auto-posting** — always present drafts for human review.

## Problem Statement

We contribute to third-party open-source repos (mainly `ollama/ollama`, `huggingface/transformers`). Open PRs accumulate review comments that need our responses. Without monitoring, slow replies risk PR churn or stale conversations.

## Scope

| In scope | Out of scope |
|----------|-------------|
| Scan open PRs in configured third-party repos | Monitoring internal/org repos |
| Detect actionable comments needing reply | Auto-posting any comment |
| Generate professional draft replies | Code modification or PR submission |
| Daily cron delivery to origin chat | Real-time / push notifications |

## Architecture

### File layout

```
pr-comment-monitor/
├── SKILL.md              # This file — spec + usage docs
├── config/
│   └── repos.json        # Configurable repo list (user-editable)
└── scripts/
    └── pr_monitor.py     # Scan logic + draft generation (Python 3.9+)
```

### Config: `config/repos.json`

User-defined array of repos to monitor. Added/removed without code changes.

```json
{
  "repos": ["ollama/ollama", "huggingface/transformers"]
}
```

Each entry is an `"owner/repo"` string — the format accepted by `gh pr list --repo` and `gh api`.

### Scan Logic: `scripts/pr_monitor.py`

See **Scan Algorithm** below for detailed design. Key behaviors:

1. **Iterate configured repos** → fetch open PRs via `gh pr list --state open -L 100` (cap at 100 per repo to bound time).
2. **For each PR**, fetch review comments via `gh api repos/{owner}/{repo}/pulls/{num}/comments`.
3. **Score each comment** for actionability using pattern-based heuristics (see scoring table).
4. **Generate draft reply** via LLM when `--generate-drafts` is used (cron path).
5. **Output structured markdown to stdout** — scannable, no disk writes.

### Actionable Comment Scoring

| Signal | Weight | Examples |
|--------|--------|----------|
| Question patterns (`how does`, `why did`, `could you`…) | Immediate → actionable | "How does this handle X?" |
| Design rationale (`rationale`, `motivation`, `why choose`) | Immediate → actionable | "What's the motivation for this choice?" |
| Imperative suggestions (`change`, `fix`, `add`, `remove`, `rename`…) | Score ≥ 1.0 | "Could you also fix…" |
| Soft suggestions (`consider`, `might want`, `would be better`) | Weight 0.5 each, threshold ≥ 1.0 | "I think you might also consider…" |
| `/cc @BuboTheWise` mentions | Immediate → actionable | Direct mention |

**Skip (non-actionable):**
- Our own accounts (see `skip_authors` in config)
- Empty body text
- Stale comments (>14 days, configurable via `--since-days`)
- Pure nits (`nit:`, `typo`, `formatting issue`)
- Pure praise ("Great work!", "LGTM")
- CI-only notifications

### Output Format

```markdown
## [org/repo #N] PR_TITLE
- Commenter: @username (YYYY-MM-DD)
- Context: <first line of comment body, truncated to 120 chars>
- Draft: <LLM-generated professional reply>
- Action needed: Approve/modify/post | Dismiss
```

### CLI Interface

| Flag | Purpose | Default |
|------|---------|---------|
| `--dry-run` | Check repo API accessibility without scanning | Off |
| `--repo OWNER/REPO` | Scan only one repo | All configured |
| `--since-days N` | Scan window for comment age | 14 days |
| `--generate-drafts` | Include LLM-generated reply drafts | Off (cron uses this) |

## Cron Job — Daily at 04:00 PST

**Schedule:** `0 4 * * *` in `America/Los_Angeles` timezone.

**Skills loaded:** `pr-comment-monitor`, `github`

**Behavior:**
1. Run `pr_monitor.py --generate-drafts` against all configured repos.
2. Deliver structured output to origin chat (user).
3. **Never auto-post** — human reviews and posts manually.
4. Handle failures gracefully: if `gh auth` fails or API rate-limits, report status per repo.

### Cron Configuration (Hermes scheduled job)

**Job ID:** `445dfd404e68` | **Schedule:** `0 4 * * *` America/Los_Angeles

The Hermes cron job is the primary deployment mechanism. Configured via:

```yaml
name: pr-comment-monitor-daily
schedule: "0 4 * * *"
timezone: America/Los_Angeles
skills: [pr-comment-monitor, github]
prompt: |
  Run the PR comment monitor skill. Execute: python3 stable/pr-comment-monitor/scripts/pr_monitor.py --generate-drafts
  
  Report findings: actionable comments across monitored repos with drafted replies. If no items need response, report "No comments needing response." Report any errors (API rate limits, auth issues) prominently.
```

For alternative cron systems (systemd timer, GitHub Actions), the same YAML config applies — update the script path to match your skill installation location.

## OPSEC Notes

- All operations via `gh` CLI with existing BuboTheWise credentials (no token exposure).
- No personal identifiers in output — "BuboTheWise" is the team identity.
- Drafts are **templates only** — never auto-posted; always human-reviewed.
- If `gh auth` status check fails, the cron job halts immediately (no silent failure).

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Configurable repo list | Yes, `config/repos.json`, no code changes needed |
| Scan time for ~50 repos | < 5 minutes |
| Actionable detection recall | Zero false negatives on comments < 7 days old |
| Output quality | Structured markdown, scannable, no fabricated claims |
| Cron resilience | Survives `gh auth` refreshes + API rate limits per repo |

## Testing Checklist

- [ ] `python3 scripts/pr_monitor.py --dry-run` — verify repo API accessibility
- [ ] `python3 scripts/pr_monitor.py --repo ollama/ollama` — verify comment parsing on a known active repo
- [ ] Cron YAML valid: `hermes cron list` shows job at 04:00 PST
- [ ] Rate-limit behavior verified: script reports and skips, does not crash

## Design Decisions

1. **Pattern-based scoring over pure LLM classification.** The scan must complete in bounded time even for repos with thousands of PRs. Heuristic scoring handles the bulk; LLM is only used for draft generation on the small set of actionable items (~0-10 per run).
2. **`gh` CLI over REST library.** We already have `gh` auth configured and rate-limit handling. A Python `requests` call would need separate token management.
3. **No state persistence between runs.** Each cron tick is independent — no last-seen cursor. This avoids stale state issues but means each run re-scans the full window. Acceptable for daily cadence.
4. **100 PR cap per repo.** Bounding scan time; if a repo has more than 100 open PRs, the most recent ones (default `gh pr list` order) are prioritized.
