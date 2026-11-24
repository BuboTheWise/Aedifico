---
name: team-health
description: 'Team health monitoring system — separates measurement from routing, uses shared evidence schema.'
version: 0.1.0
author: nyarlathotep
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [health, monitoring, automation, evidence]
    related_skills:
      - development-process
      - memchorus-pr-collab
---

# Team Health System

Lightweight health monitoring that separates measurement (health) from routing/coordination (a_edificio). One shared evidence record feeds both readers.

## Architecture Rules

1. **Separation of concerns:** Health emits evidence only. a_edificio reads evidence and routes work. No private scores.
2. **Phase gates:** A phase is not done until documented false-positive AND false-negative cases exist for every pillar.
3. **Auto-correction limits:** Health opens comments/cards only. Never modifies another profile's model, skills, or MemChorus config directly.
4. **Shared evidence schema:** All checks output `{profile, scope, check, result, time}` — no second scoreboard.

## Pillars (Phase 1)

| Pillar | Check Name | Verifies | Status Source |
|--------|-----------|----------|--------------|
| 1 | `memchorus-recall` | Actual recall injection in turns | Turn system prompt (not doctor-probe) |
| 2 | `polygraph-health` | Polygraph CLI usable, no blocked PRs | Polygraph results + repo state |
| 3 | `task-completion-rate` | % of tasks hitting completion gate | Kanban board evidence |
| 4 | `agent-communication` | Cross-agent DM delivery success rate | `message_agent` delivery results in profile `state.db` |

## Evidence Schema

See `health-rules.json` for complete schema. Each pillar outputs JSON matching:

```json
{
  "profile": "<agent profile name>",
  "scope": "<check scope tag>",
  "check": "<check identifier>",
  "result": {"status": "green|yellow|red", "details": "..."},
  "time": "ISO-8601 timestamp"
}
```

## Pillar 1 — `memchorus-recall` (implemented)

**Recipe:**

```bash
python3 team-health/scripts/check_recall.py --profile <name>   # single profile
python3 team-health/scripts/check_recall.py --all --pretty --out <file>
```

