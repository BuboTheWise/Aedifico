# Aedifico

Multi-timescale reflection for Hermes agents — independent introspection **and** collaborative cross-agent learning, both ending in durable artifacts.

"Edification" is the discipline: a reflection that does not end in a changed skill, a memory fact, a MemChorus write, a cron job, or a team convention is a journal entry, not improvement.

## Why

Agents that only act never compound. Aedificio gives an agent a bounded loop to look back across **four horizons** — turn → session → weekly → cross-agent — and convert what it learns into something that persists and loads at the right moment.

Two modes, deliberately separable:

- **Independent** — one agent reviews its own history. Works for any single Hermes agent with zero prerequisites beyond Hermes core. This is the base, not an afterthought.
- **Collaborative** — the same loop, layered with inter-agent exchange. Agents learn *from each other's different perspectives on the same interactions*: one agent's handoff-loss is another's delivery win; one agent's repeated failure is another's one-liner. Different vantage points, same events — that delta is the highest-signal collaborative finding.

## Philosophy

- **Self-first.** An agent must be able to improve alone before it improves a team. Never outsource introspection.
- **Perspective is the payload.** Collaboration is not "share your findings" — it is "here is the same event from my side; reconcile." Ground truth (repo, issue, logs) resolves conflicts, not seniority.
- **Artifacts over prose.** Every finding lands in a bucket: procedure → skill, stable fact → memory, episodic → MemChorus, recurring trigger → cron, team → shared space.
- **Portable.** No machine-local paths, no hard dependency on any one setup. It works for any Hermes agent, anywhere.

## MemChorus

**Heavily leveraged when present, a clean floor when absent.** MemChorus (MemPalace) is the durable deep-copy memory layer: diary for episodic reflections, knowledge graph for cross-session facts, drawers for verbatim records, checkpoint for session capture.

The skill detects MemChorus on every run (`tool_search`). Present → the loop reads and writes the diary, kg, and drawers, and files the deep copy there while `memory` stays the tight hot copy. Absent → the loop degrades gracefully to `memory` + `session_search`; nothing breaks, nothing is assumed. MemChorus is expected for our agents but is **not a requirement**.

## Layout

```
skills/productivity/edification/
  SKILL.md                       # the loop — independent + collaborative
  references/sources-map.md      # Hermes + MemChorus tool map, good/bad findings, anchors
  templates/reflection-report.md # the report shape (scope → findings → artifacts → collab)
```

## Installing

Point a Hermes profile at the skill so it loads for that agent:

```bash
# symlink or copy into the profile's skills tree
ln -s "$PWD/skills/productivity/edification" \
      ~/.hermes/profiles/<profile>/skills/productivity/edification
```

(Or copy the `edification/` directory. New skills are seen by a fresh session — the loader caches at session start.)

## Triggering

Natural language: *"reflect"*, *"run a retrospective"*, *"self-improvement pass"*, *"team reflection"*. Or schedule a tick with `cronjob_manage` for a recurring independent or collaborative cycle.

## License

MIT.
