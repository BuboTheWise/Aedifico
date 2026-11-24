# docs/ — Specifications & Requirements

The canonical home in this repo for specification and requirements documents.

## What lives here

- **Functional specs** (`<subject>-spec.md`) — the behavioral definition of a skill
  (what it is, what it is not, invariants, protocol) that **gates** the implementation
  in `stable/<subject>/`. The spec is written and QA'd first (spec-first gate); it is
  implemented by a separate dev card; that implementation has its own separate QA card.
- **Requirements docs** (`<subject>-requirements.md`) — cross-cutting requirements that
  constrain several skills or the repo as a whole.

## What does not live here

- Skill content itself (`SKILL.md`, `references/`) — stays in `stable/<skill>/`.
  This folder is a top-level home for spec & requirements docs, **not** a reorg of `stable/`.
- Per-card evidence, review verdicts, and board records — those live on the Kanban board,
  not in this repo.
- Code, tests, and configuration.

## Naming scheme

- Form: `<subject>-<kind>.md`
  - `<subject>`: a skill name (`mentorship`, `development-process`, `pr-comment-monitor`)
    or a short topic slug (e.g. `qa-routing`).
  - `<kind>`: `spec` or `requirements`. These are the **only two kinds in the scheme
    today** — a new kind is added by a spec change, not by drift.
- Lowercase, hyphenated.
- **No version in the filename.** Version is declared in the document header (e.g. "v1");
  a version bump edits the header, never the filename. Rationale: references from skill
  files, other docs, and the board point at stable paths — a rename on every bump would
  orphan them.

## Current contents

| File | Subject | Kind | Version | Status |
|---|---|---|---|---|
| `mentorship-spec.md` | `stable/mentorship/` | spec | v1 | In force — implemented in `stable/mentorship/` |

## Spec-first relationship

A spec in this folder **gates** its implementation: the spec is written and verified
first and merges standalone; any dev card implementing it cites it. A change to a spec
is itself a spec change and must land before the dev work it gates. The dev standard
(`development-process`) defines the mechanics; this folder holds the artifacts it
produces.
