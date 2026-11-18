---
name: team-dev-process
description: "Use for team dev tasks: atomic cards, spec-first, QA gate."
version: 0.1.7
author: BuboTheWise, Hermes Agent
metadata:
  hermes:
    tags: [development, workflow, kanban, qa, collaboration]
    related_skills:
      - requesting-code-review
      - github
---

# Team Dev Process

Canonical process for development work across Hermes profiles (Cthugha, Bubo; Nyarlathotep on standby). Applies to every project, no special paths. Where a project spec says otherwise on *what* to build, the spec wins; this process governs *how* work gets assigned, done, reviewed, and merged.

**Canonical shared copy:** the Toolbox repo, `stable/development-process/SKILL.md` (repo is the governing copy; vault docs are historical source). Project-specific gates (e.g. Polygraph's full-battery-green requirement) live in the project's spec, not in the shared standard — a shared standard with project special cases is a pitfall, not a rule.

## Roles & Priority (user-directed)

- **Development priority: Cthugha (first, if available) → Bubo (fallback) → Nyarlathotep (standby).**
- **Parallel work-share:** when BOTH Cthugha and Bubo are online, split work between them — the board is consumed in parallel, not queued one agent at a time. Priority order applies only when an agent is unavailable (a card is routed down the chain), never as a reason to hold work while another agent could take it.
- **Hard availability requirement:** the system must not stop working when Cthugha is unavailable — Cthugha's model backend goes offline some nights (user turns off ollama). Bubo and Ny must each complete the full card set end-to-end with **no dependency on Cthugha being reachable.**
- **Coordinator / orchestrator: Nyarlathotep** (local, most available — routes work, authors atomic cards, and manages the board; the fallback coordinator when Cthugha and Bubo are both offline). The user loads work; the coordinator turns it into atomic cards and routes them in the development-priority order above. A small model never self-assigns a card it would also self-review.
- **QA is task-separated, not agent-separated.** QA is always a **separate new task in a fresh context, never concurrent with development.** The same agent that implemented may perform its own QA, on that basis.
- **GitHub ops (push/PR/merge):** designated repo operator, as `BuboTheWise` account, always — never a personal identity on public repos. **Everyone uses the `gh` CLI (export GH_TOKEN) for GitHub interaction, not raw curl** — claiming, commenting, pushing, PRs, merges.

## The Board

- **GitHub Issues per project repo** are the board — no separate tooling (a second board surface drifts out of sync).
- States as labels: `ready → in-progress → qa → review → done`.
- **Claim protocol:** a card enters `in-progress` only when an agent acks it (acknowledgment of understanding, before implementation). One owner at a time; named owner always.
- Flow: creator writes the card → executor implements → creator (or partner) reviews → proof pasted → merge. This is what makes "load a bunch of work and collaborate independently" safe.

## Card Discipline

**Card types (stated on the card):**
- `RUN` — execute the existing code, report findings (pass/fail/breakage) as findings. **No edits.**
- `FIX` — named changes to named files, nothing else.
- `spec:` — spec/requirements change; must merge before dev cards that depend on it.
- **Unclear = RUN.** This is the rule that prevents scope drift on small models.

**Atomicity test (checkable):** a card is atomic only if the **weakest model on the team** can complete it verbatim from its four elements — Objective, Success Criteria, Required Testing, Verification Steps — with **zero unstated context or judgment calls**. If it needs a tradeoff decision, it is not atomic: split it, or route it to the stronger model. Test phrasing: "could the smallest model do this card from the text alone?"

**Spec-first gate:** any new feature or behavior change starts as a `spec:` card that merges on its own. Dev cards cite their spec card. See [development-process](../../development-process/SKILL.md) for detailed development standard, quality gates, and git discipline. "Read the current specs" is one step short of "specs updated and merged before dev starts" — the latter is the gate.

**QA is discrete:** QA / stress / verification is its own card, run as a separate new task in a fresh context (same agent allowed, per Roles) — never concurrent with, or rolled into, the implementation. "Done" requires pasted real output covering the claimed scope — a full test suite green where the project defines one, never a single test on a non-deterministic model.

**Stop-and-report:** unexpected outcome, or a fix outside the card's named scope → STOP and file it as a finding. The fix becomes a NEW card (usually `FIX`, sometimes `spec:`) — it is never a side quest inside the current card.

## Branch Hygiene

- Every card ends in exactly one of: **merged to main**, or **parked as a named, tracked open PR**.
- No uncommitted working-tree changes at end of a session; no orphaned local branches that exist in no issue or PR.
- Commit + push as work progresses on a feature branch (`feature/<task>` / `fix/<issue>-<desc>`); delete the branch after merge — never before review.
- Public artifacts carry team identity only: no personal names, no hostnames, no absolute home paths.

## Templates

The following templates are part of team-dev-process:

### Card Chain Bodies

See [`templates/card-chain-bodies.md`](templates/card-chain-bodies.md) for pre-authored card body templates that encode the atomicity test, four elements (Objective, Success Criteria, Required Testing, Verification Steps), and spec-first gate. Use these templates to author new cards without reinventing the pattern each time. The templates embody the team's collective knowledge of what makes a good atomic card on this project.

## Pitfalls

- **Verify state on disk, not in chat.** After any DM / stop / hold order to a bot agent, confirm with `git status` + file mtime before reporting state. A queued ack is not execution; an in-flight turn continues past a stop order.
- **Symlink is not a hardlink.** Before claiming "synced to all profiles," check the inode of EVERY profile path. Same file reached by two symlinks is one file; a different inode is a different file that changes did not reach. Check all cases before concluding.
- **One test is not a battery.** "🎉 PASSED" from a single test on a non-deterministic model is a finding, not a verdict. Scope of claim must match scope of evidence.
- **Small models need scope fences, not trust.** Scope drift shows up as edits during a RUN card or provider/config logic added while "fixing" a runtime issue. The card type on the card IS the fence — if the card doesn't say `FIX`, there are no edits.
- **No development before process alignment.** If the user has paused development pending process agreement, hold state is: baseline commit, clean tree, nothing queued. Confirm the freeze with a status check, not just a DM.
