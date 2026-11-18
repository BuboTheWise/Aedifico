---
name: development-process
description: 'Atomic card workflow: spec-first, QA gates, git discipline, OPSEC, install-from-GitHub.'
version: 0.2.7
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

## Hermes Install Source Protection (hard rule)

The live installed Hermes source tree **must** remain at the path reported by `hermes --version` (currently `~/.hermes/hermes-agent`).

- `~/Projects/hermes-agent` (or any other clone) is a **separate** development/working copy. The two locations are never interchangeable.
- No profile or agent may:
  - Move, rename, delete, or `mv` any content between `~/.hermes/hermes-agent` and another location.
  - Run git, pnpm, `hermes pm`, build, or source-modifying commands inside the live `~/.hermes/hermes-agent` tree unless the explicit, documented goal is repairing the *installed* Hermes (and only after first running `hermes --version` and confirming the Install directory).
  - Treat the live install dir as a development workspace.
- All Hermes-agent development work must occur exclusively in a separate clone (e.g. `~/Projects/hermes-agent`).
- Before any terminal/git/build work that touches a Hermes source tree, every agent **must** run `hermes --version` and record the reported "Install directory".
- Violation of this rule has already caused multiple full Hermes install breakages (stale launchers, "No such file or directory", frontend/pm failures, agents disappearing).

This rule is enforceable. Any card or action that would touch the live source without the above verification is out of scope.

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

**Spec-first gate:** any new feature or behavior change starts as a `spec:` card that merges before dev. Dev cards cite their spec card. See [team-dev-process](../../team-dev-process/SKILL.md) for atomic card workflow, collaboration patterns, and QA gates. "Read the current specs" is one step short of "specs updated and merged before dev starts" — the latter is the gate.

**Stop-and-report:** an unexpected outcome, or a fix outside the card's named scope → STOP. Report it as a finding on the card. The fix becomes a NEW card (`FIX` or sometimes `spec:`) — it is never a side quest inside the current card.

## QA: A Separate Task

- QA, stress, and verification are always a **separate new task, run in a fresh context** — never concurrent with, and never rolled into, the development task.
- The **same agent** that implemented may perform its own QA task. The requirement is *task* separation (a new context that has not seen the implementation), not *agent* separation.
- **QA tier rule.** The team maintains a capability ranking (strongest → weakest). Conformance QA on a card implemented by the **weakest** tier must be assigned to a **higher** tier. Same-model QA (a separate fresh task) remains valid only when the implementer is not the weakest tier. Rationale (checked, not assumed): same-model re-reading by the weakest tier has a demonstrated blind spot — code paths present but unexercised under their failure condition (auth/key paths, fallback branches, timeout/budget walls that only fail when the real triggering condition is hit).
- **Orchestrator duty:** when creating the QA card, set the assignee per the tier rule — do not default the QA card back to the implementer. A stronger-tier QA assignment works offline-of-whoever-implemented: the ranking lives in this standard, not in any one agent's context.
- **Graduation:** a learner in the weakest tier may earn the right to self-QA in a given domain when they pass a separate discrete QA card on a subsequent real task in that domain (evidence on the board, not acknowledgment). Until then, the tier rule stands.
- "Done" requires pasted real output covering the claimed scope — a full test suite green where the project defines one. A single test on a non-deterministic model is a finding, not a verdict.
- Reviews cite specific files/lines — no one-line "looks good" approvals.

## Executed-QA gate (v0.2.4)

A QA verdict on a change to **executable code** is not complete without at least one **executed check** of the changed code path. "Executed" is mechanical — one of these three admissible forms:

1. **Run the changed line.** The code path containing the change actually runs in the target environment (the interpreter/runtime the code ships on) — not re-reading the diff in your head.
2. **Invoke the API.** The function/method/endpoint the change touches is called with inputs that reach the changed behavior.
3. **A test exercises the path.** A test runs the changed path, asserts on its output, and would have FAILED against the pre-fix code.

A diff re-read (grep, regex, prose) is a **review**, not a QA verdict, and cannot stand alone as QA evidence for executable code.

