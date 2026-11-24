---
name: memchorus-pr-collab
description: 'General-purpose work intake and PR responsiveness workflow — detect bugs, file issues, track via kanban, handle PRs professionally.'
version: 1.0.0
author: BuboTheWise
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [work-intake, pr-management, issue-tracking, responsiveness, workflow-orchestration]
---

# Work Intake & PR Responsiveness — Workflow Orchestrator

Scan deployed systems for bugs/gaps, file issues + kanban tasks to track them, and handle open PRs with professional responsibility. **General-purpose skill** — not tied to any specific project.

## Problem Statement

Bugs and gaps in deployed systems accumulate without tracking. Review comments on our open PRs go unanswered for days, risking churn or stale conversations. The daily cron that was supposed to handle this (`nyarlathotep-memchorus-pr-collab`) was missing critical safeguards: blind merges of unreviewed code, duplicate task creation, no issue dedup, and broken external PR search filters. This skill fixes all of those patterns.

## Scope

| In scope | Out of scope |
|----------|-------------|
| Detect bugs/gaps in deployed systems (code-level) | Data quality / audit-only findings that need migration tools |
| File GitHub issues + create kanban tasks to track code bugs | Auto-merging or force-pushing anyone else's PRs |
| Monitor open PRs we care about; respond professionally | Real-time / push notifications |
| Verify before taking any action (QA, review, test) | Auto-posting comments without LLM drafting and human review |
| Collision detection — only one instance runs at a time | Running this as a background daemon |

## Architecture

### File layout

```
memchorus-pr-collab/
├── SKILL.md               # This file — spec + usage docs
├── config/
│   ├── monitored_repos.json  # PRs to monitor (user-editable)
│   └── internal_repos.json   # Internal repos for work intake scanning
└── scripts/
    └── work_intake.py      # Core workflow orchestrator (Python 3.9+)
```

### Config: `config/monitored_repos.json`

List of external/internal repos whose open PRs we monitor and need to respond to.

```json
{
  "internal": [
    "BuboTheWise/MemChorus",
    "BuboTheWise/MemPalace",
    "BuboTheWise/Toolbox"
  ],
  "external": [
    "ollama/ollama",
    "huggingface/transformers"
  ]
}
```

### Config: `config/internal_repos.json`

Repos to scan for bugs/gaps during work intake. Each repo must be cloneable locally or accessible via `gh`.

```json
{
  "repos": [
    {
      "name": "MemChorus",
      "url": "github.com/BuboTheWise/MemChorus",
      "local_path": "~/Projects/MemChorus/",
      "deploy_check": "pip show memchorus"
    }
  ]
}
```

### Core Workflow: `scripts/work_intake.py`

The workflow orchestrates three phases in sequence. Each phase has a gate that must pass before the next proceeds. If any gate fails, report and stop — do not proceed blindly.

**Phase 1 — Work Intake (detect bugs → file issues + kanban tasks)**
```
1. Check kanban: Are there active dev tasks for this repo?
   - If running/ready: STOP. Report status. Do not proceed.
2. Scan deployed system for bugs/gaps:
   - Version comparison (deployed vs HEAD)
   - Config validation
   - Data quality checks (if applicable)
   - Runtime behavior tests
3. For EACH distinct finding:
   a) Check existing open issues: `gh issue list --repo <repo> --state open`
      → SKIP if already filed (dedup).
   b) Classify: Is this a CODE BUG or AUDIT FINDING?
      - CODE BUG (crash, leak, corruption, broken behavior):
        FILE GITHUB ISSUE + CREATE kanban task
        `gh issue create -R <repo> --title "..." --body "..."`
        `kanban_create(title="[bug] <short-title>", assignee="<dev-profile>", body="<issue-URL + evidence>")`
      - AUDIT FINDING (data quality report, stale entries — no code fix yet):
        FILE GITHUB ISSUE ONLY (no kanban task). Wait for migration tool.
```

**Phase 2 — PR Professional Responsibility**
```
1. For each repo in monitored_repos.json:
   a) List open PRs: `gh pr list --repo <repo> --state open`
   b) For EACH open PR that we own/have opened:
      - Check for new review comments (>24h without response?)
      - If nits/praise/questions → draft professional reply (never auto-post)
      - If bugs/flaws found → decompose into atomic kanban tasks, route to dev
      - DO NOT merge unreviewed PRs — verification gate required:
        * Run relevant tests locally or via CI status check
        * Review actual code changes diff
        * Only then suggest merge (human confirms)
```

