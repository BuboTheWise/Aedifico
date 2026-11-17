# Toolbox — Importable Hermes Development Skills

Central repository for shared, versioned development skills used across Hermes Agent profiles.

## Purpose

Every skill in this repo follows [Hermes Agent skill authoring standards](https://hermes-agent.nousresearch.com/docs) and the team's **Development Workflow Procedure**. Skills are seeded here so all profiles can adopt a consistent, shared baseline rather than diverging independently.

## Directory Structure

```
stable/                     # All canonical, team-approved skills
  <skill-name>/
    SKILL.md                # Frontmatter + body per hermes-agent standards
LICENSE
README.md
```

Future additions will follow the same pattern (e.g., `stable/project-organization/SKILL.md`).

## How to Import a Skill

### Option A: Direct file copy

1. Copy the desired skill directory from this repo into your profile's skills tree:
   ```bash
   cp -r stable/<skill-name> ~/.hermes/profiles/<profile>/skills/<category>/<skill-name>/
   ```
2. The skill will be available on next Hermes session start.

### Option B: Git submodule (recommended for shared sync)

```bash
cd ~/.hermes/profiles/<profile>/skills/
git submodule add https://github.com/BuboTheWise/Toolbox.git toolbox
mkdir -p <category>
ln -s "$HOME/.hermes/profiles/<profile>/skills/toolbox/stable/<skill-name>" "<category>/<skill-name>"
```

### Option C: Load in-session

Once the skill is in your skills tree (Option A or B), load it by name in an active session:
```
skill_view(name='development-process')
```


## Source of Truth

This repo is the governing source for development-process skills. Where vault documentation diverges, this repo takes precedence.
## Current Skills

| Skill | Path | Description |
|-------|------|-------------|
| development-process | `stable/development-process/SKILL.md` | Development workflow with board layers, claim protocol, card types (RUN/FIX/spec), solo mode, QA separation, and OPSEC standards. |
| pr-comment-monitor | `stable/pr-comment-monitor/SKILL.md` | Scan third-party open PRs for review comments needing professional replies — score actionability patterns, generate draft responses, deliver daily via cron. No auto-posting. |
| mentorship | `stable/mentorship/SKILL.md` | Bidirectional teaching loop between heterogeneous local models: negotiate → accept (1:1) → distill → pull → hot recall → output-based graduation, with Truth-Enforcer guard and board-verifiable shared graduation state. |

## Contributing

Skills are seeded by consensus (per the team's Kanban process). To add a new skill:
1. Create it on a branch following SKILL.md authoring standards.
2. Open a PR; review against the `hermes-agent-skill-authoring` hardline requirements.
3. Merge to `main` after approval.

---

*First seed: 2026 — development-process (canonical development workflow).*