**Canonical interpreter (v0.2.5).** Runtime drift is invisible to static QA: the same stdlib call can be valid on one interpreter and crash on another (the F8 anchor below is exactly this failure mode). The interpreter is therefore named and pinned. (a) The project spec names the canonical interpreter — implementation and version — that the build and QA battery run under. (b) The QA card records the interpreter version (`python --version`, or the equivalent for the runtime) and a smoke of any changed stdlib or library call under that exact interpreter. (c) Where the project uses a dependency manifest, the pin (`requirements` or equivalent) is committed with the change. A verdict produced under a different interpreter than the canonical one is a finding, not a verdict.

**What the verdict records.** The verdict pastes the executed check: the exact command (or the named test run) plus an output excerpt showing the changed path actually ran. A verdict whose evidence is diff-reading alone is incomplete — even if its prose says "verified."

**Tier-agnostic.** This gate applies to every tier — no exemption. The QA tier rule above governs *who* may perform QA; this gate governs *what counts as a verdict*. The demonstrated failure mode (anchor below) is a property of static reading, not of the reader: a stronger model re-reading the same diff misses the same one-token typo. Execution is the only tier-independent substitute for judgment.

**Anchor (why this gate exists).** Polygraph finding F8: `datetime.now().isoformat(timesep="seconds")` — a mistyped kwarg on a stdlib call — passed a diff-re-read QA round, then crashed at runtime when the battery executed the script on the canonical interpreter. Fix: commit `6549cb7` in the Polygraph repository ("F8 regression, battery crash … re-verify"), and the change was re-verified by executing the battery. Seven earlier findings were caught by reading; the eighth was one token and was only visible when the code ran.

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
- **Clean-tree gate (v0.2.5).** A card is not done with an unclean tree, and a file that exists only on disk is not done. Before a card closes: (a) `git status --porcelain` must return empty — no modified, staged, or untracked files; (b) every artifact named on the card must appear in `git show --stat <sha>` of the card's landing commit (its merge commit, or the open PR's head commit if parked). Paste both commands' output on the card — both must be clean / present.
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

### OPSEC (public surface)

- **The team identity is the only identity on any public surface.** Commits, PRs, issues, comments, skill text, and README carry the repository owner account only — no personal names, no local usernames, no machine hostnames, no internal hostnames, no absolute home paths.
- **Assume public.** Anything that lands in the repository, a PR, an issue, or a shared skill file is public. Redact personal names, paths, and internal references before it ships.
- **Never a personal GitHub identity on a public repository.** All `gh` operations (push, PR, issue, comment) run as the designated team/repo operator account.
- **Check before shipping:** grep the diff for personal names, home paths, and hostnames — they must be zero.
- **OPSEC history purge (v0.2.6).** Scrubbing the working copy is not enough — a redacted secret is still readable in history and on the remote branch. When an OPSEC/PII leak is found in any tracked artifact: (a) scrub the content at HEAD first, per the substitution convention (personal profile or account name → role descriptor, absolute home path → portable reference); (b) purge it from all history with `git filter-repo` — dry-run first, then a `git bundle` backup, then apply — and force-push the rewritten branch (`git push --force`); (c) verify zero: a fresh grep of the leaked token must return nothing on `origin` or anywhere in history; (d) record the leak and its resolution in the task or PR for audit — which repository, the leaked token (or its shape), the commit range, and the exact `git filter-repo` command.

### Repository Operations

- A **designated repository operator** performs `gh` CLI operations (push, PR creation, merge). Implementers provide patches or diffs for review first.
- All GitHub interaction goes through the `gh` CLI (issue edit/comment, PR, push) — via shell or `subprocess` — not raw `curl`. One auth path, consistent output.

### Installation & Distribution

- Profiles install shared skills and artifacts **from the canonical GitHub repository after merge to `main`** — never from a local dev clone, a working tree, or an unpushed branch.
- **If a change is merged and pushed, the update path is a reinstall from the remote.** A local copy is never the source of truth handed to another profile.
- A profile's working copy of a shared skill must match the remote `main`; verify by sha, not by "it looks right."

## Handoff and Collaboration

