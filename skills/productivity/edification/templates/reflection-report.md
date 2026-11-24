# Reflection — <agent-role> — <date> — <mode: independent | collaborative>

## Scope & detected tiers

- Horizons: weekly, cross-agent (scheduled runs skip turn/session — owned by the agent runtime's background review)
- Window: <e.g. 2026-11-15 → 2026-11-22>
- Tiers — MemChorus: present | absent · Bot-Mode: present | absent · Cron: present | absent

## Findings → artifacts

| # | Horizon | Finding (anchored) | Bucket | Artifact | Handle | Status |
|---|---|---|---|---|---|---|
| 1 | weekly | … (sessions `<id1>`, `<id2>`) | skill | patch `<skill>` §`<section>` | `<sha>` | applied |
| 2 | weekly | … (session `<id>`: "…verbatim…") | memory | op add `<target>` | `<entry>` | applied |
| 3 | weekly | … | no-action | — | — | reason: … |
| 4 | weekly | hunch: … | cron | new job `<name>` | `<cron id>` | deferred: reason |
| 5 | weekly | `<skill>` found in `~/.hermes/skills/stable/` (Toolbox-owned) → issue/PR brief with sha256 diff instead of local edit | no-action (local) | `<issue id>` | reason: hash-parity guard | routed |

## Net-change summary (required)

```text
skills ±: <N> added, <M> removed, <K> superseded
memory entries ±: <X> net change
kg facts superseded: <Y> consolidated
```

## Collaborative (two-tick) — collaborative mode only

### Tick A output (collect)

- Self-contained digest: what happened, what was fixed, what is needed
- Lane-scoped perspective questions sent via `message_agent`:
  - [Q1] to `<role-a>`: "my side of `<event>`: … — what did you see / decide / drop on your side?"
  - [Q2] to `<role-b>`: …
- Outstanding asks left on the record (tick-A log path): `<path>` — replies expected within +24h

### Tick B output (consolidate, >= +24h after tick A)

| # | Original question | Reply source | Decision anchor |
|---|---|---|---|
| 1 | `<question text>` | `<role-a>/report.md line N` | `<issue/sha/json path>` |

- Perspective deltas (same event, two sides):
  - `<event>` — my side: "`<what I saw/decided/dropped>`" · `<role>`'s side: "`<their side>`" → delta: "`<the assumption only they could see>`" → folded into finding #`<n>`
- Conflicts (what actually happened): `<event>` — my account vs `<role>`'s — resolved against `<ground truth source>` → winner: `<side>`
- Team artifact: `<issue number / path in shared repo>` (both sides can verify)

## Follow-ups

- `<what to check next tick>` — trigger: `<condition or schedule>`