**Phase 3 — Impact Triage (only if Phases 1-2 are clear)**
```
1. Scan open issues in monitored repos for those affecting our core architecture
2. Pick highest-impact issue → decompose into atomic tasks → standard dev cycle
3. ALWAYS apply Contributing-Guidelines Gate before opening any external PR:
   - Fetch CONTRIBUTING.md first (gh api)
   - Match their conventions exactly
   - Pass ALL local CI checks BEFORE opening
   - Document in PR body how each requirement was satisfied
```

### Collision Detection

Only one instance of this workflow may run at a time. The script maintains a lock file:

```python
LOCK_FILE = Path(__file__).parent / "workflow.lock"
# Lock validity: 12 hours (covers deep investigation loops + dev cycles)
```

If a lock exists and is <12h old, **STOP immediately** — another instance is running. This is non-negotiable.

### Output Format

Structured markdown to stdout:

```markdown
=== WORK INTAKE REPORT ===
Deployed: VERSION / HEAD: SHORT_HASH (+N commits)
Bugs found: X | Audit findings: Y
GH filed: #ID,#ID (dedup checked: yes/no)
Kanban tasks created: t_<id>,t_<id>

=== PR STATUS ===
Monitored: N repos, M open PRs
Actionable comments: X
Drafted replies: X | Pending human review: X
Merges suggested: Y (requires human approval)

=== TASK BROADCASTS ===
Tasks created for @<assignee>: [titles]
Next run: Check dev progress → resume workflow if blocked tasks completed
```

## Cron Job — Daily at 04:00 PST

**Schedule:** `0 4 * * *` in `America/Los_Angeles` timezone.

**Skills loaded:** `github`, `team-dev-process`

**Behavior:**
1. Lock check → if locked, report and exit (no duplicate runs)
2. Run work_intake.py with all phases
3. Deliver structured output to origin chat
4. **Never auto-post or auto-merge** — human reviews all outputs
5. Handle failures gracefully: report status per repo

### Cron Configuration Template (Hermes scheduled job)

```yaml
name: <agent>-work-intake-pr-responsiveness
schedule: "0 4 * * *"
timezone: America/Los_Angeles
skills: [github, team-dev-process]
prompt: |
  Run the memchorus-pr-collab work intake and PR responsiveness workflow.
  Execute: python3 stable/memchorus-pr-collab/scripts/work_intake.py
  
  Report all findings as structured output (see SKILL.md output format).
  If gh auth fails or API rate-limits, report status per repo.
  NEVER auto-merge any PR — present suggestions for human approval.
```

## OPSEC Notes

- All operations via `gh` CLI with existing credentials (no token exposure)
- No personal identifiers in output — "BuboTheWise" is the team identity
- Drafts are **templates only** — never auto-posted; always human-reviewed
- Never auto-merge PRs — present suggestions for human approval
- If `gh auth` status check fails, halt immediately (no silent failure)
- Collision lock is hard: another cron may be mid-investigation

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Configurable repo lists | Yes, via config JSON files — no code changes needed |
| Issue dedup check | Every finding checked against existing open issues before filing |
| Bug vs audit classification | Clear decision criteria provided (crash/leak/corruption = bug) |
| Zero blind merges | All PR suggestions require human approval, verified before suggestion |
| Collision detection | Hard lock file with 12h TTL — one instance max |
| Cron resilience | Survives `gh auth` refreshes + API rate limits per repo |

## Testing Checklist

- [ ] Verify config JSON files are valid and contain desired repos
- [ ] `python3 scripts/work_intake.py --dry-run` — verify repo API accessibility
- [ ] Cron YAML valid: `hermes cron list` shows job at scheduled time
- [ ] Rate-limit behavior verified: script reports and skips, does not crash

## Design Decisions

1. **Work intake must distinguish bugs from audit findings.** Code-level bugs get issues + kanban tasks; data quality reports get issues only. This prevents task spam for things that aren't fixable yet.
2. **Issue dedup is mandatory.** Every finding checks existing open issues before filing. Without this, the same bug gets filed daily across cron runs.
3. **No blind merges under any circumstances.** Verification gate (tests + diff review) required before suggesting a merge. The previous cron violated this and would squash-merge unreviewed PRs into main repos.
4. **Collision lock covers investigation depth, not just execution time.** A 12h window allows for deep bug investigation spanning dev cycles, not just a quick scan.
5. **This skill is project-agnostic.** The config files define what to monitor and scan — the script logic stays the same regardless of which repos are listed.
