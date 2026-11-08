# Sources Map — Hermes + MemChorus

Tool-level source map for the edification loop. Detection-first: confirm a tier is present before reading from it.

## Detection

| Tier | Probe | Present when | Absent behavior |
|---|---|---|---|
| Hermes core | `memory`, `skills_list`, `read_file`/`search_files` in tool list | always, on any Hermes agent | (floor — cannot be absent) |
| Session recall | `session_search` in tool list, else load via `tool_search(queries=["session history"])` | history tier available | session/weekly horizon degrades to hunches (thin evidence) — label, never block |
| Cron | `cronjob_manage` in tool list or via `tool_search` | scheduled-work tier active | skip scheduled-work review |
| MemChorus | `tool_search(queries=["mempalace diary"])` returns `mcp__mempalace__*` tools | durable-memory tier active | `memory` + session recall (or hunch fallback) only |
| Bot-Mode | `message_agent` in tool list + non-empty roster | collaborative mode available | handoff doc in shared space |

## MemChorus tools (mempalace MCP)

| Tool | Use in the loop |
|---|---|
| `mcp__mempalace__mempalace_status` | sanity check the palace is reachable before relying on it |
| `mcp__mempalace__mempalace_diary_read` | recent AAAK diary entries — the episodic layer between sessions |
| `mcp__mempalace__mempalace_diary_write` | file session-end reflections that are episodic, not procedural |
| `mcp__mempalace__mempalace_kg_query` | entity relationships — find what a topic touches |
| `mcp__mempalace__mempalace_kg_timeline` | chronological facts — detect what changed and what is stale |
| `mcp__mempalace__mempalace_kg_invalidate` / `mcp__mempalace__mempalace_kg_supersede` | artifacts: retire contradicted facts, replace at a boundary |
| `mcp__mempalace__mempalace_search` | cross-session recall for a specific finding's evidence |
| `mcp__mempalace__mempalace_list_drawers` / `mcp__mempalace__mempalace_get_drawer` | check for unfiled or orphaned drawers (sediment) |
| `mcp__mempalace__mempalace_add_drawer` | file a durable fact verbatim when it does not fit kg/memory |
| `mcp__mempalace__mempalace_checkpoint` | one-call session capture at the end of a long session |
| `mcp__mempalace__mempalace_check_duplicate` | before filing anything new — avoid duplicate drawers |

**Placement rules (MemChorus vs memory vs skill):**

- Stable, cross-session, every-turn-relevant fact → `memory` (tight budget) **and** MemChorus when present (MemChorus is the deep copy; memory is the hot copy).
- Episodic, session-bound detail → MemChorus drawer/diary.
- Procedure or workflow → skill. Never file a procedure in MemChorus or memory expecting it to load at the right moment.

## session_search patterns

Only when `session_search` is available (in the tool list, or loadable via `tool_search`). On an install where it is absent (e.g. some laptop profiles), the session/weekly horizon yields hunches — label them as thin evidence and do not block the pass.

- Corrections: `session_search(query="'no' | 'not that' | 'actually'", session_id=...)` — user pushbacks are the highest-signal findings.
- Failures: `session_search(query="error | failed | blocked", session_id=...)`.
- Repetition: same command/fix appearing in 2+ sessions → skill-patch candidate.
- Scroll inside a session to recover the exact exchange before quoting it as an anchor.

## Good vs bad findings

| Bad | Why | Good |
|---|---|---|
| "I should be more careful with quoting." | no anchor, no bucket, uncheckable | "session `<id>`: 3 retries of the same heredoc quoting failure → patch `terminal` skill §quoting (anchor: turn quote + skill section)." |
| "Maybe cron would help." | no trigger defined | "weekly horizon: 4 manual T7 syncs in 10 days → cron `sync-bubo-repos` every Fri 18:00 (handle: cron id)." |
| "The team should coordinate better." | no lane, no artifact | "collab: 2 handoffs lost to queued acks → decision doc §handoff in shared repo (handle: issue #)." |

## Anchors — acceptable forms

- session id + verbatim quote of the exchange
- commit sha + file + line
- issue/PR number
- MemChorus drawer id / diary entry id / kg fact id
- cron job id
- path in a shared repo
