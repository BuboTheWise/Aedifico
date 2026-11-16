# Mentorship Skill — Loop Protocol

---

name: mentorship
version: 1.1
description: >
  Bidirectional teaching protocol between heterogeneous local models under per-profile isolation.
  The weak pulls lessons; the strong distills only on explicit accept. Includes Truth-Enforcer
  (tier-agnostic guard) and shared graduation state (board-verifiable).
category: dev

---

## Overview {#overview}

This skill establishes a **negotiation protocol** for mentorship exchanges, with three core
invariants from v1.1: (**bidirectional honesty**) — teacher files correction and pulls lesson
when learner's evidence contradicts teacher QA; (**Truth-Enforcer**) — four tier-agnostic rules,
applied strongest-first; (**shared graduation state**) — board-recorded, verifiable by any party.

The skill operates entirely through **talk-only** (Kanban/message channels), never reading
another profile's memory. All lessons are **atomic** (`development-process` shape) and
**enforceable** via mechanical checks.

## Pinned Decisions {#pinned-decisions}

| # | Decision                              | Choice                                                                                       |
|---|----------------------------------------|----------------------------------------------------------------------------------------------|
| 1 | Capability domains (routing unit)      | `spec`, `dev`, `verify`, `qa` — finite, explicit, closed enum.                             |
| 2 | Multi-teacher                          | Single-accept (1:1) only; multi-teacher is phase 2 / out of v1 scope.                       |
| 3 | Graduation mechanism                   | Output-based only — separate discrete QA card passes on a subsequent real task in domain.   |
| 4 | Scope                                 | Bidirectional, pull-emphasized — improvement symmetric: teacher pulls when learner's evidence contradicts. |

## Core Loop {#core-loop}

```
trigger (learner wants lesson in domain D)
  → negotiate (§5)            cheap: dialogue + cited evidence
  → accept (1:1)              cheap: one yes/no
  → distill                   EXPENSIVE — only on accept + explicit request
  → pull                      cheap for learner
  → hot recall                lesson is live
  → use on a real task in D
  → graduate (§9)             only on passing QA output in D, recorded on board
```

### Distillation {#distillation}

The **single expensive step** — teacher writes an atomic, enforceable lesson. Fired only on:
- explicit request from learner
- successful negotiation (§5)
- accepted 1:1 pairing

### Pull {#pull}

The learner persists the lesson into its **own** MemChorus store. Cheap and v1-emphasized.
Lesson content crosses profile boundary **as talk** (Kanban/message), then learner writes to
its own store. Learner never reads teacher's store. Talk-only verification: confirm that any
cross-profile information transfer appears in Kanban task comments or message channels, with
no references to reading another profile's private memory or internal state stores.

### Hot Recall {#hot-recall}

Lesson is live in the learner's store, ready for deployment on a real task in domain D.

### Use-on-Task {#use-on-task}

Learner applies lesson content to a real task in domain D. Output is captured and used as
evidence for graduation (§9).

### Graduation {#graduation}

Lesson graduates from `hot` to `graduated` only when:
- learner passes a **separate discrete QA card** on a subsequent real task in domain D
- graduation block populated with QA card id, domain task, pasted passing output
- record published to shared board for any-party verification

## Reverse Direction — Teacher's Correction Pull {#reverse-direction}

Improvement is **not one-directional**. Same loop runs in reverse: when the **learner's
evidence** (failing input, pasted output, QA artifact) contradicts the **teacher's QA
output** or a lesson the teacher wrote, the **teacher files correction and pulls the lesson**.

Checkable criterion for teacher correction: all of the following must hold —
(a) learner's artifact is **pasted** in the thread; (b) artifact is shown to contradict a
**specific, named** teacher assertion; (c) teacher **files** correction that names the
contradicted assertion and pulls the lesson; and (d) the exchange is **talk-only** — the
correction and the lesson transfer occur via the board/message channel, and neither profile
reads the other's private store. Correction citing no pasted artifact is rejected by
Truth-Enforcer E1 (§truth-enforcer).

In a correction lesson, schema roles are direction-neutral: the profile that distilled (here:
original learner, as source of evidence) fills `teacher`, and the profile that pulled (here:
original teacher) fills `learner`. Neither profile reads the other's store.

## Lesson Record Schema {#lesson-schema}

