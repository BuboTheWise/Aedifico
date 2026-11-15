---
name: development-process
description: "Team development standard: phases, gates, git discipline."
version: 0.1.2
author: BuboTheWise, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [development, standards, workflow, quality]
    related_skills:
      - hermes-agent-skill-authoring
      - requesting-code-review
---

# Development Standard (Team)

Canonical development standard for all profiles and all projects. It applies
equally — no project gets special paths or baked-in preferences. Rules below
are imperative and must be followable verbatim by an agent with no local
context. Where a project document says otherwise: project specs win for *what
to build*; this standard wins for *how to build it*.

## When to Use

- Starting, executing, reviewing, or handing off any development task.
- Drafting a task spec, commit, or PR.
- Don't use for: pure research or documentation authoring (vault territory).

## Rule One: Dual-Location Structure

1. Development code and skills live in a git repository. Never in the knowledge vault.
2. Documentation, requirements, decisions, and research live in the vault. Never inside a source tree.
3. Work in a clone. Never edit a live application tree in place.

## Workflow Phases

**Phase 0 — Preparation.** Query the team's shared memory first for the canonical skills and
recent learnings. Read the current specs. Verify git state and versions. Break
work into atomic tasks — one card each, no compound cards — and every card must
carry all four elements: Objective, Success Criteria, Required Testing,
Verification Steps. Assign, and require acknowledgment of understanding before
implementation starts. Completion: scope confirmed by both parties.

**Phases 1–2 — Implement.** Implement only assigned tasks. Write tests for new
code before calling it done. Build must pass. Commit and push immediately
after a green build. Completion: tests green, code pushed.

**Phase 4 — Close.** Documentation current. Repository clean and pushed.
Session lessons filed to memory. Completion: zero uncommitted work.

**Phase 5 — Improve.** After each session, identify 1–3 concrete
improvements. A gap that recurs twice becomes a permanent rule here.
Completion: the rule is written and versioned.

## Quality Gates (hard)

- No uncommitted work at the end of a session. No exceptions.
- No "done" without a real, executed verification. Paste the actual output.
- No fabricated results. A blocker reported honestly beats an invented success.
- Cite before claim. Every factual assertion ties to a tool output or a document.
- Errors are data. Deviations are disclosed immediately and fed back into process.
- Artifacts outrank prose. A claim is only as real as the file, command, or URL behind it.
- QA, stress testing, and verification are discrete steps or cards — never rolled into implementation.
- Every rule and claim carries its own checkable verification, doable from the text alone.

## Git Discipline

### Branching Conventions
- **Base branches:** `main` (default) or `develop` if team uses it.
- **Feature branches:** `feature/<task-name>` e.g. `feature/agent-orchestration`.
- **Fix branches:** `fix/<issue-id>-<short-desc>` e.g. `fix/gh-42-login-timeout`.
- Naming: lowercase, hyphens (no underscores or CamelCase).
- Delete feature branch after merge — never before review.

### Commit Discipline
- Commit format: `feat:`, `fix:`, `test:`, `docs:` followed by a short description.
- One concern per commit. Push immediately after a green build.
- **Git-first rule:** Every meaningful change is committed at the end of its discrete step. No "I'll commit everything at the end."

### Public Artifacts
- Carry the team identity only: no personal names, no machine hostnames, no absolute home paths.

### Issue Flow
- The task creator writes the issue; the executor implements; the creator reviews; proof (real output) before merge.

## Code Review

1. **Who reviews:** The other profile in a task pair OR Bubo as default reviewer for all GitHub ops.
2. **Review scope:** Implementation correctness, test coverage, documentation accuracy, workflow compliance.
3. **No silent approvals:** Reviews must cite specific files/lines with comments — no one-line "looks good" approvals.
4. **GitHub operations:** Only Bubo (or the designated profile) performs `gh` CLI operations (push, PR creation, merge). Implementers provide patches or diffs for review first.

## Handoff and Collaboration

- A handoff is durable: the artifact lands on disk in the target's workspace
  (file, memory entry, issue). Chat is the go-signal, not the handoff.
- State-changing work needs a read-back of the exact target before claiming
  success — a passing tool call is not a verified effect.
- Coordinate before two agents install or edit the same tree.

## Pitfalls

- A rule that sounds nice but isn't actionable ("be careful") — replace with a checkable criterion or cut it.
- Machine-local paths in shared documents — they break for everyone else.
- Project-specific special cases inside a shared standard — put them in the project spec.
- Verifying the tool call instead of the result.
- Accumulating rules without pruning the wording they replace.
- Session-specific language in shared documents ("as we discussed", "the current build") — only stable, canonical facts survive contact with other machines.
- Rules that need prior context to make sense — every rule must be self-contained and verifiable from its own text.

## Quality Checklist (Before Marking "Done")

- [ ] All tests pass
- [ ] No uncommitted working tree changes remain
- [ ] Task board status updated ("Review Ready" or "Done")
- [ ] Documentation matches implementation
- [ ] Peer review completed and approved
- [ ] Code location paths verified via `project-organization` skill

## Verification

- `git status` clean, `git log` shows the commit, `git ls-remote` shows the push.
- Portability test: an agent with no prior context can follow every rule
  verbatim. Any rule that needs local context to make sense is not portable.

---

*First seed, 2026 — canonical development workflow.*
