# Changelog

## [0.2.1] - 2026-11-26 (This Release)

**New CLI with --dry-run support**
- Added `python -m aedifico weekly [--dry-run]` command for generating weekly reflection reports
- Safe preview mode (`-n`) prints report without writing files or calling external tools  
- Three evidence sources: polygraph results, completion metrics, communication analysis
- Errors propagate to stderr with exit code 1
- Environment variables for testing failures (see README)

---

## [0.2.0] — 2026-11-24

**Scope narrowing (Cards 2 & 3)**
- Aedifico now owns the **weekly and cross-agent** horizons. Turn/session horizons are explicitly declared as owned by the agent runtime's background review (`agent/background_review.py`) — scheduled runs skip them.
- Added **Aedifico Guard (hash parity)**: before any `skill_manage` of a stable skill, verify the target is the canonical copy; edits go through an issue/PR brief, never local direct-to-stable.

**MemChorus write path (Card 1)**
- Durable writes go through `memchorus_remember` (category-tagged); raw palace write tools marked **legacy** in the sources map.

**Collaborative protocol (Card 4)**
- Collaborative mode is now a **two-tick protocol, +24h apart**: tick A collects (independent loop first, self-contained digest, lane-scoped perspective questions); tick B consolidates (reconcile deltas against ground truth, land team artifacts in shared space). Cron template included.
- Report template gains a **net-change summary** (skills ±, memory ±, kg facts superseded) — a pass that only adds is journaling, not consolidation.

**Install guidance (Card 5)**
- **Removed the symlink install option.** Copy (`cp -r`) or `hermes skills install` is the required path, with a sha256 verification step documented.
- Backup/export procedure documented for copy installs.
- New: `examples/weekly-pass-2026-11-21.md` — a real independent pass, OPSEC-scrubbed, showing the full collection → consolidation loop.
- **Description expanded** with trigger phrases: reflect, retrospective, weekly, cross-agent.

## 0.1.0 — 2026-11-20

Initial public release. Independent + collaborative reflection loop, sources map, report template.
