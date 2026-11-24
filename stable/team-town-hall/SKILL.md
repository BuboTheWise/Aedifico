---
name: team-town-hall
description: "Structured team sync for process improvement, mentorship, and knowledge sharing with OPSEC sanitization."
version: 0.1.0
author: <profile-a>, <profile-b>, <profile-c>
metadata:
  hermes:
    tags: [team, collaboration, town-hall, OPSEC, mentorship, process-improvement]
    related_skills:
      - memchorus-memchorus-assessment
      - development-process
      - team-dev-process
---

# Team Town Hall (Dev Team)

A structured yet open-ended collaborative session for the dev team to review processes, share knowledge, align on standards, and foster cross-agent mentorship. This is **not** a status-reporting meeting; it's a working session for iterative improvement.

## 1. OPSEC Sanitization (Strict Gate)

Before *any* topic, code snippet, file path, or task is discussed, logged to Kanban, or saved to MemChorus:
- **Strip Secrets**: Remove all API keys, tokens, raw credentials, and private infrastructure details. Discuss concepts/roles instead of exact values.
- **Anonymize if Necessary**: If a bug or issue involves a client or sensitive project that must remain unmentioned by name, use "Project X" or an internal codename.
- **No Raw Config**: Never dump full config files or `.env` contents. Use redacted snippets only.
- **Data Integrity**: No PII (Personally Identifiable Information) in session logs.

**Sanitization Rule:** If it wouldn't be safe to paste into a public channel, do not put it into the team session log, Kanban, or MemPalace.

## 2. Agenda Kick-Off (Structured Mode)

Before opening the floor, set a shared agenda to prevent chaos and ensure high-value topics are covered:
1. **Process Review**: What broke in the dev workflow recently? (e.g., decomposition issues, silent failures).
2. **Knowledge Share**: One cool pattern, bug-fix technique, or tool usage from each agent's recent work.
3. **Standard Update**: Any new rules needed in `development-process` or `team-dev-process` (Toolbox)?
4. **Action Items**: Convert discussion points into Kanban tasks (using the atomic decomposition rules).

## 3. Open Forum (Community Mode)

After agenda items are addressed, transition to open-ended conversation:
- **Mentorship Pairing**: "Agent A found a better way to do X in Python—Agent B, try this pattern next time you work on [repo]."
- **Cross-Skill Exploration**: How can we use Skill Y in an unexpected way for Team Z?
- **Ad-hoc Debugging**: If a stuck issue comes up, the team huddles (concurrently or asynchronously) to find root causes.
- **Retrospectives**: Brief "what went well / what didn't" on recent releases or large tasks.

## 4. Persistence & Capture

Use **MemChorus** or **Kanban** to capture outcomes so the session isn't lost when it ends:
- **Decisions Made**: Log any new rules or process changes explicitly (e.g., "Card decomposition rule updated").
- **Action Items**: Create atomic tasks in Kanban for anything that requires follow-up.
- **Lessons Learned**: Save one-liners or short notes to MemChorus for future reference during audits or retros.

## 5. Facilitation Guide (For the Host)

If an agent is leading the Town Hall:
1. **Start with OPSEC reminder.**
2. **Post Agenda Items** in a dedicated task/thread or Kanban ticket `t-townhall-YYYYMMDD`.
3. **Timebox agenda items** so there's room for open forum.
4. **Summarize outcomes** before closing and attach the session log to the relevant project or team memory.
