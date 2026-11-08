---
name: edification
description: "Multi-timescale reflection that ends in durable artifacts."
version: 0.1.0
author: BuboTheWise, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Reflection, Self-Improvement, Retrospective, MemChorus, Bot-Mode]
---

# Edification

Multi-timescale reflection for Hermes agents: **one bounded pass** — fired on demand or by a single scheduled tick — that reviews your history across four scales (turn → session → weekly → cross-agent) and converts findings into durable artifacts. Low overhead by design: when MemChorus is present it is the **primary durable layer** — deep reflections file there, so the tight hot `memory` stays lean instead of bloating. Two modes, separable by design:

- **Independent** (default) — one agent, its own history, fully functional on Hermes core alone (`memory` + `skill_manage`; session recall via `session_search` when loaded, else via `tool_search`, else hunches). Zero hard prerequisites. MemChorus and Bot-Mode are enhancement layers, not dependencies.
- **Collaborative** — layers Bot-Mode inter-agent exchange on top. One agent facilitates; roster members contribute scoped answers.

A reflection that does not end in artifacts is a journal entry, not edification.

**Not for:** planning the user's week (`weekly-review-planning`), root-causing one bug (`systematic-debugging`), or authoring a single new skill (just use `skill_manage`).

## When to Use

- "reflect", "retrospective", "introspection", "self-improvement pass"
- After a milestone, a long session, or a pattern of corrections
- A scheduled tick (cron) fires for a reflection cycle
- Collaborative: "team reflection", "cross-agent retrospective", or a finding that spans agents

## Capability Detection (run first, every run)

1. **MemChorus** — `tool_search(queries=["mempalace diary"])`. **Present → enhancement layer:** it is the primary durable sink, so episodic reflections, cross-session facts, and verbatim records file to the diary / kg / drawers and only the highest-signal distilled facts get promoted to tight `memory` — the mechanism that keeps the pass low-overhead. **Absent → Aedifico still runs end-to-end on Hermes core** (`memory` + session recall carry the load); it degrades, it never blocks. Not a dependency, never a requirement — detect first, every run, and never assume MemChorus output exists. (Mirrors MemChorus itself: MemPalace is its primary backend but it falls back to core Hermes files. Aedifico is one layer further out.)
2. **Bot-Mode** — `message_agent` in the tool list with a non-empty roster → collaborative mode available. Absent → collaborative degrades to a handoff document posted where the team reads (shared repo issue, decision doc).

State the detected tier set in one line at the top of the report. Done when every source in the plan is either confirmed present or explicitly skipped.

## Horizons

| Horizon | Window | Question | Artifact type |
|---|---|---|---|
| Turn (hot) | last few exchanges | What did I get wrong or waste, right now? | immediate micro-fix (inline action or one-line skill patch) |
| Session (warm) | this + last 1–3 sessions | What did I repeat? What did the user correct? | `skill_manage` patch or a `memory` fact |
| Weekly (cold) | 7–30 days | What trends across sessions? What is stale or contradicted? | skill consolidation, memory cleanup, cron for recurring checks |
| Cross-agent (archive) | collaborative only | Where did handoffs, division of labor, or escalations fail? | team convention in shared space (issue, decision doc) |

Horizons are independent of each other: a turn-level fix does not discharge the weekly level. Thin evidence for a horizon is reported as such — never filled in.

## Sources (Hermes map)

Tool-level detail — per-tier detection probes, the MemChorus tool table, `session_search` patterns, and acceptable anchor forms — lives in `references/sources-map.md`.

| Source | Tool | Extract |
|---|---|---|
| Session history | `session_search` (query + session_id, then scroll) — via `tool_search` if not loaded, else hunches | user corrections, failed attempts, retried commands |
| Working memory | `memory` (read targets) | stale entries, contradictions, entries that are procedures, not facts |
| Procedural memory | `skills_list` / `skill_view` | skills that failed mid-task, missing steps, sediment |
| Scheduled work | `cronjob_manage` (list) | jobs that never fire, fire uselessly, or drifted from intent |
| Durable memory | MemChorus (if detected): diary read, kg query/timeline, drawer search | cross-session facts, superseded facts, unfiled drawers |
| Shared truth | GitHub issues / shared repos via `gh` (collaborative) | what was committed vs delivered |

Ground rules:

- **Anchors.** Every finding carries an anchor: session id + quote, commit sha, issue number, or drawer/diary id. Unanchored findings are hunches — label them and weight them down.
- **One bucket per finding.** procedure → skill; stable fact → memory; episodic → MemChorus (or memory if absent); recurring trigger → cron; team → shared space. A procedure in memory is bloat; a one-off in a skill is sediment.
- **MemChorus boundary.** Aedifico leverages MemChorus — it never replaces or re-implements it (no home-grown memory primitives). Defects found in MemChorus during a pass → file as a normal upstream issue (`github` skill: check for duplicates first) and hand to the development agent. Aedifico reports and routes; it does not absorb MemChorus's roadmap.
- **OPSEC.** Artifacts that land in a public repo carry only the public account identity — no personal names, machine identities, or private agent handles.

## Procedure — Independent

1. **Scope.** Mode, horizons, time window, detected tier set. Done: declared in one paragraph.
2. **Gather.** Pull evidence per horizon from the source map; batch independent lookups in one turn; use `execute_code` to aggregate across sessions or files. Done: every finding anchored, or labeled hunch.
3. **Classify.** One bucket per finding (ground rule above). Done: no finding appears in two buckets.
4. **Draft & apply artifacts.** `skill_manage` (patch over rewrite where possible), `memory` ops, MemChorus writes, `cronjob_manage`. Match artifact scope to horizon scope — a weekly finding does not hot-patch a turn-level skill without cause. Done: each artifact applied, or deferred with a stated reason.
5. **Verify.** Read back every artifact: `skill_view`, memory state, MemChorus get, cron list. Done: every applied artifact has a verifiable handle.
6. **Report.** Use `templates/reflection-report.md`. Done: no finding in the table lacks an artifact/handle or an explicit no-action + reason.

## Procedure — Collaborative (additive)

1. **Run the full independent loop first** (horizons 1–3). Your own loop is the input to the team's; do not outsource introspection.
2. **Digest.** Compose a self-contained digest: what happened, what was fixed, what is needed. Self-contained = a teammate with no other source can act on it.
3. **Perspective reconciliation — the core move.** Identify the *same events* your teammates lived and ask for their side, not their opinions. One agent's handoff-loss is another's delivery win; one agent's repeated failure is another's one-liner. The delta between two vantage points on one interaction is the highest-signal collaborative finding — it names the assumption only the other side could see. Phrase the request as *"here is my side of `<event>`; what did you see / decide / drop on your side?"*, scoped to their lane, via `message_agent` (fire-and-forget — end the turn; the reply arrives as a background delivery). Never "any thoughts?". One question, one lane.
4. **Consolidate.** On reply: fold each input in. Reconcile the perspective deltas — where two sides of the same event disagree on *what actually happened*, resolve against ground truth (repo state, issue state, logs, the other side's own artifact) — evidence wins, not seniority. Acknowledge inputs that were used.
5. **Land team artifacts in shared space** — a shared-repo issue or decision doc both sides can read. A DM is a go-signal, not a storage medium. Team knowledge that exists only in one agent's private memory is a leak in waiting. Done: the team artifact has a shared handle (issue number / path) both sides can verify.

## Pitfalls

- **Prose-only reflection** — failure mode #1. If step 6 has no artifact for a finding, apply one or delete the finding.
- **Per-turn tax.** This is a bounded, scheduled pass — not a per-turn overhead. The turn (hot) scale is for the immediate moment; the scheduled pass covers session + weekly + cross-agent once, on the tick.
- **MemChorus present but unused** — or invoked when absent. Detect first, every run.
- **Absorbing MemChorus.** Re-implementing a MemChorus primitive or silently working around its bug with local scaffolding. File it per the boundary rule; another agent builds the fix.
- **Skipping the self-contained digest** in collaborative mode. Assume the reader has nothing.
- **Private memory as team storage.** Shared knowledge → shared space.
- **Turn-level fix discharging the weekly level.** Horizons are independent.
- **Unanchored findings** presented at the same confidence as anchored ones.
- **OPSEC leak** in any artifact that lands in a public repo.

## Verification

- [ ] Report opens with declared scope + detected tier set.
- [ ] Every finding carries an anchor or is labeled a hunch.
- [ ] Every finding resolves to an artifact with a verifiable handle, or an explicit no-action + reason.
- [ ] All artifacts were read back after writing.
- [ ] Collaborative: questions were lane-scoped; team artifacts have shared-space handles.