```
lesson:
  id:              <stable id>
  domain:          spec | dev | verify | qa      # closed enum — the routing unit
  teacher:         <profile that distilled>      # direction-neutral: in correction, original learner is `teacher` here
  learner:         <profile that pulled>         #   original teacher is `learner` here
  direction:       pull | correction             # pull = default; correction = teacher pulls
  pulled_at:       <timestamp>
  objective:       <what this lesson teaches>
  success_criteria:<checkable criteria — grep, command, boolean; not prose>
  required_testing:<how to test the lesson>
  verification:    <the guard / checkable criterion that proves it>
  status:          hot | graduated
  correction:      # populated only when direction = correction
    contradicted:  <specific teacher assertion that was contradicted>
    source:        <learner artifact (pasted) that contradicted it>
    filed_at:      <timestamp>
  graduation:      # populated only on graduation
    qa_card:       <id of separate discrete QA card that passed>
    domain_task:   <real task in domain D on which QA passed>
    output:        <passing output evidence (pasted, not asserted)>
    graduated_at:  <timestamp>
```

The four middle fields (`objective`, `success_criteria`, `required_testing`, `verification`)
form the atomic shape. `success_criteria` and `verification` **must be checkable** — that is
the enforceable requirement. The `direction`/`correction` fields make bidirectional loop (§6.1)
part of record, not afterthought.

## Truth-Enforcer {#truth-enforcer}

Tier-agnostic guard applicable to every profile in mentorship exchange (learner, teacher,
neutral party), applied to strongest model first. Four rules, each with checkable criterion:
mechanical yes/no on paste-able artifact. No tier exemption exists.

### E1 — evidence-before-claim {#e1}

No pass/fail/done assertion without executable artifact. Enforcer rejects assertion lacking
paste-able artifact.

**Checkable criterion:** card (or thread) carrying pass/fail/done assertion contains paste-able
artifact — command output, test result, or failing input — inline in text. Status asserted
without paste-able artifact is rejected.

### E2 — disagreement-by-evidence {#e2}

Conflict between two parties resolved by which side's artifact fails on other's code — **never**
by seniority, model size, tier, or who speaks first.

**Checkable criterion:** resolution record cites specific artifact that failed on other side's
code (pasted input + pasted output), or names command that reproduces it. Resolution citing
seniority/tier/model-size instead of artifact fails the check.

### E3 — honest-blocker-over-invented-success {#e3}

Reported failure outranks plausible-looking pass.

**Checkable criterion:** when same card or thread contains both reported failure and plausible
pass, card's status must be failure/blocked unless failure refuted by artifact under E2. Pass
asserted while unrefuted failure present fails the check.

### E4 — no tier exemption {#e4}

Enforcer applies to strongest model first; no profile, tier, or "weaker side" exempt.

**Checkable criterion:** enforcement rules contain no tier-based exception clause (no
"unless the model is …", no size/tier carve-out) — verifiable by reading §truth-enforcer. In
any concrete exchange, strongest model's claims are checked first. Presence of tier-based
exemption fails the check. Timestamp verification: when enforcing E1–E4 on multiple models,
the enforcer's earliest-recorded enforcement action (lowest timestamp in enforcement thread)
must show strongest-model-ranked target; if strongest model has not yet been checked by that
time, an "enforcement-started-at: <timestamp>" field must precede weaker-model checks. This
is verifiable from the board alone via timestamps on comments or card updates — no private
memory access needed.

## Shared Graduation State {#shared-graduation}

"Holds a passing QA card in domain D" is shared, verifiable state — not per-agent assertion
in private memory. Lives on shared board (Kanban), readable by every participant and neutral
third party.

### Recording {#recording}

Graduation recorded on QA card itself, on shared board, in three parts:
(a) card's status is passing; (b) card's title or body names domain D from closed enum; and
(c) card carries pasted passing output. Lesson record's graduation block is pointer to that
card id — resolvable on shared board — not self-declared status.

### Verification {#verification}

Any party — learner, teacher, human, neutral third party — can verify graduation by reading
shared board and checking three facts (passing status, domain D, pasted output). Requires no
access to any profile's private memory, consistent with talk-only isolation (§hard-invariants).

**Checkable criterion:** given only shared board, verifier can:
(a) find QA card by id lesson record points to; (b) confirm its status is passing; (c) confirm
domain D is named; and (d) confirm passing output is pasted inline. If any of (a)–(d) cannot
be checked from board alone, graduation state is not shared and does not count as graduation.

## Hard Constraints {#hard-invariants}

1. **Talk-only.** All cross-profile interaction through Kanban tasks and message channels. No
   profile reads another's MemChorus directly. Per-profile isolation hard invariant.
