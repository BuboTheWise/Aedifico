---
name: memchorus-maintenance
description: 'Standard procedure for reinstalling MemChorus, QA testing, and verifying memory injection.'
version: 0.1.0
author: BuboTheWise
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maintenance, qa, memchorus, verification]
---

# MemChorus Maintenance Skill

Standard procedure for reinstalling MemChorus from the source repo, running the QA test harness, and verifying that context injection is working correctly across agent profiles.

## Prerequisites
- `gh` CLI authenticated with BuboTheWise credentials.
- Access to the Hermes Kanban board to log results or create tasks if tests fail.

## Installation Steps
1. **Remove current install:** 
   ```bash
   pip uninstall memchorus -y
   ```
2. **Install fresh from GitHub:**
   ```bash
   pip install memchorus@github.com/BuboTheWise/MemChorus
   ```
3. **Verify version:**
   ```bash
   pip show memchorus
   ```

## QA Testing Steps
1. **Run the Natural-Language Test Harness:**
   - Use the test prompt or script located in the MemChorus project root. 
   - This exercises installed features end-to-end to verify functional correctness (e.g., Wings, Rooms, Tunnels, and Memory API interactions).
2. **Verify Functional Output:**
   - Confirm that the system responds correctly to natural language queries regarding agent coordination, memory state, and cross-profile operations.

## The "Sanka" Check (Memory Injection Verification)
This is the critical step to ensure agents are starting every session with the right context:
1. **Explicitly ask yourself:** Did my active memory/context for this turn include:
   - This maintenance procedure's steps?
   - The specific status of any ongoing MemChorus QA cycles?
   - Relevant cross-session context regarding our project architecture (e.g., current MemPalace issues, PR monitor status)?
2. **Fail Condition:** If these items are NOT present, the injection has failed. 
3. **Action:** Create a GitHub issue against the MemChorus repo labeled `qa-fail` detailing the missing context and re-run this procedure immediately.

## Logging & Reporting
- Log results (pass/fail, version installed, specific tests run) to the originating Cron Job or Kanban task.
- If any functional or memory injection failures are found:
  - Decompose into atomic Kanban tasks for @bubo or @cthugha.
  - Create a high-priority maintenance task on our shared board titled "MemChorus Update + Re-verify QA".
