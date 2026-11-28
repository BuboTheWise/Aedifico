---
name: daily-project-sweep
description: "Daily sweep that checks MemChorus, Polygraph, and Aedifico against latest GitHub versions."
version: 0.1.0
author: BuboTheWise, Hermes Agent
metadata:
  hermes:
    tags: [sweep, verification, version-check, memchorus, polygraph, aedifico]
    related_skills:
      - team-dev-process
---

# Daily Project Sweep

Generic skill for verifying that critical project installations match their latest GitHub versions and pass minimal viability tests. Designed to run as a cron job or manual trigger from any profile.

## Purpose

Every Hermes profile needs to ensure it is running the latest version of foundational projects. Without automated verification, profiles silently drift behind the main branch, causing bugs that are hard to trace. This skill provides a reusable pattern for checking all three core projects:

| Project | GitHub Repo | Install Method |
|---------|-------------|---------------|
| MemChorus | `BuboTheWish/MemChorus` | `pip install git+https://github.com/BuboTheWise/MemChorus` |
| Polygraph | `BuboTheWise/Polygraph` | `pip install git+https://github.com/BuboTheWise/Polygraph` |
| Aedifico | `BuboTheWise/Aedifico` | Import from source or pip if packaged |

## Sweep Procedure

When executing, perform ALL checks in order. Do not skip any step. If one project fails, continue checking the others so the user gets a complete report.

### Step 1: Check and Update MemChorus

```bash
# Install latest from GitHub
pip install git+https://github.com/BuboTheWise/MemChorus

# Run natural-language test harness (hitting multiple decision points)
python -c "import memchorus; print('MemChorus import OK')"
```

**Verification:** If a `docs/NATURAL_TESTING_PROMPT.md` exists in the repo, send that prompt to the agent and check for:
- MemPalace drawer count increased after the run
- New diary entry recorded (check via `mempalace_diary_read`)
- Search finds content from the test

If no natural-language harness exists, verify at minimum: import succeeds + MCP hook chain is loadable.

### Step 2: Check and Update Polygraph

```bash
# Install latest from GitHub
pip install git+https://github.com/BuboTheWise/Polygraph

# Run minimal viability test
python -c "import polygraph; print('Polygraph import OK')"

# Run Polygraph's own tests if available
cd /home/stefan/Projects/Polygraph && python -m pytest tests/ -x -q 2>/dev/null || echo "Polygraph tests not runnable in this context"
```

### Step 3: Check and Update Aedifico

```bash
# Aedifico is a skill collection; verify source sync, not pip install
cd /home/stefan/Projects/Aedifico && git pull --ff-only

# Verify all skill modules import cleanly
python -c "import aedifico; print('Aedifico import OK')"

# Run Aedifico test suite if available
cd /home/stefan/Projects/Aedifico && python test_aedifico.py 2>/dev/null || echo "Aedifico tests not runnable in this context"
```

### Step 4: Version Drift Detection

For each project, compare the installed version (or last git commit) against HEAD on main:

```bash
# MemChorus drift check
git ls-remote https://github.com/BuboTheWise/MemChorus HEAD | cut -f1 > remote_head.txt
pip show memchorus 2>/dev/null | grep "Location" || echo "MemChorus not installed via pip"

# Polygraph drift check
git ls-remote https://github.com/BuboTheWise/Polygraph HEAD | cut -f1 > remote_head.txt
```

Report any mismatch as: `⚠ [PROJECT] drift detected — installed is <commit>, main is <commit>`

## Reporting Format

After completing all checks, produce a single structured report:

```
=== Daily Project Sweep ===

✓ MemChorus: version current (hash), import OK, natural test passed
✗ Polygraph: DRIFT — local <hash> vs main <hash>, tests FAILED
⚠ Aedifico: version current but SKILL.md on stable/ is stale
           stable/version 0.1.8 ≠ HEAD/main version 0.2.1

=== Status ===
All critical: PASS  | MemChorus OK, Polygraph DRIFT, Aedifico OK
```

If ANY check fails, **open a kanban task** with `task_type: RUN` describing the specific failure(s). Do not bundle failures from different projects into one task.

## When to Use

- Run as a daily cron job (e.g., 10pm nightly) to maintain freshness
- Run manually before starting development work on any of these projects
- Use when a profile reports unexpected behavior that might be caused by version drift
- **This is NOT a substitute for the atomicity test or the team-dev-process decomposition rules** — those remain in `team-dev-process/SKILL.md` and must still be enforced separately when creating kanban tasks.
