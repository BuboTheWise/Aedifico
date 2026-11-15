---
name: development-process
description: "Standardize task workflow, phases, QA separation, and git-first discipline for Hermes profiles."
version: 0.1.0
author: BuboTheWise (Bubo), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [workflow, task-structure, qa-separation, git-first, kanban, development-process, phases, atomic-tasks]
---

# Development Process Skill

Shared workflow rules for every Hermes profile. Load this skill before any coding, reviewing, or task execution work.

## When to Use

- Starting any feature, fix, refactor, or QA task
- Writing Kanban tasks (must follow the task structure below)
- Before any git commit or push
- Requesting code review
- Logging session learnings

Don't use for: one-shot research queries, documentation-only edits, config changes. Load `hermes-agent` for Hermes CLI/config questions instead.

## Prerequisites

- Git installed and authenticated (`gh auth status`)
- Hermes Agent CLI available (`hermes --help`)
- Kanban board accessible (shared or profile-local)
- the team's shared memory queryable for additional workflow rules

## How to Run

This is a **process skill** — there is no single command. Follow the phases and rules below in sequence. Use the `terminal` tool for git commands, `kanban_*` tools for task management, `skill_view` or `memory` for recall.

## Core Principles

| Principle | Why It Matters |
|-----------|----------------|
| **Git-First** | No uncommitted work; complete audit trail; nothing lost overnight |
| **Testing-First** | Every feature has unit tests before release; catches issues early |
| **Living Documentation** | Skills and procedures evolve with experience |
| **Collaborative Transparency** | All progress tracked via Kanban; no manual status updates or DMs |
| **QA Separation** | Implementer does NOT do their own review; QA is a discrete task |

## Task Structure

Every Kanban task MUST have these four fields in its body:

1. **Clear Objective** — What will be accomplished (one sentence)
2. **Success Criteria** — How to know it's done (checkable items)
3. **Required Testing** — Unit + integration tests that must pass
4. **Verification Steps** — Post-completion checks the reviewer runs

No field may be omitted or left vague. If a task is missing any field, ask the creator to add it before starting work.

## Development Phases

Execute phases in order. Each phase has success criteria; do not proceed until all are met.

### Phase 0: Preparation

Before starting work:
1. Query the team's shared memory for workflow rules and recent learnings
2. Review current specs and protocols relevant to the task
3. Check git state and version numbers
4. Break down work into atomic Kanban tasks (one concern per task)
5. Assign and require acknowledgment of understanding

**Success Criteria:** Both agents aware of scope; task breakdown reviewed; clear success metrics defined.

### Phase 1: Code Quality

After implementation, before merging:
- Verify all tests passing (no compilation or lint errors)
- Review edge cases and corner case coverage
- Document significant decisions in the repo (`docs/decisions/` or PR body)
- Log learnings via the team's shared memory session log format: `SESSION:yyyy-MM-dd|workflow|ALC.req:process.improve|★★★`

### Phase 2: Feature Implementation

1. **Implement only assigned tasks** — no scope creep
2. Write unit tests covering new code (target ≥80% coverage)
3. Run full test suite locally
4. Push to GitHub immediately after all checks pass

**Success Criteria:** Feature per spec; tests passing; code committed and pushed; no untested work.

### Phase 3: QA Review

- Implementer creates a **separate review task** assigned to the reviewer
- Reviewer runs verification steps independently
- If passing: reviewer approves, merge follows (see Git Discipline below)
- If failing: return with specific changes; do NOT self-approve

### Phase 4: Documentation & Push

- Update project docs for all changes made
- Ensure GitHub sync is current (no unpushed commits)
- Log session learnings in the team's shared memory
- Update this procedure if process gaps are found

**Success Criteria:** Documentation up-to-date; repository clean and pushed; all code committed.

### Phase 5: Iterative Improvement

After each work block:
- Identify blockers or improvement areas
- Adjust task breakdown if needed
- Document learnings in the team's shared memory / team docs
- Update protocols where workflow gaps are revealed

## Git Discipline

### Commit Messages

Format: `type: description` (Conventional Commits style)

| Type | Use For |
|------|---------|
| `feat:` | New features, endpoints, capabilities |
| `fix:` | Bug fixes, corrections |
| `test:` | Test additions, test improvements |
| `docs:` | Documentation changes |
| `refactor:` | Code restructuring without behavior change |
| `chore:` | Dependencies, configs, tooling |

Examples:
```
feat: add Entity and EntityGenerator classes
fix: correct Entity.java imports
test: add EntityTest with comprehensive test cases
docs: update API reference for new endpoints
```

### Push Rules

- Commit immediately after every successful verification step
- **Never** leave unpushed or untested code overnight
- Push to the feature branch after each phase completes successfully
- Never force-push to shared branches

## QA Protocols

### Review Separation

The implementer of a task must **never** review their own work. Quality assurance requires an independent reviewer.

**Process:**
1. Implementer completes assigned task per Phase 2 criteria
2. Implementer requests review via `kanban_request_review(summary=..., metadata={changed_files: [...], tests_run: N})`
3. Reviewer independently runs verification steps
4. If passing: reviewer approves with `kanban_complete(summary="...")`
5. If failing: reviewer uses `kanban_request_changes(reason="...")` with specific actionable changes

### Code Review Checklist

- [ ] Tests added for all new code paths
- [ ] Edge cases and error conditions covered
- [ ] Commit messages follow conventional format
- [ ] No uncommitted work remains
- [ ] Documentation updated to match changes
- [ ] No debugging code, print statements, or `console.log` left behind
- [ ] Security implications considered (auth, input validation, secrets)

## Project Neutrality

When working across projects:
- Code location: `~/.hermes/workspace/Code/<project-name>/`
- Use placeholders for project-specific paths — never assume a particular project context
- Refer to the team's shared memory or team docs for current project specs, not cached memory

## Session Summary Template

Each session ends with this format logged to the team's shared memory:

```
SESSION:DATE|workflow.<category>|ALC.req:process.improve|★★★

Objective: [What we aimed to accomplish]
Actions: [What we actually did]
Results: [What succeeded, what failed]
Lessons: [What to do differently next time]
the team's shared memory Entry: [a memory entry with key decisions]
Changes: [Modified files with commit messages]
```

## Failure Modes & Mitigation

| Failure | Mitigation |
|---------|-----------|
| Unpushed code left overnight | Always commit and push before stopping. No exceptions. |
| Tests not written for complex features | Unit tests required before marking any feature complete |
| Process changes without documentation | Document in the team's shared memory (session log format) and update team docs |
| Tasks with ambiguous specs | Review task specs with assignee before implementation starts |
| Scope creep beyond assigned task | Create a new child task; do not absorb unscoped work |

## Verification Checklist

Before completing any development task:

- [ ] All four Kanban fields present (Objective, Criteria, Testing, Verification)
- [ ] Tests pass locally (full suite, not just new tests)
- [ ] Commit messages follow conventional format
- [ ] Code committed and pushed to the correct branch
- [ ] QA review completed by independent reviewer
- [ ] Documentation updated for all changes
- [ ] Session logged via the team's shared memory session log format
- [ ] No debugging code left behind

## References

- **Development Workflow Procedure**: the team's shared development standard
- **Canonical Dev Workflow Skills**: `the canonical workflow rules (see team docs)`
- **Skill Authoring Standard**: `software-development/hermes-agent-skill-authoring/SKILL.md`
