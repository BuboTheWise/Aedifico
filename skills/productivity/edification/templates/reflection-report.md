# Reflection — <agent-role> — <date> — <mode: independent | collaborative>

## Scope & detected tiers

- Horizons: turn, session, weekly [ , cross-agent]
- Window: <e.g. 2026-11-01 → 2026-11-08>
- Tiers — MemChorus: present | absent · Bot-Mode: present | absent · Cron: present | absent

## Findings → artifacts

| # | Horizon | Finding (anchored) | Bucket | Artifact | Handle | Status |
|---|---|---|---|---|---|---|
| 1 | session | … (session `<id>`: "…verbatim…") | skill | patch `<skill>` §`<section>` | `<sha>` | applied |
| 2 | weekly | … (sessions `<id1>`, `<id2>`) | memory | op add `<target>` | `<entry>` | applied |
| 3 | turn | … | no-action | — | — | reason: … |
| 4 | weekly | hunch: … | cron | new job `<name>` | `<cron id>` | deferred: reason |

## Collaborative (only in collaborative mode)

- Participants: `<roster roles>`
- Perspective deltas (same event, two sides):
  - `<event>` — my side: "`<what I saw/decided/dropped>`" · `<role>`'s side: "`<their side>`" → delta: "`<the assumption only they could see>`" → folded into finding #`<n>`
- Conflicts (what actually happened): `<event>` — my account vs `<role>`'s — resolved against `<ground truth source>` → winner: `<side>`
- Team artifact: `<issue number / path in shared repo>`

## Follow-ups

- `<what to check next tick>` — trigger: `<condition or schedule>`
