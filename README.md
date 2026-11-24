# Aedifico

Multi-timescale reflection for Hermes agents — independent introspection **and** collaborative cross-agent learning, both ending in durable artifacts.

"Edification" is the discipline: a reflection that does not end in a changed skill, a memory fact, a MemChorus write, a cron job, or a team convention is a journal entry, not improvement.

## Why

Agents that only act never compound. Aedifico gives an agent a bounded loop to look back across **four horizons** — turn → session → weekly → cross-agent — and convert what it learns into something that persists and loads at the right moment.

Two modes, deliberately separable:

- **Independent** — one agent reviews its own history. Works for any single Hermes agent with zero prerequisites beyond Hermes core. This is the base, not an afterthought.
- **Collaborative** — the same loop, layered with inter-agent exchange. Agents learn *from each other's different perspectives on the same interactions*: one agent's handoff-loss is another's delivery win; one agent's repeated failure is another's one-liner. Different vantage points, same events — that delta is the highest-signal collaborative finding.

## Philosophy

- **Self-first.** An agent must be able to improve alone before it improves a team. Never outsource introspection.
- **Perspective is the payload.** Collaboration is not "share your findings" — it is "here is the same event from my side; reconcile." Ground truth (repo, issue, logs) resolves conflicts, not seniority.
- **Artifacts over prose.** Every finding lands in a bucket: procedure → skill, stable fact → memory, episodic → MemChorus, recurring trigger → cron, team → shared space.
- **Portable.** No machine-local paths, no hard dependency on any one setup. It works for any Hermes agent, anywhere.

## How a run works

One bounded pass — fired on demand or by a single scheduled tick — never a per-turn tax:

1. **Scope.** Declare mode, horizons, time window, and which memory layers are detected (MemChorus present or absent).
2. **Gather.** Pull evidence per horizon: session history (`session_search`), `memory`, installed skills, cron jobs, and — when present — the MemChorus diary / knowledge graph / drawers. Every finding carries an anchor (session id + quote, commit sha, issue number, drawer id) or is explicitly labeled a hunch.
3. **Classify.** One bucket per finding: procedure → skill; stable fact → memory; episodic → MemChorus; recurring trigger → cron; team → shared space.
4. **Draft & apply artifacts.** `skill_manage` patches, `memory` ops, MemChorus writes, `cronjob_manage` updates, or a shared-space issue / decision doc for team findings. Match artifact scope to horizon scope.
5. **Verify.** Every applied artifact is read back (`skill_view`, memory state, cron list, MemChorus get) before the pass ends.
6. **Report.** A structured reflection report — scope → findings → artifacts → net-change — using `templates/reflection-report.md`. No finding leaves the pass without an artifact with a verifiable handle or an explicit no-action + reason. The net-change line (skills ±, memory ±, kg facts superseded) makes the pass's effect auditable.

| Horizon | Window | Question |
|---|---|---|
| Turn (hot) | last few exchanges | What did I get wrong or waste, right now? |
| Session (warm) | this + last 1–3 sessions | What did I repeat? What did the user correct? |
| Weekly (cold) | 7–30 days | What trends across sessions? What is stale or contradicted? |
| Cross-agent (archive) | collaborative only | Where did handoffs, division of labor, or escalations fail? |

Horizons are independent of each other: a turn-level fix does not discharge the weekly level. Thin evidence for a horizon is reported as such — never filled in.

**Scope:** Aedifico owns the **weekly and cross-agent** horizons. The turn and session horizons are owned by the agent runtime's background review (`agent/background_review.py` in hermes-agent) — a scheduled (cron) run therefore covers weekly + cross-agent only, and does not tax every turn.

## MemChorus

**Heavily leveraged when present, a clean floor when absent.** MemChorus (MemPalace) is the durable deep-copy memory layer: diary for episodic reflections, knowledge graph for cross-session facts, drawers for verbatim records, checkpoint for session capture.

The skill detects MemChorus on every run (`tool_search`). Present → the loop reads and writes the diary, kg, and drawers, and files the deep copy there while `memory` stays the tight hot copy. Absent → the loop degrades gracefully to `memory` + session recall (or hunches where `session_search` isn't loaded); nothing breaks, nothing is assumed. MemChorus is expected for our agents but is **not a requirement** — Aedifico never re-implements it, and defects found in a pass are filed upstream, not worked around.

## Prerequisites

- **Hermes Agent** — that's it. The skill runs end-to-end on core Hermes tools (`memory`, `skill_manage`, `session_search` when loaded).
- **MemChorus (MemPalace)** — optional enhancement layer; detected at the start of every run.
- **Bot-Mode** (`message_agent` + roster) — optional; enables the collaborative cross-agent mode. Absent, the collaborative output degrades to a handoff document in shared space.

## Layout

```
.
  README.md
  CHANGELOG.md
  LICENSE
  examples/
    weekly-pass-2026-11-21.md      # a real independent pass (OPSEC-scrubbed): collection → consolidation
  skills/productivity/edification/
    SKILL.md                       # the loop — independent + collaborative
    references/sources-map.md      # Hermes + MemChorus tool map, good/bad findings, anchors
    templates/reflection-report.md # the report shape (scope → findings → artifacts → net-change → collab)
```

## Installing

The skill lives under `skills/productivity/edification/` in this repo. Install it into a Hermes profile's skills tree — one copy per profile. **Copy install is the required path** (a symlink install is not recommended: a repo update silently changes every profile that tracks it, and a moved repo leaves every profile that points at it stale, all at once).

```bash
git clone https://github.com/BuboTheWise/Aedifico.git
cd Aedifico

PROFILE=<your-profile>
mkdir -p ~/.hermes/profiles/$PROFILE/skills/productivity
cp -r skills/productivity/edification ~/.hermes/profiles/$PROFILE/skills/productivity/
```

### Verifying the copy (sha256)

After the copy, confirm the profile's tree matches the repo:

```bash
( cd skills/productivity/edification && find . -type f | sort | xargs sha256sum )
( cd ~/.hermes/profiles/$PROFILE/skills/productivity/edification && find . -type f | sort | xargs sha256sum )
# the two listings must be identical
```

### `hermes skills install` (alternative)

```bash
hermes skills install https://raw.githubusercontent.com/BuboTheWise/Aedifico/main/skills/productivity/edification/SKILL.md --category productivity --yes
```

Then re-run the sha256 check above against the installed tree.

### Backup / export for copy installs

A copy is a snapshot, not a live link — updates must be re-applied. Keep the skill exportable and the profile's tree recoverable:

```bash
# export a known-good snapshot of a profile's skills
tar czf edification-$(date +%F).tar.gz -C ~/.hermes/profiles/$PROFILE/skills/productivity edification

# re-apply after a repo update (full copy, then the sha256 check again)
rsync -a ~/Aedifico/skills/productivity/edification/ ~/.hermes/profiles/$PROFILE/skills/productivity/edification/
```

New skills are seen by a fresh session — the loader caches at session start. In a new session, confirm the skill loads: `edification` should appear in `skills_list` under `productivity`, and `skill_view(name='edification')` should return the loop.

## Triggering

Natural language: *"reflect"*, *"run a retrospective"*, *"self-improvement pass"*, *"team reflection"*, *"weekly review"*, *"cross-agent reconciliation"*. Or schedule a tick with `cronjob_manage` for a recurring independent or collaborative cycle (the two-tick collaborative template is in `SKILL.md` §Collaborative — Two-Tick Protocol).

## License

MIT.
