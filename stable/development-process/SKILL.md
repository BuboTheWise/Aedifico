---
name: development-process
description: 'Atomic card workflow: spec-first, QA gates, git discipline.'
version: 0.2.1
author: BuboTheWise, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [development, standards, workflow, quality, kanban]
    related_skills:
      - hermes-agent-skill-authoring
      - requesting-code-review
---

# Development Standard (Team)

Canonical development standard for team work across agents and projects. It
applies equally — no project gets special paths or baked-in preferences. Every
rule below must be followable verbatim by an agent with no local context.
Where a project document says otherwise: the project spec wins for *what* to
build; this standard wins for *how* to build it.

## When to Use

- Starting, executing, reviewing, or handing off any development task.
- Drafting a task spec, commit, or PR.
- Don't use for: pure research or documentation authoring.

## Rule One: Dual-Location Structure

1. Development code and skills live in a git repository. Never in the knowledge vault.
2. Documentation, requirements, decisions, and research live in the vault or project docs. Never inside a source tree.
3. Work in a clone. Never edit a live application tree in place.

## The Board

- **GitHub Issues on the project repository is the board** (or an equivalent tracker). No second board surface: chat threads and notes drift out of sync. The board is the source of truth for *state*; the repository is the source of truth for *code*.
- **Card states as labels:** `ready → in-progress → qa → review → done`.
- **Claim protocol:** a card enters `in-progress` only when an executor is named on the card **and** acknowledges the card (acknowledgment of understanding, before implementation starts). One owner at a time; the owner is always visible on the card.
- Work that is not on the board is invisible to routing, QA, and audit: if it is not a card, it does not count.

## Card Discipline

**Card types (stated on the card):**
- `RUN` — execute existing code or commands and report findings (pass/fail/breakage). **No edits.**
- `FIX` — named changes to named files, nothing else.
- `spec:` — spec or requirements change; must merge on its own before any dev card it gates.
- **Unclear = RUN.** The card type is the scope fence. A card without a type permits no edits.

**Atomicity test (checkable):** a card is atomic only if the **weakest model on the team** can complete it verbatim from its four elements — Objective, Success Criteria, Required Testing, Verification Steps — with **zero unstated context or judgment calls**. If it needs a tradeoff decision, it is not atomic: split it, or write the decision explicitly into the card. Test phrasing: "could the smallest model do this card from the text alone?"

**Spec-first gate:** any new feature or behavior change starts as a `spec:` card that merges before dev. Dev cards cite their spec card. "Read the current specs" is one step short of "specs updated and merged before dev starts" — the latter is the gate.

**Stop-and-report:** an unexpected outcome, or a fix outside the card's named scope → STOP. Report it as a finding on the card. The fix becomes a NEW card (`FIX` or sometimes `spec:`) — it is never a side quest inside the current card.

## QA: A Separate Task

- QA, stress, and verification are always a **separate new task, run in a fresh context** — never concurrent with, and never rolled into, the development task.
- The **same agent** that implemented may perform its own QA task. The requirement is *task* separation (a new context that has not seen the implementation), not *agent* separation.
- "Done" requires pasted real output covering the claimed scope — a full test suite green where the project defines one. A single test on a non-deterministic model is a finding, not a verdict.
- Reviews cite specific files/lines — no one-line "looks good" approvals.

## Solo Mode

No rule in this standard requires a second agent to be present:

- The board and the repository are the record. "Done" is defined by evidence on the board, not by who says it.
- The fences (card type, atomicity test, stop-and-report) are **load-bearing in solo mode**, not advisory — they are the only guardrails when no one is watching.
- Evidence is mandatory, not optional: a card closes only with pasted real output covering the claimed scope.
- A solo agent must be able to claim, implement, QA, and merge a card end-to-end without contacting any other agent.

## Workflow Phases

**Phase 0 — Preparation.** Read the current specs. Verify git state and versions. Confirm the card's four elements: Objective, Success Criteria, Required Testing, Verification Steps. Acknowledge the card before implementation starts. Completion: scope confirmed on the card.

**Phase 1 — Implement.** Implement only the card's named scope. Write tests for new code before calling it done. Build must pass. Commit and push immediately after a green build. Completion: tests green, code pushed.

**Phase 2 — Close.** Documentation current. Board state updated. Repository clean and pushed. Session lessons filed to memory. Completion: zero uncommitted work.

**Phase 3 — Improve.** After each session, identify 1–3 concrete improvements. A gap that recurs twice becomes a permanent rule here. Completion: the rule is written and versioned.

