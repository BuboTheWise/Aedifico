---
name: edification
description: "Weekly retrospective and cross-agent reconciliation: reflects on recent sessions and history, consolidates durable skills and memory, prunes stale or superseded facts, and reconciles state across agents. Use when asked to reflect, run a retrospective, do a weekly or cross-agent pass — or on a scheduled tick."
version: 0.2.0
author: BuboTheWise, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Reflection, Self-Improvement, Retrospective, Weekly-Review, Cross-Agent, MemChorus, Bot-Mode]
---

# Edification (Aedifico)

Multi-timescale reflection for Hermes agents: **one bounded pass** — fired on demand or by a single scheduled tick — that reviews your history and converts findings into durable artifacts: skills that get better, memory that stays lean, kg facts that get consolidated, cron jobs that get pruned. Low overhead by design: when MemChorus is present it is the **primary durable layer** — deep reflections file there, so the tight hot `memory` stays lean instead of bloating. Two modes, separable by design:

- **Independent** (default) — one agent, its own history, fully functional on Hermes core alone (`memory` + `skill_manage`; session recall via `session_search` when loaded, else via `tool_search`, else hunches). Zero hard prerequisites. MemChorus and Bot-Mode are enhancement layers, not dependencies.
- **Collaborative** — layers Bot-Mode inter-agent exchange on top. One agent facilitates; roster members contribute scoped answers. Runs as **two ticks, +24h apart** (see Procedure — Collaborative).

A reflection that does not end in artifacts is a journal entry, not edification.

**Not for:** planning the user's week (`weekly-review-planning`), root-causing one bug (`systematic-debugging`), or authoring a single new skill (just use `skill_manage`).

## Scope boundaries

Aedifico owns the **weekly and cross-agent** horizons. It does not duplicate what the agent runtime already does:

| What Aedifico does | What Aedifico does not do |
|---|---|
| Weekly consolidation: merge, prune, supersede across skills / memory / MemChorus kg | Turn/session horizons — owned by the agent runtime's background review (`agent/background_review.py` in hermes-agent) |
| Cross-agent reconciliation of the same event from multiple vantage points | Per-turn taxation — the scheduled pass runs once, bounded |
| Pruning stale or contradicted durable facts | Reimplementing MemChorus primitives |
| Filing skill defects / upstream defects with handles | Team planning (separate skill) |

Scheduled (cron) runs **skip the turn horizon** — that work is already covered by the runtime background review. A manual on-demand run may still look at recent turns when the question calls for it.

## When to Use

- "reflect", "retrospective", "weekly review", "cross-agent reconciliation", "introspection", "self-improvement pass"
- After a milestone, a long session, or a pattern of corrections
- A scheduled tick (cron) fires the weekly pass
- Collaborative: "team reflection", "cross-agent retrospective", or a finding that spans agents

## Capability detection (run first, every run)

1. **MemChorus** — `tool_search(queries=["mempalace diary"])`. **Present → enhancement layer:** it is the primary durable sink, so episodic reflections, cross-session facts, and verbatim records file to the diary / kg / drawers and only the highest-signal distilled facts get promoted to tight `memory` — the mechanism that keeps the pass low-overhead. **Absent → Aedifico still runs end-to-end on Hermes core** (`memory` + session recall carry the load); it degrades, it never blocks. Not a dependency, never a requirement — detect first, every run, and never assume MemChorus output exists. (Mirrors MemChorus itself: MemPalace is its primary backend but it falls back to core Hermes files. Aedifico is one layer further out.)
2. **Bot-Mode** — `message_agent` in the tool list with a non-empty roster → collaborative mode available. Absent → collaborative degrades to a handoff document posted where the team reads (shared repo issue, decision doc).

State the detected tier set in one line at the top of the report. Done when every source in the plan is either confirmed present or explicitly skipped.

## Horizons