**How it verifies (content-first, per #312):**
1. Collects the last N (default 3) captured turns from `request_dump_*.json` under the profile's `~/.hermes/<profiles>/<name>/sessions/` (or `~/.hermes/sessions/` for `default`). Dumps are API-failure captures — the only on-disk copy of a turn's real prompt.
2. Searches turn text for CONTENT markers: `[MemChorus injected context]` / `<!-- memchorus:recalled -->` (recall actually landed). The WRAPPER `[MemChorus Memory Recall]` alone means block-present-but-no-content — the #312 false-positive class, NOT a landing.
3. Runs `memchorus-doctor` (stdout parsed, NOT exit code) as contrast signal only. `inprocess_interpreter` is the #312 root-cause probe.

**Verdicts:**
- **GREEN** — content marker in ≥1 of the last N captured turns, landing within the freshness window (`--max-landing-age-hours`, default 72h).
- **YELLOW** — (a) #312 signature: probe green but no content landed; or (b) content landed but the newest landing is older than the freshness window (stale evidence cannot verify current recall state).
- **RED** — no content in the last N captured turns AND probe red/unknown; or zero captured turns with probe red.

**Documented misses (phase gate, live evidence from 2026-11-22 run, `evidence/recall-run-20261122.json`):**
- **False positive — `default` profile:** check initially went GREEN on a landing from 2026-11-03 (461h / 19 days old) while the profile had zero captured turns since. A green verdict built on 19-day-old evidence asserts a current recall state that is unverified — the check said green, but no work in the last 19 days actually used that recall. **Miss → check change:** freshness window added (`--max-landing-age-hours`, default 72h); `default` now downgrades to YELLOW (stale evidence) instead of GREEN.
- **False negative — `cthugha` profile:** check says RED (no content in last 3 captured turns; newest captured turn 2026-11-18, probe `inprocess_interpreter` red) while the cthugha session of 2026-11-22 is actively receiving an injected `[MemChorus injected context]` block in its turn prompt (visible in-session). The work is succeeding with recall; the check misses it because request dumps are only written on API-failure paths, so healthy turns never produce evidence, and the probe red reflects the gateway/tools interpreter (which cannot import memchorus) rather than the interpreter actually serving the session (install-env venv, where `import memchorus` succeeds). **Miss → check change (next):** add a second, live evidence source — an active in-process probe that executes the hook's `on_pre_llm_call` under the profile's actual Python and asserts non-empty `context_items`, so GREEN can be verified without waiting for an API failure. Until then, RED verdicts for profiles with an active session should be read as "no captured evidence of landing" rather than "recall is dead".

## Pillar 2 — `polygraph-health` (implemented)

**Recipe:**

```bash
python3 team-health/scripts/check_polygraph.py
python3 team-health/scripts/check_polygraph.py --polygraph-repo <path> --github-repo <owner/repo>
```

**How it verifies (two probes, combined):**
1. **CLI usability** — runs `python3 scripts/run_polygraph.py --help` inside the Polygraph repo and captures the real exit code. Non-zero (missing dependency, entrypoint crash) → RED.
2. **Blocker scan** — lists OPEN issues on the GitHub repo and classifies each: P0 (CLI cannot start/parse — import/startup failure, entrypoint crash), P1 (CLI runs but result wrong/unusable-in-context — hardcoded model, OPSEC/hardcoded home paths), P2 (non-blocking). `critical_issues` = P0 + P1 count.
3. **Stale-issue cross-reference** — P0 import failures are checked against the live `--help` probe; if the described failure no longer reproduces, the issue is flagged `reproduces: false` in evidence.

**Verdicts:**
- **GREEN** — CLI `--help` exit 0 AND no open P0/P1 issues.
- **YELLOW** — CLI `--help` exit 0 BUT ≥1 open P0/P1 issue (tooling partially blocked).
- **RED** — CLI `--help` exit != 0 (CLI not usable at all).

**Documented misses (phase gate, live evidence from 2026-11-22 run, `evidence/polygraph-run-20261122.json`):**
- **False positive — `cthugha`:** `--help` returns exit 0 (would be green for the usability probe) but a real run `--tests 1A --base-url http://127.0.0.1:9 --no-tools` fails: `1A ERROR — All connection attempts failed`, Overall Grade FAIL, exit 1. `--help` proves importability + arg-parsing only, NOT that the tool produces a verified result. **Miss → check change:** a green `--help` is treated as necessary but not sufficient — the verdict pairs the usability probe with the blocker scan and records `cli_import_error`, and actual verification still requires exercising the model endpoint.
- **False negative — `cthugha`:** issue #12 (P0, startup import failure on a missing local package) is OPEN so the blocker scan flags YELLOW, but the current code no longer imports that package and `--help` returns exit 0 from every context (repo root, neutral cwd, nyarlathotep skill dir) — the failure no longer reproduces. A stale open issue over-penalises a tool that works. **Miss → check change (next):** the check records `reproduces: false` on P0 import issues whose described failure the live `--help` probe does not show, so the stale issue is visible in evidence rather than silently over-penalising; such issues should be closed or re-scoped rather than left to keep the tool yellow.

## Pillar 3 — `task-completion-rate` (implemented)

**Recipe:**

```bash
python3 team-health/scripts/check_completion.py
python3 team-health/scripts/check_completion.py --limit 50 --kanban-db <path>
```

**How it verifies (board evidence, not UI):**
1. Opens the shared kanban SQLite store (`~/.hermes/kanban.db` — the same rows the `kanban_list`/`kanban_show` tools read) **read-only** (`mode=ro`); never mutates task data.
2. Takes the last N (default 20) tasks with `status='done'`, most-recent first.
3. A task is **clean** iff (a) zero `blocked` events in `task_events` (the board's record of a `blocked` or `needs_input` status change — covers dependency/needs_input/capability/transient) AND (b) every row in `task_runs` has a successful outcome (`completed`, `review_requested`). Any `blocked`/`crashed`/`timed_out`/`spawn_failed`/`gave_up`/`reclaimed`/`changes_requested` run counts as rework.
4. `completion_rate` = clean / total.

**Verdicts:**
- **GREEN** — completion rate > 80%.
- **YELLOW** — 60–80% rate, OR fewer than 10 tasks in the window (insufficient data).
- **RED** — < 60% rate.

**Documented misses (phase gate, live evidence from 2026-11-22 run, `evidence/completion-run-20261122.json`):**
- **False positive — cthugha:** t_caa89f9b ("wing_isolation: accept `{PROFILE}_{CATEGORY}` as NATIVE for owning profile") shows ONE `completed` run and zero blocked events — a clean completion by this measure — yet issue #304 still required two later [FIX] tasks (t_f360c2e8, t_468a6223, "Fix wing_isolation flags owning-profile wings as foreign") because the delivered code was wrong. Same pattern: t_448d9258 (qa+merge #306, clean) was followed by t_b794de90 ("#308 follow-up: platform guards for 2 Windows test artifacts"). **Miss → reading rule:** a clean run history proves the *gate* passed, not that the *work* was right; a green rate must be read alongside the follow-up-fix density on the same issues (the per-task breakdown in `_evidence.tasks` makes the clean set auditable).
- **False negative — cthugha:** t_c4232521 ("memchorus-recall retrieve: flat-file fallback") ran 3× crashed (2× "owner admission settled failed", 1× worker exited without a lifecycle call) before one successful `completed` run. This check counts it as rework (correct — the cost is real), but the deliverable landed and the work succeeded; the verdict is a delayed-success penalty, not a failed task. t_fd00e142 (blocked on a behavioral guard, then completed) is the same class. **Miss → check change (next):** distinguish transient-infrastructure rework (`crashed`/`reclaimed`/`timed_out`) from work-content rework (`blocked`/`changes_requested`) in metrics so a green rate is not silently eroded by spawn flakiness.

**Live run 2026-11-22 (verification):** 16/20 clean (80.0%) → **YELLOW** (60–80 band). Penalised: t_718c1bc1 (blocked event), t_fd00e142 (blocked + rework run), t_c4232521 (3 crashed runs), t_db91c30e (1 crashed run). Edge cases verified on a scratch copy of the DB: 15% → RED; 5-task window → YELLOW insufficient data; missing DB → exit 1.

## Pillar 4 — `agent-communication` (implemented)

**Recipe:**

```bash
python3 team-health/scripts/check_communication.py
python3 team-health/scripts/check_communication.py --window-days 7 --pretty
```

**How it verifies (transcript evidence, not gateway status):**
1. Opens every local profile's `state.db` (`~/.hermes/profiles/<name>/state.db`, plus the shared `~/.hermes/state.db`) **read-only** (`mode=ro`); never mutates the transcripts.
2. Selects every `message_agent` tool row (one DM attempt) inside the window (default 30d). The unit of measurement is one tool **call**: rows are grouped by `tool_call_id` and the best-classified row wins, because the harness stores two rows per call (a `[message_agent] …` truncated summary plus the real delivery result) — attempts are not double-counted.
3. Classifies each call from the delivery-result JSON: **delivered** = `status` in {queued,settled,delivered,ok,success} and no error/reason (accepted by the gateway); **failed** = `error` present (with or without a delivery_id, e.g. `reason:"unknown"`), or `status`/`reason` in a known-failure set (`runtime_unavailable` "NOT sent", `ambiguous` "admission could not be confirmed"); **unknown** = anything else (kept in the total, lowers the rate conservatively).
4. `delivery_rate` = delivered / total. Cross-checks the `hermes-dm-*` outbox under `~/.hermes/cache/scratch/` for currently-stuck/stale DMs — the outbox is corroborating, real-time "stuck now" evidence (a settled DM is unlinked on settle), **not** the rate source.

**Verdicts:**
- **GREEN** — delivery rate > 95%.
- **YELLOW** — 80–95% rate, OR fewer than 10 DMs in the window (insufficient data).
- **RED** — < 80% rate.

**Documented misses (phase gate, live evidence from 2026-11-22 run, `evidence/communication-run-20261122.json`):**
- **False positive — cthugha→bubo:** a DM (delivery_id `31725c02…`) shows `status:queued` — accepted by the gateway, so counted as *delivered* — yet the DM body is absent from bubo's transcript, i.e. it was dropped before bubo ever read it. "Delivered" = *accepted/queued by the gateway*, NOT *consumed by the recipient*. **Miss → reading rule:** accepted/queued is not proof the recipient received it; an accepted DM can still be a true drop that the rate alone cannot see (recipient-side absence, as here).
- **False negative — cthugha→nyarlathotep:** a DM (delivery_id `ca57dda5…`) is marked `status:ambiguous` ("admission could not be confirmed" — classified as a *failure*), yet the recipient actually processed it: nyarlathotep's transcript shows the DM body plus a disposition decision on its content. An ambiguous admission is not necessarily a drop; the recipient may still be consuming it. **Miss → reading rule:** `ambiguous`/`failed` means "admission not confirmed", not "definitely dropped" — where the recipient transcript shows consumption, the failure verdict is a false negative.
- **Miss → check change (made this run):** the first implementation filtered `content LIKE '%delivery_id%'`, which missed 14 failed DMs (error-only results carrying no delivery_id) and double-counted successes stored across two rows — reporting 93.4% (18 failures) instead of the true 88.3% (28 failures). Fixed by grouping on `tool_call_id` and including error-only rows; both were false negatives of the original query (the check under-counted failures).

**Live run 2026-11-22 (verification):** 212/240 DMs delivered (88.3%) → **YELLOW** (80–95 band). Failure modes: ambiguous x9, runtime_unavailable x5, reason=unknown x14. Outbox stuck=1, stale=0. Edge cases verified: 1d window → 4 DMs < 10 → YELLOW (insufficient data); missing `--scratch-dir` → outbox 0, rate still computed; missing `--profiles-dir` → 0 DMs → YELLOW (no records); `--no-shared` → rate still computed.

## Phase Gate Requirement

Before advancing Phase N to N+1:
- Document at least one false-positive (check said green, work failed)
- Document at least one false-negative (check said red/yellow, work succeeded)
- The miss becomes the next change to the check, not a chat note

## Pitfalls

- Doctor-probe status ≠ actual recall injection (#312 constraint)
- No silent config edits — auto-correction = new card
- Don't stack Phase N+1 without Phase N's documented misses
- Evidence schema must be reusable across all checks
