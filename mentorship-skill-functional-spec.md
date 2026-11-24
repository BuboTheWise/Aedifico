# Mentorship Skill — Functional Specification (v1)

**Status:** `spec:` — draft, awaiting **separate** QA card (separate-QA rule; this spec is not QA'd in-line)
**Date:** 2026-11-16
**Author:** BuboTheWise
**Standard (how to build):** `development-process` v0.2.2
**Gates (what this spec is the definition for):** the later, **separate** atomic task that implements the mentorship `SKILL.md` in the public Toolbox repo (`stable/mentorship/`), with its **own** separate QA card.
**Related invariants:** per-profile memory isolation (MemChorus) — cross-profile interaction is talk-only.

> Scope fence: this document is **documentation only**. It changes no code and makes no
> MemChorus-core edits. It is a `spec:` card deliverable. Implementing the `SKILL.md` it
> defines is a downstream atomic task, not part of this one.

---

## 1. Pinned Decisions

These four are **pinned and recorded up front**. They are not open questions and are not
re-derived mid-draft. The rest of the spec is the consequence of these.

### 1.1 Closed capability-domain vocabulary (the routing unit)
- The routing unit for a lesson is a **finite, explicit, closed** set of task-type domains.
  The v1 set is exactly: **`spec`, `dev`, `verify`, `qa`**.
- A lesson carries **exactly one** `domain` from this closed enum. Domain is the routing
  unit: it selects the teacher, the recall bucket, and the graduation task domain.
- **Capability attributes** — self-declared skills, model class/size, board history — are
  **cited evidence** used *inside negotiation*. They are **never the routing unit**. A model's
  size or a static rule never routes a lesson.
- The set is **closed in v1**. Adding or removing a domain is a `spec:` card change, not an
  ad-hoc addition at lesson-write time.

### 1.2 1:1 vs multi-teacher
- v1 is **single-accept (1:1)**: one learner, exactly **one** accepted teacher per lesson.
- **Multi-teacher** (a lesson with several teachers, or a learner pulling one lesson from
  several) is **phase 2 / out of v1 scope**.

### 1.3 Output-based graduation
- A lesson starts in **hot recall**.
- It **graduates** (drops out of hot recall) **only** when the learner passes a **separate
  discrete QA card** on a **subsequent real task** in that lesson's domain.
- Graduation is **verified by output** (the passing QA evidence), **not by read** (the fact
  that the learner read or acknowledged the lesson).
- It is **outcome-based, not time-based decay alone.** A lesson does not graduate on a timer;
  it graduates on evidence.

### 1.4 Scope — v1 is pull-emphasized
- v1 is **pull-emphasized**: the weak (learner) **pulls** lessons; the strong (teacher)
  **distills** lessons **only on explicit request** and **only on accept**.
- The **growth loop in which the strong learns from the weak's failures** is **explicitly
  phase 2 / out of v1 scope.**

---

## 2. Objective

Produce a self-contained functional specification for a general `mentorship` Hermes skill:
bidirectional teaching between heterogeneous local models (the strong distills lessons, the
weak pulls them) under a **hard per-profile isolation invariant**, where **all cross-profile
interaction is talk** (Kanban tasks and message channels) and no profile reads another
profile's memory directly. The spec must be directly implementable as a standalone
`SKILL.md` in the public Toolbox repo under the **BuboTheWise** identity, with a direct
requirement on MemChorus for local per-profile storage and recall. Every lesson must be
**atomic** (`development-process` shape) and **enforceable** (a mechanical guard, not prose).
Overhead on stronger models is **strictly controlled** (distillation is on-demand only).

## 3. What it is / is not

**Is:**
- A negotiation protocol that determines which profile is *stronger* for a given domain, by
  self-declared capability + inter-bot dialogue + board-history evidence, with manual override
  always winning.
- An overhead-controlled loop: weak pulls, strong distills only on accept.
- A lesson schema that is atomic and enforceable before it is written.
- An output-based graduation rule that retires a lesson from hot recall only on passing QA
  evidence in the domain.

**Is not (v1):**
- Not a static "bigger model = teacher" rule.
- Not multi-teacher, not a strong-learns-from-weak-failure loop (both phase 2).
- Not a time-based decay mechanism.
- Not a cross-profile memory reader. Profiles never read each other's MemChorus.

## 4. Hard constraints (invariants)

1. **Talk-only.** All cross-profile interaction goes through Kanban tasks and message
   channels. **No profile reads another profile's MemChorus directly.** Per-profile isolation
   is a hard invariant, not a convention.
2. **"Stronger" is negotiated, never assumed.** Determined in-skill by dialogue +
   self-declared capabilities + board-history evidence. **Never** by implicit model size or a
   static rule. **Manual override always wins** and is recorded on the card.
3. **Bidirectional, pull-emphasized.** Negotiation is the cheap gate; **distillation is the
   only expensive step and fires only on accept + explicit request.**
4. **Lessons are atomic and enforceable before they are written.** Atomic = the
   `development-process` shape (objective + success criteria + required testing + verification).
   Enforceable = the success criteria and verification are **checkable** (a grep pattern, a
   test command, a boolean predicate), mechanically applicable without judgment. A criterion
   that cannot be reduced to a checkable form is not yet enforceable and is not written.
5. **Separate QA.** QA of this spec, and QA of the later `SKILL.md`, are **separate discrete
   tasks**, each in a fresh context — never rolled into the implementing task.
6. **Portable + OPSEC-clean.** BuboTheWise identity only. No personal names, no local
   filesystem paths, no machine/hostnames. References to the dev standard use the canonical
   name `development-process` (not any alternate spelling). Any reference to an
   internal-only store or tool is replaced with the public equivalent — or dropped —
   before promotion to the public Toolbox.

## 5. Core — the negotiation protocol (determining "stronger")

Inputs: a learner wanting a lesson in a closed-enum `domain`, or a real task in that domain.

1. **Capability declaration.** Each profile self-declares the domains it claims. This is
   *data* (cited evidence), **not** the routing unit.
2. **Dialogue.** The learner and the candidate teacher talk over Kanban/message channels. The
   learner states the domain and the specific task; the candidate states its capability and
   the evidence behind it.
3. **Board-history evidence.** The learner (or a neutral party) checks board history for the
   domain: who holds **passing QA cards** in that domain. Cited evidence.
4. **Decision.** Exactly **one** teacher is accepted (1:1). The basis is the dialogue + cited
   evidence. **Model size is not a factor.**
5. **Manual override.** A human may pin the teacher. This **always wins** and is recorded on
   the card.
6. **Accept.** The teacher accepts (or declines). **Only on accept does distillation fire.**

## 6. Core — the distillation / pull loop (overhead-controlled)

```
trigger (learner wants a lesson in domain D)
  → negotiate (§5)            cheap: dialogue + cited evidence
  → accept (1:1)              cheap: one yes/no
  → distill                   EXPENSIVE — only on accept + explicit request
  → pull                      cheap for learner
  → hot recall                lesson is live
  → use on a real task in D
  → graduate (§7)             only on passing QA output in D
```

- **Distillation** (teacher writes the atomic, enforceable lesson) is the **single expensive
  step**. It is gated by accept and by an explicit request. This is the overhead control.
- **Pull** (learner persists the lesson into its **own** MemChorus) is cheap and is the v1
  emphasis.
- The lesson content crosses the profile boundary **as talk** (Kanban/message), then the
  learner writes it to its **own** store. The learner never reads the teacher's store.

## 7. Lesson record schema (atomic + enforceable)

```
lesson:
  id:              <stable id>
  domain:          spec | dev | verify | qa      # closed enum — the routing unit
  teacher:         <profile that distilled>
  learner:         <profile that pulled>
  pulled_at:       <timestamp>
  objective:       <what this lesson teaches>
  success_criteria:<checkable criteria — a grep, a command, a boolean; not prose>
  required_testing:<how to test the lesson>
  verification:    <the guard / checkable criterion that proves it>
  status:          hot | graduated
  graduation:      # populated only on graduation
    qa_card:       <id of the separate discrete QA card that passed>
    domain_task:   <the real task in domain D on which that QA passed>
    output:        <the passing output evidence (pasted, not asserted)>
    graduated_at:  <timestamp>
```

The four middle fields (`objective`, `success_criteria`, `required_testing`, `verification`)
are the atomic shape. `success_criteria` and `verification` **must be checkable** — that is the
enforceable requirement.

## 8. Graduation (output-based)

- A lesson in `hot` state graduates to `graduated` **only** when the learner passes a
  **separate discrete QA card** on a **subsequent real task** in the lesson's `domain`.
- The record's `graduation` block is populated with the QA card id, the domain task, and the
  **pasted passing output**. No output, no graduation.
- Read/acknowledgement is not graduation. A timer is not graduation. Evidence is.

## 9. Success criteria (this spec is "done" when)

- §1 records all four pinned decisions as **pinned** (each states a definite choice, not a
  "TBD").
- The spec carries the four atomic elements: **Objective, Success Criteria, Required
  Testing, Verification Steps** (§2, §9, §10, §11).
- The spec covers every core requirement: negotiation protocol, per-profile isolation,
  talk-only, atomic+enforceable lessons, overhead control (on-demand distillation), 1:1,
  output-based graduation, pull-emphasis, and the named phase-2 exclusions.
- The spec is **portable**: zero local filesystem paths, zero personal names, BuboTheWise
  identity only, no internal-only store references.
- The spec states that (a) the `SKILL.md` implementation is a **separate later atomic task**
  with its **own separate QA card**, and (b) promotion into the public Toolbox
  (`stable/mentorship/`) is a **separate git-process step**, not part of this card.
- The spec is consistent with the `development-process` standard (how) and the MemChorus
  per-profile-isolation invariant (talk-only).

## 10. Required testing (for this `spec:` card)

- **T1 — Pinned.** Read §1.1–1.4. Each of the four decisions states a definite choice (closed
  enum + exact set; 1:1; output-based graduation; pull-emphasis + named phase-2 exclusion).
- **T2 — Four elements.** Confirm §2 (Objective), §9 (Success Criteria), §10 (Required
  Testing), §11 (Verification Steps) are all present and non-empty.
- **T3 — Portability / OPSEC.** Grep the body for (a) absolute home-directory paths,
  (b) home-relative project paths, (c) mounted-volume labels, (d) personal names or local
  usernames, and (e) any account identity other than the team account. The only permitted
  identity is `BuboTheWise`. Expect **zero** hits across (a)–(d).
- **T4 — Coverage.** Map each core requirement in §9 to a section that implements it; expect
  no requirement left unaddressed.
- **T5 — Solo/portability test.** A reader with **no** prior context can, from this document
  alone, name the four pinned decisions and the four atomic elements.
- **T6 — Consistency.** Cross-check against the `development-process` standard (how to build)
  and the MemChorus isolation invariant (talk-only, no cross-profile memory reads).

## 11. Verification steps

- **V1.** Read §1; confirm the four pinned decisions are recorded as pinned, each with a
  definite choice.
- **V2.** Run T3's grep; confirm zero personal-name / local-path leaks; confirm the dev
  standard is referenced only as `development-process`.
- **V3.** Confirm the four atomic elements are present (T2).
- **V4.** Confirm the spec states the `SKILL.md` implementation is a **separate** atomic task
  with a **separate** QA card, and that promotion to `stable/mentorship/` is a separate
  git-process step.
- **V5.** Confirm the spec is consistent with the `development-process` SKILL.md in the
  public Toolbox repo (talk-only, isolation).
- **V6.** Confirm the spec is consistent with the MemChorus per-profile-isolation invariant
  (no profile reads another's memory directly).
- **V7.** Confirm no code was changed and no MemChorus-core edit was made (documentation-only
  fence), per `git status` in the affected tree.

## 12. Explicitly out of scope (phase 2)

- Multi-teacher lessons (see §1.2).
- The strong-learns-from-weak-failure growth loop (see §1.4).
- Time-based decay as a graduation mechanism (see §1.3).
- Adding/removing closed-enum domains without a `spec:` card.

## 13. OPSEC / portability checklist (pre-promotion)

- [ ] No absolute home-directory paths, no home-relative project paths, no volume labels.
- [ ] No personal names, local usernames, or machine/internal hostnames; team identity only.
- [ ] Dev standard referenced only as `development-process`.
- [ ] No internal-only store references (dropped before promotion).
- [ ] Any profile can follow this spec verbatim with no local context.

## 14. Dependencies / related documents

- `development-process` (Team Development Standard) — the "how" this spec follows.
- MemChorus per-profile isolation invariant — talk-only, no cross-profile memory reads.
- The later atomic task implementing `stable/mentorship/SKILL.md` (gated by this spec;
  separate QA card).

## 15. Handoff

- This spec **gates** the later atomic task: implement the mentorship `SKILL.md` in the
  public Toolbox repo (`stable/mentorship/`), then run a **separate** QA card on it.
- Promotion of this document (or a distilled version) into the public Toolbox is a **separate
  git-process step** (branch → PR → merge → install-from-remote), owned by the repository
  operator — not part of this card.
- This card closes with the spec document in place, the four pinned decisions recorded, and
  the separate-QA handoff named. No code, no MemChorus-core edit.