| Horizon | Window | Question | Owner |
|---|---|---|---|
| Turn (hot) | last few exchanges | What did I get wrong or waste, right now? | agent runtime (background review) |
| Session (warm) | this + last 1–3 sessions | What did I repeat? What did the user correct? | agent runtime (background review) |
| Weekly (cold) | 7–30 days | What trends across sessions? What is stale or contradicted? | **Aedifico** — skill consolidation, memory cleanup, cron for recurring checks |
| Cross-agent (archive) | collaborative only | Where did handoffs, division of labor, or escalations fail? | **Aedifico** — team convention in shared space (issue, decision doc) |

Horizons are independent of each other: a turn-level fix does not discharge the weekly level. Thin evidence for a horizon is reported as such — never filled in.

## Weekly pass = subtraction

The weekly horizon exists to **reduce** the agent's durable state, not just add to it:

1. **Merge** duplicate or overlapping skills / memory entries (keep the best phrasing, retire the rest).
2. **Prune** facts contradicted by newer evidence or no longer true (verify against ground truth before pruning).
3. **Supersede** at kg boundaries — retire the old fact, keep the new one, with a link between.
4. **Net-change line** in the report: skills ±, memory entries ±, kg facts superseded — so the pass's effect is auditable.

Additions (new skill patches, new memory facts, new cron jobs) are fine — but a pass that only adds is a journaling pass, not a consolidation pass. A weekly pass that adds nothing and removes nothing is still a pass: it states what it checked and why nothing qualified.

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
- **MemChorus boundary.** Aedifico leverages MemChorus — it never replaces or re-implements it (no home-grown memory primitives). Writes go through MemChorus's own write path (`memchorus_remember`, category-tagged) — Aedifico never writes to the MemPalace backend directly. Defects found in MemChorus during a pass → file as a normal upstream issue (`github` skill: check for duplicates first) and hand to the development agent. Aedifico reports and routes; it does not absorb MemChorus's roadmap.
- **OPSEC.** Artifacts that land in public repos carry only the public account identity — no personal names, machine identities, or private agent handles.

## Procedure — Independent (weekly pass)

1. **Scope.** Mode, horizons (weekly + cross-agent; turn/session are handled by the runtime background review), time window, detected tier set. Done: declared in one paragraph.
2. **Gather.** Pull evidence per horizon from the source map; batch independent lookups in one turn; use `execute_code` to aggregate across sessions or files. Done: every finding anchored, or labeled hunch.
3. **Classify.** One bucket per finding (ground rule above). Done: no finding appears in two buckets.
4. **Consolidate.** The subtraction step first: merge / prune / supersede across skills, memory, and MemChorus kg — then apply net additions: `skill_manage` (patch over rewrite where possible), `memory` ops, MemChorus writes, `cronjob_manage`. Match artifact scope to horizon scope — a weekly finding does not hot-patch a turn-level skill without cause. Done: each artifact applied, or deferred with a stated reason; the net-change line is computable.
5. **Verify.** Read back every artifact: `skill_view`, memory state, MemChorus get, cron list. Done: every applied artifact has a verifiable handle.
6. **Report.** Use `templates/reflection-report.md` — including the net-change line. Done: no finding in the table lacks an artifact/handle or an explicit no-action + reason.

## Procedure — Collaborative (additive, two-tick)

Collaborative mode runs in **two ticks, +24h apart** — not in one long session:

- **Tick A (collect).** 1. **Run the full independent loop first** (weekly + cross-agent). Your own loop is the input to the team's; do not outsource introspection. 2. **Digest.** Compose a self-contained digest: what happened, what was fixed, what is needed. Self-contained = a teammate with no other source can act on it. 3. **Perspective questions — the core move.** Identify the *same events* your teammates lived and ask for their side, not their opinions. One agent's handoff-loss is another's delivery win; one agent's repeated failure is another's one-liner. The delta between two vantage points on one interaction is the highest-signal collaborative finding — it names the assumption only the other side could see. Phrase the request as *"here is my side of `<event>`; what did you see / decide / drop on your side?"*, scoped to their lane, via `message_agent` (fire-and-forget — end the turn; the reply arrives as a background delivery). Never "any thoughts?". One question, one lane. 4. Leave the outstanding questions on the record (a tick-A log the next pass can read).
- **Gap.** +24h minimum. Replies accumulate; other work proceeds.
- **Tick B (consolidate).** 1. **Consolidate.** Read the tick-A log and the replies; fold each input in. Reconcile the perspective deltas — where two sides of the same event disagree on *what actually happened*, resolve against ground truth (repo state, issue state, logs, the other side's own artifact) — evidence wins, not seniority. Acknowledge inputs that were used. 2. **Land team artifacts in shared space** — a shared-repo issue or decision doc both sides can read. A DM is a go-signal, not a storage medium. Team knowledge that exists only in one agent's private memory is a leak in waiting. Done: the team artifact has a shared handle (issue number / path) both sides can verify.

**Why two ticks:** a same-turn "ask and wait" blocks the facilitator, and a same-turn reply arrives before the teammate has actually thought about it. The gap is what makes the delta real.

### Cron template (two-tick, weekly)

```
# weekly collaborative edification — two ticks, +24h apart
# tick A (collect): independent loop + digest + lane-scoped questions; log outstanding asks
0 4 * * 1
# tick B (consolidate): read tick-A log + replies; reconcile; land team artifact in shared space
30 4 * * 2
```

(Exact schedule is per-deployment; the constraint is the +24h separation, not the clock times.)

## Toolbox Guard (hash parity)

Before any `skill_manage` on a skill: check whether the skill also exists in the team's shared stable tree (`~/.hermes/skills/stable/`).

- **Found in stable/** → Toolbox-owned: do not edit the local copy. Create an issue/PR brief (with the sha256 diff between the local and stable copies) against the stable repo instead, and let the stable owner review.
- **Not found** → community-maintained: proceed with the local edit.

Why: a stable copy is byte-identical by contract — a silent local drift breaks parity across every profile that links it.

## Installation

Copy the skill into the profile's skills tree (one copy per profile) — the repo is the source, the profile copy is the working state. **No symlinks**: an update or local patch to the source silently changes every linked profile at once, and a deleted source breaks the link without warning. Full install, verification, and backup steps are in the README.

## Pitfalls

- **Prose-only reflection** — the #1 failure mode. If step 6 has no artifact for a finding, apply one or delete the finding.
- **Additive-only weekly pass** — a pass that only adds entries is journaling, not consolidation. Every weekly pass performs the merge/prune/supersede step, or states why nothing qualified.
- **Per-turn taxation.** This is a bounded, scheduled pass — not a per-turn overhead. The scheduled pass covers weekly + cross-agent once, on the tick; turn/session work belongs to the runtime background review.
- **MemChorus present but unused** — or invoked when absent. Detect first, every run.
- **MemPalace MCP intermittently unreachable on scheduled runs** — the server may not be connected at tick time, and a slow model response can abort the run before any artifact lands. Degrade to core-only, state the durable sink was unreachable in the report, and re-run once the MCP is up. (2026-11-14 run: no `mempalace` source in `tool_search`; aborted at 210s; zero artifacts.)
- **Absorbing MemChorus.** Re-implementing a MemChorus primitive or silently working around its bug with local scaffolding. File it per the boundary rule; another agent builds the fix.
- **Same-turn collaborative ask.** Asking and waiting in one turn blocks the facilitator and gets unthought replies. Two ticks, +24h gap.
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
- [ ] Net-change line present (skills ±, memory ±, kg superseded).
- [ ] Collaborative: questions were lane-scoped; two-tick separation observed; team artifacts have shared-space handles.
- [ ] Toolbox Guard ran before any `skill_manage` on a shared skill.

## Files

- `SKILL.md` — this loop (independent + collaborative).
- `references/sources-map.md` — tool-level sources map, MemChorus tool table, `session_search` patterns, anchor forms.
- `templates/reflection-report.md` — the report shape (scope → findings → artifacts → net-change → collab).
- `examples/` (repo root) — a real independent pass, scrubbed for OPSEC: the full loop, collection → consolidation.