- A handoff is durable: the artifact lands on disk in the target's workspace (file, memory entry, issue). Chat is the go-signal, not the handoff.
- State-changing work needs a read-back of the exact target before claiming success — a passing tool call is not a verified effect.
- Coordinate before two agents edit the same tree.
- **Bot-to-bot cap (v0.2.5).** Bot-to-bot exchanges are capped by a small per-exchange message budget (observed: 4). When the budget is hit — or when a reply must outlive the exchange — route it as a kanban card (durable, auditable, board-visible) instead of continuing a long chat thread. Do not keep retrying in chat. Short DMs remain fine as go-signals.

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
- [ ] Clean-tree gate satisfied: `git status --porcelain` empty, and every artifact named on the card present in `git show --stat <sha>` of the landing commit; both outputs pasted on the card
- [ ] Task board status updated ("review" or "done")
- [ ] Documentation matches implementation
- [ ] QA task completed as a separate task, in a fresh context, with pasted output
- [ ] Executed-QA gate satisfied: the QA verdict pastes an executed check of the changed path — command (or test-run name) + output excerpt, and the check fails on the pre-fix code
- [ ] Canonical interpreter named and pinned: QA records `python --version` (or equivalent) matching the project spec's named canonical interpreter, plus a smoke of any changed stdlib/library call under it
- [ ] If the implementer is the weakest tier: QA was assigned to a higher tier (QA tier rule), or the learner holds a passing QA card in this domain
- [ ] Code location verified per Rule One (dual-location: code in the git repo, docs in the vault)
- [ ] Card state is merged-or-park: branch merged, or a named open PR tracking it
- [ ] OPSEC history purge satisfied (only if this card resolved an OPSEC/PII leak): the leaked token is scrubbed at HEAD, purged from all history via `git filter-repo` (dry-run → backup → apply → force-push), a fresh grep of the token returns zero on origin and across all history, and the leak + resolution (repo, token, commit range, filter-repo command) is recorded on the card or PR

## Verification

- `git status` clean, `git log` shows the commit, `git ls-remote` shows the push.
- Portability test: an agent with no prior context can follow every rule verbatim. Any rule that needs local context to make sense is not portable.
- Solo test: every gate above can be satisfied by one agent, one machine, no second agent reachable.

---

*v0.2.7 — Hermes Install Source Protection (hard rule): live source at path reported by `hermes --version` (e.g. `~/.hermes/hermes-agent`) must never be moved, edited, or operated on as a dev tree; all Hermes-agent work must use a separate clone (e.g. `~/Projects/hermes-agent`); every agent must run `hermes --version` and record the Install directory before touching any Hermes source tree. Added after repeated install breakages from profile confusion between live install and dev clone. v0.2.6 — OPSEC history purge: a resolved OPSEC/PII leak is scrubbed at HEAD and purged from all history (git filter-repo: dry-run, bundle backup, apply, force-push), verified zero on origin and across all history, with the leak + resolution recorded for audit (Toolbox #22). v0.2.5 — Clean-tree gate (done gated on `git status --porcelain` clean + named artifacts in commit, Toolbox #11); canonical interpreter named and pinned in QA (Toolbox #12); bot-to-bot per-exchange cap + kanban-card fallback (Toolbox #14). v0.2.4 — Executed-QA gate added (mechanical gate with three admissible forms: run changed line, invoke API, or test exercises path; verdict records executed check and demonstrates pre-fix failure). v0.2.3 — QA tier rule: weakest-tier implementation requires higher-tier conformance QA; orchestrator sets the QA assignee per the rule; weakest-tier self-QA valid only after a passing QA card in that domain (output-based graduation). v0.2.2 — OPSEC promoted to an explicit checkable rule (team-identity-only, assume-public, never a personal GitHub identity, grep-before-ship); Installation & Distribution rule added (install shared skills from GitHub after merge, never from a local dev tree; verify by sha). v0.2.1 — promoted field rules. v0.2.0 — board layer, card types, atomicity test, spec-first gate, stop-and-report, QA task separation (same agent, fresh context), solo mode, branch hygiene merged-or-park. Prior: v0.1.4 (quality gates, git discipline, dual-location structure).*