2. **"Stronger" negotiated, never assumed.** Determined in-skill by dialogue + self-declared
   capability + board-history evidence. Never implicit model size or static rule. Manual
   override always wins, recorded on card.
3. **Bidirectional honesty, pull-emphasized.** Negotiation cheap gate; distillation only
   expensive step firing on accept + explicit request. Improvement not one-directional: teacher
   files correction and pulls lesson when learner's evidence contradicts. Talk-only both ways.
4. **Lessons atomic and enforceable before written.** Atomic = development-process shape
   (objective + success criteria + required testing + verification). Enforceable = checkable
   without judgment; criterion not reducible to checkable form is not enforced.
5. **Portable + OPSEC-clean.** BuboTheWise identity only. No personal names, local filesystem
   paths, machine/hostnames. Dev standard referenced as canonical name `development-process`.
6. **Truth-Enforcer tier-agnostic.** Four rules apply every profile in exchange, strongest model
   first. No tier-based exemption (§truth-enforcer).
7. **Graduation shared state.** "Holds passing QA card in domain D" recorded on shared board,
   verifiable by any party from board alone (§shared-graduation).

## Success Criteria {#success-criteria}

This spec is done when:

- §pinned-decisions records all four pinned decisions as definite choices (including bidirectional
  honesty in v1) and multi-teacher named phase-2 scope item.
- Spec carries four atomic elements: **objective**, **success criteria**, **required testing**,
  **verification steps** (§overview, §core-loop, §hard-invariants).
- All core requirements covered: negotiation protocol, per-profile isolation, talk-only, atomic+enforceable
  lessons, overhead control (on-demand distillation), 1:1, bidirectional honesty, Truth-Enforcer four
  checkable rules, shared graduation state, output-based graduation, pull-emphasis. Phase-2 exclusions named.
- Spec portable: zero local filesystem paths, zero personal names, BuboTheWise identity only.
- Spec states SKILL.md implementation is separate later atomic task with own QA card; promotion to `stable/mentorship/`
  is separate git-process step (branch → PR → merge).
- Spec consistent with `development-process` standard and MemChorus isolation invariant (talk-only, no cross-profile memory reads).

## Required Testing {#required-testing}

- **TC1 — Pinned decisions.** Read §pinned-decisions. Each states definite choice (closed enum +
  exact set; 1:1; output-based graduation; pull-emphasis with bidirectional honesty in v1 + phase-2
  exclusion).
- **TC2 — Four elements.** Confirm objective, success criteria, required testing, verification
  steps present and non-empty.
- **TC3 — Portability / OPSEC.** Grep body for absolute home-directory paths, home-relative project
  paths, mounted-volume labels, personal names/local usernames, account identities other than team
  identity. Only permitted identity: BuboTheWise. Expect zero hits across prohibited categories.
- **TC4 — Coverage.** Map each core requirement in success criteria to section implementing it; expect
  no requirement unaddressed.
- **TC5 — Solo / portability test.** Reader with no prior context can, from document alone, name four
  pinned decisions, four atomic elements, and three v1.1 clauses (bidirectional honesty, Truth-Enforcer,
  shared graduation state).

## Verification Steps {#verification-steps}

- **VS1.** Read §overview; confirm four pinned decisions recorded as definite choices; confirm bidirectional
  honesty in v1.
- **VS2.** Run TC3 grep; confirm zero personal-name / local-path leaks; confirm dev standard referenced only
  as `development-process`.
- **VS3.** Confirm four atomic elements present (TC2).
- **VS4.** Confirm spec states SKILL.md implementation is separate atomic task with own QA card; promotion to
  `stable/mentorship/` is separate git-process step.
- **VS5.** Confirm spec consistent with MemChorus isolation invariant (talk-only, no cross-profile memory reads).
- **VS6.** Confirm Truth-Enforcer §truth-enforcer: four rules (E1 evidence-before-claim, E2 disagreement-by-evidence,
  E3 honest-blocker-over-invented-success, E4 no tier exemption), each with checkable criterion, strongest model
  first. No tier-based exemption clause.
- **VS7.** Confirm shared graduation state §shared-graduation: recording + verifier + board-only checkable criterion
  all defined.
- **VS8.** Confirm bidirectional honesty per reverse-direction (§reverse-direction): in v1, symmetric, talk-only, checkable.

## Phase-2 Exclusions {#phase-two}

Multi-teacher lessons; time-based decay as graduation mechanism; adding/removing closed-enum domains
without spec: card; note: strong-learns-from-weak-failure growth loop promoted into v1 and no longer phase-2.