## Quality Gates (hard)

- No uncommitted work at the end of a session. No exceptions.
- No "done" without a real, executed verification. Paste the actual output.
- No fabricated results. A blocker reported honestly beats an invented success.
- Cite before claim. Every factual assertion ties to a tool output or a document.
- Errors are data. Deviations are disclosed immediately and fed back into process.
- Artifacts outrank prose. A claim is only as real as the file, command, or URL behind it.
- QA, stress testing, and verification are separate tasks — never rolled into implementation.
- Every rule and claim carries its own checkable verification, doable from the text alone.
- A card ends in exactly one of: **merged to main**, or **parked as a named, tracked open PR**. No orphaned local branches that exist in no card or PR.

## Git Discipline

### Branching Conventions
- **Base branches:** `main` (default) or `develop` if the team uses it.
- **Feature branches:** `feature/<task-name>` e.g. `feature/agent-orchestration`.
- **Fix branches:** `fix/<issue-id>-<short-desc>` e.g. `fix/gh-42-login-timeout`.
- Naming: lowercase, hyphens (no underscores or CamelCase).
- Delete feature branch after merge — never before review.

### Commit Discipline
- Commit format: `feat:`, `fix:`, `test:`, `docs:` followed by a short description.
- One concern per commit. Push immediately after a green build.
- **Git-first rule:** Every meaningful change is committed at the end of its discrete step. No "I'll commit everything at the end."

### Branch Hygiene
- No uncommitted working-tree changes at end of a session.
- No local branch that exists in no issue or PR.
- Every card's final state is merge-or-park (see Quality Gates).

### Public Artifacts
- Carry the team identity only: no personal names, no machine hostnames, no absolute home paths.

### Repository Operations
- A **designated repository operator** performs `gh` CLI operations (push, PR creation, merge). Implementers provide patches or diffs for review first.
- All GitHub interaction goes through the `gh` CLI (issue edit/comment, PR, push) — via shell or `subprocess` — not raw `curl`. One auth path, consistent output.
- Never a personal identity on a public repository.

## Handoff and Collaboration

- A handoff is durable: the artifact lands on disk in the target's workspace (file, memory entry, issue). Chat is the go-signal, not the handoff.
- State-changing work needs a read-back of the exact target before claiming success — a passing tool call is not a verified effect.
- Coordinate before two agents edit the same tree.

## Pitfalls

- Scope drift on small models — edits during a RUN card, or provider/config logic added while "fixing" a runtime issue. The card type IS the fence: if the card doesn't say `FIX`, there are no edits.
- A queued acknowledgment is not execution — verify state on disk (`git status`, file mtimes) after any stop/hold order, not just in chat.
- One test is not a battery — "🎉 PASSED" from a single test on a non-deterministic model is a finding, not a verdict. Scope of claim must match scope of evidence.
- A rule that sounds nice but isn't actionable ("be careful") — replace with a checkable criterion or cut it.
- Machine-local paths in shared documents — they break for everyone else.
- Project-specific special cases inside a shared standard — put them in the project spec.
- Verifying the tool call instead of the result.
- Tool parameter discipline — `execute_code(code=...)` not `command=...`; use `terminal()` for shell commands. A wrong parameter name is a silent failure or crash — verify by reading returned output, not tool-call success.
- Accumulating rules without pruning the wording they replace.
- Session-specific language in shared documents ("as we discussed", "the current build") — only stable, canonical facts survive contact with other machines.
- Rules that need prior context to make sense — every rule must be self-contained and verifiable from its own text.

## Quality Checklist (Before Marking "Done")

- [ ] All tests pass
- [ ] No uncommitted working-tree changes remain
- [ ] Task board status updated ("review" or "done")
- [ ] Documentation matches implementation
- [ ] QA task completed as a separate task, in a fresh context, with pasted output
- [ ] Code location verified per Rule One (dual-location: code in the git repo, docs in the vault)
- [ ] Card state is merged-or-park: branch merged, or a named open PR tracking it

## Verification

- `git status` clean, `git log` shows the commit, `git ls-remote` shows the push.
- Portability test: an agent with no prior context can follow every rule verbatim. Any rule that needs local context to make sense is not portable.
- Solo test: every gate above can be satisfied by one agent, one machine, no second agent reachable.

---

*v0.2.0 — board layer, card types, atomicity test, spec-first gate, stop-and-report, QA task separation (same agent, fresh context), solo mode, branch hygiene merged-or-park. Prior: v0.1.4 (quality gates, git discipline, dual-location structure).*
