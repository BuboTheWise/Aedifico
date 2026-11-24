#!/usr/bin/env python3
"""
memchorus-pr-collab Workflow Orchestrator

Handles the daily loop for MemChorus QA, PR Monitoring, and MemPalace Issue triage.
Designed to be called by a Hermes Cron Job (nyarlathotep-memchorus-pr-collab).
"""

import subprocess
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# State file location (shared with the cron job's workspace)
STATE_FILE = Path(__file__).parent / "state.json"
LOCK_FILE = Path(__file__).parent / "workflow.lock"

# Configuration
MEMCHORUS_GIT_URL = "github.com/BuboTheWise/MemChorus"
MONITORED_PR_REPOS = ["ollama/ollama", "huggingface/transformers"]
TARGET_AGENTS = ["bubo", "cthugha"]

class StateManager:
    def __init__(self):
        self.state = {
            "current_phase": "memchorus_qa",
            "last_run": None,
            "issues": [], # List of GH issue numbers being tracked
            "qa_passes": [], # Log of successful QA runs
            "broadcast_sent": False,
            "lock_until": None
        }
        self.load()

    def load(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                self.state = json.load(f)
    
    def save(self):
        self.state["last_run"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def is_locked(self):
        """Check if we are currently running a previous instance of this workflow."""
        if not LOCK_FILE.exists():
            return False
        try:
            with open(LOCK_FILE) as f:
                lock_time = datetime.fromisoformat(f.read())
                # Lock is valid for 12 hours (enough to cover deep loops + dev cycles)
                if (datetime.now(timezone.utc) - lock_time).total_seconds() < 43200:
                    return True
        except: pass
        return False

    def acquire_lock(self):
        with open(LOCK_FILE, "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())

def run_command(cmd, **kwargs):
    """Helper to run CLI commands."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, **kwargs)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed ({cmd}): {e.stderr}")
        return None

def get_open_tasks(status="running", assignee=None):
    """Delegate Kanban checks via the Hermes prompt context."""
    # This function doesn't execute tools directly; it instructs the Agent
    # to perform the check. We print a structured "Agenda Item" instead.
    pass

def main():
    state = StateManager()

    if state.is_locked():
        print(">> WORKFLOW SKIP: Instance is still running (locked). Skipping this tick.")
        return

    state.acquire_lock()
    print(f">> STARTING WORKFLOW (Phase: {state.state['current_phase']}) at {datetime.now(timezone.utc).isoformat()}")

    if state.state['current_phase'] == 'memchorus_qa':
        handle_memchorus_qa(state)
    elif state.state['current_phase'] == 'pr_monitor':
        handle_pr_monitor(state)
    elif state.state['current_phase'] == 'mempalace_triage':
        handle_mempalace_triage(state)
    else:
        print("Unknown phase. Resetting to memchorus_qa.")
        state.state['current_phase'] = 'memchorus_qa'
        state.save()

def handle_memchorus_qa(state):
    """Phase 1: Install, Test, and Verify MemChorus."""
    
    # --- Step 1: Check Kanban for active dev tasks related to MemChorus ---
    print(">> ACTION REQUIRED: Check Kanban board for tasks assigned to @bubo or @cthugha involving 'MemChorus'.")
    print("   - If any are still in 'running' or 'ready': STOP and report status. Do not proceed.")
    print("   - If all MemChorus dev tasks are 'done': Proceed to Step 2.")

    # --- Step 2: Fresh Install from GitHub ---
    print("\n>> ACTION REQUIRED: Execute the following to install fresh MemChorus:")
    print(f"   `pip install memchorus@{MEMCHORUS_GIT_URL}`")
    print("   - Verify version update via `pip show memchorus`.")

    # --- Step 3: Run Test Harness (Natural Language) ---
    print("\n>> ACTION REQUIRED: Execute the MemChorus Test Harness.")
    print("   - Use a natural-language test prompt that exercises installed features end-to-end.")
    print("   - Reference the `QA Harness` documentation found in the MemChorus project root or installed docs.")

    # --- Step 4: Memory Injection Verification (The "Sanka" Check) ---
    print("\n>> MEMORY INJECTION CHECK:")
    print("   Verify that your current context was FORCED by MemChorus to include:")
    print("   - This workflow's status and history.")
    print("   - The specific MemChorus QA testing procedures you should be following.")
    print("   - Relevant cross-session context regarding our project architecture.")
    print("   - If these items are NOT in your active memory, FAIL the test and file an issue.")

    # --- Step 5: Update State ---
    print("\n>> STATE UPDATE:")
    print("   If QA passed and Memory Check passed:")
    print("   - Change state to 'pr_monitor' and save state.json")
    print("   - Report success here so the workflow can proceed.")
    
    # Save lock so we don't loop forever in one turn, but allow resumption
    state.save()

def handle_pr_monitor(state):
    """Phase 2: Monitor external PRs."""
    
    # --- Step 1: Scan Open PRs ---
    print(">> ACTION REQUIRED: Scan for comments on our open PRs in:")
    for repo in MONITORED_PR_REPOS:
        print(f"   - {repo}")
    print("   Use `gh` CLI to list PRs created by us and check recent comments.")

    # --- Step 2: Reply or Decompose ---
    print("\n>> ACTION REQUIRED:")
    print("- For 'Nit' / 'Praise' / 'Question' comments: Draft a professional response with full ownership.")
    print("- For comments indicating bugs/flaws:")
    print("   1. Decompose the fix onto our Kanban board (Atomic Task).")
    print("   2. Wait for @bubo/@cthugha to finish dev/QA/Merge.")
    print("   3. Once merged: Reply professionally on the PR confirming the fix.")

    # --- Step 3: Update State ---
    print("\n>> STATE UPDATE:")
    print("   If all PR comments are handled (or no new actionable items):")
    print("   - Change state to 'mempalace_triage' and save state.json")

def handle_mempalace_triage(state):
    """Phase 3: Triage MemPalace issues."""

    # --- Step 0: Contributing-Guidelines Gate (NEW) ---
    print("\n>> CONTRIBUTING-GUIDELINES GATE:")
    print("   For every PR you open on a third-party repo, you MUST:")
    print("   1. Fetch the repo's CONTRIBUTING.md / CONTRIBUTING.rst (gh api repos/{owner}/{repo}/readme?path=CONTRIBUTING.md)")
    print("   2. Match their conventions exactly: commit style, PR template fields, branch naming.")
    print("   3. Pass ALL their local CI/linting/style checks BEFORE opening the PR — never submit untested work.")
    print("   4. Document in your PR body how you satisfied their contributing requirements (checklist of applied rules).")
    print("   This is non-negotiable: throwing unvetted code over the wall burns political capital and signals carelessness.")

    # --- Step 1: Evaluate Issues ---
    print("\n>> ACTION REQUIRED: Analyze open MemPalace issues.")
    print("   - Filter for issues affecting our architecture (Wings, Rooms, Tunnels, etc.).")
    print("   - Prioritize blocking bugs or architectural misalignments.")

    # --- Step 2: Select and Decompose ---
    print("\n>> ACTION REQUIRED:")
    print("- Select the highest-impact issue.")
    print("- Decompose the work onto our Kanban board using standard development process (Spec -> QA -> Dev -> Merge).")
    print("- Note: We submit PRs, we do not merge 3rd party repos ourselves.")

    # --- Step 3: Finalize ---
    print("\n>> FINALIZE:")
    print("   If a task is created: Set broadcast_sent=false and save state. Next run resumes here to check dev progress.")
    print("   If NO MemPalace issues affect us: Reset cycle (memchorus_qa) and handle broadcasts.")

def check_open_issues(label):
    """Check if any open issues exist with the given label in monitored repos.
    
    Returns dict: {repo: [issue_numbers]} or empty if none found.
    Used to deduplicate before filing new issues/creating tasks.
    """
    from datetime import datetime, timezone, timedelta
    
    results = {}
    now = datetime.now(timezone.utc)
    
    for repo in ["ollama/ollama", "huggingface/transformers", "BuboTheWise/MemPalace"]:
        try:
            # Use gh issue list with label filter; only return issues < 7 days old
            cmd = [
                "gh", "issue", "list",
                "--repo", repo,
                "--state", "open",
                "--label", label,
                "--json", "number,title,created_at",
                "--limit", 10
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                issues = json.loads(result.stdout)
                recent = []
                for issue in issues:
                    created = datetime.fromisoformat(issue["created_at"])
                    if (now - created).days < 7:
                        recent.append(issue["number"])
                if recent:
                    results[repo] = recent
        except Exception as e:
            print(f"  Warning: issue check failed for {repo}: {e}")
    
    return results


def create_broadcast_tasks(state):
    """Phase 4: Notify other agents."""
    
    if state.state.get('broadcast_sent'):
        return

    # Dedup check: are there recent open issues on this?
    dedup = check_open_issues("memchorus-update")
    if dedup:
        repos_str = ", ".join(f"{repo}#{nums}" for repo, nums in dedup.items())
        print(f"\n>> DEDUP: Recent open memchorus-update issues found — {repos_str}")
        print("   No new broadcast tasks needed. Check existing issues first.")
        state.state['broadcast_sent'] = True
        state.save()
        return

    print("\n>> BROADCAST TASKS:")
    for agent in TARGET_AGENTS:
        print(f"   Create Kanban task 'Update MemChorus + Run QA' for @agent.")
        print("   - Include exact pip install command and link to test harness.")
        print("   - Mark as high priority (maintenance).")

    state.state['broadcast_sent'] = True
    state.save()
    print("\nBroadcast tasks created. Cycle complete for this tick.")

if __name__ == "__main__":
    main()
